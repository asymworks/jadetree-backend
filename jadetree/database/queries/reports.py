"""Database Queries for Reports.

Jade Tree Personal Budgeting Application | jadetree.io
Copyright (c) 2021 Asymworks, LLC.  All Rights Reserved.
"""

from sqlalchemy import case, func

from jadetree.domain.models import (
    Account,
    Transaction,
    TransactionEntry,
    TransactionLine,
)
from jadetree.domain.types import AccountType


def q_report_net_worth(session, user_id):
    """Report Assets and Liabilities by month.

    Summarizes a user's total assets and liabilities by month. The net worth
    can then be calculated by subtracting the liability amounts from the asset
    amounts.

    Args:
        session: Database Session
        user_id: User Id for Net Worth Calculation

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
    ).subquery()

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
