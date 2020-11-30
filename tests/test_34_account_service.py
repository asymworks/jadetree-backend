# =============================================================================
#
# Jade Tree Personal Budgeting Application | jadetree.io
# Copyright (c) 2020 Asymworks, LLC.  All Rights Reserved.
#
# =============================================================================

import pytest   # noqa: F401

from arrow import utcnow
from decimal import Decimal

from jadetree.domain.models import Account, Budget, Transaction
from jadetree.domain.types import AccountRole, AccountType, PayeeRole, \
    TransactionType
from jadetree.service import account as account_service
from jadetree.service import budget as budget_service

from .helpers import check_transaction_entries as check_entries


@pytest.fixture(scope='function')
def budget_id(session, user_with_profile):
    u = user_with_profile
    b = budget_service.create_budget(session, u, 'Test Budget', 'USD')
    return b.id


def test_create_user_account_zero_balance(session, user_with_profile):
    a = account_service.create_user_account(
        session=session,
        user=user_with_profile,
        name='Test Account',
        type=AccountType.Asset,
        currency='USD',
        balance=Decimal(0),
        balance_date=utcnow()
    )

    assert a.id > 0
    assert len(session.query(Account).filter(Account.role == AccountRole.Personal).all()) == 1

    assert a.user == user_with_profile
    assert a.name == 'Test Account'
    assert a.role == AccountRole.Personal
    assert a.type == AccountType.Asset
    assert a.subtype is None
    assert a.currency == user_with_profile.currency

    assert len(a.transaction_lines) == 0


def test_create_user_asset_account_with_capital(session, user_with_profile):
    a = account_service.create_user_account(
        session=session,
        user=user_with_profile,
        name='Test Account',
        type=AccountType.Asset,
        currency='USD',
        balance=Decimal(100),
        balance_date=utcnow()
    )

    assert a.id > 0
    assert len(session.query(Account).filter(Account.role == AccountRole.Personal).all()) == 1

    assert a.user == user_with_profile
    assert a.name == 'Test Account'
    assert a.role == AccountRole.Personal
    assert a.type == AccountType.Asset
    assert a.subtype is None
    assert a.currency == user_with_profile.currency

    t = session.query(Transaction).filter(Transaction.account == a).one()

    assert t.payee is not None
    assert t.payee.user == user_with_profile
    assert t.payee.role == PayeeRole.Initial
    assert t.payee.system is True

    assert len(t.lines) == 2
    assert t.lines[0].account.role == AccountRole.System
    assert t.lines[0].account.type == AccountType.Capital
    assert t.lines[0].amount == Decimal(100)
    assert t.lines[1].account == a
    assert t.lines[1].amount == Decimal(100)

    assert len(t.splits) == 1
    assert t.splits[0].left_line == t.lines[1]
    assert t.splits[0].right_line == t.lines[0]
    assert t.splits[0].type == TransactionType.System
    assert t.splits[0].amount == Decimal(100)

    check_entries(t.splits[0], [
        (a,                  Decimal(100), 'USD'),
        (t.lines[0].account, Decimal(100), 'USD'),
    ])

    assert t.amount == Decimal(100)


def test_create_user_liability_account_with_capital(session, user_with_profile):
    a = account_service.create_user_account(
        session=session,
        user=user_with_profile,
        name='Test Account',
        type=AccountType.Liability,
        currency='USD',
        balance=Decimal(100),
        balance_date=utcnow()
    )

    assert a.id > 0
    assert len(session.query(Account).filter(Account.role == AccountRole.Personal).all()) == 1

    assert a.user == user_with_profile
    assert a.name == 'Test Account'
    assert a.role == AccountRole.Personal
    assert a.type == AccountType.Liability
    assert a.subtype is None
    assert a.currency == user_with_profile.currency

    t = session.query(Transaction).filter(Transaction.account == a).one()

    assert t.payee is not None
    assert t.payee.user == user_with_profile
    assert t.payee.role == PayeeRole.Initial
    assert t.payee.system is True

    assert len(t.lines) == 2
    assert t.lines[0].account.role == AccountRole.System
    assert t.lines[0].account.type == AccountType.Capital
    assert t.lines[0].amount == Decimal(-100)
    assert t.lines[1].account == a
    assert t.lines[1].amount == Decimal(100)

    assert len(t.splits) == 1
    assert t.splits[0].left_line == t.lines[1]
    assert t.splits[0].right_line == t.lines[0]
    assert t.splits[0].type == TransactionType.System
    assert t.splits[0].amount == Decimal(100)

    check_entries(t.splits[0], [
        (a,                  Decimal( 100), 'USD'),
        (t.lines[0].account, Decimal(-100), 'USD'),
    ])

    assert t.amount == Decimal(100)


def test_create_user_asset_account_with_income(session, user_with_profile, budget_id):
    a = account_service.create_user_account(
        session=session,
        user=user_with_profile,
        budget_id=budget_id,
        name='Test Account',
        type=AccountType.Asset,
        currency='USD',
        balance=Decimal(100),
        balance_date=utcnow()
    )

    assert a.id > 0
    assert len(session.query(Account).filter(Account.role == AccountRole.Personal).all()) == 1

    b = session.query(Budget).filter(Budget.id == budget_id).one()

    assert a.user == user_with_profile
    assert a.name == 'Test Account'
    assert a.role == AccountRole.Personal
    assert a.type == AccountType.Asset
    assert a.subtype is None
    assert a.currency == user_with_profile.currency
    assert a.budget == b

    t = session.query(Transaction).filter(Transaction.account == a).one()

    assert t.payee is not None
    assert t.payee.user == user_with_profile
    assert t.payee.role == PayeeRole.Initial
    assert t.payee.system is True

    assert len(t.lines) == 2
    assert t.lines[0].account.role == AccountRole.Budget
    assert t.lines[0].account.type == AccountType.Income
    assert t.lines[0].account.name == '_income'
    assert t.lines[0].amount == Decimal(100)
    assert t.lines[1].account == a
    assert t.lines[1].amount == Decimal(100)

    assert len(t.splits) == 1
    assert t.splits[0].left_line == t.lines[1]
    assert t.splits[0].right_line == t.lines[0]
    assert t.splits[0].type == TransactionType.System
    assert t.splits[0].amount == Decimal(100)
    assert t.splits[0].category is not None
    assert t.splits[0].category.name == '_cur_month'
    assert t.splits[0].category.parent.name == '_income'

    check_entries(t.splits[0], [
        (a,                  Decimal(100), 'USD'),
        (t.lines[0].account, Decimal(100), 'USD'),
    ])

    assert t.amount == Decimal(100)


def test_create_user_liability_account_with_debt(session, user_with_profile, budget_id):
    a = account_service.create_user_account(
        session=session,
        user=user_with_profile,
        budget_id=budget_id,
        name='Test Account',
        type=AccountType.Liability,
        currency='USD',
        balance=Decimal(100),
        balance_date=utcnow()
    )

    assert a.id > 0
    assert len(session.query(Account).filter(Account.role == AccountRole.Personal).all()) == 1

    b = session.query(Budget).filter(Budget.id == budget_id).one()

    assert a.user == user_with_profile
    assert a.name == 'Test Account'
    assert a.role == AccountRole.Personal
    assert a.type == AccountType.Liability
    assert a.subtype is None
    assert a.currency == user_with_profile.currency
    assert a.budget == b

    t = session.query(Transaction).filter(Transaction.account == a).one()

    assert t.payee is not None
    assert t.payee.user == user_with_profile
    assert t.payee.role == PayeeRole.Initial
    assert t.payee.system is True

    assert len(t.lines) == 2
    assert t.lines[0].account.role == AccountRole.Budget
    assert t.lines[0].account.type == AccountType.Expense
    assert t.lines[0].account.name == '_expense'
    assert t.lines[0].amount == Decimal(100)
    assert t.lines[1].account == a
    assert t.lines[1].amount == Decimal(100)

    assert len(t.splits) == 1
    assert t.splits[0].left_line == t.lines[1]
    assert t.splits[0].right_line == t.lines[0]
    assert t.splits[0].type == TransactionType.System
    assert t.splits[0].amount == Decimal(100)
    assert t.splits[0].category is not None
    assert t.splits[0].category.name == a.name
    assert t.splits[0].category.parent.name == '_debt'

    check_entries(t.splits[0], [
        (a,                  Decimal(100), 'USD'),
        (t.lines[0].account, Decimal(100), 'USD'),
    ])

    assert t.amount == Decimal(100)
