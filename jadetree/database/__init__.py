# =============================================================================
#
# Jade Tree Personal Budgeting Application | jadetree.io
# Copyright (c) 2020 Asymworks, LLC.  All Rights Reserved.
#
# =============================================================================

import re

from alembic.command import upgrade
from alembic.config import Config
from alembic.script import ScriptDirectory
from flask import current_app

from jadetree.exc import Error

from .globals import db, migrate
from .util import make_uri

__all__ = ('db', 'migrate', 'init_db')


def check_database():
    '''Called before each request to ensure database schema is initialized'''
    if current_app.config.get('_JT_DB_NEEDS_INIT'):
        raise Error('Database is not initialized')


def init_db(app):
    '''Initialize the Global Database Object for the Application'''

    # Set SQLalchemy Defaults (suppresses warning)
    app.config.setdefault('SQLALCHEMY_TRACK_MODIFICATIONS', False)

    # Load SQLalchemy URI
    if 'SQLALCHEMY_DATABASE_URI' not in app.config:
        if 'DB_URI' in app.config:
            app.config['SQLALCHEMY_DATABASE_URI'] = app.config['DB_URI']
        else:
            app.config['SQLALCHEMY_DATABASE_URI'] = make_uri(app)

    # Initialize Object Relational Mapping
    from .orm import init_orm
    init_orm()

    # Log the URI (masked)
    app.logger.debug(
        'Starting SQLalchemy with URI: "%s"', re.sub(
            r':([.+]|[0-9a-z\'_-~]|%[0-9A-F]{2})+@',
            ':(masked)@',
            app.config['SQLALCHEMY_DATABASE_URI'],
            flags=re.I
        )
    )

    # Initialize Database
    db.init_app(app)
    migrate.init_app(app, db)

    # Check the Database Revision
    app.config['_JT_DB_NEEDS_INIT'] = True
    app.config['_JT_DB_NEEDS_UPGRADE'] = False
    app.config['_JT_DB_HEAD_REV'] = None
    app.config['_JT_DB_CUR_REV'] = None
    with app.app_context():
        if db.engine.dialect.has_table(db.engine, 'alembic_version'):
            app.config['_JT_DB_NEEDS_INIT'] = False

            db_version_sql = db.text('select version_num from alembic_version')
            db_version = db.engine.execute(db_version_sql).scalar()
            app.config['_JT_DB_CUR_REV'] = db_version

            script_dir = ScriptDirectory.from_config(migrate.get_config())
            for rev in script_dir.walk_revisions():
                if rev.is_head:
                    app.config['_JT_DB_HEAD_REV'] = rev.revision
                if rev.revision == db_version:
                    app.config['_JT_DB_NEEDS_UPGRADE'] = not rev.is_head

    # Register Database Setup Hook
    app.before_request(check_database)

    # Notify Initialization
    app.logger.debug('Database Initialized')

    # Return Success
    return True
