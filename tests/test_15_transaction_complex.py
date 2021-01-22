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


def test_transaction_can_add_splits_bff_nonsplit():
    # Base Currency Transaction between Foreign Currency Accounts
    # Use Case: ??

    # Setup User and Accounts
    u = User(currency='EUR')
    a = Account(user=u, active=True, name='A', role=AccountRole.Personal, type=AccountType.Liability, currency='USD')
    o = Account(user=u, active=True, name='O', role=AccountRole.Budget, type=AccountType.Expense, currency='USD')

    # Setup Transaction
    t = Transaction(
        user=u,
        account=a,
        currency='EUR',
        foreign_currency='USD',
        foreign_exchrate=Decimal('0.8'),
    )

    # Add Transaction Line for EUR 100
    t.add_split(o, Decimal(100), 'EUR')

    # Ensure Lines were Added
    assert t.lines is not None
    assert isinstance(t.lines, list)
    assert len(t.lines) == 2
    assert t.lines[0].account == a
    assert t.lines[0].amount == Decimal(125)
    assert t.lines[1].account == o
    assert t.lines[1].amount == Decimal(125)

    # Ensure Split was Added
    assert t.splits is not None
    assert isinstance(t.splits, list)
    assert len(t.splits) == 1

    assert t.splits[0].left_line == t.lines[0]
    assert t.splits[0].right_line == t.lines[1]
    assert t.splits[0].type == TransactionType.Outflow
    assert t.splits[0].amount == Decimal(100)

    # Ensure Entries were Added
    check_entries(t.splits[0], [
        (a, Decimal(125), 'USD'),
        (o, Decimal(125), 'USD'),
    ])

    assert t.amount == Decimal(100)


def test_transaction_can_add_splits_bff_split():
    # Base Currency Transaction between Foreign Currency Accounts
    # Use Case: ??

    # Setup User and Accounts
    u = User(currency='EUR')
    a = Account(user=u, active=True, name='A', role=AccountRole.Personal, type=AccountType.Liability, currency='USD')
    o1 = Account(user=u, active=True, name='O1', role=AccountRole.Budget, type=AccountType.Expense, currency='USD')
    o2 = Account(user=u, active=True, name='O2', role=AccountRole.Budget, type=AccountType.Expense, currency='USD')

    # Setup Transaction
    t = Transaction(
        user=u,
        account=a,
        currency='EUR',
        foreign_currency='USD',
        foreign_exchrate=Decimal('0.8'),
    )

    # Add Transaction Line for EUR 100
    t.add_split(o1, Decimal(80), 'EUR')
    t.add_split(o2, Decimal(20), 'EUR')

    # Ensure Lines were Added
    assert t.lines is not None
    assert isinstance(t.lines, list)
    assert len(t.lines) == 3
    assert t.lines[0].account == a
    assert t.lines[0].amount == Decimal(125)
    assert t.lines[1].account == o1
    assert t.lines[1].amount == Decimal(100)
    assert t.lines[2].account == o2
    assert t.lines[2].amount == Decimal(25)

    # Ensure Split was Added
    assert t.splits is not None
    assert isinstance(t.splits, list)
    assert len(t.splits) == 2

    assert t.splits[0].left_line == t.lines[0]
    assert t.splits[0].right_line == t.lines[1]
    assert t.splits[0].type == TransactionType.Outflow
    assert t.splits[0].amount == Decimal(80)

    assert t.splits[1].left_line == t.lines[0]
    assert t.splits[1].right_line == t.lines[2]
    assert t.splits[1].type == TransactionType.Outflow
    assert t.splits[1].amount == Decimal(20)

    # Ensure Entries were Added
    check_entries(t.splits[0], [
        (a, Decimal(100), 'USD'),
        (o1, Decimal(100), 'USD'),
    ])
    check_entries(t.splits[1], [
        (a, Decimal(25), 'USD'),
        (o2, Decimal(25), 'USD'),
    ])

    assert t.amount == Decimal(100)


def test_transaction_can_add_splits_ffb_nonsplit():
    # Foreign Transaction between Foreign and Base Currency
    # Use Case: Expat budgeting in "home" currency spending from "local"
    # checking account

    # Setup User and Accounts
    u = User(currency='USD')
    a = Account(user=u, active=True, name='A', role=AccountRole.Personal, type=AccountType.Asset, currency='EUR')
    o = Account(user=u, active=True, name='O', role=AccountRole.Budget, type=AccountType.Expense, currency='USD')
    ta = Account(user=u, active=True, name='T', role=AccountRole.System, type=AccountType.Trading, currency=u.currency)

    # Setup Transaction
    t = Transaction(
        user=u,
        account=a,
        currency='EUR',
        foreign_currency='EUR',
        foreign_exchrate=Decimal('1.25'),
    )

    # Add Transaction Line for EUR 100
    t.add_split(o, Decimal(-100), 'EUR', trading=ta)

    # Ensure Lines were Added
    assert t.lines is not None
    assert isinstance(t.lines, list)
    assert len(t.lines) == 3
    assert t.lines[0].account == a
    assert t.lines[0].amount == Decimal(-100)
    assert t.lines[1].account == o
    assert t.lines[1].amount == Decimal(125)
    assert t.lines[2].account == ta

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
        (a, Decimal(-100), 'EUR'),
        (ta, Decimal(-100), 'EUR'),
        (ta, Decimal( 125), 'USD'),
        (o, Decimal( 125), 'USD'),
    ])

    assert t.amount == Decimal(-100)


def test_transaction_can_add_splits_ffb_split():
    # Foreign Transaction between Base Currency Accounts
    # Use Case: Buy something while travelling in a foreign country

    # Setup User and Accounts
    u = User(currency='USD')
    a = Account(user=u, active=True, name='A', role=AccountRole.Personal, type=AccountType.Liability, currency='EUR')
    o1 = Account(user=u, active=True, name='O1', role=AccountRole.Budget, type=AccountType.Expense, currency='USD')
    o2 = Account(user=u, active=True, name='O2', role=AccountRole.Budget, type=AccountType.Expense, currency='USD')
    ta = Account(user=u, active=True, name='T', role=AccountRole.System, type=AccountType.Trading, currency=u.currency)

    # Setup Transaction
    t = Transaction(
        user=u,
        account=a,
        currency='EUR',
        foreign_currency='EUR',
        foreign_exchrate=Decimal('1.25'),
    )

    # Add Transaction Line for EUR 80
    t.add_split(o1, Decimal(80), 'EUR', trading=ta)
    t.add_split(o2, Decimal(20), 'EUR', trading=ta)

    # Ensure Lines were Added
    assert t.lines is not None
    assert isinstance(t.lines, list)
    assert len(t.lines) == 4
    assert t.lines[0].account == a
    assert t.lines[0].amount == Decimal(100)
    assert t.lines[1].account == o1
    assert t.lines[1].amount == Decimal(100)
    assert t.lines[3].account == o2
    assert t.lines[3].amount == Decimal(25)
    assert t.lines[2].account == ta

    # Ensure Split was Added
    assert t.splits is not None
    assert isinstance(t.splits, list)
    assert len(t.splits) == 2

    assert t.splits[0].left_line == t.lines[0]
    assert t.splits[0].right_line == t.lines[1]
    assert t.splits[0].type == TransactionType.Outflow
    assert t.splits[0].amount == Decimal(80)

    assert t.splits[1].left_line == t.lines[0]
    assert t.splits[1].right_line == t.lines[3]
    assert t.splits[1].type == TransactionType.Outflow
    assert t.splits[1].amount == Decimal(20)

    # Ensure Entries were Added
    check_entries(t.splits[0], [
        ( a, Decimal(  80), 'EUR'),
        (ta, Decimal( -80), 'EUR'),
        (ta, Decimal( 100), 'USD'),
        (o1, Decimal( 100), 'USD'),
    ])
    check_entries(t.splits[1], [
        ( a, Decimal(  20), 'EUR'),
        (ta, Decimal( -20), 'EUR'),
        (ta, Decimal(  25), 'USD'),
        (o2, Decimal(  25), 'USD'),
    ])

    assert t.amount == Decimal(100)


def test_transaction_can_add_splits_fbf_nonsplit():
    # Foreign Transaction between Foreign and Base Currency
    # Use Case: Expat budgeting in "foreign" currency spending from "local"
    # checking account

    # Setup User and Accounts
    u = User(currency='USD')
    a = Account(user=u, active=True, name='A', role=AccountRole.Personal, type=AccountType.Asset, currency='USD')
    o = Account(user=u, active=True, name='O', role=AccountRole.Budget, type=AccountType.Expense, currency='EUR')
    ta = Account(user=u, active=True, name='T', role=AccountRole.System, type=AccountType.Trading, currency=u.currency)

    # Setup Transaction
    t = Transaction(
        user=u,
        account=a,
        currency='EUR',
        foreign_currency='EUR',
        foreign_exchrate=Decimal('1.25'),
    )

    # Add Transaction Line for EUR 100
    t.add_split(o, Decimal(-100), 'EUR', trading=ta)

    # Ensure Lines were Added
    assert t.lines is not None
    assert isinstance(t.lines, list)
    assert len(t.lines) == 3
    assert t.lines[0].account == a
    assert t.lines[0].amount == Decimal(-125)
    assert t.lines[1].account == o
    assert t.lines[1].amount == Decimal(100)
    assert t.lines[2].account == ta

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
        (a, Decimal(-125), 'USD'),
        (ta, Decimal(-125), 'USD'),
        (ta, Decimal( 100), 'EUR'),
        (o, Decimal( 100), 'EUR'),
    ])

    assert t.amount == Decimal(-100)


def test_transaction_can_add_splits_fbf_split():
    # Foreign Transaction between Base Currency Accounts
    # Use Case: Buy something while travelling in a foreign country

    # Setup User and Accounts
    u = User(currency='USD')
    a = Account(user=u, active=True, name='A', role=AccountRole.Personal, type=AccountType.Liability, currency='USD')
    o1 = Account(user=u, active=True, name='O1', role=AccountRole.Budget, type=AccountType.Expense, currency='EUR')
    o2 = Account(user=u, active=True, name='O2', role=AccountRole.Budget, type=AccountType.Expense, currency='EUR')
    ta = Account(user=u, active=True, name='T', role=AccountRole.System, type=AccountType.Trading, currency=u.currency)

    # Setup Transaction
    t = Transaction(
        user=u,
        account=a,
        currency='EUR',
        foreign_currency='EUR',
        foreign_exchrate=Decimal('1.25'),
    )

    # Add Transaction Line for EUR 100
    t.add_split(o1, Decimal(80), 'EUR', trading=ta)
    t.add_split(o2, Decimal(20), 'EUR', trading=ta)

    # Ensure Lines were Added
    assert t.lines is not None
    assert isinstance(t.lines, list)
    assert len(t.lines) == 4
    assert t.lines[0].account == a
    assert t.lines[0].amount == Decimal(125)
    assert t.lines[1].account == o1
    assert t.lines[1].amount == Decimal(80)
    assert t.lines[3].account == o2
    assert t.lines[3].amount == Decimal(20)
    assert t.lines[2].account == ta

    # Ensure Split was Added
    assert t.splits is not None
    assert isinstance(t.splits, list)
    assert len(t.splits) == 2

    assert t.splits[0].left_line == t.lines[0]
    assert t.splits[0].right_line == t.lines[1]
    assert t.splits[0].type == TransactionType.Outflow
    assert t.splits[0].amount == Decimal(80)

    assert t.splits[1].left_line == t.lines[0]
    assert t.splits[1].right_line == t.lines[3]
    assert t.splits[1].type == TransactionType.Outflow
    assert t.splits[1].amount == Decimal(20)

    # Ensure Entries were Added
    check_entries(t.splits[0], [
        ( a, Decimal( 100), 'USD'),
        (ta, Decimal(-100), 'USD'),
        (ta, Decimal(  80), 'EUR'),
        (o1, Decimal(  80), 'EUR'),
    ])
    check_entries(t.splits[1], [
        ( a, Decimal(  25), 'USD'),
        (ta, Decimal( -25), 'USD'),
        (ta, Decimal(  20), 'EUR'),
        (o2, Decimal(  20), 'EUR'),
    ])

    assert t.amount == Decimal(100)


def test_transaction_can_add_splits_bfb_nonsplit():
    # Foreign Transaction between Foreign and Base Currency
    # Use Case: Expat budgeting in "local" currency spending from "home"
    # checking account

    # Setup User and Accounts
    u = User(currency='EUR')
    a = Account(user=u, active=True, name='A', role=AccountRole.Personal, type=AccountType.Asset, currency='USD')
    o = Account(user=u, active=True, name='O', role=AccountRole.Budget, type=AccountType.Expense, currency='EUR')
    ta = Account(user=u, active=True, name='T', role=AccountRole.System, type=AccountType.Trading, currency=u.currency)

    # Setup Transaction
    t = Transaction(
        user=u,
        account=a,
        currency='EUR',
        foreign_currency='USD',
        foreign_exchrate=Decimal('0.8'),
    )

    # Add Transaction Line for EUR 100
    t.add_split(o, Decimal(-100), 'EUR', trading=ta)

    # Ensure Lines were Added
    assert t.lines is not None
    assert isinstance(t.lines, list)
    assert len(t.lines) == 3
    assert t.lines[0].account == a
    assert t.lines[0].amount == Decimal(-125)
    assert t.lines[1].account == o
    assert t.lines[1].amount == Decimal(100)
    assert t.lines[2].account == ta

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
        (a, Decimal(-125), 'USD'),
        (ta, Decimal(-125), 'USD'),
        (ta, Decimal( 100), 'EUR'),
        (o, Decimal( 100), 'EUR'),
    ])

    assert t.amount == Decimal(-100)


def test_transaction_can_add_splits_bfb_split():
    # Foreign Transaction between Base Currency Accounts
    # Use Case: Buy something while travelling in a foreign country

    # Setup User and Accounts
    u = User(currency='USD')
    a = Account(user=u, active=True, name='A', role=AccountRole.Personal, type=AccountType.Liability, currency='EUR')
    o1 = Account(user=u, active=True, name='O1', role=AccountRole.Budget, type=AccountType.Expense, currency='USD')
    o2 = Account(user=u, active=True, name='O2', role=AccountRole.Budget, type=AccountType.Expense, currency='USD')
    ta = Account(user=u, active=True, name='T', role=AccountRole.System, type=AccountType.Trading, currency=u.currency)

    # Setup Transaction
    t = Transaction(
        user=u,
        account=a,
        currency='USD',
        foreign_currency='EUR',
        foreign_exchrate=Decimal('1.25'),
    )

    # Add Transaction Line for USD 125
    t.add_split(o1, Decimal(100), 'USD', trading=ta)
    t.add_split(o2, Decimal(25), 'USD', trading=ta)

    # Ensure Lines were Added
    assert t.lines is not None
    assert isinstance(t.lines, list)
    assert len(t.lines) == 4
    assert t.lines[0].account == a
    assert t.lines[0].amount == Decimal(100)
    assert t.lines[1].account == o1
    assert t.lines[1].amount == Decimal(100)
    assert t.lines[3].account == o2
    assert t.lines[3].amount == Decimal(25)
    assert t.lines[2].account == ta

    # Ensure Split was Added
    assert t.splits is not None
    assert isinstance(t.splits, list)
    assert len(t.splits) == 2

    assert t.splits[0].left_line == t.lines[0]
    assert t.splits[0].right_line == t.lines[1]
    assert t.splits[0].type == TransactionType.Outflow
    assert t.splits[0].amount == Decimal(100)

    assert t.splits[1].left_line == t.lines[0]
    assert t.splits[1].right_line == t.lines[3]
    assert t.splits[1].type == TransactionType.Outflow
    assert t.splits[1].amount == Decimal(25)

    # Ensure Entries were Added
    check_entries(t.splits[0], [
        ( a, Decimal(  80), 'EUR'),
        (ta, Decimal( -80), 'EUR'),
        (ta, Decimal( 100), 'USD'),
        (o1, Decimal( 100), 'USD'),
    ])
    check_entries(t.splits[1], [
        ( a, Decimal(  20), 'EUR'),
        (ta, Decimal( -20), 'EUR'),
        (ta, Decimal(  25), 'USD'),
        (o2, Decimal(  25), 'USD'),
    ])

    assert t.amount == Decimal(125)


def test_transaction_can_add_splits_bbf_nonsplit():
    # Foreign Transaction between Foreign and Base Currency
    # Use Case: Expat budgeting in "local" currency spending from "home"
    # checking account

    # Setup User and Accounts
    u = User(currency='EUR')
    a = Account(user=u, active=True, name='A', role=AccountRole.Personal, type=AccountType.Asset, currency='EUR')
    o = Account(user=u, active=True, name='O', role=AccountRole.Budget, type=AccountType.Expense, currency='USD')
    ta = Account(user=u, active=True, name='T', role=AccountRole.System, type=AccountType.Trading, currency=u.currency)

    # Setup Transaction
    t = Transaction(
        user=u,
        account=a,
        currency='EUR',
        foreign_currency='USD',
        foreign_exchrate=Decimal('0.8'),
    )

    # Add Transaction Line for EUR 100
    t.add_split(o, Decimal(-100), 'EUR', trading=ta)

    # Ensure Lines were Added
    assert t.lines is not None
    assert isinstance(t.lines, list)
    assert len(t.lines) == 3
    assert t.lines[0].account == a
    assert t.lines[0].amount == Decimal(-100)
    assert t.lines[1].account == o
    assert t.lines[1].amount == Decimal(125)
    assert t.lines[2].account == ta

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
        (a, Decimal(-100), 'EUR'),
        (ta, Decimal(-100), 'EUR'),
        (ta, Decimal( 125), 'USD'),
        (o, Decimal( 125), 'USD'),
    ])

    assert t.amount == Decimal(-100)


def test_transaction_can_add_splits_bbf_split():
    # Foreign Transaction between Base Currency Accounts
    # Use Case: Buy something while travelling in a foreign country

    # Setup User and Accounts
    u = User(currency='USD')
    a = Account(user=u, active=True, name='A', role=AccountRole.Personal, type=AccountType.Liability, currency='USD')
    o1 = Account(user=u, active=True, name='O1', role=AccountRole.Budget, type=AccountType.Expense, currency='EUR')
    o2 = Account(user=u, active=True, name='O2', role=AccountRole.Budget, type=AccountType.Expense, currency='EUR')
    ta = Account(user=u, active=True, name='T', role=AccountRole.System, type=AccountType.Trading, currency=u.currency)

    # Setup Transaction
    t = Transaction(
        user=u,
        account=a,
        currency='USD',
        foreign_currency='EUR',
        foreign_exchrate=Decimal('1.25'),
    )

    # Add Transaction Line for USD 125
    t.add_split(o1, Decimal(100), 'USD', trading=ta)
    t.add_split(o2, Decimal(25), 'USD', trading=ta)

    # Ensure Lines were Added
    assert t.lines is not None
    assert isinstance(t.lines, list)
    assert len(t.lines) == 4
    assert t.lines[0].account == a
    assert t.lines[0].amount == Decimal(125)
    assert t.lines[1].account == o1
    assert t.lines[1].amount == Decimal(80)
    assert t.lines[3].account == o2
    assert t.lines[3].amount == Decimal(20)
    assert t.lines[2].account == ta

    # Ensure Split was Added
    assert t.splits is not None
    assert isinstance(t.splits, list)
    assert len(t.splits) == 2

    assert t.splits[0].left_line == t.lines[0]
    assert t.splits[0].right_line == t.lines[1]
    assert t.splits[0].type == TransactionType.Outflow
    assert t.splits[0].amount == Decimal(100)

    assert t.splits[1].left_line == t.lines[0]
    assert t.splits[1].right_line == t.lines[3]
    assert t.splits[1].type == TransactionType.Outflow
    assert t.splits[1].amount == Decimal(25)

    # Ensure Entries were Added
    check_entries(t.splits[0], [
        ( a, Decimal( 100), 'USD'),
        (ta, Decimal(-100), 'USD'),
        (ta, Decimal(  80), 'EUR'),
        (o1, Decimal(  80), 'EUR'),
    ])
    check_entries(t.splits[1], [
        ( a, Decimal(  25), 'USD'),
        (ta, Decimal( -25), 'USD'),
        (ta, Decimal(  20), 'EUR'),
        (o2, Decimal(  20), 'EUR'),
    ])

    assert t.amount == Decimal(125)
