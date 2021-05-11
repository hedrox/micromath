from typing import Dict
from functools import lru_cache

from flask import Flask, request, jsonify

from config import JSONIFY_PRETTYPRINT_REGULAR, FLASK_SECRET_KEY, FLASK_NAME
from utils import validate_input, get_logger

app = Flask(FLASK_NAME)
app.config.from_mapping(
    SECRET_KEY=FLASK_SECRET_KEY,
    JSONIFY_PRETTYPRINT_REGULAR=JSONIFY_PRETTYPRINT_REGULAR
)

logger = get_logger('logstash-logger')


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
    else:
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

@lru_cache(maxsize=None)
def fib(n):
    """
    Recursively compute the fibonacci sequence
    """
    if n<=1:
        return n
    else:
        return fib(n-1)+fib(n-2)

def compute_fibonacci(number):
    res = 0
    for no in range(number):
        res = fib(no)
    return res


@app.route('/api/<version>/fibonacci', methods=['POST'])
def fibonacci(version:str) -> Dict:
    """
    Endpoint that computes the fibonacci sequence.

    Parameters
    ----------
    version : str
        version of the API to identify the correct fibonacci endpoint

    Returns
    -------
    dict
        a dict containing either the result or error key set depending on the situation
    """

    if version == "v1":
        if request.environ['CONTENT_TYPE'] == "application/json":
            data = request.json
        elif request.form:
            data = request.form

        try:
            validate_input(data)
        except Exception as e:
            logger.exception(e)
            raise

        res = compute_fibonacci(data['number'])
        if res:
            return {"result": str(res), "error": None}
        return {"result": None, "error": "Fibonacci function failed"}
    else:
        return ({"result": None, "error": f"API version {version} not found"}, 404)


if __name__ == "__main__":
    app.run()
