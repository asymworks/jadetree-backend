"""Test Initial Onboarding Flow.

Test the initial server onboarding flow, using a personal type server setup.
"""

import json

import pytest  # noqa: F401

# Always use 'jt_setup' fixture so server gets initialized
pytestmark = pytest.mark.usefixtures('jt_setup')


@pytest.fixture(scope='module')
def jt_setup(app):
    """Set up Jade Tree in Personal Mode as a PyTest fixture."""
    with app.test_client() as client:
        setup_data = {
            'mode': 'personal',
            'email': 'test@jadetree.io',
            'password': 'hunter2JT',
            'name': 'Test User',
        }

        client.post(
            '/api/v1/setup',
            content_type='application/json',
            data=json.dumps(setup_data),
        )


@pytest.fixture(scope='function')
def token(app):
    """Log in the Personal User."""
    with app.test_client() as client:
        login_data = { 'email': 'test@jadetree.io', 'password': 'hunter2JT' }
        rv = client.post(
            '/api/v1/auth/login',
            content_type='application/json',
            data=json.dumps(login_data),
        )

        assert rv.status_code == 200
        data = json.loads(rv.data)
        return data['token']


def test_user_info_needs_onboard(app, token):
    """Ensure that the new user is marked to be onboarded."""
    headers = [('Authorization', f'Bearer {token}')]
    with app.test_client() as client:
        rv = client.get('/api/v1/user', headers=headers)
        assert rv.status_code == 200

        data = json.loads(rv.data)
        assert 'profile_setup' in data
        assert data['profile_setup'] is False
