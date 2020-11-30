# =============================================================================
#
# Jade Tree Personal Budgeting Application | jadetree.io
# Copyright (c) 2020 Asymworks, LLC.  All Rights Reserved.
#
# =============================================================================

from dataclasses import dataclass
from decimal import Decimal

from ..mixins import TimestampMixin
from ..types import PayeeRole

__all__ = ('Payee', )


@dataclass
class Payee(TimestampMixin):
    '''
    '''
    name: str = None
    role: PayeeRole = None
    system: bool = None
    hidden: bool = None

    memo: str = None
    amount: Decimal = None

    # Relationship Fields
    user: 'User' = None             # noqa: F821
    category: 'Category' = None     # noqa: F821
    account: 'Account' = None       # noqa: F821

    # Helpers
    def __repr__(self):
        return '<Payee {}>'.format(self.name)
