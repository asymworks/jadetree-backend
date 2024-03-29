"""Jade Tree Reports Service.

Jade Tree Personal Budgeting Application | jadetree.io
Copyright (c) 2020 Asymworks, LLC.  All Rights Reserved.
"""

import datetime

from jadetree.database.queries import q_report_net_worth
from jadetree.database.queries.reports import (
    q_report_by_category,
    q_report_by_payee,
    q_report_income,
)

from .budget import _load_budget
from .util import check_session, check_user


def net_worth(session, user, filter=None):
    """Report the user's net worth in assets and liabilities per month."""
    check_session(session)
    check_user(user)

    accounts = filter['accounts'] if 'accounts' in filter else None

    q = q_report_net_worth(session, user.id, filter_accounts=accounts)
    data = []
    cur_date = datetime.date.today().replace(day=1)
    last_date = None
    for y, m, assets, liabilities in q.all():
        last_date = datetime.date(year=int(y), month=int(m), day=1)
        data.append(dict(
            month=last_date,
            assets=assets,
            liabilities=liabilities,
            currency=user.currency,
        ))

    # Append missing months
    if cur_date > last_date:
        while cur_date > last_date:
            last_date = (last_date + datetime.timedelta(days=32)).replace(day=1)
            data.append(dict(
                month=last_date,
                assets=data[-1]['assets'],
                liabilities=data[-1]['liabilities'],
                currency=user.currency,
            ))

    if 'start_date' in filter:
        return [
            d for d in data
            if d['month'] >= filter['start_date'] and d['month'] <= filter['end_date']
        ]

    return data


def spending_by_category(session, user, budget_id, filter=None):
    """Report the user's spending by category."""
    check_session(session)
    check_user(user)

    # Check existence and authorization for budget id
    _load_budget(session, user, budget_id)

    q = q_report_by_category(session, budget_id, filter=filter)
    data = []
    for category_id, amount, currency in q.all():
        data.append(dict(
            category_id=category_id,
            amount=amount,
            currency=currency,
        ))

    return data


def spending_by_payee(session, user, budget_id, filter=None):
    """Report the user's spending by payee."""
    check_session(session)
    check_user(user)

    # Check existence and authorization for budget id
    _load_budget(session, user, budget_id)

    q = q_report_by_payee(session, budget_id, filter=filter)
    data = []
    for payee_id, amount, currency in q.all():
        data.append(dict(
            payee_id=payee_id,
            amount=amount,
            currency=currency,
        ))

    return data


def income_allocation(session, user, budget_id, filter=None):
    """Report the user's income allocation."""
    check_session(session)
    check_user(user)

    # Check existence and authorization for budget id
    _load_budget(session, user, budget_id)

    q_income = q_report_income(session, budget_id, filter=filter)
    income, currency = q_income.one()
    categories = spending_by_category(session, user, budget_id, filter=filter)
    # TODO: Multi-Currency Support
    spent = sum([c['amount'] for c in categories])

    return dict(
        income=income,
        spent=spent,
        unspent=income - spent,
        currency=currency,
        categories=categories,
    )
