# =============================================================================
#
# Jade Tree Personal Budgeting Application | jadetree.io
# Copyright (c) 2020 Asymworks, LLC.  All Rights Reserved.
#
# =============================================================================

from sqlalchemy import and_, case, func
from sqlalchemy.orm import aliased

from jadetree.domain.models import (
    Account,
    Category,
    Transaction,
    TransactionEntry,
    TransactionLine,
    TransactionSplit,
)
from jadetree.domain.types import AccountRole

__all__ = (
    'q_txn_account_amounts',
    'q_txn_account_balances',
    'q_txn_account_lines',
    'q_txn_category_amounts',
    'q_txn_category_lines',
    'q_txn_split_fields',
    'q_txn_schema_fields',
)


def q_txn_account_amounts(session):
    '''Query Transaction Amounts by Account'''
    return session \
        .query(
            Transaction.id.label('transaction_id'),
            Account.id.label('account_id'),
            TransactionLine.id.label('line_id'),
            func.sum(TransactionEntry.amount).label('amount'),
            TransactionEntry.currency.label('currency')
        ).join(
            TransactionLine,
            TransactionLine.transaction_id == Transaction.id
        ).join(
            Account,
            Account.id == TransactionLine.account_id
        ).join(
            TransactionEntry,
            TransactionEntry.line_id == TransactionLine.id
        ).group_by(
            Account.id,
            Transaction.id,
            TransactionLine.id,
            TransactionEntry.currency,
        )


def q_txn_account_balances(session):
    '''Retrieve Running Account Balances indexed by Account and Transaction'''
    sq_txn_amts = q_txn_account_amounts(session).subquery()
    return session \
        .query(
            sq_txn_amts.c.transaction_id.label('transaction_id'),
            sq_txn_amts.c.account_id.label('account_id'),
            sq_txn_amts.c.amount.label('amount'),
            func.sum(sq_txn_amts.c.amount).over(
                partition_by=sq_txn_amts.c.account_id,
                # Note: this should match what is used in q_txn_schema_fields
                order_by=(
                    Transaction.date,
                    sq_txn_amts.c.amount,
                    sq_txn_amts.c.transaction_id
                ),
                range_=(None, 0)
            ).label('balance'),
            sq_txn_amts.c.currency.label('currency')
        ) \
        .join(
            Transaction,
            Transaction.id == sq_txn_amts.c.transaction_id
        )


def q_txn_category_amounts(session):
    '''Query Transaction Amounts by Category'''
    return session \
        .query(
            Transaction.id.label('transaction_id'),
            Category.id.label('category_id'),
            TransactionSplit.id.label('split_id'),
            func.sum(TransactionEntry.amount).label('amount'),
            TransactionEntry.currency.label('currency')
        ).join(
            TransactionLine,
            TransactionLine.transaction_id == Transaction.id
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
            TransactionEntry,
            TransactionEntry.line_id == TransactionLine.id
        ).filter(
            Account.role == AccountRole.Budget
        ).group_by(
            Transaction.id,
            TransactionLine.id,
            TransactionSplit.id,
            TransactionEntry.currency,
            Category.id
        )


def q_txn_split_fields(session):
    '''Query the fields required for the TransactionSplitSchema interface'''
    sq_other_line = session \
        .query(
            TransactionLine.id.label('line_id'),
            case(
                [
                    (
                        TransactionLine.id == TransactionSplit.left_line_id,
                        TransactionSplit.right_line_id
                    ),
                    (
                        TransactionLine.id == TransactionSplit.right_line_id,
                        TransactionSplit.left_line_id
                    ),
                ],
                else_=None
            ).label('other_line_id'),
        ).join(
            TransactionEntry,
            TransactionEntry.line_id == TransactionLine.id
        ).join(
            TransactionSplit,
            TransactionSplit.id == TransactionEntry.split_id
        ).group_by(
            TransactionLine.id,
            'other_line_id'
        ).subquery()

    OtherLine = aliased(TransactionLine)
    sq_transfer_id = session.query(
        TransactionLine.id.label('line_id'),
        case(
            [
                (
                    Account.role == AccountRole.Personal,
                    Account.id
                ),
            ],
            else_=None
        ).label('transfer_id'),
    ).join(
        sq_other_line,
        sq_other_line.c.line_id == TransactionLine.id
    ).join(
        OtherLine,
        OtherLine.id == sq_other_line.c.other_line_id
    ).join(
        Account,
        Account.id == OtherLine.account_id
    ).distinct().subquery()

    return session \
        .query(
            TransactionLine.id.label('line_id'),
            TransactionSplit.id.label('split_id'),
            TransactionSplit.category_id,
            sq_transfer_id.c.transfer_id,
            TransactionEntry.amount,
            TransactionEntry.currency,
            TransactionSplit.type,
            TransactionSplit.memo,
        ).join(
            TransactionEntry,
            TransactionEntry.line_id == TransactionLine.id
        ).join(
            TransactionSplit,
            TransactionSplit.id == TransactionEntry.split_id
        ).join(
            sq_transfer_id,
            sq_transfer_id.c.line_id == TransactionLine.id
        )


def q_txn_schema_fields(session, *, reverse=False):
    '''Query the fields required by the TransactionSchema interface'''
    sq_txn_bals = q_txn_account_balances(session).subquery()
    sq_txn_splits = q_txn_split_fields(session).subquery()
    q = session \
        .query(
            Transaction.id.label('transaction_id'),
            Transaction.account_id.label('account_id'),
            TransactionLine.id.label('line_id'),
            TransactionLine.account_id.label('line_account_id'),
            Transaction.date.label('date'),
            Transaction.payee_id.label('payee_id'),
            Transaction.check.label('check'),
            Transaction.memo.label('memo'),
            sq_txn_bals.c.amount.label('amount'),
            sq_txn_bals.c.balance.label('balance'),
            sq_txn_bals.c.currency.label('currency'),
            Transaction.currency.label('transaction_currency'),
            Transaction.foreign_currency.label('foreign_currency'),
            Transaction.foreign_exchrate.label('foreign_exchrate'),
            TransactionLine.cleared.label('cleared'),
            TransactionLine.cleared_at.label('cleared_at'),
            TransactionLine.reconciled.label('reconciled'),
            TransactionLine.reconciled_at.label('reconciled_at'),
            # Splits (note 'split_' prefix will be dropped)
            sq_txn_splits.c.split_id.label('split_split_id'),
            sq_txn_splits.c.category_id.label('split_category_id'),
            sq_txn_splits.c.transfer_id.label('split_transfer_id'),
            sq_txn_splits.c.amount.label('split_amount'),
            sq_txn_splits.c.currency.label('split_currency'),
            sq_txn_splits.c.type.label('split_type'),
            sq_txn_splits.c.memo.label('split_memo'),
        ).join(
            TransactionLine,
            TransactionLine.transaction_id == Transaction.id
        ).join(
            Account,
            Account.id == TransactionLine.account_id,
        ).join(
            sq_txn_bals,
            and_(
                sq_txn_bals.c.transaction_id == Transaction.id,
                sq_txn_bals.c.account_id == TransactionLine.account_id
            )
        ).join(
            sq_txn_splits,
            sq_txn_splits.c.line_id == TransactionLine.id,
        )

    # Ensure predictable transaction / balance ordering; needs to match what
    # is used in q_txn_account_balances
    if reverse:
        return q.order_by(
            Transaction.date.desc(),
            sq_txn_bals.c.amount.desc(),
            Transaction.id.desc(),
        )

    return q.order_by(
        Transaction.date.asc(),
        sq_txn_bals.c.amount.asc(),
        Transaction.id.asc(),
    )


def q_txn_account_lines(session, account_id=None, *, reverse=False, reconciled=True):
    '''Return TransactionSchema lines for an account (or all user accounts)'''
    q = q_txn_schema_fields(session, reverse=reverse) \
        .filter(Account.role == AccountRole.Personal)

    if not reconciled:
        q = q.filter(TransactionLine.reconciled == False)   # noqa: E712

    if account_id is not None:
        q = q.filter(Account.id == account_id)

    return q


def q_txn_category_lines(session, category_id, *, reverse=False):
    '''Return TransactionSchema lines for an expense category'''
    return q_txn_schema_fields(session, reverse=reverse) \
        .filter(Account.role == AccountRole.Budget) \
        .filter_by(category_id=category_id)
