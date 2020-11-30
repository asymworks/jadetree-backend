# =============================================================================
#
# Jade Tree Personal Budgeting Application | jadetree.io
# Copyright (c) 2020 Asymworks, LLC.  All Rights Reserved.
#
# =============================================================================

import flask
import os
import pytest

from alembic.command import upgrade
from alembic.config import Config

from jadetree.factory import create_app
from jadetree.database import db as _db
from jadetree.service import auth as auth_service
from jadetree.service import user as user_service

DATA_DIR = '.pytest-data'


# FIXME: needs autouse=True to setup ORM even when using fake UOW
@pytest.fixture(scope='session', autouse=True)
def app(request):
    '''
    Session-Wide Jade Tree Flask Application

    Loads configuration from config/test.py, patches the database file with
    a session-global temporary file, and initializes the application.
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

    # Initialize Application and Context
    app = create_app(cfg_data, __name__)
    ctx = app.app_context()
    ctx.push()

    # Add Finalizers
    def teardown():
        ctx.pop()

    request.addfinalizer(teardown)

    return app


@pytest.fixture(scope='session')
def db(app, request):
    '''Session-Wide Test Database'''
    db_file = app.config['DB_FILE']
    db_dir = os.path.dirname(db_file)
    if os.path.exists(db_file):
        os.unlink(db_file)
    if not os.path.isdir(db_dir):
        os.mkdir(db_dir)
    if not os.path.isdir(db_dir):
        raise Exception('Database path "%s" does not exist' % (db_dir))

    def teardown():
        _db.drop_all()
        os.unlink(db_file)
        if len(os.listdir(db_dir)) == 0:
            os.rmdir(db_dir)

    _db.app = app

    # Apply Migrations
    alembic_config = Config('migrations/alembic.ini')
    alembic_config.set_main_option('script_location', 'migrations')
    upgrade(alembic_config, 'head')

    request.addfinalizer(teardown)
    return _db


@pytest.fixture(scope='function')
def session(db, request):
    '''Create a new Database Session for the Request'''
    connection = db.engine.connect()
    transaction = connection.begin()

    options = dict(bind=connection, binds={})
    session = db.create_scoped_session(options=options)

    db.session = session

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
