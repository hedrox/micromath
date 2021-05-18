import logging
import json
import math

from server import app

app.testing = True
logging.disable(logging.ERROR)


class TestPow:

    def test_correct_pow(self):
        with app.test_client() as client:
            body = {'base': 32, 'power': 2}
            result = client.post('/api/v1/pow', json=body)
            assert result.status_code == 200

            data = json.loads(result.data)
            assert math.isclose(float(data['result']), 1024.0)
            assert data['error'] is None

    def test_missing_attribute(self):
        with app.test_client() as client:
            body = {'power': 2}
            result = client.post('/api/v1/pow', json=body)
            assert result.status_code == 500

            data = json.loads(result.data)
            assert data['result'] is None
            assert 'name' in data['error']
            assert data['error']['name'] == 'ValidationError'

    def test_invalid_attribute_type(self):
        with app.test_client() as client:
            body = {'base': None, 'power': 2}
            result = client.post('/api/v1/pow', json=body)
            assert result.status_code == 500

            data = json.loads(result.data)
            assert data['result'] is None
            assert 'name' in data['error']
            assert data['error']['name'] == 'ValidationError'

            body = {'base': '2', 'power': 2}
            result = client.post('/api/v1/pow', json=body)
            assert result.status_code == 500

            data = json.loads(result.data)
            assert data['result'] is None
            assert 'name' in data['error']
            assert data['error']['name'] == 'ValidationError'

    def test_empty_body(self):
        with app.test_client() as client:
            body = {}
            result = client.post('/api/v1/pow', json=body)
            assert result.status_code == 500

            data = json.loads(result.data)
            assert data['result'] is None
            assert 'name' in data['error']
            assert data['error']['name'] == 'ValidationError'

    def test_extra_attribute(self):
        with app.test_client() as client:
            body = {'base': 32, 'power': 2, 'extra_key': 32}
            result = client.post('/api/v1/pow', json=body)
            assert result.status_code == 500

            data = json.loads(result.data)
            assert data['result'] is None
            assert 'name' in data['error']
            assert data['error']['name'] == 'ValidationError'

    def test_no_body(self):
        with app.test_client() as client:
            result = client.post('/api/v1/pow')
            assert result.status_code == 400

            data = json.loads(result.data)
            assert data['result'] is None
            assert data['error'] == 'Data not provided'

    def test_invalid_api_version(self):
        with app.test_client() as client:
            body = {'base': 32, 'power': 2}
            result = client.post('/api/v2/pow', json=body)
            assert result.status_code == 404

            data = json.loads(result.data)
            assert data['result'] is None
            assert data['error'] == 'API version v2 not found'
