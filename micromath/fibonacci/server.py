import os
import logging

from flask import Flask
from flask import request
from jsonschema import validate
from logstash_async.handler import AsynchronousLogstashHandler

from typing import Dict

schema = {
    "type": "object",
    "properties": {
        "number": {"type": "number"}
    },
    "required": ["number"]
}


flask_name = "fibonacci_server"
FLASK_SECRET_KEY = open('flask_secret_key').read()

app = Flask(flask_name)
app.config.from_mapping(
    SECRET_KEY=FLASK_SECRET_KEY
)

logger = logging.getLogger('logstash-logger')
logger.setLevel(logging.DEBUG)

async_handler = AsynchronousLogstashHandler('logstash', 5000, database_path=None)
console_handler = logging.StreamHandler()
console_handler.setLevel(logging.DEBUG)

logger.addHandler(async_handler)
logger.addHandler(console_handler)


@app.errorhandler(Exception)
def internal_error(error):
    if hasattr(error, 'get_response'):
        # In case a exception that inherits from werkzeug.exceptions.HTTPException is received
        original_error = getattr(error, "original_exception", None)
        reponse = {
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


def fib(n):
    """
    Recursively compute the fibonacci sequence
    """
    if n<=1:
        return n
    else:
        return fib(n-1)+fib(n-2)


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
            validate(data, schema=schema)
        except Exception as e:
            logger.exception(e)
            raise

        res = fib(data['number'])
        if res:
            return {"result": res, "error": None}
        return {"result": None, "error": "Fibonacci function failed"}
    else:
        return ({"result": None, "error": f"API version {version} not found"}, 404)


if __name__ == "__main__":
    app.run()
