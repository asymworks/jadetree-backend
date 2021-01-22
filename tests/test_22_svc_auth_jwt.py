# =============================================================================
#
# Jade Tree Personal Budgeting Application | jadetree.io
# Copyright (c) 2020 Asymworks, LLC.  All Rights Reserved.
#
# =============================================================================

import datetime

import jwt
import pytest

from jadetree.exc import JwtExpiredTokenError, JwtInvalidTokenError, JwtPayloadError
from jadetree.service import auth as auth_service

RS256_PRIV_KEY = b'''-----BEGIN RSA PRIVATE KEY-----
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
-----END RSA PRIVATE KEY-----'''

RS256_PUB_KEY = b'''-----BEGIN PUBLIC KEY-----
MIICIjANBgkqhkiG9w0BAQEFAAOCAg8AMIICCgKCAgEAowoEwlHPSbvloiDfTcI9
bET4Hk0HdOdZNWtjn4tx4p27l8eygd4w++UL69OHxjsAxSImFBWbfPv+q9o1nvMv
ivGpINFwonwa1ulL8Y8BeqXfywOa+f9dskmK5vAYAQk9AEjnC7p2BzIcN0jLyRxv
5y6YyiRWLnZyZJS8BStpw6vWI9BohXI2YSg8Yobs/tcQjG6wfmuYDYxqaHarfFJG
0VYrtApLitD9Tmn5XWiEcgFKQD16SlvO+xjYCeGwR/JWFQzyd8BeyKdU2lWYwlc1
fHViNuxLhckoB0mvRxIVvuLTVrOFL8VigWvYbgo4QZCyhtAEiiOPkMl1e11O0Vrf
eyt5zQpXKHV80/gJ8TwXn9P/yKdtHEOyH2sFgK2uLb+FdgZnODf2cCU1Cc6VL9Ke
MQsdcWtrDmrEX8cOeHY5YF++jAiMg5vkG3Hp0+deYm1+hyTpR+wVyTGatLT30+Ro
A7lDI7tjOcpf205B29QClvQwkBcb3Ix7F8DXkpOe5QjgMgrTV2rRs2GRwj36Zez8
Vur/96hA3zkNLjlDSYOTCACPfr4OehTM/K6VzBY73KjrYdAE6iKfPiQZaBDU8ug1
rmarDUp+qKkQN91PlF+OdD0dmYUKHB+PJm8S/5PxOX65ZA4kXXy1QPZi59DEFPpM
I/ZyTgtKsT0dFQE9xpe6Qa0CAwEAAQ==
-----END PUBLIC KEY-----'''


def test_gen_valid_jwt(app):
    '''Ensure the auth_service.encodeJwt function generates a valid JWT'''
    token = auth_service.encodeJwt(
        app,
        subject='urn:jadetree.auth.register'
    )

    payload = jwt.decode(token, verify=False)

    assert payload is not None
    assert 'iat' in payload
    assert 'iss' in payload
    assert 'aud' in payload
    assert 'sub' in payload

    assert len(payload.keys()) == 4


def test_decode_jwt(app):
    '''
    Ensure the auth_service.decodeJwt can decode a token generated by
    auth_service.encodeJwt
    '''
    token = auth_service.encodeJwt(
        app,
        subject='urn:jadetree.auth.register'
    )

    payload = auth_service.decodeJwt(app, token)

    assert payload is not None
    assert 'iat' in payload
    assert 'iss' in payload
    assert 'aud' in payload
    assert 'sub' in payload


def test_invalid_jwt(app):
    '''
    Ensure an exception is raised when auth_service.decodeJwt is provided
    an invalid token
    '''
    with pytest.raises(JwtInvalidTokenError):
        auth_service.decodeJwt(app, 'not-a-token')


def test_invalid_jwt_unsigned(app):
    '''
    Ensure an exception is raised when auth_service.decodeJwt is provided
    a valid token with an invalid algorithm (e.g. RSA)
    '''
    token = jwt.encode(
        {
            'iat':  datetime.datetime.utcnow(),
            'iss':  'urn:jadetree.auth',
            'aud':  [ 'urn:jadetree.auth' ],
            'sub':  'urn:jadetree.auth.register',
        },
        None,
        algorithm='none'
    )

    with pytest.raises(JwtInvalidTokenError) as excinfo:
        auth_service.decodeJwt(app, token)

    assert excinfo.value.token_key == 'alg'


def test_invalid_jwt_badalgo(app):
    '''
    Ensure an exception is raised with the Token is not signed
    '''
    token = jwt.encode(
        {
            'iat':  datetime.datetime.utcnow(),
            'iss':  'urn:jadetree.auth',
            'aud':  [ 'urn:jadetree.auth' ],
            'sub':  'urn:jadetree.auth.register',
        },
        RS256_PRIV_KEY,
        algorithm='RS256'
    )

    # Ensure it decodes successfully with RSA256
    jwt.decode(
        token,
        RS256_PUB_KEY,
        algorithms=['RS256'],
        issuer='urn:jadetree.auth',
        audience='urn:jadetree.auth',
    )

    # Ensure it raises an exception with HS256
    with pytest.raises(JwtInvalidTokenError) as excinfo:
        auth_service.decodeJwt(app, token)

    assert excinfo.value.token_key == 'alg'


def test_invalid_jwt_signature(app):
    '''
    Ensure an exception is raised when auth_service.decodeJwt is provided
    a valid token with an invalid signature
    '''
    token = auth_service.encodeJwt(
        app,
        subject='urn:jadetree.auth.register'
    )

    # Invalidate the Token by setting the final
    if token.decode()[-2:] == '44':
        token = token[:-2] + b'55'
    else:
        token = token[:-2] + b'44'

    with pytest.raises(JwtInvalidTokenError):
        auth_service.decodeJwt(app, token)


def test_invalid_jwt_subject_missing_encode(app):
    '''
    Ensure an exception is raised when auth_service.encodeJwt is provided
    a valid token with a missing subject
    '''
    with pytest.raises(JwtPayloadError, match='Missing subject claim'):
        auth_service.encodeJwt(app)


def test_invalid_jwt_subject_decode(app):
    '''
    Ensure an exception is raised when auth_service.decodeJwt is provided
    a valid token with a missing subject
    '''
    token = jwt.encode(
        {
            'iat':  datetime.datetime.utcnow(),
            'iss':  'urn:jadetree.test',
            'aud':  [ 'urn:jadetree.test' ],
        },
        app.config['APP_TOKEN_KEY'],
        algorithm='HS256'
    )

    with pytest.raises(JwtInvalidTokenError) as excinfo:
        auth_service.decodeJwt(app, token, subject='urn:jadetree.auth.register')

    assert excinfo.value.token_key == 'sub'


def test_invalid_jwt_subject_invalid(app):
    '''
    Ensure an exception is raised when auth_service.decodeJwt is provided
    a valid token with an invalid subject
    '''
    token = auth_service.encodeJwt(
        app,
        subject='urn:jadetree.auth.login'
    )

    with pytest.raises(JwtPayloadError, match='Invalid subject claim'):
        auth_service.decodeJwt(app, token, subject='urn:jadetree.auth.register')


def test_invalid_jwt_payload_missing(app):
    '''
    Ensure an exception is raised when auth_service.decodeJwt is provided
    a valid token with a missing payload key
    '''
    token = auth_service.encodeJwt(
        app,
        subject='urn:jadetree.auth.login'
    )

    with pytest.raises(JwtPayloadError, match='Missing or invalid key nonce in payload'):
        auth_service.decodeJwt(
            app,
            token,
            subject='urn:jadetree.auth.login',
            nonce='abc',
        )


def test_invalid_jwt_payload_invalid(app):
    '''
    Ensure an exception is raised when auth_service.decodeJwt is provided
    a valid token with a invalid payload key
    '''
    token = auth_service.encodeJwt(
        app,
        subject='urn:jadetree.auth.login',
        nonce='def',
    )

    with pytest.raises(JwtPayloadError, match='Missing or invalid key nonce in payload'):
        auth_service.decodeJwt(
            app,
            token,
            subject='urn:jadetree.auth.login',
            nonce='abc',
        )


def test_invalid_jwt_immature(app):
    '''
    Ensure an exception is raised when auth_service.decodeJwt is provided a
    valid token with a not-valid before time in the future
    '''
    now = datetime.datetime.utcnow()
    token = auth_service.encodeJwt(
        app,
        subject='urn:jadetree.auth.login',
        nbf=now + datetime.timedelta(minutes=1)
    )

    with pytest.raises(JwtInvalidTokenError, match='token is not yet valid') as excinfo:
        auth_service.decodeJwt(
            app,
            token,
            subject='urn:jadetree.auth.login',
        )

    assert excinfo.value.token_key == 'nbf'


def test_invalid_jwt_expired(app):
    '''
    Ensure an exception is raised when auth_service.decodeJwt is provided a
    valid token with an expiration date in the past
    '''
    now = datetime.datetime.utcnow()
    token = auth_service.encodeJwt(
        app,
        subject='urn:jadetree.auth.login',
        exp=now - datetime.timedelta(minutes=1)
    )

    with pytest.raises(JwtExpiredTokenError, match='Signature has expired'):
        auth_service.decodeJwt(
            app,
            token,
            subject='urn:jadetree.auth.login',
        )


def test_invalid_jwt_audience(app):
    '''
    Ensure an exception is raised when auth_service.decodeJwt is provided a
    valid token with an invalid audience
    '''
    token = auth_service.encodeJwt(
        app,
        subject='urn:jadetree.auth.login',
        audience='abc'
    )

    with pytest.raises(JwtInvalidTokenError, match='Invalid audience') as excinfo:
        auth_service.decodeJwt(
            app,
            token,
            subject='urn:jadetree.auth.login',
            audience='def'
        )

    assert excinfo.value.token_key == 'aud'


def test_invalid_jwt_issuer(app):
    '''
    Ensure an exception is raised when auth_service.decodeJwt is provided a
    valid token with an invalid issuer
    '''
    token = auth_service.encodeJwt(
        app,
        subject='urn:jadetree.auth.login',
        issuer='abc'
    )

    with pytest.raises(JwtInvalidTokenError, match='Invalid issuer') as excinfo:
        auth_service.decodeJwt(
            app,
            token,
            subject='urn:jadetree.auth.login',
            issuer='def'
        )

    assert excinfo.value.token_key == 'iss'


def test_invalid_jwt_issued_at(app):
    '''
    Ensure an exception is raised when auth_service.decodeJwt is provided
    a valid token with a missing subject
    '''
    token = jwt.encode(
        {
            'iat':  'abc',
            'iss':  'urn:jadetree.test',
            'aud':  [ 'urn:jadetree.test' ],
            'sub':  'urn:jadetree.auth.login',
        },
        app.config['APP_TOKEN_KEY'],
        algorithm='HS256'
    )

    with pytest.raises(JwtInvalidTokenError) as excinfo:
        auth_service.decodeJwt(app, token, subject='urn:jadetree.auth.login')

    assert excinfo.value.token_key == 'iat'


def test_invalid_jwt_missing_issuer(app):
    '''
    Ensure an exception is raised when auth_service.decodeJwt is provided
    a valid token with a missing issuer
    '''
    token = jwt.encode(
        {
            'iat':  datetime.datetime.utcnow(),
            'aud':  [ 'urn:jadetree.test' ],
            'sub':  'urn:jadetree.auth.login',
        },
        app.config['APP_TOKEN_KEY'],
        algorithm='HS256'
    )

    with pytest.raises(JwtInvalidTokenError) as excinfo:
        auth_service.decodeJwt(app, token, subject='urn:jadetree.auth.login')

    assert excinfo.value.token_key == 'iss'


def test_generate_jwt_default_expiration(app, session):
    '''
    Ensure a token can be generated for a user with default expiration time
    '''
    config_exp = app.config.get('TOKEN_VALID_INTERVAL', None)
    if config_exp is not None:
        del app.config['TOKEN_VALID_INTERVAL']

    u = auth_service.register_user(session, 'test@jadetree.io', 'hunter2JT', 'Test User')
    token = auth_service.generate_user_token(u, 'urn:jadetree.auth.test')
    payload = auth_service.decodeJwt(app, token, subject='urn:jadetree.auth.test')

    if config_exp is not None:
        app.config['TOKEN_VALID_INTERVAL'] = config_exp

    now = datetime.datetime.utcnow()
    exp = datetime.datetime.utcfromtimestamp(payload['exp'])

    # Ensure default expiration was assigned (+/- 1 sec)
    assert abs((exp - now).total_seconds() - 7200) <= 1


def test_generate_jwt_config_expiration(app, session):
    '''
    Ensure a token can be generated for a user with expiration time set from
    application config
    '''
    config_exp = app.config.get('TOKEN_VALID_INTERVAL', None)
    app.config['TOKEN_VALID_INTERVAL'] = 7300

    u = auth_service.register_user(session, 'test@jadetree.io', 'hunter2JT', 'Test User')
    token = auth_service.generate_user_token(u, 'urn:jadetree.auth.test')
    payload = auth_service.decodeJwt(app, token, subject='urn:jadetree.auth.test')

    if config_exp is not None:
        app.config['TOKEN_VALID_INTERVAL'] = config_exp

    now = datetime.datetime.utcnow()
    exp = datetime.datetime.utcfromtimestamp(payload['exp'])

    # Ensure default expiration was assigned (+/- 1 sec)
    print(payload)
    assert abs((exp - now).total_seconds() - 7300) <= 1


def test_generate_jwt_fixed_expiration(app, session):
    '''
    Ensure a token can be generated for a user with expiration time set from
    a keyword argument
    '''
    config_exp = app.config.get('TOKEN_VALID_INTERVAL', None)
    if config_exp != 7200:
        app.config['TOKEN_VALID_INTERVAL'] = 7200

    u = auth_service.register_user(session, 'test@jadetree.io', 'hunter2JT', 'Test User')
    token = auth_service.generate_user_token(u, 'urn:jadetree.auth.test', 7400)
    payload = auth_service.decodeJwt(app, token, subject='urn:jadetree.auth.test')

    if config_exp is not None:
        app.config['TOKEN_VALID_INTERVAL'] = config_exp

    now = datetime.datetime.utcnow()
    exp = datetime.datetime.utcfromtimestamp(payload['exp'])

    # Ensure default expiration was assigned (+/- 1 sec)
    print(payload)
    assert abs((exp - now).total_seconds() - 7400) <= 1
