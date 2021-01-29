"""Jade Tree Server Setup Services.

Jade Tree Personal Budgeting Application | jadetree.io
Copyright (c) 2020 Asymworks, LLC.  All Rights Reserved.
"""

import datetime

from flask import current_app, request

from jadetree.database import db
from jadetree.database.tables import jadetree_config
from jadetree.exc import Error
from jadetree.service import auth as auth_service
from jadetree.service.util import check_session

__all__ = (
    'init_setup', 'jt_config_get', 'jt_config_has', 'jt_config_set',
    'setup_jadetree'
)

JT_SERVER_MODES = ('personal', 'family', 'public')


def jt_config_has(key):
    """Check if a Jade Tree Configuration Value exists in the Database."""
    q = db.select([jadetree_config.c.key]).where(jadetree_config.c.key == key)
    return db.engine.execute(q).scalar() is not None


def jt_config_get(key, default=None):
    """Get a Jade Tree Configuration Value from the Database."""
    q = db.select([jadetree_config.c.value]).where(jadetree_config.c.key == key)
    return db.engine.execute(q).scalar() or default


def jt_config_set(key, value):
    """Set a Jade Tree Configuration Value in the Database."""
    q = jadetree_config.insert().values(key=key, value=value)
    if jt_config_has(key):
        q = jadetree_config.update().values(
            value=value
        ).where(
            jadetree_config.c.key == key
        )

    with db.engine.begin() as conn:
        conn.execute(q)


def setup_jadetree(session, **kwargs):
    """Set up the Jade Tree Server.

    Runs initial setup tasks for Jade Tree and populates the Jade Tree settings
    database table.
    """
    check_session(session)

    if current_app.config.get('_JT_DB_NEEDS_UPGRADE'):
        message = 'Database schema needs to be upgraded. Please run ' \
            "'flask db upgrade' and restart the server to complete the " \
            'automated setup.'
        raise Error(message)

    # Ensure the server mode and user email are set
    if 'mode' not in kwargs:
        raise Error('Server mode was not specified', status_code=422)
    if kwargs['mode'] not in JT_SERVER_MODES:
        raise Error('Invalid server mode "{}"'.format(kwargs['mode']))
    if 'email' not in kwargs:
        raise Error('User email address was not specified', status_code=422)

    server_mode = kwargs.pop('mode')
    user_email = kwargs.pop('email')
    user_password = kwargs.pop('password', None)
    user_name = kwargs.pop('name', None)

    if len(kwargs) > 0:
        raise Error(
            'Unexpected keys "{}" in setup_jadetree'.format(
                ', '.join(kwargs.keys())
            )
        )

    # Ensure a password is provided for public servers
    if server_mode == 'public' and user_password is None:
        raise Error(
            'Administrator user password must be provided to set up a '
            'public server'
        )

    # Set the Server Mode so that register_user knows not to require a
    # password for 'personal' or 'family' modes
    current_app.config['_JT_SERVER_MODE'] = server_mode

    # Register and Confirm the User
    u = auth_service.register_user(
        session,
        user_email,
        user_password,
        user_name,
    )

    if not u.active:
        u = auth_service.confirm_user(session, u.uid_hash, user_email)

    # Store the Setup Date and Server Mode
    jt_config_set('setup', datetime.date.today().isoformat())
    jt_config_set('server_mode', server_mode)

    # Update Configuration
    current_app.config['_JT_NEEDS_SETUP'] = False
    current_app.config['DEFAULT_CURRENCY'] = jt_config_get(
        'server_currency',
        current_app.config.get('FALLBACK_CURRENCY', 'USD')
    )
    current_app.config['DEFAULT_LANGUAGE'] = jt_config_get(
        'server_language',
        current_app.config.get('FALLBACK_LANGUAGE', 'en')
    )
    current_app.config['DEFAULT_LOCALE'] = jt_config_get(
        'server_locale',
        current_app.config.get('FALLBAK_LOCALE', 'en_US')
    )


def auto_setup(app):
    """Automatically set up Jade Tree from the application configuration."""
    if app.config.get('_JT_DB_NEEDS_UPGRADE'):
        message = 'Database schema needs to be upgraded. Please run ' \
            "'flask db upgrade' and restart the server to complete the " \
            'automated setup.'
        app.logger.error(message)
        return False

    server_mode = app.config.get('SERVER_MODE', None)
    if server_mode not in ('personal', 'family'):
        message = 'Automated setup is only available for servers running in ' \
            "'personal' or 'family' mode."
        app.logger.error(message)
        return False

    if app.config.get('USER_EMAIL', None) is None:
        message = 'A user email address must be specified in the server ' \
            'configuration settings to use automated setup.'
        app.logger.error(message)
        return False

    setup_args = dict(mode=server_mode)
    user_keys = ('email', 'name', 'language', 'locale', 'currency')
    for key in user_keys:
        cfg_key = f'USER_{key.upper()}'
        if cfg_key in app.config:
            setup_args[key] = app.config[cfg_key]

    setup_jadetree(app, db.session, **setup_args)


def ensure_setup():
    """Ensure that the Server Setup has completed before each request."""
    if current_app.config['_JT_NEEDS_SETUP']:
        # Special blueprint names are exempted
        if request.blueprint not in ('version', 'setup'):
            raise Error('Jade Tree server is not yet set up', status_code=500)


def init_setup(app):
    """Register the Setup Service with the Application."""
    if app.config.get('_JT_DB_NEEDS_INIT'):
        return

    needs_setup = False
    with app.app_context():
        needs_setup = not jt_config_has('setup')

    # If we can setup the server automatically
    if needs_setup:
        app.config['_JT_NEEDS_SETUP'] = needs_setup
        app.logger.info(
            'Welcome to your new Jade Tree server. Please set up the '
            'server via the setup script or web application before use.'
        )

        app.before_request(ensure_setup)

    # Load server settings from the configuration database
    else:
        with app.app_context():
            app.config['_JT_SERVER_MODE'] = jt_config_get(
                'server_mode',
                app.config.get('SERVER_MODE', 'public')
            )
            app.config['DEFAULT_CURRENCY'] = jt_config_get(
                'server_currency',
                app.config.get('FALLBACK_CURRENCY', 'USD')
            )
            app.config['DEFAULT_LANGUAGE'] = jt_config_get(
                'server_language',
                app.config.get('FALLBACK_LANGUAGE', 'en')
            )
            app.config['DEFAULT_LOCALE'] = jt_config_get(
                'server_locale',
                app.config.get('FALLBAK_LOCALE', 'en_US')
            )

    # Notify Initialization
    app.logger.debug('Setup Service Initialized')
