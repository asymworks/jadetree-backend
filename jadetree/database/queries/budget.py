# =============================================================================
#
# Jade Tree Personal Budgeting Application | jadetree.io
# Copyright (c) 2020 Asymworks, LLC.  All Rights Reserved.
#
# =============================================================================

from sqlalchemy import and_, case, func

from jadetree.domain.models import (
    Account,
    BudgetEntry,
    Category,
    Transaction,
    TransactionEntry,
    TransactionLine,
    TransactionSplit,
)
from jadetree.domain.types import AccountRole, AccountType

__all__ = ('q_budget_summary', 'q_budget_tuples')


def q_budget_tuples(session, budget_id):
    '''
    Return a list of "Budget Tuples" for a budget, which are 3-tuples of
    (`Category.id`, ``year``, ``month``) for each `BudgetEntry` and
    `Transaction` items associated with the budget. This is used to build up
    the budget summary of budgeted income vs. outflows by month.
    '''
    sq1 = session \
        .query(
            TransactionSplit.category_id.label('category_id'),
            func.extract('year', Transaction.date).label('year'),
            func.extract('month', Transaction.date).label('month'),
        ).join(
            TransactionEntry,
            TransactionEntry.split_id == TransactionSplit.id,
        ).join(
            TransactionLine,
            TransactionLine.id == TransactionEntry.line_id,
        ).join(
            Account,
            Account.id == TransactionLine.account_id,
        ).join(
            Transaction,
            Transaction.id == TransactionSplit.transaction_id,
        ).filter(
            Account.role == AccountRole.Budget,
        ).distinct()

    # (Category, Year, Month) tuples from BudgetEntries
    sq2 = session \
        .query(
            Category.id.label('category_id'),
            func.extract('year', BudgetEntry.month).label('year'),
            func.extract('month', BudgetEntry.month).label('month'),
        ) \
        .join(Category, Category.id == BudgetEntry.category_id)

    # All (Category, Year, Month) tuples (incl. uncategorized)
    return sq2.union(sq1)


def q_budget_outflows(session, budget_id, month=None):
    '''
    '''
    sq_acct_sign = session.query(
        Account.id.label('account_id'),
        case(
            [
                (Account.type == AccountType.Liability, -1),
                (Account.type == AccountType.Expense, -1),
            ],
            else_=1,
        ).label('inflow_sign'),
        case(
            [
                (Account.type == AccountType.Liability, 1),
                (Account.type == AccountType.Expense, 1),
            ],
            else_=-1,
        ).label('outflow_sign'),
    ).subquery()

    # Outflows by Tuple
    return session.query(
        TransactionSplit.category_id.label('category_id'),
        func.extract('year', Transaction.date).label('year'),
        func.extract('month', Transaction.date).label('month'),
        func.sum(
            TransactionEntry.amount * sq_acct_sign.c.outflow_sign
        ).label('outflow'),
        func.count(Transaction.id.distinct()).label('num_transactions'),
    ).join(
        TransactionEntry,
        TransactionEntry.split_id == TransactionSplit.id,
    ).join(
        TransactionLine,
        TransactionLine.id == TransactionEntry.line_id,
    ).join(
        Account,
        Account.id == TransactionLine.account_id,
    ).join(
        sq_acct_sign,
        sq_acct_sign.c.account_id == Account.id,
    ).join(
        Transaction,
        Transaction.id == TransactionSplit.transaction_id,
    ).filter(
        Account.role == AccountRole.Budget,
    ).group_by('category_id', 'year', 'month')


def q_budget_summary(session, budget_id, month=None):
    '''
    '''
    sq_tuples = q_budget_tuples(session, budget_id).subquery()
    sq_outflows = q_budget_outflows(session, budget_id).subquery()

    # Budget Entries by Tuple
    sq2 = session \
        .query(
            BudgetEntry.id.label('entry_id'),
            BudgetEntry.category_id.label('category_id'),
            func.extract('year', BudgetEntry.month).label('year'),
            func.extract('month', BudgetEntry.month).label('month'),
            BudgetEntry.amount.label('budget'),
            BudgetEntry.rollover.label('rollover'),
            BudgetEntry.notes.label('notes'),
        ) \
        .filter(BudgetEntry.budget_id == budget_id) \
        .subquery()

    # Load Outflows and Budget Entries by Tuple
    q = session \
        .query(
            sq2.c.entry_id,
            sq_tuples.c.category_id,
            sq_tuples.c.year,
            sq_tuples.c.month,
            sq_outflows.c.outflow,
            sq_outflows.c.num_transactions,
            sq2.c.budget,
            sq2.c.rollover,
            sq2.c.notes,
        ) \
        .outerjoin(
            sq_outflows,
            and_(
                sq_outflows.c.category_id == sq_tuples.c.category_id,
                sq_outflows.c.year == sq_tuples.c.year,
                sq_outflows.c.month == sq_tuples.c.month
            )
        ) \
        .outerjoin(
            sq2,
            and_(
                sq2.c.category_id == sq_tuples.c.category_id,
                sq2.c.year == sq_tuples.c.year,
                sq2.c.month == sq_tuples.c.month
            )
        ) \
        .order_by(sq_tuples.c.year, sq_tuples.c.month, sq_tuples.c.category_id)

    # Filter by Month
    if month is not None:
        if len(month) != 2:
            raise TypeError('Expected (year, month) tuple in q_budget_summary')
        q = q.filter(
            sq_tuples.c.year == month[0],
            sq_tuples.c.month == month[1],
        )

    # Return Query
    return q
