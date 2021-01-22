import json
import pytest   # noqa: F401


def test_setup_api_no_defaults(app):
    with app.test_client() as client:
        rv = client.get('/api/v1/setup')
        assert rv.status_code == 200

        data = json.loads(rv.data)
        assert len(data.keys()) == 0


def test_setup_api_forced_mode_hint(app, monkeypatch):
    with app.test_client() as client:
        monkeypatch.setitem(app.config, 'SERVER_MODE', 'family')

        rv = client.get('/api/v1/setup')
        assert rv.status_code == 200

        data = json.loads(rv.data)
        assert 'mode' in data
        assert data['mode'] == 'family'


def test_setup_api_forced_mode(app, monkeypatch):
    with app.test_client() as client:
        monkeypatch.setitem(app.config, 'SERVER_MODE', 'family')

        # Setup Server
        setup_data = {
            'mode': 'personal',
            'email': 'test@jadetree.io',
            'password': 'hunter2JT',
            'name': 'Test User',
        }
        rv = client.post(
            '/api/v1/setup',
            content_type='application/json',
            data=json.dumps(setup_data),
        )
        assert rv.status_code == 422

        data = json.loads(rv.data)
        assert 'status' in data
        assert 'code' in data
        assert 'errors' in data

        assert data['code'] == 422
        assert data['status'] == 'Unprocessable Entity'

        assert len(data['errors']) == 1
        assert 'json' in data['errors']
        assert len(data['errors']['json']) == 1
        assert 'mode' in data['errors']['json']
        assert len(data['errors']['json']['mode']) == 1
        assert "must be set to 'family'" in data['errors']['json']['mode'][0]
        assert 'forced by configuration' in data['errors']['json']['mode'][0]


def test_setup_api_invalid_mode(app):
    with app.test_client() as client:
        rv = client.get('/api/v1/version')
        assert rv.status_code == 200

        data = json.loads(rv.data)
        assert 'needs_setup' in data
        assert data['needs_setup'] is True

        # Setup Server
        setup_data = {
            'mode': 'private',
            'email': 'test@jadetree.io',
            'password': 'hunter2JT',
            'name': 'Test User',
        }
        rv = client.post(
            '/api/v1/setup',
            content_type='application/json',
            data=json.dumps(setup_data),
        )
        assert rv.status_code == 422

        data = json.loads(rv.data)
        assert 'status' in data
        assert 'code' in data
        assert 'errors' in data

        assert data['code'] == 422
        assert data['status'] == 'Unprocessable Entity'

        assert len(data['errors']) == 1
        assert 'json' in data['errors']
        assert len(data['errors']['json']) == 1
        assert 'mode' in data['errors']['json']
        assert len(data['errors']['json']['mode']) == 1
        assert 'must be one of:' in data['errors']['json']['mode'][0]


def test_setup_api_forced_user_hint(app, monkeypatch):
    with app.test_client() as client:
        monkeypatch.setitem(app.config, 'USER_EMAIL', 'test2@jadetree.io')
        monkeypatch.setitem(app.config, 'USER_NAME', 'Test User 2')

        rv = client.get('/api/v1/setup')
        assert rv.status_code == 200

        data = json.loads(rv.data)
        assert 'email' in data
        assert 'name' in data
        assert data['email'] == 'test2@jadetree.io'
        assert data['name'] == 'Test User 2'


def test_setup_api_forced_user_email(app, monkeypatch):
    with app.test_client() as client:
        monkeypatch.setitem(app.config, 'USER_EMAIL', 'test2@jadetree.io')
        monkeypatch.setitem(app.config, 'USER_NAME', 'Test User 2')

        # Setup Server
        setup_data = {
            'mode': 'personal',
            'email': 'test@jadetree.io',
            'password': 'hunter2JT',
            'name': 'Test User',
        }
        rv = client.post(
            '/api/v1/setup',
            content_type='application/json',
            data=json.dumps(setup_data),
        )
        assert rv.status_code == 422

        data = json.loads(rv.data)
        assert 'status' in data
        assert 'code' in data
        assert 'errors' in data

        assert data['code'] == 422
        assert data['status'] == 'Unprocessable Entity'

        assert len(data['errors']) == 1
        assert 'json' in data['errors']
        assert len(data['errors']['json']) == 1

        assert 'email' in data['errors']['json']
        assert len(data['errors']['json']['email']) == 1
        assert "must be set to 'test2@jadetree.io'" in data['errors']['json']['email'][0]
        assert 'forced by configuration' in data['errors']['json']['email'][0]


def test_setup_api_forced_user_name(app, monkeypatch):
    with app.test_client() as client:
        monkeypatch.setitem(app.config, 'USER_EMAIL', 'test2@jadetree.io')
        monkeypatch.setitem(app.config, 'USER_NAME', 'Test User 2')

        # Setup Server
        setup_data = {
            'mode': 'personal',
            'email': 'test2@jadetree.io',
            'password': 'hunter2JT',
            'name': 'Test User',
        }
        rv = client.post(
            '/api/v1/setup',
            content_type='application/json',
            data=json.dumps(setup_data),
        )
        assert rv.status_code == 422

        data = json.loads(rv.data)
        assert 'status' in data
        assert 'code' in data
        assert 'errors' in data

        assert data['code'] == 422
        assert data['status'] == 'Unprocessable Entity'

        assert len(data['errors']) == 1
        assert 'json' in data['errors']
        assert len(data['errors']['json']) == 1

        assert 'name' in data['errors']['json']
        assert len(data['errors']['json']['name']) == 1
        assert "must be set to 'Test User 2'" in data['errors']['json']['name'][0]
        assert 'forced by configuration' in data['errors']['json']['name'][0]


def test_setup_api_invalid_email(app):
    with app.test_client() as client:
        rv = client.get('/api/v1/version')
        assert rv.status_code == 200

        data = json.loads(rv.data)
        assert 'needs_setup' in data
        assert data['needs_setup'] is True

        # Setup Server
        setup_data = {
            'mode': 'family',
            'email': 'test user@jadetree.io',
            'password': 'hunter2JT',
            'name': 'Test User',
        }
        rv = client.post(
            '/api/v1/setup',
            content_type='application/json',
            data=json.dumps(setup_data),
        )
        assert rv.status_code == 422

        data = json.loads(rv.data)
        assert 'status' in data
        assert 'code' in data
        assert 'errors' in data

        assert data['code'] == 422
        assert data['status'] == 'Unprocessable Entity'

        assert len(data['errors']) == 1
        assert 'json' in data['errors']
        assert len(data['errors']['json']) == 1
        assert 'email' in data['errors']['json']
        assert len(data['errors']['json']['email']) == 1
        assert 'Not a valid email' in data['errors']['json']['email'][0]


def test_setup_api_invalid_password(app):
    with app.test_client() as client:
        rv = client.get('/api/v1/version')
        assert rv.status_code == 200

        data = json.loads(rv.data)
        assert 'needs_setup' in data
        assert data['needs_setup'] is True

        # Setup Server
        setup_data = {
            'mode': 'public',
            'email': 'test@jadetree.io',
            'password': 'hunter2',
            'name': 'Test User',
        }
        rv = client.post(
            '/api/v1/setup',
            content_type='application/json',
            data=json.dumps(setup_data),
        )
        assert rv.status_code == 422

        data = json.loads(rv.data)
        assert 'status' in data
        assert 'code' in data
        assert 'errors' in data

        assert data['code'] == 422
        assert data['status'] == 'Unprocessable Entity'

        assert len(data['errors']) == 1
        assert 'json' in data['errors']
        assert len(data['errors']['json']) == 1
        assert 'password' in data['errors']['json']
        assert len(data['errors']['json']['password']) == 1
        assert 'Password' in data['errors']['json']['password'][0]


def test_setup_api_removes_endpoint(app):
    with app.test_client() as client:
        rv = client.get('/api/v1/version')
        assert rv.status_code == 200

        data = json.loads(rv.data)
        assert 'needs_setup' in data
        assert data['needs_setup'] is True

        # Setup Server
        setup_data = {
            'mode': 'personal',
            'email': 'test@jadetree.io',
            'password': 'hunter2JT',
            'name': 'Test User',
        }
        rv = client.post(
            '/api/v1/setup',
            content_type='application/json',
            data=json.dumps(setup_data),
        )
        assert rv.status_code == 204

        # Setup endpoint should be removed for GET
        rv = client.get('/api/v1/setup')
        assert rv.status_code == 410

        # Setup endpoint should be removed for POST
        rv = client.post(
            '/api/v1/setup',
            content_type='application/json',
            data=json.dumps(setup_data),
        )
        assert rv.status_code == 410
