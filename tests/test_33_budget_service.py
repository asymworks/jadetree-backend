# =============================================================================
#
# Jade Tree Personal Budgeting Application | jadetree.io
# Copyright (c) 2020 Asymworks, LLC.  All Rights Reserved.
#
# =============================================================================

import pytest  # noqa: F401

from jadetree.domain.models import Account, Budget, Category
from jadetree.domain.types import AccountRole, AccountType
from jadetree.service import budget as budget_service


def test_create_budget_adds_budget(session, user_with_profile):
    b = budget_service.create_budget(session, user_with_profile, 'Test Budget')

    assert b.id > 0
    assert len(session.query(Budget).all()) == 1

    u = user_with_profile

    assert b.user == u
    assert b.name == 'Test Budget'
    assert b.currency == u.currency

    assert session.query(Account).filter(Account.budget == b).count() == 2
    assert session.query(Category).filter(Category.budget == b).count() == 4

    e1 = session.query(Account).filter(Account.budget == b, Account.name == '_income').one()
    e2 = session.query(Account).filter(Account.budget == b, Account.name == '_expense').one()

    g1 = session.query(Category).filter(Category.budget == b, Category.name == '_income').one()
    c1 = session.query(Category).filter(Category.budget == b, Category.name == '_cur_month').one()
    c2 = session.query(Category).filter(Category.budget == b, Category.name == '_next_month').one()
    g2 = session.query(Category).filter(Category.budget == b, Category.name == '_debt').one()

    assert e1.user == u
    assert e1.budget == b
    assert e1.role == AccountRole.Budget
    assert e1.type == AccountType.Income
    assert e1.currency == b.currency

    assert e2.user == u
    assert e2.budget == b
    assert e2.role == AccountRole.Budget
    assert e2.type == AccountType.Expense
    assert e2.currency == b.currency

    assert g1.parent is None
    assert g1.system is True
    assert g1.hidden is True

    assert c1.parent is g1
    assert c1.system is True
    assert c1.hidden is True

    assert c2.parent is g1
    assert c2.system is True
    assert c2.hidden is True

    assert g2.parent is None
    assert g2.system is False
    assert g2.hidden is True


def test_create_budget_with_currency(session, user_with_profile):
    b = budget_service.create_budget(
        session,
        user_with_profile,
        'Test Budget 2',
        currency='EUR',
    )

    u = user_with_profile

    assert b is not None

    assert b.user == u
    assert b.name == 'Test Budget 2'
    assert b.currency != u.currency
    assert b.currency == 'EUR'

    assert session.query(Account).filter(Account.budget == b).count() == 2
    assert session.query(Category).filter(Category.budget == b).count() == 4

    assert [a.currency for a in session.query(Account).filter(Account.budget == b).all()] == ['EUR', 'EUR']


def test_create_budget_with_only_groups(session, user_with_profile):
    b = budget_service.create_budget(
        session,
        user_with_profile,
        'Test Budget',
        categories=[
            { 'name': 'Monthly Expenses' },
            { 'name': 'Rainy Day Funds' },
        ],
    )

    u = user_with_profile

    assert b is not None

    assert b.user == u
    assert b.name == 'Test Budget'
    assert b.currency == u.currency

    assert session.query(Category).filter(Category.budget == b).filter(Category.parent == None).count() == 4    # noqa: E711

    c1 = session.query(Category).filter(Category.budget == b, Category.name == 'Monthly Expenses').one()
    c2 = session.query(Category).filter(Category.budget == b, Category.name == 'Rainy Day Funds').one()

    assert c1.parent is None
    assert c1.system is False
    assert c1.hidden is False

    assert c2.parent is None
    assert c2.system is False
    assert c2.hidden is False


def test_create_budget_with_simple_categories(session, user_with_profile):
    b = budget_service.create_budget(
        session,
        user_with_profile,
        'Test Budget',
        categories=[
            {
                'name': 'Monthly Expenses',
                'categories': ['Rent', 'Groceries'],
            },
            {
                'name': 'Rainy Day Funds',
                'categories': ['Car Insurance'],
            }
        ],
    )

    assert session.query(Category).filter(Category.budget == b).count() == 9
    assert session.query(Category).filter(Category.budget == b).filter(Category.parent == None).count() == 4    # noqa: E711
    assert session.query(Category).filter(Category.budget == b).filter(Category.parent != None).count() == 5    # noqa: E711

    c1 = session.query(Category).filter(Category.budget == b, Category.name == 'Rent').one()
    c2 = session.query(Category).filter(Category.budget == b, Category.name == 'Groceries').one()
    c3 = session.query(Category).filter(Category.budget == b, Category.name == 'Car Insurance').one()

    g1 = session.query(Category).filter(Category.budget == b, Category.name == 'Monthly Expenses').one()
    g2 = session.query(Category).filter(Category.budget == b, Category.name == 'Rainy Day Funds').one()

    assert g1.parent is None
    assert g1.system is False
    assert g1.hidden is False

    assert g2.parent is None
    assert g2.system is False
    assert g2.hidden is False

    assert c1.parent == g1
    assert c1.system is False
    assert c1.hidden is False

    assert c2.parent == g1
    assert c2.system is False
    assert c2.hidden is False

    assert c3.parent == g2
    assert c3.system is False
    assert c3.hidden is False


def test_create_budget_with_complex_categories(session, user_with_profile):
    b = budget_service.create_budget(
        session,
        user_with_profile,
        'Test Budget',
        categories=[
            {
                'name': 'Monthly Expenses',
                'categories': [
                    'Rent',
                    {
                        'name': 'Groceries',
                        'system': True,
                        'hidden': True,
                    }
                ]
            },
            {
                'name': 'Rainy Day Funds',
                'categories': [
                    {
                        'name': 'Car Insurance',
                        'system': True,
                        'hidden': False,
                    }
                ],
                'system': False,
                'hidden': True,
            }
        ],
    )

    assert session.query(Category).filter(Category.budget == b).count() == 9
    assert session.query(Category).filter(Category.budget == b).filter(Category.parent == None).count() == 4    # noqa: E711
    assert session.query(Category).filter(Category.budget == b).filter(Category.parent != None).count() == 5    # noqa: E711

    c1 = session.query(Category).filter(Category.budget == b, Category.name == 'Rent').one()
    c2 = session.query(Category).filter(Category.budget == b, Category.name == 'Groceries').one()
    c3 = session.query(Category).filter(Category.budget == b, Category.name == 'Car Insurance').one()

    g1 = session.query(Category).filter(Category.budget == b, Category.name == 'Monthly Expenses').one()
    g2 = session.query(Category).filter(Category.budget == b, Category.name == 'Rainy Day Funds').one()

    assert g1.parent is None
    assert g1.system is False
    assert g1.hidden is False

    assert g2.parent is None
    assert g2.system is False
    assert g2.hidden is True

    assert c1.parent == g1
    assert c1.system is False
    assert c1.hidden is False

    assert c2.parent == g1
    assert c2.system is True
    assert c2.hidden is True

    assert c3.parent == g2
    assert c3.system is True
    assert c3.hidden is False
