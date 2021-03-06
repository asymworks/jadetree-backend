"""Test Initial Onboarding Flow.

Test the initial server onboarding flow, using a personal type server setup.
"""

import json

import pytest  # noqa: F401

from jadetree.service.auth import load_user_by_email
from tests.helpers import check_login, check_unauthorized

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


def test_user_can_log_in_with_password(app, session):
    """Ensure the user can log in with a password (all modes)."""
    with app.test_client() as client:
        login_data = { 'email': 'test@jadetree.io', 'password': 'hunter2JT' }
        rv = client.post(
            '/api/v1/auth/login',
            content_type='application/json',
            data=json.dumps(login_data),
        )

        check_login(rv, 'test@jadetree.io', session)


def test_user_can_log_in_without_password(app, session):
    """Ensure the user can log in without a password (personal and family modes)."""
    with app.test_client() as client:
        login_data = { 'email': 'test@jadetree.io', 'password': '' }
        rv = client.post(
            '/api/v1/auth/login',
            content_type='application/json',
            data=json.dumps(login_data),
        )

        check_login(rv, 'test@jadetree.io', session)


def test_user_can_log_in_with_bad_password(app, session):
    """Ensure the user can log in with an incorrect password (personal and family modes)."""
    with app.test_client() as client:
        login_data = { 'email': 'test@jadetree.io', 'password': 'hunter2' }
        rv = client.post(
            '/api/v1/auth/login',
            content_type='application/json',
            data=json.dumps(login_data),
        )

        check_login(rv, 'test@jadetree.io', session)


def test_nonexistant_user(app, session):
    """Ensure a non-existent user cannot be logged in (all modes)."""
    with app.test_client() as client:
        login_data = { 'email': 'test2@jadetree.io', 'password': '' }
        rv = client.post(
            '/api/v1/auth/login',
            content_type='application/json',
            data=json.dumps(login_data),
        )

        check_unauthorized(rv)


def test_change_password_keep_logins(app, session):
    """Check that the user can change a password and not change User ID Hash."""
    with app.test_client() as client:
        login_data = { 'email': 'test@jadetree.io', 'password': '' }
        rv = client.post(
            '/api/v1/auth/login',
            content_type='application/json',
            data=json.dumps(login_data),
        )

        token = check_login(rv, 'test@jadetree.io', session)
        user = load_user_by_email(session, 'test@jadetree.io')
        assert user.check_password('hunter2JT')
        uid1 = user.uid_hash

        rv = client.post(
            '/api/v1/auth/changePassword',
            content_type='application/json',
            headers=[('Authorization', f'Bearer {token}')],
            data=json.dumps({
                'old_password': 'hunter2JT',
                'new_password': 'aSecur3Pa55w0rd',
                'logout_sessions': False,
            }),
        )

        check_login(rv, 'test@jadetree.io', session)
        user = load_user_by_email(session, 'test@jadetree.io')
        assert user.check_password('aSecur3Pa55w0rd')
        uid2 = user.uid_hash

        assert uid1 == uid2


def test_change_password_invalidate_logins(app, session):
    """Check that the user can change a password and change User ID Hash."""
    with app.test_client() as client:
        login_data = { 'email': 'test@jadetree.io', 'password': '' }
        rv = client.post(
            '/api/v1/auth/login',
            content_type='application/json',
            data=json.dumps(login_data),
        )

        token = check_login(rv, 'test@jadetree.io', session)
        user = load_user_by_email(session, 'test@jadetree.io')
        assert user.check_password('hunter2JT')

        rv = client.post(
            '/api/v1/auth/changePassword',
            content_type='application/json',
            headers=[('Authorization', f'Bearer {token}')],
            data=json.dumps({
                'old_password': 'hunter2JT',
                'new_password': 'aSecur3Pa55w0rd',
                'logout_sessions': True,
            }),
        )

        check_login(rv, 'test@jadetree.io', session)
        user = load_user_by_email(session, 'test@jadetree.io')
        assert user.check_password('aSecur3Pa55w0rd')


def test_change_password_bad_new_password(app, session):
    """Check that invalid new passwords are rejected."""
    with app.test_client() as client:
        login_data = { 'email': 'test@jadetree.io', 'password': '' }
        rv = client.post(
            '/api/v1/auth/login',
            content_type='application/json',
            data=json.dumps(login_data),
        )

        token = check_login(rv, 'test@jadetree.io', session)
        user = load_user_by_email(session, 'test@jadetree.io')
        assert user.check_password('hunter2JT')

        rv = client.post(
            '/api/v1/auth/changePassword',
            content_type='application/json',
            headers=[('Authorization', f'Bearer {token}')],
            data=json.dumps({
                'old_password': 'hunter2JT',
                'new_password': 'aBadPW',
            }),
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
        assert 'new_password' in data['errors']['json']
        assert len(data['errors']['json']['new_password']) == 1
        assert 'Password' in data['errors']['json']['new_password'][0]


def test_logout(app, session):
    """Ensure the user can be logged out and the ID hash changes."""
    with app.test_client() as client:
        login_data = { 'email': 'test@jadetree.io', 'password': 'hunter2JT' }
        rv = client.post(
            '/api/v1/auth/login',
            content_type='application/json',
            data=json.dumps(login_data),
        )

        token = check_login(rv, 'test@jadetree.io', session)

        user = load_user_by_email(session, 'test@jadetree.io')
        user_hash = user.uid_hash

        headers = [('Authorization', f'Bearer {token}')]
        rv = client.get('/api/v1/auth/logout', headers=headers)

        assert rv.status_code == 204
        assert user.uid_hash != user_hash


def test_register_user_unavailable(app):
    """Ensure the /auth/register endpoint is unavailable in Personal mode."""
    with app.test_client() as client:
        # Register a new User
        user_data = {
            'email': 'test2@jadetree.io',
            'password': 'aSecu43Pa55w0rd',
            'name': 'Second User',
        }
        rv = client.post(
            '/api/v1/auth/register',
            content_type='application/json',
            data=json.dumps(user_data),
        )

        assert rv.status_code == 410


def test_user_list(app):
    """Check that the User List is the list of registered users."""
    with app.test_client() as client:
        rv = client.get('/api/v1/auth/login')
        assert rv.status_code == 200

        data = json.loads(rv.data)
        assert len(data) == 1

        assert 'email' in data[0]
        assert 'name' in data[0]
        assert data[0]['email'] == 'test@jadetree.io'
        assert data[0]['name'] == 'Test User'
