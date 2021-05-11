import requests

from flask import Flask
from flask import request, jsonify

from pymongo import MongoClient

from utils import initialize_kibana, logging_request, get_data_from_request, \
    make_cache_key, get_redis_cache, get_logger
from config import MONGO_DEFAULT_PAGE_SIZE, JSONIFY_PRETTYPRINT_REGULAR, \
    FLASK_SECRET_KEY, FLASK_NAME


logger = get_logger('logstash-logger')

app = Flask(FLASK_NAME)
app.config.from_mapping(
    SECRET_KEY=FLASK_SECRET_KEY,
    JSONIFY_PRETTYPRINT_REGULAR=JSONIFY_PRETTYPRINT_REGULAR
)

cache = get_redis_cache(app)
initialize_kibana()

mongo_client = MongoClient("mongo", 27017)
mongo_db = mongo_client["micromath"]
request_collection = mongo_db["requests"]


@app.errorhandler(Exception)
def internal_error(error):
    if hasattr(error, 'get_response'):
        # In case a exception that inherits from werkzeug.exceptions.HTTPException is received
        original_error = getattr(error, "original_exception", None)
        response = {
            "result": None,
            "error": {
                "code": error.code,
                "name": error.name,
                "description": original_error or error.description
            }
        }
        return jsonify(response), error.code

    # In case a normal Python exception is caught
    response = {
        "result": None,
        "error": {
            "code": 500,
            "name": type(error).__name__,
            "description": str(error)
        }
    }
    return jsonify(response), 500


@app.route('/api/<version>/pow', methods=['POST'])
@logging_request
@cache.cached(timeout=600, key_prefix=make_cache_key)
def power(version: str):
    if version == "v1":
        data = get_data_from_request()
        res = requests.post(f"http://pow:8081/api/{version}/pow", json=data)
        if res.status_code == 200:
            return res.json()
        return (res.text, res.status_code)
    return ({"result": None, "error": f"API version {version} not found"}, 404)


@app.route('/api/<version>/fibonacci', methods=['POST'])
@logging_request
@cache.cached(timeout=600, key_prefix=make_cache_key)
def fibonacci(version: str):
    if version == "v1":
        data = get_data_from_request()
        res = requests.post(f"http://fibonacci:8082/api/{version}/fibonacci", json=data)
        if res.status_code == 200:
            return res.json()
        return (res.text, res.status_code)
    return ({"result": None, "error": f"API version {version} not found"}, 404)


@app.route('/api/<version>/factorial', methods=['POST'])
@logging_request
@cache.cached(timeout=600, key_prefix=make_cache_key)
def factorial(version: str):
    if version == "v1":
        data = get_data_from_request()
        res = requests.post(f"http://factorial:8083/api/{version}/factorial", json=data)
        if res.status_code == 200:
            return res.json()
        return (res.text,res.status_code)
    return ({"result": None, "error": f"API version {version} not found"}, 404)


@app.route('/api/<version>/logs', methods=['GET'])
@logging_request
def get_logs(version: str):
    if version == "v1":
        # Pagination
        page_no = request.args.get('page')
        if page_no:
            skip = MONGO_DEFAULT_PAGE_SIZE * (int(page_no)-1)
            logged_requests = list(request_collection.find().skip(skip).limit(MONGO_DEFAULT_PAGE_SIZE))
        else:
            logged_requests = list(request_collection.find())
        for req in logged_requests:
            req['_id'] = str(req['_id'])

        return jsonify(logged_requests)
    return ({"result": None, "error": f"API version {version} not found"}, 404)


if __name__ == "__main__":
    app.run()
