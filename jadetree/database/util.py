# =============================================================================
#
# Jade Tree Personal Budgeting Application | jadetree.io
# Copyright (c) 2020 Asymworks, LLC.  All Rights Reserved.
#
# =============================================================================

import os

from urllib.parse import quote_plus

from jadetree.exc import ConfigError

__all__ = ('make_uri', )


def make_uri(app):
    '''
    Assembles the Database URI from Application Configuration values.

    :param app: :class:`Flask` application object
    '''
    if 'DB_DRIVER' not in app.config:
        raise ConfigError(
            'DB_DRIVER must be defined in application configuration',
            config_key='DB_DRIVER'
        )

    # SQLite
    if app.config['DB_DRIVER'] == 'sqlite':
        if 'DB_FILE' not in app.config:
            raise ConfigError(
                'DB_FILE must be defined in application configuration for '
                'SQLite Database',
                config_key='DB_FILE'
            )
        return 'sqlite:///{db_file}'.format(
            db_file=os.path.abspath(app.config['DB_FILE']),
        )

    # Database Servers (note only MySQL and PostgreSQL are tested)
    uri_auth = ''
    uri_port = ''

    for k in ('DB_HOST', 'DB_NAME'):
        if k not in app.config:
            raise ConfigError(
                '{} must be defined in application configuration'.format(k),
                config_key=k
            )

    # Assemble Port Suffix
    if 'DB_PORT' in app.config:
        uri_port = ':{}'.format(app.config['DB_PORT'])

    # Assemble Authentication Portion
    if 'DB_USERNAME' in app.config:
        if 'DB_PASSWORD' in app.config:
            uri_auth = '{username}:{password}@'.format(
                username=quote_plus(app.config['DB_USERNAME']),
                password=quote_plus(app.config['DB_PASSWORD']),
            )
        else:
            uri_auth = '{username}@'.format(
                username=quote_plus(app.config['DB_USERNAME']),
            )
    elif 'DB_PASSWORD' in app.config:
        raise ConfigError(
            'DB_USERNAME must be defined if DB_PASSWORD is set in '
            'application configuration',
            config_key='DB_USERNAME'
        )

    return '{driver}://{auth}{host}{port}/{name}'.format(
        driver=app.config['DB_DRIVER'],
        auth=uri_auth,
        host=app.config['DB_HOST'],
        port=uri_port,
        name=app.config['DB_NAME'],
    )
