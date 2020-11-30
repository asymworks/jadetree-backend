# =============================================================================
#
# Jade Tree Personal Budgeting Application | jadetree.io
# Copyright (c) 2020 Asymworks, LLC.  All Rights Reserved.
#
# =============================================================================

import pytest

from jadetree.database.util import make_uri
from jadetree.exc import ConfigError

BASE_TEST_CONFIG = {
    'APP_SESSION_KEY':      'test',
    'APP_TOKEN_KEY':        'test',
    'APP_TOKEN_SALT':       'test',
    'DB_DRIVER':            'sqlite',
    'DB_FILE':              '/dev/null',
    'MAIL_SERVER':          'localhost',
    'MAIL_SENDER':          'test@localhost',
}


class MockApp(object):
    def __init__(self, config):
        self.config = config


def test_dbconfig_no_driver():
    '''
    Application startup should fail if DB_DRIVER is not in the configuration
    '''
    test_cfg = dict(BASE_TEST_CONFIG)
    del test_cfg['DB_DRIVER']

    app = MockApp(test_cfg)
    with pytest.raises(ConfigError, match='application configuration') as excinfo:
        make_uri(app)

    # Ensure that the offending key is DB_DRIVER
    assert excinfo.value.config_key == 'DB_DRIVER'


def test_dbconfig_sqlite_no_file():
    '''
    Application Startup should fail if an SQlite database is specified
    without a DB_FILE key
    '''
    test_cfg = dict(BASE_TEST_CONFIG)
    del test_cfg['DB_FILE']

    app = MockApp(test_cfg)
    with pytest.raises(ConfigError, match='application configuration') as excinfo:
        make_uri(app)

    # Ensure that the offending key is DB_FILE
    assert excinfo.value.config_key == 'DB_FILE'


def test_dbconfig_sqlite_with_file():
    '''
    Application Startup should succeed if an SQlite database is specified
    with a DB_FILE key
    '''
    test_cfg = dict(BASE_TEST_CONFIG)
    app = MockApp(test_cfg)
    uri = make_uri(app)

    # Ensure that the URI was correctly configured and logged
    assert uri == 'sqlite:////dev/null'


def test_dbconfig_mysql_no_host():
    '''
    Application Startup should fail if a MySQL database is specified
    without a DB_HOST key
    '''
    test_cfg = dict(BASE_TEST_CONFIG)
    test_cfg['DB_DRIVER'] = 'mysql'
    app = MockApp(test_cfg)

    with pytest.raises(ConfigError, match='application configuration') as excinfo:
        make_uri(app)

    # Ensure that the offending key is DB_FILE
    assert excinfo.value.config_key == 'DB_HOST'


def test_dbconfig_mysql_no_name():
    '''
    Application Startup should fail if a MySQL database is specified
    without a DB_HOST key
    '''
    test_cfg = dict(BASE_TEST_CONFIG)
    test_cfg['DB_DRIVER'] = 'mysql'
    test_cfg['DB_HOST'] = 'localhost'
    app = MockApp(test_cfg)

    with pytest.raises(ConfigError, match='application configuration') as excinfo:
        make_uri(app)

    # Ensure that the offending key is DB_NAME
    assert excinfo.value.config_key == 'DB_NAME'


def test_dbconfig_mysql_no_username():
    '''
    Application Startup should fail if a MySQL database is specified
    with a DB_USERNAME key but without a DB_PASSWORD key
    '''
    test_cfg = dict(BASE_TEST_CONFIG)
    test_cfg['DB_DRIVER'] = 'mysql'
    test_cfg['DB_HOST'] = 'localhost'
    test_cfg['DB_NAME'] = 'test'
    test_cfg['DB_PASSWORD'] = 'hunter2'
    app = MockApp(test_cfg)

    with pytest.raises(ConfigError, match='application configuration') as excinfo:
        make_uri(app)

    # Ensure that the offending key is DB_USERNAME
    assert excinfo.value.config_key == 'DB_USERNAME'


def test_dbconfig_mysql_without_port():
    '''
    Application Startup should succeed when a MySQL database is specified
    with a DB_PORT key
    '''
    test_cfg = dict(BASE_TEST_CONFIG)
    test_cfg['DB_DRIVER'] = 'mysql'
    test_cfg['DB_HOST'] = 'localhost'
    test_cfg['DB_NAME'] = 'test'
    test_cfg['DB_USERNAME'] = 'root'
    test_cfg['DB_PASSWORD'] = 'hunter^2'

    app = MockApp(test_cfg)
    uri = make_uri(app)

    # Ensure that the application startup succeeded
    assert uri == 'mysql://root:hunter%5E2@localhost/test'


def test_dbconfig_mysql_with_port():
    '''
    Application Startup should succeed when a MySQL database is specified
    with a DB_PORT key
    '''
    test_cfg = dict(BASE_TEST_CONFIG)
    test_cfg['DB_DRIVER'] = 'mysql'
    test_cfg['DB_HOST'] = 'localhost'
    test_cfg['DB_PORT'] = 1234
    test_cfg['DB_NAME'] = 'test'
    test_cfg['DB_USERNAME'] = 'root'
    test_cfg['DB_PASSWORD'] = 'hunter^2'

    app = MockApp(test_cfg)
    uri = make_uri(app)

    # Ensure that the application startup succeeded
    assert uri == 'mysql://root:hunter%5E2@localhost:1234/test'


def test_dbconfig_mysql_with_username():
    '''
    Application Startup should succeed when a MySQL database is specified
    with a DB_USERNAME key and without a DB_PASSWORD key
    '''
    test_cfg = dict(BASE_TEST_CONFIG)
    test_cfg['DB_DRIVER'] = 'mysql'
    test_cfg['DB_HOST'] = 'localhost'
    test_cfg['DB_PORT'] = 1234
    test_cfg['DB_NAME'] = 'test'
    test_cfg['DB_USERNAME'] = 'root'

    app = MockApp(test_cfg)
    uri = make_uri(app)

    # Ensure that the application startup succeeded
    assert uri == 'mysql://root@localhost:1234/test'
