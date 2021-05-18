import logging
import json

from server import app

app.testing = True
logging.disable(logging.ERROR)


class TestFibonacci:

    def test_correct_fibonacci(self):
        with app.test_client() as client:
            body = {'number': 16}
            result = client.post('/api/v1/fibonacci', json=body)
            assert result.status_code == 200

            data = json.loads(result.data)
            assert int(data['result']) == 610
            assert data['error'] is None

    def test_invalid_attribute_type(self):
        with app.test_client() as client:
            body = {'number': None}
            result = client.post('/api/v1/fibonacci', json=body)
            assert result.status_code == 500

            data = json.loads(result.data)
            assert data['result'] is None
            assert 'name' in data['error']
            assert data['error']['name'] == 'ValidationError'

            body = {'number': '2'}
            result = client.post('/api/v1/fibonacci', json=body)
            assert result.status_code == 500

            data = json.loads(result.data)
            assert data['result'] is None
            assert 'name' in data['error']
            assert data['error']['name'] == 'ValidationError'

    def test_empty_body(self):
        with app.test_client() as client:
            body = {}
            result = client.post('/api/v1/fibonacci', json=body)
            assert result.status_code == 500

            data = json.loads(result.data)
            assert data['result'] is None
            assert 'name' in data['error']
            assert data['error']['name'] == 'ValidationError'

    def test_extra_attribute(self):
        with app.test_client() as client:
            body = {'number': 32, 'extra_key': 32}
            result = client.post('/api/v1/fibonacci', json=body)
            assert result.status_code == 500

            data = json.loads(result.data)
            assert data['result'] is None
            assert 'name' in data['error']
            assert data['error']['name'] == 'ValidationError'

    def test_no_body(self):
        with app.test_client() as client:
            result = client.post('/api/v1/fibonacci')
            assert result.status_code == 400

            data = json.loads(result.data)
            assert data['result'] is None
            assert data['error'] == 'Data not provided'

    def test_invalid_api_version(self):
        with app.test_client() as client:
            body = {'number': 32}
            result = client.post('/api/v2/fibonacci', json=body)
            assert result.status_code == 404

            data = json.loads(result.data)
            assert data['result'] is None
            assert data['error'] == 'API version v2 not found'
