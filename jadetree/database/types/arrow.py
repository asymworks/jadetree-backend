# =============================================================================
#
# Jade Tree Personal Budgeting Application | jadetree.io
# Copyright (c) 2020 Asymworks, LLC.  All Rights Reserved.
#
# =============================================================================

import arrow
from collections.abc import Iterable
from datetime import date, datetime
from sqlalchemy.types import TypeDecorator, Date, DateTime

__all__ = ('ArrowDate', 'ArrowType')


class ArrowDate(TypeDecorator):
    '''
    Stores :class:`Arrow <arrow:arrow.arrow.Arrow>` objects in the database by
    converting to date objects for database storage and changing back to
    Arrow objects when loaded. The Arrow_ library must be installed.

    .. _Arrow: https://arrow.readthedocs.io/en/latest/

    '''
    impl = Date

    def __init__(self, *args, **kwargs):
        super(ArrowDate, self).__init__(*args, **kwargs)

    def process_bind_param(self, value, dialect):
        '''
        Assign the Bind Parameter Value from an
        :class:`Arrow <arrow:arrow.arrow.Arrow>` object
        '''
        if value is None:
            return None

        utc_val = value
        if isinstance(value, (str, date, datetime)):
            utc_val = arrow.get(value).to('UTC')
        elif isinstance(value, Iterable):
            utc_val = arrow.get(*value).to('UTC')

        return utc_val.date()

    def process_result_value(self, value, dialect):
        '''
        Assign the Result Value to an
        :class:`Arrow <arrow:arrow.arrow.Arrow>` object
        '''
        if value:
            return arrow.get(value)
        return value

    def process_literal_param(self, value, dialect):
        return str(value)


class ArrowType(TypeDecorator):
    '''
    Stores :class:`Arrow <arrow:arrow.arrow.Arrow>` objects in the database by
    converting to datetime objects for database storage and changing back to
    Arrow objects when loaded. The Arrow_ library must be installed.

    .. _Arrow: https://arrow.readthedocs.io/en/latest/

    ::

        from jadetree.models.types import ArrowType
        import arrow

        class Article(Base):
            __tablename__ = 'article'
            id = sa.Column(sa.Integer, primary_key=True)
            name = sa.Column(sa.Unicode(255))
            created_at = sa.Column(ArrowType)

        article = Article(created_at=arrow.utcnow())

    The created_at column can now be used just like any Arrow object:

    ::

        article.created_at = article.created_at.shift(hours=-1)
        article.created_at.humanize() # 'an hour ago'

    '''
    impl = DateTime

    def __init__(self, *args, **kwargs):
        super(ArrowType, self).__init__(*args, **kwargs)

    def process_bind_param(self, value, dialect):
        '''
        Assign the Bind Parameter Value from an
        :class:`Arrow <arrow:arrow.arrow.Arrow>` object
        '''
        if value is None:
            return None

        utc_val = value
        if isinstance(value, (str, date, datetime)):
            utc_val = arrow.get(value).to('UTC')
        elif isinstance(value, Iterable):
            utc_val = arrow.get(*value).to('UTC')

        return utc_val.datetime if self.impl.timezone else utc_val.naive

    def process_result_value(self, value, dialect):
        '''
        Assign the Result Value to an
        :class:`Arrow <arrow:arrow.arrow.Arrow>` object
        '''
        if value:
            return arrow.get(value)
        return value

    def process_literal_param(self, value, dialect):
        return str(value)
