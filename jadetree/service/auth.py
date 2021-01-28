"""Jade Tree Authorization and Authentication Service.

Jade Tree Personal Budgeting Application | jadetree.io
Copyright (c) 2020 Asymworks, LLC.  All Rights Reserved.
"""

import datetime

from arrow import utcnow
from flask import current_app, render_template
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
from jadetree.mail import send_email

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
    """Decode a JSON Web Token.

    Verifies and decodes a JSON Web Token (JWT) which is signed using HS256
    with the key set in the `APP_TOKEN_KEY` configuration parameter. The token
    payload is returned as a Python dictionary using standard JWT claim names.

    Args:
        app: Jade Tree Flask application instance
        token: JSON Web Token as Base-64 encoded text
        leeway: Leeway in seconds when validating the expiration and not-valid-
            before payload claims
        issuer: Optional; verify that the token issuer URN matches the provided
            value and raise an exception if not
        audience: Optional; verify that the token audience URN matches the
            provied value and raise an exception if not
        **kwargs: Additional keyword arguments are checked for existence within
            the JWT payload and an exception is raised if they are not present
            or do not match the argument value

    Returns:
        A dictionary with the decoded JWT payload,

        {
            'iss': 'urn:issuer',
            'aud': 'urn:audience',
            'sub': 'urn:subject.claim',
            'exp': 12345678,
        }

    Raises:
        JwtExpiredTokenError: When the token is expired
        JwtInvalidTokenError: When the token is not a valid JWT or has an
            invalid field setting
        JwtPayloadError: When the token has an invalid subject or other
            payload claim
    """
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
    """Generate a signed JSON Web Token.

    Generates a JSON Web Token (JWT) which is signed using HS256 with the
    key set in the `APP_TOKEN_KEY` configuration parameter. Subject claims
    are passed with keyword arguments. The `subject` parameter is required,
    but other claims are optional.

    Args:
        app: Jade Tree Flask application instance
        subject: The subject URN of the token. Must be provided to the function
            or an exception is raised.
        issued: Optional; the timestamp or datetime object at which the token
            will report it was issued. Defaults to the current time.
        issuer: Optional; the issuer URN of the token. Defaults to the value
            set in the `APP_TOKEN_ISSUER` configuration setting or to
            `urn:jadetree.auth` if the configuration parameter is not set.
        audience: Optional; the audience URN of the token. Defaults to the
            value set in the `APP_TOKEN_AUDIENCE` configuration setting or to
            `urn:jadetree.auth` if the configuration parameter is not set.

    Returns:
        Signed and encoded JSON Web Token

    Raises:
        JwtPayloadError: If the `subject` claim is not given
    """
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
    """Generate a JWT Bearer Token for a User.

    Generate a JWT for the user with the given subject, optional token
    expiration interval (application default is used otherwise), and
    containing the user hash along with any other provided arguments.

    Args:
        user: User object for which to generate a secure token
        subject: JWT subject claim
        expiration: token expiration interval in seconds
        **kwargs: Extra arguments for encodeJwt

    Returns:
        Encoded and signed JavaScript Web Token
    """
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
    """Load a User Instance by User ID.

    Args:
        session: Database session
        id: User ID

    Returns:
        User object or None if there is no user with the given ID
    """
    return session.query(User).filter(User.id == id).one_or_none()


def load_user_by_email(session, email):
    """Load a User Instance by email address.

    Args:
        session: Database session
        email: Email address

    Returns:
        User object or None if there is no user with the given email
    """
    return session.query(User).filter(User.email == email).one_or_none()


def load_user_by_hash(session, uid_hash):
    """Load a User Instance by User ID hash.

    Args:
        session: Database session
        uid_hash: User ID hash

    Returns:
        User object or None if there is no user with the given ID hash
    """
    return session.query(User).filter(User.uid_hash == uid_hash).one_or_none()


def load_user_by_token(session, token):
    """Load a User instance from a JWT Bearer Token.

    Decodes and verifies a JWT bearer token, and loads a User instance using
    the `uid` field in the token, which is mapped to the User ID hash.

    Args:
        session: Database session
        token: JWT bearer token in Base 64 encoded text

    Returns:
        User object or None if the User ID hash in the token does not match
        a user currently in the database.

    Raises:
        JwtInvalidTokenError: When the token is not a valid JWT or has an
            invalid field setting
        JwtExpiredTokenError: When the token has expired
        JwtPayloadError: When the token has an invalid subject or other
            payload claim
    """
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
    """Change a user's ID hash.

    Changes a user's ID Hash, resulting in all login sessions becoming stale
    and forcing new password logins.  This method does not change the user's
    password.

    Args:
        session: Database session
        uid_hash: User ID hash to change

    Returns:
        updated User object

    Raises:
        NoResults: If a user was not found with the given ID hash
    """
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
    """Register a new User.

    Create a User Object with an email and password. The password must be at
    least eight characters long and contain an upper case letter, a lower
    case letter, and a number. The password will be hashed prior to being
    inserted into the database.

    Args:
        session: Database session
        email: User email address
        password: User password
        name: User name
        confirm: Optional; Set to True to automatically confirm the user's
            registration and email address. Should only be used in cases like
            initial server setup.

    Returns:
        new User object

    Raises:
        ValueError: If the user email address is not unique, or if the password
            does not meet requirements
        DomainError: If the server mode is set to Personal, no new users can be
            registered
    """
    check_session(session)

    server_mode = current_app.config.get('_JT_SERVER_MODE', None)
    if server_mode == 'personal':
        # Only one User can be registered in personal mode
        if session.query(User).count() != 0:
            raise DomainError(
                'Cannot register users when the server mode is set to Personal'
            )

    EmailValidator()(email)

    if not password and server_mode not in ('personal', 'family'):
        raise ValueError('Password must be provided for public mode servers')

    if password:
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

    # Automatically confirm user registration if the server mode is 'personal'
    # or 'family'; otherwise send an email to confirm the email address is
    # valid and the user wants to register. The CONFIRM_REGISTRATION_EMAIL
    # configuration value can override this default.
    send_email = current_app.config.get(
        'CONFIRM_REGISTRATION_EMAIL',
        server_mode not in ('personal', 'family'),
    )
    if send_email:
        # Send the registration confirmation email
        send_confirmation_email(u)

    else:
        # Automatically confirm the user
        u.active = True
        u.confirmed = True
        u.confirmed_at = utcnow()

    session.add(u)
    session.commit()

    return u


def resend_confirmation(session, email):
    """Resend a Registration Confirmation Email.

    Invalidates the User ID Hash and resends the confirmation email with a new
    confirmation and cancellation token.
    """
    check_session(session)

    # FIXME: Add Context Manager
    # with session:
    u = load_user_by_email(session, email)
    if u is None:
        raise NoResults('Could not find a user with the given hash')

    if u.confirmed:
        raise DomainError(
            f'User already confirmed {u.confirmed_at.humanize()}'
        )

    u = invalidate_uid_hash(session, u.uid_hash)
    send_confirmation_email(u)
    return u


def confirm_user(session, uid_hash, email):
    """Confirm a User's Email Address.

    Confirm a user's registration status, and set the user to the active state
    so they can log in to Jade Tree.

    Args:
        session: Database session
        uid_hash: User ID Hash (`User.uid_hash`)
        email: User Email Address

    Returns:
        User object

    Raises:
        NoResults: A user was not found with the given ID hash
        DomainError: If the user has already confirmed their email address
        ValueError: If the email address provided does not match the database
    """
    check_session(session)

    # FIXME: Add Context Manager
    # with session:
    u = load_user_by_hash(session, uid_hash)
    if u is None:
        raise NoResults('Could not find a user with the given hash')

    if email != u.email:
        raise ValueError('Email address does not match database value')

    if u.confirmed:
        raise DomainError(
            f'User already confirmed {u.confirmed_at.humanize()}'
        )

    u.active = True
    u.confirmed = True
    u.confirmed_at = utcnow()

    session.add(u)
    session.commit()

    # Send a Welcome Email if they previously had to confirm their
    # email address
    server_mode = current_app.config.get('_JT_SERVER_MODE', None)
    send_email = current_app.config.get(
        'CONFIRM_REGISTRATION_EMAIL',
        server_mode not in ('personal', 'family'),
    )
    if send_email:
        send_welcome_email(u)

    return u


def cancel_registration(session, email):
    """Cancel a User's Registration.

    Cancels a user's registration and removes the unverified user from the Jade
    Tree database.

    Args:
        session: Database session
        email: User Email Address

    Raises:
        NoResults: A user was not found with the given ID hash
        DomainError: If the user has already confirmed their email address
    """
    check_session(session)

    # FIXME: Add Context Manager
    # with session:

    u = load_user_by_email(session, email)
    if u is None:
        raise NoResults('Could not find a user with the given email address')

    if u.confirmed:
        raise DomainError(
            f'User already confirmed {u.confirmed_at.humanize()}'
        )

    session.delete(u)
    session.commit()


def confirm_user_with_token(session, token):
    """Confirm a User Registration from the Confirmation Token.

    Uses the confirmation token sent in the registration confirmation email to
    confirm user registration. If the token is invalid, the user is already
    confirmed, or the email address in the token does not match the user email
    address, an exception is raised.

    Args:
        session: Database session
        token: JSON Web Token from send_confirmation_email()

    Returns:
        User instance

    Raises:
        JwtInvalidTokenError: When the token is not a valid JWT or has an
            invalid field setting
        JwtExpiredTokenError: When the token has expired
        JwtPayloadError: When the token has an invalid subject or other
            payload claim
        DomainError: When the user is already registered
        ValueError: When the token email address does not match the database
    """
    payload = decodeJwt(
        current_app,
        token,
        leeway=30,
        subject=JWT_SUBJECT_CONFIRM_EMAIL,
    )

    if 'uid' not in payload:
        raise JwtPayloadError('Missing uid claim in token', payload_key='uid')
    if 'email' not in payload:
        raise JwtPayloadError('Missing email claim in token', payload_key='email')

    return confirm_user(session, payload['uid'], payload['email'])


def cancel_registration_with_token(session, token):
    """Cancel a User Registration from the Cancellation Token.

    Uses the confirmation token sent in the registration confirmation email to
    cancel user registration. If the token is invalid or the user is already
    confirmed, an exception is raised.

    Args:
        session: Database session
        token: JSON Web Token from send_confirmation_email()

    Returns:
        User instance

    Raises:
        JwtInvalidTokenError: When the token is not a valid JWT or has an
            invalid field setting
        JwtExpiredTokenError: When the token has expired
        JwtPayloadError: When the token has an invalid subject or other
            payload claim
        DomainError: When the user is already registered
    """
    payload = decodeJwt(
        current_app,
        token,
        leeway=30,
        subject=JWT_SUBJECT_CANCEL_EMAIL,
    )

    if 'email' not in payload:
        raise JwtPayloadError('Missing email claim in token', payload_key='email')

    return cancel_registration(session, payload['email'])


def login_user(session, email, password):
    """Log a user in to Jade Tree and return the authorization token.

    Args:
        session: Database session
        email: User email address
        password: User password

    Returns:
        Dictionary containing a new authorization token and the updated User
        object. The dictionary structure is:

        {
            'token': '<bearer token>',
            'user': User(),
        }

    Raises:
        AuthError: A user was not found with the email address or the password
            was incorrect
    """
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


def change_password(session, uid_hash, current_password, new_password, logout_sessions=True):
    """Change the User's Password.

    Change or set the user password and create a new user hash so that
    any login tokens referencing the current user will be invalidated and
    the sessions must log in again with the new password. Set the
    `logout_sessions` parameter to false to keep all sessions logged in.

    Args:
        uid_hash: User ID hash to load
        current_password: current user password, which must match the currently
            set user password if the Server Mode is set to Public.
        new_password: new user password, which must meet Jade Tree password
            rules
        logout_sessions: Optional; If logout_sessions is False, the user
            id hash will not be updated, and all currently logged in sessions
            can continue. The default is to update the uid_hash value so that
            all currently logged in sessions are required to log in again
            with the new password.

    Returns:
        Dictionary containing a new authorization token and the updated User
        object. The dictionary structure is:

        {
            'token': '<bearer token>',
            'user': User(),
        }

    Raises:
        ValueError: The new password did not meet requirements
        AuthError: The current password did not match
        NoResults: A user was not found with the given ID hash
    """
    check_session(session)

    u = load_user_by_hash(session, uid_hash)
    if u is None:
        raise NoResults('Could not find a user with the given hash')

    if not u.active:
        raise AuthError('User is not active')

    if current_app.config['_JT_SERVER_MODE'] not in ('family, personal'):
        if not u.check_password(current_password):
            raise AuthError(
                'The current password is not correct for the user',
                status_code=401,
            )

        # Validate new password rules
        LengthValidator(
            min=8,
            message='Password must be at least 8 characters long'
        )(new_password)
        HasLowerCaseValidator(
            message='Password must contain a lower-case letter'
        )(new_password)
        HasUpperCaseValidator(
            message='Password must contain an upper-case letter'
        )(new_password)
        HasNumberValidator(
            message='Password must contain a number'
        )(new_password)

    # Update user password
    u.set_password(new_password, logout_sessions)

    session.add(u)
    session.commit()

    # Generate Token
    token = generate_user_token(
        u,
        JWT_SUBJECT_BEARER_TOKEN,
        # Expiration time set to 1 year
        expiration=31536000,
    )

    # Return Token
    return { 'token': token, 'user': u }


def send_confirmation_email(user):
    """Send an email to confirm registration.

    Sends an email to the user containing a registration confirmation token
    and a cancellation token so they can confirm their email address and that
    they intended to register with Jade Tree.  The tokens are JWTs generated
    from the user ID hash and the confirmation expiration time is taken from
    the application configuration `TOKEN_VALID_INTERVAL` setting.  The cancel
    registration token does not expire.
    """
    confirm_token = generate_user_token(
        user,
        JWT_SUBJECT_CONFIRM_EMAIL,
        email=user.email,
    )
    cancel_token = encodeJwt(
        current_app,
        subject=JWT_SUBJECT_CANCEL_EMAIL,
        email=user.email,
    )

    app_title = current_app.config.get('APP_TITLE', 'Jade Tree')
    send_email(
        subject=f'[{app_title}] Confirm Your Registration',
        recipients=user.email,
        body=render_template(
            'email/text/reg-verify.text.j2',
            confirm_token=confirm_token,
            cancel_token=cancel_token,
            email=user.email,
        ),
        html=render_template(
            'email/html/reg-verify.html.j2',
            confirm_token=confirm_token,
            cancel_token=cancel_token,
            email=user.email,
        ),
    )


def send_welcome_email(user):
    """Send an email to welcome user to Jade Tree."""
    app_title = current_app.config.get('APP_TITLE', 'Jade Tree')
    send_email(
        subject=f'[{app_title}] Welcome to {app_title}',
        recipients=user.email,
        body=render_template(
            'email/text/reg-welcome.text.j2', email=user.email,
        ),
        html=render_template(
            'email/html/reg-welcome.html.j2', email=user.email,
        ),
    )


def auth_user_list(session):
    """Return the list of Registered Users.

    Load the list of available server users, when the server is in Personal
    or Family mode. The tokens returned will have an issued-at date set to the
    user's creation time, and the expiration date will be 100 years after that
    time, effectively not expiring.

    Args:
        session: Database Session

    Returns:
        list of `User` objects

    Raises:
        DomainError: If the server is not in Personal or Family mode
    """
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
