import os

from flask import Flask
from flask import request
from jsonschema import validate


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

def fib(n):
    if n<=1:
        return n
    else:
        return fib(n-1)+fib(n-2)


@app.route('/api/<version>/fibonacci', methods=['POST'])
def fibonacci(version):
    if version == "v1":
        if request.environ['CONTENT_TYPE'] == "application/json":
            data = request.json
        elif request.form:
            data = request.form

        validate(data, schema=schema)
        res = fib(data['number'])
        if res:
            return {"result": res, "error": None}
        return {"result": None, "error": "Fibonacci function failed"}
    else:
        return {"result": None, "error": f"API version {version} not found"}


if __name__ == "__main__":
    app.run()
