import logging
import requests
import time

from datetime import datetime
from copy import copy
from multiprocessing import Process
from functools import wraps

from flask import request
from flask_caching import Cache
from pymongo import MongoClient
from elasticsearch import Elasticsearch

from logstash_async.handler import AsynchronousLogstashHandler


def initialize_kibana():
    """
    Creating a daemon process to initialize kibana with two index pattern so that they don't have to be
    manually added by the user when entering kibana for the first time.
    """
    def poll_kibana_index_pattern():
        """
        We are polling for 5 minutes for kibana to be up so that the requests and logging index 
        pattern can be created.
        Tasks such as this could be more scalable done using Celery.
        """

        indices = ["requests", "logging", "container_logs"]
        tries = 30
        while indices and tries > 0:
            for index in indices:
                payload = {"attributes": {"title": index, "timeFieldName": "@timestamp"}}
                try:
                    res = requests.post("http://kibana:5601/api/saved_objects/index-pattern/{}".format(index), json=payload, headers={"kbn-xsrf": "true"}, verify=False)
                    if res.status_code == 200:
                        indices.remove(index)
                    else:
                        time.sleep(10)
                        tries -= 1
                except Exception as e:
                    time.sleep(10)
                    tries -= 1
                    continue

    proc = Process(target=poll_kibana_index_pattern)
    proc.daemon = True
    proc.start()

def get_data_from_request():
    """
    Extract the content from the POST request
    """

    if request.method == 'POST':
        if request.environ['CONTENT_TYPE'] == "application/json":
            data = request.json
        else:
            data = request.form
        return data

def make_cache_key(*args, **kwargs):
    """
    Compute the cache hash based not only on the request path,
    but also on the contents of the request.
    """
    data = get_data_from_request()
    cache_key_hash = hash(request.path + str(data) + str(request.args))
    return str(cache_key_hash)

def filter_request(req):
    """
    Extract request attributes from the request metadata
    """

    res = {'path': req['environ']['PATH_INFO'],
           'method': req['environ']['REQUEST_METHOD'],
           'user-agent': req['environ']['HTTP_USER_AGENT'],
           'remote_addr': req['environ']['REMOTE_ADDR'],
           'remote_port': req['environ']['REMOTE_PORT']
           }
    if req['environ'].get('CONTENT_TYPE'):
        res['content_type'] = req['environ']['CONTENT_TYPE']
    return res

def get_redis_cache(app):
    cache = Cache(app, config={'CACHE_TYPE': 'redis',
                               'CACHE_DEFAULT_TIMEOUT': 60,
                               'CACHE_REDIS_HOST': 'redis',
                               'CACHE_REDIS_PORT': '6379',
                               'CACHE_REDIS_URL': 'redis://redis:6379'}
                  )
    return cache

def get_logger(name):
    logger = logging.getLogger(name)
    logger.setLevel(logging.DEBUG)

    async_handler = AsynchronousLogstashHandler('logstash', 5000, database_path=None)
    console_handler = logging.StreamHandler()
    formatter = logging.Formatter('%(asctime)s - %(module)s:%(lineno)d - %(levelname)s - %(message)s')
    console_handler.setFormatter(formatter)
    console_handler.setLevel(logging.DEBUG)

    logger.addHandler(async_handler)
    logger.addHandler(console_handler)
    return logger


mongo_client = MongoClient("mongo", 27017)
mongo_db = mongo_client["micromath"]
request_collection = mongo_db["requests"]

logger = get_logger('logstash-logger')
es_client = Elasticsearch(hosts=[{"host": "elasticsearch", "port": 9200}])

def logging_request(func):
    @wraps(func)
    def inner(*args, **kwargs):
        req_log = filter_request(request.__dict__)
        req_log['data'] = get_data_from_request()

        before_func = time.time()
        res = func(*args, **kwargs)
        req_log['took'] = "{:.3f}s".format(time.time()-before_func)
        req_log['@timestamp'] = datetime.now().isoformat()
        if isinstance(res, dict):
            req_log.update(res)
        else:
            req_log['result'] = None

        # mongodb changes the req_log after it has been inserted
        es_log = copy(req_log)
        request_collection.insert_one(req_log)
        es_client.index(index="requests", body=es_log)
        logger.debug("Received request on path: {}".format(req_log['path']))

        return res
    return inner
