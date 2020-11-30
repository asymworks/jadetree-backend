# =============================================================================
#
# Jade Tree Personal Budgeting Application | jadetree.io
# Copyright (c) 2020 Asymworks, LLC.  All Rights Reserved.
#
# =============================================================================

import pytest   # noqa: F401

from arrow import utcnow
import datetime

from jadetree.domain.models import User
from jadetree.exc import DomainError, NoResults, JwtPayloadError
from jadetree.service import auth as auth_service
from jadetree.service.auth import JWT_SUBJECT_BEARER_TOKEN


def test_register_user_adds_user(session):
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
    auth_service.register_user(session, 'test@jadetree.io', 'hunter2JT', 'Test User')
    with pytest.raises(ValueError) as exc_data:
        auth_service.register_user(session, 'test@jadetree.io', 'hunter2JTa', 'Test User')
    assert len(session.query(User).all()) == 1
    assert 'already exists' in str(exc_data.value)


def test_register_user_throws_bad_email(session):
    with pytest.raises(ValueError) as exc_data:
        auth_service.register_user(session, 'jadetree', 'hunter2JT', 'Test User')
    assert len(session.query(User).all()) == 0
    assert 'Invalid Email Address' in str(exc_data.value)


def test_register_user_throws_bad_pw_short(session):
    with pytest.raises(ValueError) as exc_data:
        auth_service.register_user(session, 'test@jadetree.io', 'aBc5', 'Test User')
    assert len(session.query(User).all()) == 0
    assert 'Password' in str(exc_data.value)
    assert 'at least 8 characters' in str(exc_data.value)


def test_register_user_throws_bad_pw_lowercase(session):
    with pytest.raises(ValueError) as exc_data:
        auth_service.register_user(session, 'test@jadetree.io', 'HUNTER2JT', 'Test User')
    assert len(session.query(User).all()) == 0
    assert str(exc_data.value) == 'Password must contain a lower-case letter'


def test_register_user_throws_bad_pw_uppercase(session):
    with pytest.raises(ValueError) as exc_data:
        auth_service.register_user(session, 'test@jadetree.io', 'hunter2jt', 'Test User')
    assert len(session.query(User).all()) == 0
    assert str(exc_data.value) == 'Password must contain an upper-case letter'


def test_register_user_throws_bad_pw_number(session):
    with pytest.raises(ValueError) as exc_data:
        auth_service.register_user(session, 'test@jadetree.io', 'hunter_JT', 'Test User')
    assert len(session.query(User).all()) == 0
    assert str(exc_data.value) == 'Password must contain a number'


def test_confirm_user(session):
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
    u = auth_service.register_user(session, 'test@jadetree.io', 'hunter2JT', 'Test User')
    assert u.id == 1

    with pytest.raises(NoResults) as exc_data:
        auth_service.confirm_user(session, '0000')

    assert str(exc_data.value) == 'Could not find a user with the given hash'
    assert u.active is False
    assert u.confirmed is False


def test_confirm_user_already_confirmed(session):
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
    nu = auth_service.register_user(session, 'test@jadetree.io', 'hunter2JT', 'Test User')
    assert nu.id == 1

    u = session.query(User).filter(User.id == nu.id).one_or_none()
    assert auth_service.get_user(session, u.id) == nu


def test_get_user_not_exists(session):
    assert auth_service.get_user(session, 1) is None


def test_get_user_invalid(session):
    u = auth_service.register_user(session, 'test@jadetree.io', 'hunter2JT', 'Test User')
    assert u.id == 1

    assert auth_service.get_user(session, 'one') is None


def test_load_user_by_hash(session):
    nu = auth_service.register_user(session, 'test@jadetree.io', 'hunter2JT', 'Test User')
    assert nu.id == 1

    u = session.query(User).filter(User.id == nu.id).one_or_none()
    assert u.uid_hash is not None
    assert auth_service.load_user_by_hash(session, u.uid_hash) == nu


def test_load_user_by_hash_not_exists(session):
    assert auth_service.load_user_by_hash(session, '00000000000000000000000000000000') is None


def test_load_user_by_hash_invalid(session):
    u = auth_service.register_user(session, 'test@jadetree.io', 'hunter2JT', 'Test User')
    assert u.id == 1

    assert auth_service.load_user_by_hash(session, 'one') is None


def test_invalidate_uid_hash(session):
    u = auth_service.register_user(session, 'test@jadetree.io', 'hunter2JT', 'Test User')
    old_id = u.id
    old_hash = u.uid_hash

    nu = auth_service.invalidate_uid_hash(session, old_hash)
    assert nu.id == old_id
    assert nu.uid_hash != old_hash


def test_invalidate_uid_hash_invalid(session):
    auth_service.register_user(session, 'test@jadetree.io', 'hunter2JT', 'Test User')
    with pytest.raises(NoResults, match='Could not find a user'):
        auth_service.invalidate_uid_hash(session, 'xxx')


def test_load_user_by_email(session):
    nu = auth_service.register_user(session, 'test@jadetree.io', 'hunter2JT', 'Test User')
    assert nu.id == 1

    assert auth_service.load_user_by_email(session, 'test@jadetree.io') == nu


def test_load_user_by_token(session):
    nu = auth_service.register_user(session, 'test@jadetree.io', 'hunter2JT', 'Test User')
    assert nu.id == 1

    # load_user_by_token is hardcoded for JWT_SUBJECT_BEARER_TOKEN
    token = auth_service.generate_user_token(nu, JWT_SUBJECT_BEARER_TOKEN)

    assert auth_service.load_user_by_token(session, token) == nu


def test_load_user_by_token_no_uid(app, session):
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
