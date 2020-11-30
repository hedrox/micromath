import os
import math
import time

from flask import Flask
from flask import request, jsonify
from jsonschema import validate


schema = {
    "type": "object",
    "properties": {
        "base": {"type": "number"},
        "power": {"type": "number"},
    },
    "required": ["base", "power"]
}

flask_name = "pow_server"
FLASK_SECRET_KEY = open('flask_secret_key').read()

app = Flask(flask_name)
app.config.from_mapping(
    SECRET_KEY=FLASK_SECRET_KEY
)

@app.route('/api/<version>/pow', methods=['POST'])
def power(version):
    if version == "v1":
        if request.environ['CONTENT_TYPE'] == "application/json":
            data = request.json
        elif request.form:
            data = request.form

        # this error should be handled
        validate(data, schema=schema)

        res = math.pow(data['base'], data['power'])
        return {"result": res, "error": None}
    else:
        return {"result": None, "error": f"API version {version} not found"}


if __name__ == "__main__":
    app.run()
