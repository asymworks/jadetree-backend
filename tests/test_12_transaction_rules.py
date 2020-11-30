# =============================================================================
#
# Jade Tree Personal Budgeting Application | jadetree.io
# Copyright (c) 2020 Asymworks, LLC.  All Rights Reserved.
#
# =============================================================================

import pytest

from jadetree.domain.models import Account, Transaction
from jadetree.domain.types import AccountType

test_cases = [
    # Account Type,          Opposing Type,          Opposing Sign
    (AccountType.Asset,      AccountType.Asset,      -1),
    (AccountType.Asset,      AccountType.Liability,  +1),
    (AccountType.Asset,      AccountType.Capital,    +1),
    (AccountType.Asset,      AccountType.Trading,    +1),
    (AccountType.Asset,      AccountType.Income,     +1),
    (AccountType.Asset,      AccountType.Expense,    -1),
    (AccountType.Liability,  AccountType.Asset,      +1),
    (AccountType.Liability,  AccountType.Liability,  -1),
    (AccountType.Liability,  AccountType.Capital,    -1),
    (AccountType.Liability,  AccountType.Trading,    -1),
    (AccountType.Liability,  AccountType.Income,     -1),
    (AccountType.Liability,  AccountType.Expense,    +1),
    (AccountType.Capital,    AccountType.Asset,      +1),
    (AccountType.Capital,    AccountType.Liability,  -1),
    (AccountType.Capital,    AccountType.Capital,    -1),
    (AccountType.Capital,    AccountType.Trading,    -1),
    (AccountType.Capital,    AccountType.Income,     -1),
    (AccountType.Capital,    AccountType.Expense,    +1),
    (AccountType.Trading,    AccountType.Asset,      +1),
    (AccountType.Trading,    AccountType.Liability,  -1),
    (AccountType.Trading,    AccountType.Capital,    -1),
    (AccountType.Trading,    AccountType.Trading,    -1),
    (AccountType.Trading,    AccountType.Income,     -1),
    (AccountType.Trading,    AccountType.Expense,    +1),
    (AccountType.Income,     AccountType.Asset,      +1),
    (AccountType.Income,     AccountType.Liability,  -1),
    (AccountType.Income,     AccountType.Capital,    -1),
    (AccountType.Income,     AccountType.Trading,    -1),
    (AccountType.Income,     AccountType.Income,     -1),
    (AccountType.Income,     AccountType.Expense,    +1),
    (AccountType.Expense,    AccountType.Asset,      -1),
    (AccountType.Expense,    AccountType.Liability,  +1),
    (AccountType.Expense,    AccountType.Capital,    +1),
    (AccountType.Expense,    AccountType.Trading,    +1),
    (AccountType.Expense,    AccountType.Income,     +1),
    (AccountType.Expense,    AccountType.Expense,    -1),
]


@pytest.mark.unit
@pytest.mark.parametrize("a_type,o_type,o_sgn", test_cases)
def test_opposing_signs(a_type, o_type, o_sgn):
    a = Account(type=a_type, currency='USD')
    o = Account(type=o_type, currency='USD')
    t = Transaction()
    t.account = a

    assert t._opposing_sign(o) == o_sgn
