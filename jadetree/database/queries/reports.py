"""Database Queries for Reports.

Jade Tree Personal Budgeting Application | jadetree.io
Copyright (c) 2021 Asymworks, LLC.  All Rights Reserved.
"""

import datetime

from sqlalchemy import and_, case, func

from jadetree.domain.models import (
    Account,
    Category,
    Payee,
    Transaction,
    TransactionEntry,
    TransactionLine,
    TransactionSplit,
)
from jadetree.domain.types import AccountRole, AccountType


def q_report_net_worth(session, user_id, *, filter_accounts=None):
    """Report Assets and Liabilities by month.

    Summarizes a user's total assets and liabilities by month. The net worth
    can then be calculated by subtracting the liability amounts from the asset
    amounts.

    Args:
        session: Database Session
        user_id: User Id for Net Worth Calculation
        filter_accounts: List of Account Ids to include in the report. If the
            argument is None (the default), all accounts are used.

    Returns:
        SQLalchemy Query with columns (year, month, assets, liabilities)
    """
    # FIXME: Not multiple currency-aware
    sq = session.query(
        func.extract('year', Transaction.date).label('year'),
        func.extract('month', Transaction.date).label('month'),
        func.sum(
            case(
                [(Account.type == AccountType.Asset, TransactionEntry.amount)],
                else_=0
            )
        ).label('asset'),
        func.sum(
            case(
                [(Account.type == AccountType.Liability, TransactionEntry.amount)],
                else_=0
            )
        ).label('liability'),
    ).join(
        TransactionLine,
        TransactionLine.transaction_id == Transaction.id
    ).join(
        TransactionEntry,
        TransactionEntry.line_id == TransactionLine.id
    ).join(
        Account,
        Account.id == TransactionLine.account_id
    ).group_by(
        'year', 'month',
    ).order_by(
        'year', 'month'
    ).filter(
        Account.type.in_((AccountType.Asset, AccountType.Liability)),
        Account.user_id == user_id
    )

    # Apply filters to subquery
    if filter_accounts:
        sq = sq.filter(Account.id.in_(filter_accounts))

    sq = sq.subquery()

    return session.query(
        sq.c.year,
        sq.c.month,
        func.sum(sq.c.asset).over(
            order_by=(sq.c.year, sq.c.month),
            range_=(None, 0)
        ).label('assets'),
        func.sum(sq.c.liability).over(
            order_by=(sq.c.year, sq.c.month),
            range_=(None, 0)
        ).label('liabilities'),
    ).order_by(
        'year', 'month'
    )


def sq_spending_report(session, budget_id, *, filter):
    """Generate a Spending Report subquery for Category or Payee reporting.

    Summarizes a user's spending per category over a range of months. Note this
    only returns expenses; income is not reported.

    Args:
        session: Database Session
        budget_id: Budget Id for Reporting
        filter: Dictionary of filters to apply to the query (accepts `start_date`,
            `end_date`, `categories`, `payees`, and `accounts` keys)

    Returns:
        SQLalchemy Query with columns (`year`, `month`, `account_id`, `category_id`,
            `payee_id`, `amount`, `currency`)
    """
    sq = session.query(
        Category.id.label('category_id'),
        Payee.id.label('payee_id'),
        func.sum(TransactionEntry.amount).label('amount'),
        TransactionEntry.currency.label('currency')
    ).join(
        TransactionLine,
        TransactionLine.id == TransactionEntry.line_id
    ).join(
        Transaction,
        Transaction.id == TransactionLine.transaction_id
    ).join(
        Account,
        Account.id == TransactionLine.account_id
    ).join(
        TransactionSplit,
        TransactionSplit.transaction_id == Transaction.id
    ).join(
        Category,
        Category.id == TransactionSplit.category_id
    ).join(
        Payee,
        Payee.id == Transaction.payee_id
    ).filter(
        Account.role == AccountRole.Budget,
        Account.type == AccountType.Expense,
        Account.budget_id == budget_id,
        Category.system == False,               # noqa: E712
        Payee.system == False,                  # noqa: E712
    ).group_by(
        TransactionEntry.currency,
        Payee.id,
        Category.id
    )

    # Apply filters to subquery
    if 'accounts' in filter:
        sq = sq.filter(Transaction.account_id.in_(filter['accounts']))

    if 'categories' in filter:
        sq = sq.filter(Category.id.in_(filter['categories']))

    if 'payees' in filter:
        sq = sq.filter(Payee.id.in_(filter['payees']))

    if 'start_date' in filter and 'end_date' in filter:
        end_month = filter['end_date'] + datetime.timedelta(days=32)
        end_month.replace(day=1)

        sq = sq.filter(and_(
            Transaction.date >= filter['start_date'],
            Transaction.date < end_month,
        ))

    return sq.subquery()


def q_report_by_category(session, budget_id, *, filter=None):
    """Report Category spending by month.

    Summarizes a user's spending per category over a range of months. Note this
    only returns expenses; income is not reported.

    Args:
        session: Database Session
        budget_id: Budget Id for Reporting
        filter: Dictionary of filters to apply to the query (accepts `start_date`,
            `end_date`, `categories`, `payees`, and `accounts` keys)

    Returns:
        SQLalchemy Query with columns (category_id, amount, currency)
    """
    sq = sq_spending_report(session, budget_id, filter=filter)

    return session.query(
        sq.c.category_id,
        func.sum(sq.c.amount),
        sq.c.currency
    ).group_by(
        sq.c.currency,
        sq.c.category_id
    )


def q_report_by_payee(session, budget_id, *, filter=None):
    """Report Payee spending by month.

    Summarizes a user's spending per payee over a range of months. Note this
    only returns expenses; income is not reported.

    Args:
        session: Database Session
        budget_id: Budget Id for Reporting
        filter: Dictionary of filters to apply to the query (accepts `start_date`,
            `end_date`, `categories`, `payees`, and `accounts` keys)

    Returns:
        SQLalchemy Query with columns (payee_id, amount, currency)
    """
    sq = sq_spending_report(session, budget_id, filter=filter)

    return session.query(
        sq.c.payee_id,
        func.sum(sq.c.amount),
        sq.c.currency
    ).group_by(
        sq.c.currency,
        sq.c.payee_id
    )


def q_report_income(session, budget_id, *, filter=None):
    """Report Income over a Time.

    Args:
        session: Database Session
        budget_id: Budget Id for Reporting
        filter: Dictionary of filters to apply to the query (accepts `start_date`
            and `end_date`)

    Returns:
        SQLalchemy Query with columns (income, currency)
    """
    q = session.query(
        func.sum(TransactionEntry.amount).label('amount'),
        TransactionEntry.currency.label('currency')
    ).join(
        TransactionLine,
        TransactionLine.id == TransactionEntry.line_id
    ).join(
        Transaction,
        Transaction.id == TransactionLine.transaction_id
    ).join(
        Account,
        Account.id == TransactionLine.account_id
    ).filter(
        Account.role == AccountRole.Budget,
        Account.type == AccountType.Income,
        Account.budget_id == budget_id,
    ).group_by(
        TransactionEntry.currency,
    )

    # Apply filters to subquery
    if 'start_date' in filter and 'end_date' in filter:
        end_month = filter['end_date'] + datetime.timedelta(days=32)
        end_month.replace(day=1)

        q = q.filter(and_(
            Transaction.date >= filter['start_date'],
            Transaction.date < end_month,
        ))

    return q
