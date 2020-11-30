import os

from flask import Flask
from flask import request
from math import factorial
from jsonschema import validate


schema = {
    "type": "object",
    "properties": {
        "number": {"type": "number"}
    },
    "required": ["number"]
}


flask_name = "factorial_server"
FLASK_SECRET_KEY = open('flask_secret_key').read()

app = Flask(flask_name)
app.config.from_mapping(SECRET_KEY=FLASK_SECRET_KEY)

@app.route('/api/<version>/factorial', methods=['POST'])
def post_factorial(version):
    if version == "v1":
        if request.environ['CONTENT_TYPE'] == "application/json":
            data = request.json
        elif request.form:
            data = request.form

        validate(data, schema=schema)
        res = factorial(data['number'])
        return {"result": res, "error": None}
    else:
        return {"result": None, "error": f"API version {version} not found"}


if __name__ == "__main__":
    app.run()
