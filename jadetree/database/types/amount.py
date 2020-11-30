# =============================================================================
#
# Jade Tree Personal Budgeting Application | jadetree.io
# Copyright (c) 2020 Asymworks, LLC.  All Rights Reserved.
#
# =============================================================================

from decimal import Decimal, getcontext
from sqlalchemy.types import TypeDecorator, Integer, Numeric

__all__ = ('AmountType', )


class AmountType(TypeDecorator):
    '''
    Implements a database-agnostic fixed-point decimal datatype suitable for
    storing currency amounts.  Internally this either uses the database-native
    fixed-point type for MySQL and PostgreSQL (DECIMAL and MONEY, respectively)
    and falls back to an integer representation in SQLite.  The values are
    converted to Python :class:`decimal.Decimal` objects on save and load.

    By default, the type implements GAAP-compliant 4 decimal points and stores
    a maximum of 13 digits (-999,999,999.9999 to +999,999,999.9999).  It is
    unlikely that most applications will require storing numbers in excess of
    one trillion currency units, but the precision and scale may be overridden.
    SQLite and PostgreSQL use 64-bit integers as the underlying storage, so the
    practical limit on the precision (total digits) is 18.
    '''

    #: Native Column Implementation
    impl = Numeric

    def __init__(self, precision=13, scale=4):
        super(AmountType, self).__init__()
        self._precision = precision
        self._scale = scale
        self._multiplier = 10**scale

    def load_dialect_impl(self, dialect):
        '''
        Use the native Numeric class if possible; on SQLite fall back to
        Integer
        '''
        if dialect.name == 'sqlite':
            return dialect.type_descriptor(Integer())
        else:
            return dialect.type_descriptor(
                Numeric(self._precision, self._scale)
            )

    def process_bind_param(self, value, dialect):
        '''Assign the Bind Parameter Value from :class:`decimal.Decimal`'''
        if value is None:
            return None
        elif dialect.name == 'sqlite':
            # Note: casting to str is important in case the value passed in
            #       is a float object.  For example, without the explicit cast,
            #       Decimal(17.99) * 10000 = 179899, while
            #       Decimal('17.99') * 10000 = 179900
            #
            # Expliticly setting the precision may do the same thing, but we do
            # both to be safe (this also fixes Decimal(17.99) expanding to
            # "17.989999999999998436805981327779591083526611328125")
            getcontext().prec = self._precision
            return int(Decimal(str(value)) * self._multiplier)
        return value

    def process_result_value(self, value, dialect):
        '''Assign the Result Value to :class:`decimal.Decimal`'''
        if value is None:
            return None
        elif dialect.name == 'sqlite':
            return Decimal(value) / self._multiplier
        return Decimal(value)
