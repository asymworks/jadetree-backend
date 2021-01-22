"""Test Authentication and Authorization Service."""

import datetime

from arrow import utcnow
from flask import current_app
import pytest  # noqa: F401

from jadetree.domain.models import User
from jadetree.exc import AuthError, DomainError, JwtPayloadError, NoResults
from jadetree.service import auth as auth_service
from jadetree.service.auth import JWT_SUBJECT_BEARER_TOKEN


def test_register_user_adds_user(session):
    """Ensure user is added when register_user is called."""
    u = auth_service.register_user(session, 'test@jadetree.io', 'hunter2JT', 'Test User')

    assert u is not None
    assert isinstance(u, User)
    assert u.id > 0
    assert len(session.query(User).all()) == 1

    assert u.email == 'test@jadetree.io'
    assert u.pw_hash is not None
    assert u.pw_hash != 'hunter2JT'
    assert u.uid_hash is not None
    assert u.currency is None
    assert u.active is False
    assert u.confirmed is False


def test_register_user_throws_duplicate_email(session):
    """Ensure two users with the same email cannot be registered."""
    auth_service.register_user(session, 'test@jadetree.io', 'hunter2JT', 'Test User')
    with pytest.raises(ValueError) as exc_data:
        auth_service.register_user(session, 'test@jadetree.io', 'hunter2JTa', 'Test User')
    assert len(session.query(User).all()) == 1
    assert 'already exists' in str(exc_data.value)


def test_register_user_throws_bad_email(session):
    """Ensure invalid email addresses are rejected."""
    with pytest.raises(ValueError) as exc_data:
        auth_service.register_user(session, 'jadetree', 'hunter2JT', 'Test User')
    assert len(session.query(User).all()) == 0
    assert 'Invalid Email Address' in str(exc_data.value)


def test_register_user_throws_bad_pw_short(session):
    """Ensure passwords which are too short are rejected."""
    with pytest.raises(ValueError) as exc_data:
        auth_service.register_user(session, 'test@jadetree.io', 'aBc5', 'Test User')
    assert len(session.query(User).all()) == 0
    assert 'Password' in str(exc_data.value)
    assert 'at least 8 characters' in str(exc_data.value)


def test_register_user_throws_bad_pw_lowercase(session):
    """Ensure passwords with no lowercase letter are rejected."""
    with pytest.raises(ValueError) as exc_data:
        auth_service.register_user(session, 'test@jadetree.io', 'HUNTER2JT', 'Test User')
    assert len(session.query(User).all()) == 0
    assert str(exc_data.value) == 'Password must contain a lower-case letter'


def test_register_user_throws_bad_pw_uppercase(session):
    """Ensure passwords with no uppercase letter are rejected."""
    with pytest.raises(ValueError) as exc_data:
        auth_service.register_user(session, 'test@jadetree.io', 'hunter2jt', 'Test User')
    assert len(session.query(User).all()) == 0
    assert str(exc_data.value) == 'Password must contain an upper-case letter'


def test_register_user_throws_bad_pw_number(session):
    """Ensure passwords with no number are rejected."""
    with pytest.raises(ValueError) as exc_data:
        auth_service.register_user(session, 'test@jadetree.io', 'hunter_JT', 'Test User')
    assert len(session.query(User).all()) == 0
    assert str(exc_data.value) == 'Password must contain a number'


def test_register_user_throws_personal_mode(app, session, monkeypatch):
    """Ensure a second user cannot be registered in Personal mode."""
    auth_service.register_user(session, 'test@jadetree.io', 'hunter2JT', 'Test User')
    with app.app_context():
        monkeypatch.setitem(current_app.config, '_JT_SERVER_MODE', 'personal')
        with pytest.raises(DomainError) as exc_data:
            auth_service.register_user(session, 'test2@jadetree.io', 'hunter2JT', 'Test User 2')

    assert len(session.query(User).all()) == 1
    assert str(exc_data.value) == 'Cannot register users when the server mode is set to Personal'


def test_register_user_confirmed_family_mode(app, session, monkeypatch):
    """Ensure new users are automatically confirmed in Family mode."""
    auth_service.register_user(session, 'test@jadetree.io', 'hunter2JT', 'Test User')
    with app.app_context():
        monkeypatch.setitem(current_app.config, '_JT_SERVER_MODE', 'family')
        u = auth_service.register_user(session, 'test2@jadetree.io', 'hunter2JT', 'Test User 2')

        assert u.active is True
        assert u.confirmed is True


def test_confirm_user(session):
    """Ensure a user can be confirmed."""
    u = auth_service.register_user(session, 'test@jadetree.io', 'hunter2JT', 'Test User')

    assert u.id == 1
    assert u.uid_hash is not None
    assert u.active is False
    assert u.confirmed is False
    assert u.confirmed_at is None

    u2 = auth_service.confirm_user(session, u.uid_hash)

    assert u2 == u
    assert u2.active is True
    assert u2.confirmed is True
    assert u2.confirmed is not None


def test_confirm_user_not_exists(session):
    """Ensure a non-existent user is not confirmed."""
    u = auth_service.register_user(session, 'test@jadetree.io', 'hunter2JT', 'Test User')
    assert u.id == 1

    with pytest.raises(NoResults) as exc_data:
        auth_service.confirm_user(session, '0000')

    assert str(exc_data.value) == 'Could not find a user with the given hash'
    assert u.active is False
    assert u.confirmed is False


def test_confirm_user_already_confirmed(session):
    """Ensure a user already confirmed cannot be confirmed again."""
    u = auth_service.register_user(session, 'test@jadetree.io', 'hunter2JT', 'Test User')
    assert u.id == 1
    assert u.active is False
    assert u.confirmed is False

    # Set confirmed to True as in a user who had confirmed but then was
    # deactivated
    u.confirmed = True
    u.confirmed_at = utcnow()

    with pytest.raises(DomainError) as exc_data:
        auth_service.confirm_user(session, u.uid_hash)

    assert 'already confirmed' in str(exc_data.value)
    assert u.active is False
    assert u.confirmed is True


def test_get_user(session):
    """Ensure a user can be looked up by ID."""
    nu = auth_service.register_user(session, 'test@jadetree.io', 'hunter2JT', 'Test User')
    assert nu.id == 1

    u = session.query(User).filter(User.id == nu.id).one_or_none()
    assert auth_service.get_user(session, u.id) == nu


def test_get_user_not_exists(session):
    """Ensure a non-existent User ID returns None."""
    assert auth_service.get_user(session, 1) is None


def test_get_user_invalid(session):
    """Ensure an invalid User ID returns None."""
    u = auth_service.register_user(session, 'test@jadetree.io', 'hunter2JT', 'Test User')
    assert u.id == 1

    assert auth_service.get_user(session, 'one') is None


def test_load_user_by_hash(session):
    """Ensure a user can be looked up by ID Hash."""
    nu = auth_service.register_user(session, 'test@jadetree.io', 'hunter2JT', 'Test User')
    assert nu.id == 1

    u = session.query(User).filter(User.id == nu.id).one_or_none()
    assert u.uid_hash is not None
    assert auth_service.load_user_by_hash(session, u.uid_hash) == nu


def test_load_user_by_hash_not_exists(session):
    """Ensure an ID hash which does not exist returns None."""
    assert auth_service.load_user_by_hash(session, '00000000000000000000000000000000') is None


def test_load_user_by_hash_invalid(session):
    """Ensure an invalid ID hash returns None."""
    u = auth_service.register_user(session, 'test@jadetree.io', 'hunter2JT', 'Test User')
    assert u.id == 1

    assert auth_service.load_user_by_hash(session, 'one') is None


def test_invalidate_uid_hash(session):
    """Ensure the ID hash can be changed to invalidate login sessions."""
    u = auth_service.register_user(session, 'test@jadetree.io', 'hunter2JT', 'Test User')
    old_id = u.id
    old_hash = u.uid_hash

    nu = auth_service.invalidate_uid_hash(session, old_hash)
    assert nu.id == old_id
    assert nu.uid_hash != old_hash


def test_invalidate_uid_hash_invalid(session):
    """Ensure an error is raised when invalidating a non-existent ID hash."""
    auth_service.register_user(session, 'test@jadetree.io', 'hunter2JT', 'Test User')
    with pytest.raises(NoResults, match='Could not find a user'):
        auth_service.invalidate_uid_hash(session, 'xxx')


def test_load_user_by_email(session):
    """Ensure a user can be looked up by email address."""
    nu = auth_service.register_user(session, 'test@jadetree.io', 'hunter2JT', 'Test User')
    assert nu.id == 1

    assert auth_service.load_user_by_email(session, 'test@jadetree.io') == nu


def test_load_user_by_token(session):
    """Ensure a user can be looked up by JSON Web Token."""
    nu = auth_service.register_user(session, 'test@jadetree.io', 'hunter2JT', 'Test User')
    assert nu.id == 1

    # load_user_by_token is hardcoded for JWT_SUBJECT_BEARER_TOKEN
    token = auth_service.generate_user_token(nu, JWT_SUBJECT_BEARER_TOKEN)

    assert auth_service.load_user_by_token(session, token) == nu


def test_load_user_by_token_no_uid(app, session):
    """Ensure a JWT missing the user ID hash key is rejected."""
    nu = auth_service.register_user(session, 'test@jadetree.io', 'hunter2JT', 'Test User')
    assert nu.id == 1

    # load_user_by_token is hardcoded for JWT_SUBJECT_BEARER_TOKEN
    token = auth_service.encodeJwt(
        app,
        subject=JWT_SUBJECT_BEARER_TOKEN,
        exp=datetime.datetime.utcnow() + datetime.timedelta(minutes=1),
    )

    with pytest.raises(JwtPayloadError, match='Missing uid key') as excinfo:
        auth_service.load_user_by_token(session, token)

    assert excinfo.value.payload_key == 'uid'


def test_change_user_password(app, session, monkeypatch):
    """Ensure a user password can be changed."""
    u = auth_service.register_user(session, 'test@jadetree.io', 'hunter2JT', 'Test User')
    u_hash = u.uid_hash
    assert u.check_password('hunter2JT')

    monkeypatch.setitem(app.config, '_JT_SERVER_MODE', 'public')

    u2 = auth_service.confirm_user(session, u.uid_hash)
    rv = auth_service.change_password(
        session,
        u2.uid_hash,
        'hunter2JT',
        'aSecu43Pa55w0rd'
    )

    assert 'token' in rv
    assert 'user' in rv

    u3 = auth_service.load_user_by_email(session, 'test@jadetree.io')
    assert u3.check_password('aSecu43Pa55w0rd')
    assert u_hash != u3.uid_hash


def test_change_user_password_keep_hash(app, session, monkeypatch):
    """Ensure a user password can be changed without changing ID hash."""
    u = auth_service.register_user(session, 'test@jadetree.io', 'hunter2JT', 'Test User')
    u_hash = u.uid_hash
    assert u.check_password('hunter2JT')

    monkeypatch.setitem(app.config, '_JT_SERVER_MODE', 'public')

    u2 = auth_service.confirm_user(session, u.uid_hash)
    rv = auth_service.change_password(
        session,
        u2.uid_hash,
        'hunter2JT',
        'aSecu43Pa55w0rd',
        logout_sessions=False,
    )

    assert 'token' in rv
    assert 'user' in rv

    u3 = auth_service.load_user_by_email(session, 'test@jadetree.io')
    assert u3.check_password('aSecu43Pa55w0rd')
    assert u_hash == u3.uid_hash


def test_change_user_password_invalid_hash(app, session, monkeypatch):
    """Ensure a user password with an invalid User ID hash is rejected."""
    monkeypatch.setitem(app.config, '_JT_SERVER_MODE', 'public')

    with pytest.raises(NoResults) as excinfo:
        auth_service.change_password(
            session,
            '0',
            'hunter2JT',
            'aSecu43Pa55w0rd',
            logout_sessions=False,
        )

    assert 'Could not find' in str(excinfo.value)


def test_change_user_password_inactive(app, session, monkeypatch):
    """Ensure an inactive user cannot change their password."""
    monkeypatch.setitem(app.config, '_JT_SERVER_MODE', 'public')

    u = auth_service.register_user(session, 'test@jadetree.io', 'hunter2JT', 'Test User')
    with pytest.raises(AuthError) as excinfo:
        auth_service.change_password(
            session,
            u.uid_hash,
            'hunter2JT',
            'aSecu43Pa55w0rd',
            logout_sessions=False,
        )

    assert 'is not active' in str(excinfo.value)


def test_user_list_personal(app, session, monkeypatch):
    """Ensure a list of authorized users can be generated in Personal mode."""
    monkeypatch.setitem(app.config, '_JT_SERVER_MODE', 'personal')

    u = auth_service.register_user(session, 'test@jadetree.io', 'hunter2JT', 'Test User')
    users = auth_service.auth_user_list(session)

    assert len(users) == 1
    assert users[0] == u


def test_user_list_family(app, session, monkeypatch):
    """Ensure a list of authorized users can be generated in Family mode."""
    monkeypatch.setitem(app.config, '_JT_SERVER_MODE', 'family')

    u1 = auth_service.register_user(session, 'test@jadetree.io', 'hunter2JT', 'Test User')
    u2 = auth_service.register_user(session, 'test2@jadetree.io', 'hunter2JT', 'Test User 2')
    users = auth_service.auth_user_list(session)

    assert len(users) == 2
    assert users[0] == u1
    assert users[1] == u2


def test_user_list_public(app, session, monkeypatch):
    """Ensure the authorized user list is not available in Public mode."""
    monkeypatch.setitem(app.config, '_JT_SERVER_MODE', 'public')
    with pytest.raises(DomainError):
        auth_service.auth_user_list(session)
