
with open('flask_secret_key') as f:
    FLASK_SECRET_KEY = f.read()

FLASK_NAME = "controller"
# Used in case of a paginated response from mongodb
MONGO_DEFAULT_PAGE_SIZE = 5
JSONIFY_PRETTYPRINT_REGULAR = True
