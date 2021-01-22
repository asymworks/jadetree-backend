# =============================================================================
#
# Jade Tree Personal Budgeting Application | jadetree.io
# Copyright (c) 2020 Asymworks, LLC.  All Rights Reserved.
#
# =============================================================================

# Authorization and Authentication Services

import datetime

from arrow import utcnow
from flask import current_app
import jwt

from jadetree.domain.models import User
from jadetree.exc import (
    AuthError,
    DomainError,
    JwtExpiredTokenError,
    JwtInvalidTokenError,
    JwtPayloadError,
    NoResults,
)

from .util import check_session
from .validator import (
    EmailValidator,
    HasLowerCaseValidator,
    HasNumberValidator,
    HasUpperCaseValidator,
    LengthValidator,
)

# JWT Subjects for Jade Tree
JWT_SUBJECT_BEARER_TOKEN = 'urn:jadetree.auth.bearer'
JWT_SUBJECT_CANCEL_EMAIL = 'urn:jadetree.auth.cancel'
JWT_SUBJECT_CONFIRM_EMAIL = 'urn:jadetree.auth.confirm'


def decodeJwt(app, token, leeway=None, **kwargs):
    '''
    Decode a JSON Web Token (JWT) which is signed using the HMAC-SHA
    {256,384,512} with the provided key. Required claims are passed with
    keyword arguments.

    :param app: Jade Tree Flask application instance
    :type app: :class:`flask.Flask`
    :param token: JSON Web Token string
    :type token: str
    :param leeway: Leeway for ``exp`` and ``nbf`` claim validation (in
        seconds)
    :type leeway: int or :class:`datetime.timedelta`
    :return: Decoded token payload
    :raises jadetree.exc.JwtInvalidTokenError: when the token is not a
        valid JWT or has an invalid field setting
    :raises jadetree.exc.JwtExpiredTokenError: when the token is expired
    :raises jadetree.exc.JwtPayloadError: when the token has an invalid
        subject or other payload claim
    '''
    req_claims = dict()
    req_claims['issuer'] = kwargs.pop(
        'issuer',
        app.config.get('APP_TOKEN_ISSUER', 'urn:jadetree.auth')
    )
    req_claims['audience'] = kwargs.pop(
        'audience',
        app.config.get('APP_TOKEN_AUDIENCE', 'urn:jadetree.auth')
    )

    try:
        payload = jwt.decode(
            token,
            app.config['APP_TOKEN_KEY'],
            algorithms=['HS256', 'HS384', 'HS512'],
            leeway=leeway or 0,
            **req_claims
        )

    except jwt.exceptions.ExpiredSignatureError as e:
        raise JwtExpiredTokenError(str(e))

    except jwt.exceptions.InvalidAlgorithmError as e:
        raise JwtInvalidTokenError(e, token_key='alg')

    except jwt.exceptions.InvalidAudienceError as e:
        raise JwtInvalidTokenError(e, token_key='aud')

    except jwt.exceptions.InvalidIssuerError as e:
        raise JwtInvalidTokenError(e, token_key='iss')

    except jwt.exceptions.InvalidIssuedAtError as e:
        raise JwtInvalidTokenError(e, token_key='iat')

    except jwt.exceptions.ImmatureSignatureError as e:
        raise JwtInvalidTokenError(e, token_key='nbf')

    except jwt.exceptions.MissingRequiredClaimError as e:
        raise JwtInvalidTokenError(e, token_key=e.claim)

    except jwt.exceptions.PyJWTError as e:
        raise JwtInvalidTokenError(e)

    if 'subject' in kwargs:
        if 'sub' not in payload:
            raise JwtInvalidTokenError(
                'Missing subject claim',
                token_key='sub'
            )
        if payload['sub'] != kwargs.pop('subject'):
            raise JwtPayloadError(
                'Invalid subject claim',
                payload_key='sub'
            )

    for k, v in kwargs.items():
        if k not in payload or payload[k] != v:
            raise JwtPayloadError(
                f'Missing or invalid key {k} in payload',
                payload_key=k
            )

    return payload


def encodeJwt(app, **kwargs):
    '''
    Generate a JSON Web Token (JWT) which is signed using HS256 with the
    provided key. Subject claims are passed with keyword arguments.
    '''
    iat_ts = kwargs.pop('issued', datetime.datetime.utcnow())
    if isinstance(iat_ts, datetime.datetime):
        iat_ts = iat_ts.replace(tzinfo=datetime.timezone.utc).timestamp()

    payload = dict()
    payload['iat'] = iat_ts
    payload['iss'] = kwargs.pop(
        'issuer',
        app.config.get('APP_TOKEN_ISSUER', 'urn:jadetree.auth')
    )
    payload['aud'] = kwargs.pop(
        'audience',
        app.config.get('APP_TOKEN_AUDIENCE', 'urn:jadetree.auth')
    )
    payload['sub'] = kwargs.pop('subject', None)
    payload.update(kwargs)

    if 'sub' not in payload or payload['sub'] is None:
        raise JwtPayloadError('Missing subject claim')

    if isinstance(payload['aud'], str):
        payload['aud'] = [payload['aud']]

    return jwt.encode(
        payload,
        app.config['APP_TOKEN_KEY'],
        algorithm='HS256'
    )


def generate_user_token(user, subject, expiration=None, **kwargs):
    '''
    Generate a JWT for the user with the given subject, optional token
    expiration interval (application default is used otherwise), and
    containing the user hash along with any other provided arguments.

    :param user: User for whom to generate a secure token
    :type user: ~jadetree.models.User
    :param subject: JWT subject claim
    :type subject: str
    :param expiration: token expiration interval in seconds
    :type expiration: int or :class:`~datetime.timedelta`
    '''
    if expiration is None:
        expiration = current_app.config.get('TOKEN_VALID_INTERVAL', 7200)
    if not isinstance(expiration, datetime.timedelta):
        expiration = datetime.timedelta(seconds=expiration)

    dt = datetime.datetime.utcnow()
    if 'issued' in kwargs and isinstance(kwargs['issued'], datetime.datetime):
        dt = kwargs['issued']

    exp = dt.replace(tzinfo=datetime.timezone.utc) + expiration

    return encodeJwt(
        current_app,
        subject=subject,
        exp=exp,
        uid=user.uid_hash,
        **kwargs
    )


def get_user(session, id):
    '''
    Load a User Instance by User ID

    :param session: Database session
    :type session: ~sqlalchemy.orm.session.Session
    :param id: User Id (Primary Key)
    :type id: int
    :returns: User object with the given id or None
    :rtype: :class:`User`
    '''
    return session.query(User).filter(User.id == id).one_or_none()


def load_user_by_email(session, email):
    '''
    Load a User Instance by Email Address

    :param session: Database session
    :type session: ~sqlalchemy.orm.session.Session
    :param uid_hash: User Email Address (`User.email`)
    :type uid_hash: str
    :returns: User object with the given email or None
    :rtype: :class:`User`
    '''
    return session.query(User).filter(User.email == email).one_or_none()


def load_user_by_hash(session, uid_hash):
    '''
    Load a User Instance by User ID Hash

    :param session: Database session
    :type session: ~sqlalchemy.orm.session.Session
    :param uid_hash: User ID Hash (`User.uid_hash`)
    :type uid_hash: str
    :returns: User object with the given hash or None
    :rtype: :class:`User`
    '''
    return session.query(User).filter(User.uid_hash == uid_hash).one_or_none()


def load_user_by_token(session, token):
    '''
    Load a User Instance from a JWT Bearer Token

    :param session: Database session
    :type session: ~sqlalchemy.orm.session.Session
    :param token: Bearer Token from HTTP Authorization Header, stripped of the
        "Bearer " prefix
    :type token: str
    :returns: User object with the given hash or None
    :rtype: :class:`User`
    :raises jadetree.exc.JwtInvalidTokenError: when the token is not a
        valid JWT or has an invalid field setting
    :raises jadetree.exc.JwtExpiredTokenError: when the token is expired
    :raises jadetree.exc.JwtPayloadError: when the token has an invalid
        subject or other payload claim
    '''
    payload = decodeJwt(
        current_app,
        token,
        leeway=30,
        subject=JWT_SUBJECT_BEARER_TOKEN,
    )

    # Load User Hash from Payload
    if 'uid' not in payload:
        raise JwtPayloadError('Missing uid key', payload_key='uid')

    # Load User from Token Hash
    return load_user_by_hash(session, payload['uid'])


def invalidate_uid_hash(session, uid_hash):
    '''
    Invalidate a user's ID Hash, resulting in all login sessions becoming stale
    and forcing new password logins.  This method does not change the user's
    password.

    :param session: Database session
    :type session: ~sqlalchemy.orm.session.Session
    :param uid_hash: User ID Hash (`User.uid_hash`)
    :type uid_hash: str
    :returns: User object
    :rtype: :class:`User`
    '''
    check_session(session)

    # FIXME: Add Context Manager
    # with session:

    u = load_user_by_hash(session, uid_hash)
    if u is None:
        raise NoResults('Could not find a user with the given hash')

    # Generate a new User Id Hash
    u.uid_hash = u._generate_user_hash()

    session.add(u)
    session.commit()

    return u


def register_user(session, email, password, name):
    '''
    Create a User Object with an email and password. The password must be at
    least eight characters long and contain an upper case letter, a lower
    case letter, and a number. The password will be hashed prior to being
    inserted into the database.

    :param session: Database session
    :type session: ~sqlalchemy.orm.session.Session
    :param email: User email address (must be unique)
    :type email: str
    :param password: User password
    :type password: str
    :param name: User name
    :type name: str
    :returns: User object
    :rtype: :class:`User`
    '''
    check_session(session)

    EmailValidator()(email)

    skip_pw_modes = ('personal', 'family')
    if current_app.config.get('_JT_SERVER_MODE', None) not in skip_pw_modes:
        LengthValidator(
            min=8,
            message='Password must be at least 8 characters long'
        )(password)
        HasLowerCaseValidator(
            message='Password must contain a lower-case letter'
        )(password)
        HasUpperCaseValidator(
            message='Password must contain an upper-case letter'
        )(password)
        HasNumberValidator(
            message='Password must contain a number'
        )(password)

        if session.query(User).filter(User.email == email).first() is not None:
            raise ValueError(
                f'A user with email address {email} already exists'
            )

    # FIXME: Add Context Manager
    # with session:

    u = User(email=email, name=name)
    u.set_password(password or '')
    u.active = False
    u.confirmed = False
    u.created_at = utcnow()

    session.add(u)
    session.commit()

    return u


def confirm_user(session, uid_hash):
    '''
    Confirm a user's registration status, and set the user to the active state
    so they can log in to Jade Tree.

    :param session: Database session
    :type session: ~sqlalchemy.orm.session.Session
    :param uid_hash: User ID Hash (`User.uid_hash`)
    :type uid_hash: str
    :returns: User object
    :rtype: :class:`User`
    '''
    check_session(session)

    # FIXME: Add Context Manager
    # with session:

    u = load_user_by_hash(session, uid_hash)
    if u is None:
        raise NoResults('Could not find a user with the given hash')

    if u.confirmed:
        raise DomainError(
            f'User already confirmed {u.confirmed_at.humanize()}'
        )

    u.active = True
    u.confirmed = True
    u.confirmed_at = utcnow()

    session.add(u)
    session.commit()

    return u


def login_user(session, email, password):
    '''
    Log a user in to Jade Tree and return the user and the authorization token
    '''
    check_session(session)

    u = load_user_by_email(session, email)
    if u is None:
        raise AuthError('Invalid credentials', status_code=401)

    if current_app.config['_JT_SERVER_MODE'] not in ('family, personal'):
        if not u.check_password(password):
            raise AuthError('Invalid credentials', status_code=401)

    # Generate Token
    token = generate_user_token(
        u,
        JWT_SUBJECT_BEARER_TOKEN,
        # Expiration time set to 1 year
        expiration=31536000,
    )

    # Return Token
    return { 'token': token, 'user': u }


def auth_user_list(session):
    '''
    Load the list of available server users, when the server is in Personal
    or Family mode. The tokens returned will have an issued-at date set to the
    user's creation time, and the expiration date will be 100 years after that
    time, effectively not expiring.

    :param session: Database session
    :type session: ~sqlalchemy.orm.session.Session
    :returns: list of `User` objects
    :rtype: list
    '''
    check_session(session)

    if current_app.config['_JT_SERVER_MODE'] not in ('family', 'personal'):
        raise DomainError(
            'auth_user_list() may only be called when the server mode '
            'is "personal" or "family".'
        )

    return session.query(User).filter(
        User.active == True,        # noqa: E712
        User.confirmed == True,     # noqa: E712
    ).all()
