"""Jade Tree Database ORM Setup.

Jade Tree Personal Budgeting Application | jadetree.io
Copyright (c) 2021 Asymworks, LLC.  All Rights Reserved.
"""

from sqlalchemy import and_

from jadetree.domain.models import (
    Account,
    Budget,
    BudgetEntry,
    Category,
    Payee,
    Transaction,
    TransactionEntry,
    TransactionLine,
    TransactionSplit,
    User,
)

from .globals import db
from .tables import (
    accounts,
    budget_entries,
    budgets,
    categories,
    payees,
    transaction_entries,
    transaction_lines,
    transaction_splits,
    transactions,
    users,
)

__all__ = ('init_orm', )


def init_orm():
    """Initialize the SQLalchemy ORM."""
    # User
    db.mapper(User, users, properties={
        'accounts': db.relationship(
            Account,
            backref='user',
            cascade='all, delete-orphan'
        ),
        'budgets': db.relationship(
            Budget,
            backref='user',
            cascade='all, delete-orphan'
        ),
        'payees': db.relationship(
            Payee,
            backref='user',
            cascade='all, delete-orphan',
        ),
        'transactions': db.relationship(
            Transaction,
            backref='user',
            cascade='all, delete-orphan',
        ),
    })

    # Account
    db.mapper(Account, accounts, properties={
        'payee': db.relationship(
            Payee,
            backref='account',
            uselist=False,
            cascade='all, delete-orphan'
        ),
        'transaction_lines': db.relationship(
            TransactionLine,
            backref='account'
        ),
    })

    # Budget
    db.mapper(Budget, budgets, properties={
        'accounts': db.relationship(
            Account,
            backref='budget'
        ),
        'categories': db.relationship(
            Category,
            backref='budget',
            cascade='all, delete-orphan'
        ),
        'entries': db.relationship(
            BudgetEntry,
            backref='budget',
            cascade='all, delete-orphan'
        ),
        'groups': db.relationship(
            Category,
            lazy='select',
            primaryjoin=and_(
                categories.c.budget_id == budgets.c.id,
                categories.c.parent_id == None              # noqa: E711
            ),
            viewonly=True,
        )
    })

    # BudgetEntry
    db.mapper(BudgetEntry, budget_entries)

    # Category
    db.mapper(Category, categories, properties={
        'parent': db.relationship(
            Category,
            remote_side=[categories.c.id],
        ),
        'children': db.relationship(Category, viewonly=True),
        'entries': db.relationship(
            BudgetEntry,
            backref='category',
            cascade='all, delete-orphan',
        )
    })

    # Transaction
    db.mapper(Transaction, transactions, properties={
        'account': db.relationship(Account),
        'lines': db.relationship(
            TransactionLine,
            backref='transaction',
            cascade='all, delete-orphan',
            lazy='joined',
        ),
        'splits': db.relationship(
            TransactionSplit,
            backref='transaction',
            cascade='all, delete-orphan',
            lazy='joined',
        )
    })

    # TransactionLine
    db.mapper(TransactionLine, transaction_lines, properties={
        'entries': db.relationship(
            TransactionEntry,
            backref='line',
        ),
    })

    # TransactionSplit
    db.mapper(TransactionSplit, transaction_splits, properties={
        'entries': db.relationship(
            TransactionEntry,
            backref='split',
            cascade='all, delete-orphan',
            lazy='joined',
        ),
        'category': db.relationship(Category),
        'left_line': db.relationship(
            TransactionLine,
            foreign_keys=[transaction_splits.c.left_line_id],
        ),
        'right_line': db.relationship(
            TransactionLine,
            foreign_keys=[transaction_splits.c.right_line_id],
        ),
    })

    # TransactionEntry
    db.mapper(TransactionEntry, transaction_entries)

    # Payee
    db.mapper(Payee, payees, properties={
        'category': db.relationship(Category),
        'transactions': db.relationship(
            Transaction,
            backref='payee',
        )
    })
