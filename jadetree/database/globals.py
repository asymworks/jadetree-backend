# =============================================================================
#
# Jade Tree Personal Budgeting Application | jadetree.io
# Copyright (c) 2020 Asymworks, LLC.  All Rights Reserved.
#
# =============================================================================

from flask_migrate import Migrate
from flask_sqlalchemy import SQLAlchemy
import sqlalchemy as sa
from sqlalchemy.ext import compiler
from sqlalchemy.schema import DDLElement


class CreateView(DDLElement):
    def __init__(self, name, selectable):
        self.name = name
        self.selectable = selectable


class DropView(DDLElement):
    def __init__(self, name, cascade=True):
        self.name = name
        self.cascade = cascade


@compiler.compiles(CreateView)
def compile_create_materialized_view(element, compiler, **kw):
    return 'CREATE VIEW {} AS {}'.format(
        element.name,
        compiler.sql_compiler.process(element.selectable, literal_binds=True),
    )


@compiler.compiles(DropView)
def compile_drop_materialized_view(element, compiler, **kw):
    return 'DROP VIEW IF EXISTS {} {}'.format(
        element.name,
        'CASCADE' if element.cascade else ''
    )


def _make_view(db):
    def create_view(name, selectable, cascade_on_drop=True):
        _mt = db.MetaData()

        # Create Table object using temporary Metadata (prevents SQLalchemy
        # from trying to create and drop the table in Metadata.create_all() and
        # Metadata.drop_app())
        cols = [
            sa.Column(c.name, c.type, key=c.name, primary_key=c.primary_key)
            for c in selectable.c
        ]
        table = sa.Table(
            name,
            _mt,
            *cols,
            info=dict(is_view=True, selectable=selectable)
        )

        # Create a fake Primary Key constraint if needed
        if not any([c.primary_key for c in selectable.c]):
            table.append_constraint(
                sa.PrimaryKeyConstraint(*[c.name for c in selectable.c])
            )

        # Add Create/Drop Listeners
        sa.event.listen(db.metadata, 'after_create', CreateView(name, selectable))
        sa.event.listen(
            db.metadata,
            'before_drop',
            DropView(name, cascade=cascade_on_drop)
        )

        # Return new Table Objects
        return table

    return create_view


#: Global Database Object for Models and Views
db = SQLAlchemy()

# Patch Database Object to create Views
db.View = _make_view(db)

#: Global Alembic Migration Object
migrate = Migrate()
