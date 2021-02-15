"""Test Initial Setup Flow."""

import json

import pytest  # noqa: F401

from jadetree.mail import mail

# Always use 'mock_jt_config' and 'session' fixtures so database changes
# are rolled back
pytestmark = pytest.mark.usefixtures('mock_jt_config', 'mock_jt_setup', 'session')


@pytest.fixture(scope='function')
def mock_jt_setup(app, monkeypatch):
    """Reset the `_JT_NEEDS_SETUP` configuration value between tests."""
    monkeypatch.setitem(app.config, '_JT_NEEDS_SETUP', True)


def test_setup_api_no_defaults(app):
    """Check that the Setup API does not return defaults when not set."""
    with app.test_client() as client:
        rv = client.get('/api/v1/setup')
        assert rv.status_code == 200

        data = json.loads(rv.data)
        assert len(data.keys()) == 0


def test_setup_api_personal_with_no_password(app, monkeypatch):
    """Check the Setup API in Personal Mode with no password."""
    with app.test_client() as client:
        # Setup Server
        setup_data = {
            'mode': 'personal',
            'email': 'test@jadetree.io',
            'name': 'Test User',
        }
        rv = client.post(
            '/api/v1/setup',
            content_type='application/json',
            data=json.dumps(setup_data),
        )

        assert rv.status_code == 204


def test_setup_api_personal_with_blank_password(app):
    """Check the Setup API in Personal Mode with a blank password."""
    with app.test_client() as client:
        # Setup Server
        setup_data = {
            'mode': 'personal',
            'email': 'test@jadetree.io',
            'password': '',
            'name': 'Test User',
        }
        rv = client.post(
            '/api/v1/setup',
            content_type='application/json',
            data=json.dumps(setup_data),
        )

        assert rv.status_code == 204


def test_setup_api_family_with_no_password(app):
    """Check the Setup API in Personal Mode with no password."""
    with app.test_client() as client:
        # Setup Server
        setup_data = {
            'mode': 'family',
            'email': 'test@jadetree.io',
            'name': 'Test User',
        }
        rv = client.post(
            '/api/v1/setup',
            content_type='application/json',
            data=json.dumps(setup_data),
        )

        assert rv.status_code == 204


def test_setup_api_family_with_blank_password(app):
    """Check the Setup API in Family Mode with a blank password."""
    with app.test_client() as client:
        # Setup Server
        setup_data = {
            'mode': 'family',
            'email': 'test@jadetree.io',
            'password': '',
            'name': 'Test User',
        }
        rv = client.post(
            '/api/v1/setup',
            content_type='application/json',
            data=json.dumps(setup_data),
        )

        assert rv.status_code == 204


def test_setup_api_public_with_no_password(app):
    """Check the Setup API in Public Mode with no password."""
    with app.test_client() as client:
        # Setup Server
        setup_data = {
            'mode': 'public',
            'email': 'test@jadetree.io',
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


def test_setup_api_public_with_blank_password(app):
    """Check the Setup API in Family Mode with a blank password."""
    with app.test_client() as client:
        # Setup Server
        setup_data = {
            'mode': 'public',
            'email': 'test@jadetree.io',
            'password': '',
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


def test_setup_api_forced_mode_hint(app, monkeypatch):
    """Check that the Setup API gives a mode hint when forced."""
    with app.test_client() as client:
        monkeypatch.setitem(app.config, 'SERVER_MODE', 'family')

        rv = client.get('/api/v1/setup')
        assert rv.status_code == 200

        data = json.loads(rv.data)
        assert 'mode' in data
        assert data['mode'] == 'family'


def test_setup_api_forced_mode(app, monkeypatch):
    """Check that the Setup API honors a forced mode."""
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
    """Check that the Setup API fails when the mode is invalid."""
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
    """Check that the Setup API gives a user hint when forced."""
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
    """Check that the Setup API respects a forced user email address."""
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
    """Check that the Setup API respects a forced user name."""
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
    """Check that the Setup API rejects an invalid email address."""
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
    """Check that the Setup API rejects an invalid password."""
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
    """Check that the Setup API removes the endpoint after server setup."""
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


def test_setup_api_does_not_send_email(app):
    """Check that the Setup API does not send a confirmation email."""
    with app.test_client() as client:
        with mail.record_messages() as outbox:
            # Setup Server
            setup_data = {
                'mode': 'public',
                'email': 'test@jadetree.io',
                'name': 'Test User',
                'password': 'aSecr3tPa55w0rd',
            }
            rv = client.post(
                '/api/v1/setup',
                content_type='application/json',
                data=json.dumps(setup_data),
            )

            assert rv.status_code == 204

        assert len(outbox) == 0
