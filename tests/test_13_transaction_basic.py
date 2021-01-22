# =============================================================================
#
# Jade Tree Personal Budgeting Application | jadetree.io
# Copyright (c) 2020 Asymworks, LLC.  All Rights Reserved.
#
# =============================================================================

from decimal import Decimal

import pytest  # noqa: F401

from jadetree.domain.models import Account, Transaction, User
from jadetree.domain.types import AccountRole, AccountType, TransactionType

from .helpers import check_transaction_entries as check_entries

# Always use 'app' fixture so ORM gets initialized
pytestmark = pytest.mark.usefixtures('app')


def test_transaction_reprs():
    from jadetree.domain.models import (
        TransactionEntry,
        TransactionLine,
        TransactionSplit,
    )

    # Setup User and Accounts
    u = User(currency='USD')
    a = Account(user=u, active=True, name='A', role=AccountRole.Personal, type=AccountType.Asset, currency='USD')
    o = Account(user=u, active=True, name='O', role=AccountRole.Budget, type=AccountType.Expense, currency='CAD')

    # Create Transaction, TransactionLine, and TransactionSplit
    t = Transaction(user=u, account=a, currency='USD')
    tll = TransactionLine(transaction=t, account=a)
    tlr = TransactionLine(transaction=t, account=o)

    ts = TransactionSplit(transaction=t, left_line=tll, right_line=tlr)

    # Test TransactionEntry
    te1 = TransactionEntry(line=tll, split=ts, amount=Decimal(-10), currency='USD')
    te2 = TransactionEntry(line=tlr, split=ts, amount=Decimal( 15), currency='CAD')

    assert repr(te1) == '<TransactionEntry -10 USD>'
    assert repr(te2) == '<TransactionEntry 15 CAD>'

    # Test TransactionLine
    assert repr(tll) == '<TransactionLine -10 USD>'
    assert repr(tlr) == '<TransactionLine 15 CAD>'

    # Test TransactionSplit
    assert repr(ts) == '<TransactionSplit A -> O>'

    # Test Transaction
    assert repr(t) == '<Transaction -10 USD>'


def test_transaction_can_add_lines_simple_nonsplit():
    # Setup User and Accounts
    u = User(currency='USD')
    a = Account(user=u, active=True, name='A', role=AccountRole.Personal, type=AccountType.Asset, currency='USD')
    o = Account(user=u, active=True, name='O', role=AccountRole.Budget, type=AccountType.Expense, currency='USD')

    # Setup Transaction
    t = Transaction(user=u, account=a)

    # Add Transaction Split for $-100
    t.add_split(o, Decimal(-100), 'USD')

    # Ensure Lines were Added
    assert t.lines is not None
    assert isinstance(t.lines, list)
    assert len(t.lines) == 2
    assert t.lines[0].account == a
    assert t.lines[0].amount == Decimal(-100)
    assert t.lines[1].account == o
    assert t.lines[1].amount == Decimal(100)

    # Ensure Split was Added
    assert t.splits is not None
    assert isinstance(t.splits, list)
    assert len(t.splits) == 1

    assert t.splits[0].left_line == t.lines[0]
    assert t.splits[0].right_line == t.lines[1]
    assert t.splits[0].type == TransactionType.Outflow
    assert t.splits[0].amount == Decimal(-100)

    # Ensure Entries were Added
    check_entries(t.splits[0], [
        (a, Decimal(-100), 'USD'),
        (o, Decimal( 100), 'USD'),
    ])

    assert t.amount == Decimal(-100)


def test_transaction_can_add_lines_simple_split():
    # Setup User and Accounts
    u = User(currency='USD')
    a = Account(user=u, active=True, name='A', role=AccountRole.Personal, type=AccountType.Asset, currency='USD')
    o1 = Account(user=u, active=True, name='O1', role=AccountRole.Budget, type=AccountType.Expense, currency='USD')
    o2 = Account(user=u, active=True, name='O2', role=AccountRole.Budget, type=AccountType.Expense, currency='USD')

    # Setup Transaction
    t = Transaction(user=u, account=a)

    # Add Transaction Line for $-100
    t.add_split(o1, Decimal(-25), 'USD')
    t.add_split(o2, Decimal(-75), 'USD')

    # Ensure Lines were Added
    assert t.lines is not None
    assert isinstance(t.lines, list)
    assert len(t.lines) == 3
    assert t.lines[0].account == a
    assert t.lines[0].amount == Decimal(-100)
    assert t.lines[1].account == o1
    assert t.lines[1].amount == Decimal(25)
    assert t.lines[2].account == o2
    assert t.lines[2].amount == Decimal(75)

    # Ensure Split was Added
    assert t.splits is not None
    assert isinstance(t.splits, list)
    assert len(t.splits) == 2

    assert t.splits[0].left_line == t.lines[0]
    assert t.splits[0].right_line == t.lines[1]
    assert t.splits[0].type == TransactionType.Outflow
    assert t.splits[0].amount == Decimal(-25)

    assert t.splits[1].left_line == t.lines[0]
    assert t.splits[1].right_line == t.lines[2]
    assert t.splits[1].type == TransactionType.Outflow
    assert t.splits[1].amount == Decimal(-75)

    # Ensure Entries were Added
    check_entries(t.splits[0], [
        (a, Decimal(-25), 'USD'),
        (o1, Decimal( 25), 'USD'),
    ])
    check_entries(t.splits[1], [
        (a, Decimal(-75), 'USD'),
        (o2, Decimal( 75), 'USD'),
    ])

    assert t.amount == Decimal(-100)
