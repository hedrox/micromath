import os
import flask_login
import requests
import time
import json
import logging

from flask import Flask
from flask import request, jsonify
from flask_caching import Cache

from elasticsearch import Elasticsearch
from pymongo import MongoClient

from functools import wraps
from copy import copy
from datetime import datetime
from logstash_async.handler import AsynchronousLogstashHandler
from utils import initialize_kibana


logger = logging.getLogger('logstash-logger')
logger.setLevel(logging.DEBUG)

async_handler = AsynchronousLogstashHandler('logstash', 5000, database_path=None)
console_handler = logging.StreamHandler()
console_handler.setLevel(logging.DEBUG)

logger.addHandler(async_handler)
logger.addHandler(console_handler)

flask_name = "controller_server"
FLASK_SECRET_KEY = open('flask_secret_key').read()

app = Flask(flask_name)
app.config.from_mapping(
    SECRET_KEY=FLASK_SECRET_KEY,
    JSONIFY_PRETTYPRINT_REGULAR=True
)

cache = Cache(app, config={'CACHE_TYPE': 'redis',
                           'CACHE_DEFAULT_TIMEOUT': 60,
                           'CACHE_REDIS_HOST': 'redis',
                           'CACHE_REDIS_PORT': '6379',
                           'CACHE_REDIS_URL': 'redis://redis:6379'})

es_client = Elasticsearch(hosts=[{"host": "elasticsearch", "port": 9200}])
initialize_kibana()

mongo_client = MongoClient("mongo", 27017)
mongo_db = mongo_client["micromath"]
request_collection = mongo_db["requests"]

users_collection = mongo_db["users"]
users_collection.insert_one({'email': 'null@null.com', 'username': 'null', 'password': 'null'})

login_manager = flask_login.LoginManager(app)
class User(flask_login.UserMixin):
    """
    User object used by the flask login to store and validate credentials
    """
    pass

def get_user_from_db(username:str):
    """
    Search the username in mongodb
    """
    user = list(users_collection.find({"username": username}))
    if user:
        return user

@login_manager.user_loader
def user_loader(username):
    _user = get_user_from_db(username)
    if not _user:
        return

    user = User()
    user.id = username
    user.email = _user[0]['email']
    return user


@login_manager.request_loader
def request_loader(request):
    username = request.form.get('username')
    _user = get_user_from_db(username)
    if not _user:
        return

    user = User()
    user.id = username
    user.email = _user[0]['email']

    # Do this comparison better
    user.is_authenticated = request.form['password'] == _user[0]['password']
    return user


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'GET':
        return '''
               <form action='login' method='POST'>
                <input type='text' name='username' id='username' placeholder='username'/>
                <input type='password' name='password' id='password' placeholder='password'/>
                <input type='submit' name='submit'/>
               </form>
               '''

    username = request.form['username']
    logger.info(f"Requested login for user {username}")

    user = get_user_from_db(username)
    if not user:
        logger.info(f"User {username} not found in db")
        return {'result': None, 'error': 'User not in db'}

    if request.form['password'] == user[0]['password']:
        user = User()
        user.id = username
        flask_login.login_user(user)
        logger.info(f"Login successful for user {username}")
        return {'result': f'User {username} logged in', 'error': None}

    logger.info(f"Login failed for user: {username}")
    return {'result': None, 'error': 'Bad login'}


@app.route('/logout')
def logout():
    flask_login.logout_user()
    logger.info(f"User {username} logged out")
    return {'result': 'Logged out', 'error': None}


@login_manager.unauthorized_handler
def unauthorized_handler():
    logger.warning("Unauthorized access")
    return {'result': None, 'error': 'Unauthorized'}


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


@app.errorhandler(Exception)
def internal_error(error):
    response = error.get_response()
    response.data = json.dumps({"code": error.code,
                                "name": error.name,
                                "description": error.description
                                })
    response.content_type = "application/json"
    return response

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


@app.route('/api/<version>/pow', methods=['POST'])
@flask_login.login_required
@logging_request
@cache.cached(timeout=600, key_prefix=make_cache_key)
def power(version:str):
    if version == "v1":
        data = get_data_from_request()
        res = requests.post(f"http://pow:8081/api/{version}/pow", json=data)
        if res.status_code == 200:
            return res.json()


@app.route('/api/<version>/fibonacci', methods=['POST'])
@flask_login.login_required
@logging_request
@cache.cached(timeout=600, key_prefix=make_cache_key)
def fibonacci(version:str):
    if version == "v1":
        data = get_data_from_request()
        res = requests.post(f"http://fibonacci:8082/api/{version}/fibonacci", json=data)
        if res.status_code == 200:
            return res.json()


@app.route('/api/<version>/factorial', methods=['POST'])
@flask_login.login_required
@logging_request
@cache.cached(timeout=600, key_prefix=make_cache_key)
def factorial(version:str):
    if version == "v1":
        data = get_data_from_request()
        res = requests.post(f"http://factorial:8083/api/{version}/factorial", json=data)
        if res.status_code == 200:
            return res.json()


@app.route('/api/<version>/logs', methods=['GET'])
@flask_login.login_required
@logging_request
@cache.cached(timeout=30)
def get_logs(version:str):
    if version == "v1":
        logged_requests = list(request_collection.find())
        for req in logged_requests:
            req['_id'] = str(req['_id'])

        return jsonify(logged_requests)


if __name__ == "__main__":
    app.run()
