# =============================================================================
#
# Jade Tree Personal Budgeting Application | jadetree.io
# Copyright (c) 2020 Asymworks, LLC.  All Rights Reserved.
#
# =============================================================================

from sqlalchemy import and_, func

from jadetree.domain.models import Account, TransactionEntry, TransactionLine
from jadetree.domain.types import AccountRole

__all__ = ('q_account_balances', 'q_account_list')


def q_account_balances(session):
    '''Retrieve Account Balances indexed by Account'''
    return session\
        .query(
            TransactionLine.account_id.label('account_id'),
            func.sum(TransactionEntry.amount).label('balance')
        ).join(
            TransactionEntry,
            TransactionEntry.line_id == TransactionLine.id
        ).group_by(
            TransactionLine.account_id
        )


def q_account_list(session, user_id):
    '''Retrieve a listing of User Accounts'''
    sq = q_account_balances(session).subquery()
    return session\
        .query(
            Account.id.label('id'),
            Account.name.label('name'),
            Account.type.label('type'),
            Account.subtype.label('subtype'),
            Account.budget_id.label('budget_id'),
            sq.c.balance.label('balance'),
            Account.currency.label('currency'),
            Account.display_order.label('display_order'),
        ).outerjoin(
            sq,
            sq.c.account_id == Account.id,
        ).filter(
            and_(
                Account.user_id == user_id,
                Account.role == AccountRole.Personal
            )
        )
