# =============================================================================
#
# Jade Tree Personal Budgeting Application | jadetree.io
# Copyright (c) 2020 Asymworks, LLC.  All Rights Reserved.
#
# =============================================================================

import os

from alembic.command import upgrade
from alembic.config import Config
import flask
import pytest

from jadetree.database import db as _db
from jadetree.factory import create_app
from jadetree.service import auth as auth_service, user as user_service

DATA_DIR = '.pytest-data'


@pytest.fixture(scope='session')
def app_config(request):
    '''
    Application Configuration for the Test Session

    Loads configuration from config/test.py, patches the database file with
    a session-global temporary file, and returns the new configuration data
    to pass to create_app().
    '''
    test_dir = os.path.dirname(__file__)
    test_cfg = os.path.join(test_dir, '../config/test.py')
    cfg_file = os.environ.get('JADETREE_TEST_CONFIG', test_cfg)
    cfg_data = flask.Config(test_dir)
    cfg_data.from_pyfile(cfg_file)

    # Patch Test Configuration
    cfg_data['TESTING'] = True
    cfg_data['DB_DRIVER'] = 'sqlite'
    cfg_data['DB_FILE'] = os.path.join(test_dir, DATA_DIR, 'test.db')

    # Ensure Database Path exists
    db_dir = os.path.dirname(cfg_data['DB_FILE'])
    if not os.path.isdir(db_dir):
        os.mkdir(db_dir)
    if not os.path.isdir(db_dir):
        raise Exception('Database path "%s" does not exist' % (db_dir))

    db_file = cfg_data['DB_FILE']
    if os.path.exists(db_file):
        os.unlink(db_file)

    def teardown():
        if os.path.exists(db_file):
            os.unlink(db_file)
        if os.path.exists(db_dir) and len(os.listdir(db_dir)) == 0:
            os.rmdir(db_dir)

    request.addfinalizer(teardown)
    return cfg_data


@pytest.fixture(scope='module')
def app(request, app_config):
    '''
    Module-Wide Jade Tree Flask Application with Database

    Loads configuration from config/test.py, patches the database file with
    a session-global temporary file, and initializes the application.
    '''
    # Apply Database Migrations
    _app = create_app(app_config, __name__)
    with _app.app_context():
        alembic_config = Config('migrations/alembic.ini')
        alembic_config.set_main_option('script_location', 'migrations')
        upgrade(alembic_config, 'head')
        _db.clear_mappers()

    # Initialize Application and Context
    app = create_app(app_config, __name__)
    ctx = app.app_context()
    ctx.push()

    # Add Finalizers
    def teardown():
        _db.drop_all()
        _db.clear_mappers()
        if os.path.exists(app.config['DB_FILE']):
            os.unlink(app.config['DB_FILE'])
        ctx.pop()

    request.addfinalizer(teardown)
    return app


@pytest.fixture(scope='module')
def app_without_database(request, app_config):
    '''
    Module-Wide Jade Tree Flask Application without Database

    Loads configuration from config/test.py and initializes the application,
    but does not create the database.
    '''
    _db.clear_mappers()

    # Initialize Application and Context
    app = create_app(app_config, __name__)
    ctx = app.app_context()
    ctx.push()

    # Add Finalizers
    def teardown():
        _db.clear_mappers()
        _db.drop_all()
        ctx.pop()

    request.addfinalizer(teardown)
    return app


@pytest.fixture(scope='function')
def session(request, monkeypatch, app):
    '''Create a new Database Session for the Request'''
    with app.app_context():
        connection = _db.engine.connect()
        transaction = connection.begin()

        options = dict(bind=connection, binds={})
        session = _db.create_scoped_session(options=options)

        # Patch jadetree.db with the current session
        monkeypatch.setattr(_db, 'session', session)

    def teardown():
        transaction.rollback()
        connection.close()
        session.remove()

    request.addfinalizer(teardown)
    return session


@pytest.fixture(scope='function')
def user_without_profile(session):
    u = auth_service.register_user(session, 'test@jadetree.io', 'hunter2JT', 'Test User')
    u = auth_service.confirm_user(session, u.uid_hash)
    return u


@pytest.fixture(scope='function')
def user_with_profile(session, user_without_profile):
    u = user_service.setup_user(session, user_without_profile, 'en', 'en_US', 'USD')
    return u
