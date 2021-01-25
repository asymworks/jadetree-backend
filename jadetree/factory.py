"""Jade Tree Application Factory.

The :mod:`jadetree.factory` module contains a method :func:`create_app` which
implements the Flask `Application Factory`_ pattern to create the application
object dynamically.

Application default configuration values are found in the
:mod:`jadetree.settings` module.

.. _`Application Factory`:
    https://flask.palletsprojects.com/en/1.1.x/patterns/appfactories/

Jade Tree Personal Budgeting Application | jadetree.io
Copyright (c) 2020 Asymworks, LLC.  All Rights Reserved.
"""

import configparser
import os
import pathlib

from flask import Flask


def read_version():
    """Read the Name and Version String from pyproject.toml."""
    # Search for pyproject.toml
    d = pathlib.Path(__file__)
    name = None
    version = None
    while d.parent != d:
        d = d.parent
        path = d / 'pyproject.toml'
        if path.exists():
            # Use configparser to parse toml like INI to avoid dependency on
            # tomlkit or similar
            config = configparser.ConfigParser()
            config.read(str(path))
            if 'tool.poetry' in config:
                name = config['tool.poetry'].get('name').strip('"\'')
                version = config['tool.poetry'].get('version').strip('"\'')
                return (name, version)

    return (None, None)


def create_app(app_config=None, app_name=None):
    """Create and Configure the Flask Application.

    Create and Configure the Application with the Flask `Application Factory`_
    pattern. The `app_config` dictionary will override configuration keys set
    via other methods, and is intended primarily for use in test frameworks to
    provide a predictable configuration for testing.

    Args:
        app_config: Configuration override values which are applied after all
            other configuration sources have been loaded
        app_name: Application name override

    Returns:
        Flask application
    """
    app = Flask(
        'jadetree',
        template_folder='templates'
    )

    # Load Application Name and Version from pyproject.toml
    pkg_name, pkg_version = read_version()
    app.config['APP_NAME'] = pkg_name
    app.config['APP_VERSION'] = pkg_version

    # Load Default Settings
    app.config.from_object('jadetree.settings')

    # Load Configuration File from Environment
    if 'JADETREE_CONFIG' in os.environ:
        app.config.from_envvar('JADETREE_CONFIG')

    # Load Configuration Variables from Environment
    for k, v in os.environ.items():
        if k.startswith('JADETREE_') and k != 'JADETREE_CONFIG':
            app.config[k[9:]] = v

    # Load Factory Configuration
    if app_config is not None:
        if isinstance(app_config, dict):
            app.config.update(app_config)
        elif app_config.endswith('.py'):
            app.config.from_pyfile(app_config)

    # Setup Secret Keys
    app.config['SECRET_KEY'] = app.config.get('APP_SESSION_KEY', None)

    # Override Application Name
    if app_name is not None:
        app.name = app_name

    try:
        # Initialize Logging
        from .logging import init_logging
        init_logging(app)

        app.logger.info('{} starting up as "{}"'.format(
            app.config['APP_NAME'],
            app.name
        ))

        # Initialize Database
        from .database import init_db
        init_db(app)

        if app.config.get('_JT_DB_NEEDS_INIT', True):
            message = 'The database schema has not been initialized or the ' \
                'database is corrupt. Please initialize the database using ' \
                "'flask db upgrade' and restart the server."
            app.logger.error(message)

        if app.config.get('_JT_DB_NEEDS_UPGRADE'):
            message = 'The database schema is outdated (current version: {}, ' \
                'newest version: {}). Please update the database using ' \
                "'flask db upgrade' and restart the server."
            app.logger.warning(message)

        # Setup E-mail
        from .mail import init_mail
        init_mail(app)

        # Initialize CLI
        from .cli import init_cli
        init_cli(app)

        # Initialize API
        from .api import init_api
        init_api(app)

        # Initialize Setup Helpers
        from .setup import init_setup
        init_setup(app)

        # Initialize Web Sockets
        from .socketio import init_socketio
        init_socketio(app)

        # Startup Complete
        app.logger.info('{} startup complete'.format(app.config['APP_NAME']))

        # Return Application
        return app

    except Exception as e:
        # Ensure startup exceptions get logged
        app.logger.exception(
            'Startup Error (%s): %s',
            e.__class__.__name__,
            str(e)
        )
        raise e
