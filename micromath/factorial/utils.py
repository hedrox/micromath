import logging

from logstash_async.handler import AsynchronousLogstashHandler
from jsonschema import validate

input_schema = {
    "type": "object",
    "properties": {
        "number": {"type": "number"}
    },
    "required": ["number"],
    "additionalProperties": False
}

def validate_input(data):
    validate(data, schema=input_schema)

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

