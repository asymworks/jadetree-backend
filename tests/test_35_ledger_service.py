# =============================================================================
#
# Jade Tree Personal Budgeting Application | jadetree.io
# Copyright (c) 2020 Asymworks, LLC.  All Rights Reserved.
#
# =============================================================================

import pytest   # noqa: F401

from datetime import date
from decimal import Decimal
from sqlalchemy import func, and_

from jadetree.domain.models import Account, Category, TransactionEntry, \
    TransactionLine, TransactionSplit
from jadetree.domain.types import AccountType, AccountSubtype, PayeeRole, \
    TransactionType
from jadetree.service import account as account_service
from jadetree.service import budget as budget_service
from jadetree.service import ledger as ledger_service
from jadetree.service import payee as payee_service

from .helpers import check_transaction_entries as check_entries


@pytest.fixture(scope='function')
def budget_id(session, user_with_profile):
    u = user_with_profile
    b = budget_service.create_budget(session, u, 'Test Budget', 'USD')
    return b.id


@pytest.fixture(scope='function')
def default_accounts(session, user_with_profile, budget_id):
    accts = []
    cats = []

    # Create personal accounts for Checking, Savings and CC
    accts.append(account_service.create_user_account(session, user_with_profile, 'Checking', AccountType.Asset, 'USD', Decimal(10000), date(2020, 1, 1), AccountSubtype.Checking, budget_id=budget_id))
    accts.append(account_service.create_user_account(session, user_with_profile, 'Savings', AccountType.Asset, 'USD', Decimal(50000), date(2020, 1, 1), AccountSubtype.Savings, budget_id=budget_id))
    accts.append(account_service.create_user_account(session, user_with_profile, 'Credit Card', AccountType.Liability, 'USD', Decimal(500), date(2020, 1, 1), AccountSubtype.CreditCard, budget_id=budget_id))

    # Create budget categories for Rent, Groceries, and Insurance
    g1 = budget_service.create_budget_category_group(session, user_with_profile, budget_id, 'Monthly Expenses')
    g2 = budget_service.create_budget_category_group(session, user_with_profile, budget_id, 'Yearly Expenses')
    cats.append(budget_service.create_budget_category(session, user_with_profile, budget_id, g1.id, 'Rent'))
    cats.append(budget_service.create_budget_category(session, user_with_profile, budget_id, g1.id, 'Groceries'))
    cats.append(budget_service.create_budget_category(session, user_with_profile, budget_id, g2.id, 'Insurance'))

    # Return ID List
    return tuple([a.id for a in accts]), tuple([c.id for c in cats])


@pytest.fixture(scope='function')
def default_payees(session, user_with_profile):
    u = user_with_profile
    payees = []

    payees.append(payee_service.create_payee(session, u, 'Vons'))
    payees.append(payee_service.create_payee(session, u, 'Landlord'))

    return tuple([p.id for p in payees])


def test_add_simple_transaction(
    session, user_with_profile, budget_id, default_accounts, default_payees
):
    (a_chk, a_svg, a_cc), (c_rent, c_groc, c_ins) = default_accounts
    (p_vons, p_landlord) = default_payees
    t = ledger_service.create_transaction(
        session=session,
        user=user_with_profile,
        account_id=a_cc,
        date=date(2020, 1, 2),
        amount=Decimal(80),
        payee_id=p_vons,
        splits=[
            dict(
                category_id=c_groc,
                amount=Decimal(80),
            ),
        ]
    )

    assert t.id > 0

    a = session.query(Account).filter(Account.id == a_cc).one()
    o = session.query(Account).filter(Account.name == '_expense').one()
    c = session.query(Category).get(c_groc)

    assert t.account == a
    assert t.date == date(2020, 1, 2)
    assert t.memo is None
    assert t.currency == 'USD'
    assert t.foreign_currency is None
    assert t.foreign_exchrate is None

    assert t.payee is not None
    assert t.payee.user == user_with_profile
    assert t.payee.name == 'Vons'
    assert t.payee.role == PayeeRole.Expense
    assert t.payee.system is False
    assert t.payee.hidden is False

    assert len(t.lines) == 2

    assert t.lines[0].account == a
    assert t.lines[0].amount == Decimal(80)
    assert t.lines[0].cleared is False
    assert t.lines[0].reconciled is False

    assert t.lines[1].account == o
    assert t.lines[1].amount == Decimal(80)
    assert t.lines[1].cleared is False
    assert t.lines[1].reconciled is False

    assert len(t.splits) == 1
    assert t.splits[0].amount == Decimal(80)
    assert t.splits[0].left_line == t.lines[0]
    assert t.splits[0].right_line == t.lines[1]
    assert t.splits[0].category == c
    assert t.splits[0].type == TransactionType.Outflow

    check_entries(t.splits[0], [
        (a, Decimal(80), 'USD'),
        (o, Decimal(80), 'USD'),
    ])

    assert t.amount == Decimal(80)
    assert sum([ln.amount for ln in a.transaction_lines]) == Decimal(580)
    assert sum([ln.amount for ln in o.transaction_lines]) == Decimal(580)

    cat_balance = session.query(func.sum(TransactionEntry.amount)) \
        .join(TransactionSplit) \
        .join(TransactionLine, and_(
            TransactionLine.id == TransactionEntry.line_id,
            TransactionLine.account == o
        )) \
        .filter(TransactionSplit.category == c) \
        .scalar()

    assert cat_balance == Decimal(80)
