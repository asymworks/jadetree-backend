"""Test Initial Onboarding Flow.

Test the initial server onboarding flow, using a personal type server setup.
"""

import json
import re
from urllib.parse import quote

import pytest  # noqa: F401

from jadetree.mail import mail
from jadetree.service import auth as auth_service
from tests.helpers import check_error

# Always use 'jt_setup' fixture so server gets initialized
# Always use 'session' fixture so database changes are rolled back
pytestmark = pytest.mark.usefixtures('jt_setup', 'session')


@pytest.fixture(scope='module')
def jt_setup(app):
    """Set up Jade Tree in Public Mode as a PyTest fixture."""
    with app.test_client() as client:
        setup_data = {
            'mode': 'public',
            'email': 'test@jadetree.io',
            'password': 'hunter2JT',
            'name': 'Test User',
        }

        client.post(
            '/api/v1/setup',
            content_type='application/json',
            data=json.dumps(setup_data),
        )


def test_confirm_new_user(app):
    """Confirm a new User's Email."""
    with app.test_client() as client:
        with mail.record_messages() as outbox:
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

            assert rv.status_code == 200

            assert len(outbox) == 1
            assert outbox[0].subject == '[Jade Tree] Confirm Your Registration'

            # Load Tokens from Email
            m = re.search(r'confirm\?token=([A-Za-z0-9-_=]+\.[A-Za-z0-9-_=]+\.?[A-Za-z0-9-_.+/=]*)', outbox[0].body)
            assert m is not None
            confirm_token = str(m.group(1))

            # Confirm the User Registration
            rv = client.get(
                f'/api/v1/auth/confirm?token={quote(confirm_token)}'
            )

            assert rv.status_code == 200

            data = json.loads(rv.data)
            assert 'email' in data
            assert 'active' in data
            assert 'confirmed' in data

            assert data['email'] == 'test2@jadetree.io'
            assert data['active'] is True
            assert data['confirmed'] is True

            assert len(outbox) == 2
            assert outbox[1].subject == '[Jade Tree] Welcome to Jade Tree'


def test_confirm_new_user_expired_token(app, session):
    """Ensure the API returns an error for an expired token."""
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

        assert rv.status_code == 200

        # Generate an expired confirmation token
        user = auth_service.load_user_by_email(session, 'test2@jadetree.io')
        confirm_token = auth_service.generate_user_token(
            user,
            auth_service.JWT_SUBJECT_CONFIRM_EMAIL,
            email=user.email,
            expiration=-3600,
        )

        rv = client.get(
            f'/api/v1/auth/confirm?token={quote(confirm_token)}'
        )

        check_error(rv, 400, 'JwtExpiredTokenError', 'expired')


def test_confirm_new_user_invalid_token(app, session):
    """Ensure the API returns an error for an invalid token."""
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

        assert rv.status_code == 200

        # Generate an invalid confirmation token
        user = auth_service.load_user_by_email(session, 'test2@jadetree.io')
        confirm_token = auth_service.generate_user_token(
            user,
            auth_service.JWT_SUBJECT_CANCEL_EMAIL,
            email=user.email,
        )

        rv = client.get(
            f'/api/v1/auth/confirm?token={quote(confirm_token)}'
        )

        check_error(rv, 400, 'JwtPayloadError', 'subject')


def test_confirm_new_user_wrong_hash(app, session):
    """Ensure the API returns an error for an unknown user."""
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

        assert rv.status_code == 200

        # Generate an invalid confirmation token
        class MockUser:
            uid_hash = '0000'

        confirm_token = auth_service.generate_user_token(
            MockUser(),
            auth_service.JWT_SUBJECT_CONFIRM_EMAIL,
            email='test2@jadetree.io',
        )

        rv = client.get(
            f'/api/v1/auth/confirm?token={quote(confirm_token)}'
        )

        check_error(rv, 404, 'NoResults', 'find a user')


def test_confirm_new_user_wrong_email(app, session):
    """Ensure the API returns an error for an invalid email."""
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

        assert rv.status_code == 200

        # Generate an invalid confirmation token
        user = auth_service.load_user_by_email(session, 'test2@jadetree.io')
        confirm_token = auth_service.generate_user_token(
            user,
            auth_service.JWT_SUBJECT_CONFIRM_EMAIL,
            email='wrong@jadetree.io',
        )

        rv = client.get(
            f'/api/v1/auth/confirm?token={quote(confirm_token)}'
        )

        check_error(rv, 400, 'DomainError', 'Email address')


def test_confirm_new_user_already_confirmed(app, session):
    """Ensure the API returns an error for a re-confirmation."""
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

        assert rv.status_code == 200

        # Confirm the user
        user = auth_service.load_user_by_email(session, 'test2@jadetree.io')
        confirm_token = auth_service.generate_user_token(
            user,
            auth_service.JWT_SUBJECT_CONFIRM_EMAIL,
            email=user.email,
        )

        rv = client.get(
            f'/api/v1/auth/confirm?token={quote(confirm_token)}'
        )

        assert rv.status_code == 200

        # Re-Confirm the user
        rv = client.get(
            f'/api/v1/auth/confirm?token={quote(confirm_token)}'
        )

        check_error(rv, 400, 'DomainError', 'already confirmed')


def test_cancel_new_user(app, session):
    """Cancel a new User's Registration."""
    with app.test_client() as client:
        with mail.record_messages() as outbox:
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

            assert rv.status_code == 200

            # Load Tokens from Email
            m = re.search(r'cancel\?token=([A-Za-z0-9-_=]+\.[A-Za-z0-9-_=]+\.?[A-Za-z0-9-_.+/=]*)', outbox[0].body)
            assert m is not None
            cancel_token = str(m.group(1))

            # Cancel the User Registration
            rv = client.get(
                f'/api/v1/auth/cancel?token={quote(cancel_token)}'
            )

            assert rv.status_code == 204
            assert len(outbox) == 1

            assert auth_service.load_user_by_email(session, 'test2@jadetree.io') is None


def test_cancel_new_user_invalid_token(app, session):
    """Ensure the API returns an error for an invalid token."""
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

        assert rv.status_code == 200

        # Generate an invalid cancellation token
        cancel_token = auth_service.encodeJwt(
            app,
            subject=auth_service.JWT_SUBJECT_CONFIRM_EMAIL,
            email='test2@jadetree.io',
        )

        rv = client.get(
            f'/api/v1/auth/cancel?token={quote(cancel_token)}'
        )

        check_error(rv, 400, 'JwtPayloadError', 'subject')


def test_cancel_new_user_wrong_email(app, session):
    """Ensure the API returns an error for an invalid email."""
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

        assert rv.status_code == 200

        # Generate an invalid confirmation token
        cancel_token = auth_service.encodeJwt(
            app,
            subject=auth_service.JWT_SUBJECT_CANCEL_EMAIL,
            email='wrong@jadetree.io',
        )

        rv = client.get(
            f'/api/v1/auth/cancel?token={quote(cancel_token)}'
        )

        check_error(rv, 404, 'NoResults', 'email address')


def test_cancel_new_user_already_confirmed(app, session):
    """Ensure the API returns an error for a re-confirmation."""
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

        assert rv.status_code == 200

        # Confirm the user
        user = auth_service.load_user_by_email(session, 'test2@jadetree.io')
        confirm_token = auth_service.generate_user_token(
            user,
            auth_service.JWT_SUBJECT_CONFIRM_EMAIL,
            email=user.email,
        )

        rv = client.get(
            f'/api/v1/auth/confirm?token={quote(confirm_token)}'
        )

        assert rv.status_code == 200

        # Cancel the user
        cancel_token = auth_service.encodeJwt(
            app,
            subject=auth_service.JWT_SUBJECT_CANCEL_EMAIL,
            email='test2@jadetree.io',
        )

        rv = client.get(
            f'/api/v1/auth/cancel?token={quote(cancel_token)}'
        )

        check_error(rv, 400, 'DomainError', 'already confirmed')


def test_resend_confirmation(app):
    """Re-Send a new Confirmation Email."""
    with app.test_client() as client:
        with mail.record_messages() as outbox:
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

            assert rv.status_code == 200

            assert len(outbox) == 1
            assert outbox[0].subject == '[Jade Tree] Confirm Your Registration'

            # Load Tokens from Email
            m = re.search(r'confirm\?token=([A-Za-z0-9-_=]+\.[A-Za-z0-9-_=]+\.?[A-Za-z0-9-_.+/=]*)', outbox[0].body)
            assert m is not None
            confirm_token_1 = str(m.group(1))

            # Send a New Confirmation
            rv = client.get(
                f'/api/v1/auth/resendConfirmation?email={quote("test2@jadetree.io")}'
            )

            assert rv.status_code == 200

            assert len(outbox) == 2
            assert outbox[1].subject == '[Jade Tree] Confirm Your Registration'

            # Load Tokens from Second Email
            m = re.search(r'confirm\?token=([A-Za-z0-9-_=]+\.[A-Za-z0-9-_=]+\.?[A-Za-z0-9-_.+/=]*)', outbox[1].body)
            assert m is not None
            confirm_token_2 = str(m.group(1))

            assert confirm_token_1 != confirm_token_2


def test_resend_confirmation_wrong_email(app):
    """Re-Send a new Confirmation Email to a nonexistent user."""
    with app.test_client() as client:
        with mail.record_messages() as outbox:
            # Request Re-Send for Invalid Email
            rv = client.get(
                f'/api/v1/auth/resendConfirmation?email={quote("wrong@jadetree.io")}'
            )

            check_error(rv, 404, 'NoResults', 'Invalid email or email is not pending registration')

            assert len(outbox) == 0


def test_resend_confirmation_already_confirmed(app, session):
    """Re-Send a new Confirmation Email to an already confirmed user."""
    with app.test_client() as client:
        with mail.record_messages() as outbox:
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

            assert rv.status_code == 200

            # Confirm the user
            user = auth_service.load_user_by_email(session, 'test2@jadetree.io')
            confirm_token = auth_service.generate_user_token(
                user,
                auth_service.JWT_SUBJECT_CONFIRM_EMAIL,
                email=user.email,
            )

            rv = client.get(
                f'/api/v1/auth/confirm?token={quote(confirm_token)}'
            )

            assert rv.status_code == 200

            # Request Re-Send for User
            rv = client.get(
                f'/api/v1/auth/resendConfirmation?email={quote("test2@jadetree.io")}'
            )

            check_error(rv, 404, 'NoResults', 'Invalid email or email is not pending registration')

            assert len(outbox) == 2     # Confirmation and Welcome
