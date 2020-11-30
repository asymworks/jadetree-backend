# =============================================================================
#
# Jade Tree Personal Budgeting Application | jadetree.io
# Copyright (c) 2020 Asymworks, LLC.  All Rights Reserved.
#
# =============================================================================

from jadetree.domain.types import AccountRole, AccountType, AccountSubtype, \
    PayeeRole, TransactionType

from .globals import db
from .types import AmountType, ArrowType


def _enum_values(x):
    return [e.value for e in x]


#: `jadetree_config` table
jadetree_config = db.Table(
    'jadetree_config',

    # Key / Value Store
    db.Column('key', db.String, primary_key=True),
    db.Column('value', db.String(128)),
)

#: `User` table
users = db.Table(
    'users',

    # Primary Key
    db.Column('id', db.Integer, primary_key=True),

    # User Attributes
    db.Column('email', db.String(128), nullable=False, unique=True, index=True),
    db.Column('pw_hash', db.String(128)),
    db.Column('uid_hash', db.String(32), nullable=False, unique=True, index=True),

    db.Column('admin', db.Boolean, nullable=False, default=False),

    db.Column('active', db.Boolean, nullable=False, default=False),
    db.Column('confirmed', db.Boolean, nullable=False, default=False),
    db.Column('confirmed_at', ArrowType),
    db.Column('profile_setup', db.Boolean, nullable=False, default=False),
    db.Column('profile_setup_at', ArrowType),

    # Profile Settings
    db.Column('name', db.String(128)),
    db.Column('language', db.String(2), nullable=False, default='en'),
    db.Column('locale', db.String(20), default=None),
    db.Column('currency', db.String(8)),

    # Formatting Overrides (Dates)
    db.Column('fmt_date_short', db.String(32), default=None),
    db.Column('fmt_date_long', db.String(32), default=None),

    # Formatting Overrides (Numbers)
    db.Column('fmt_decimal', db.String(64), default=None),
    db.Column('fmt_currency', db.String(64), default=None),
    db.Column('fmt_accounting', db.String(64), default=None),

    # Mixin Columns
    db.Column('created_at', ArrowType),
    db.Column('modified_at', ArrowType),
)


#: `Account` table
accounts = db.Table(
    'accounts',

    # Primary Key
    db.Column('id', db.Integer, primary_key=True),

    # Foreign Keys
    db.Column('user_id', db.Integer, db.ForeignKey('users.id'), nullable=False),
    db.Column('budget_id', db.Integer, db.ForeignKey('budgets.id'), nullable=True),

    # Account Attributes
    db.Column('name', db.String(128), nullable=False),
    db.Column('role', db.Enum(AccountRole, values_callable=_enum_values), nullable=False),
    db.Column('type', db.Enum(AccountType, values_callable=_enum_values), nullable=False),
    db.Column('subtype', db.Enum(AccountSubtype, values_callable=_enum_values)),

    db.Column('currency', db.String(8), nullable=False),
    db.Column('active', db.Boolean, default=True),
    db.Column('iban', db.String(34)),

    db.Column('opened', db.Date),
    db.Column('closed', db.Date),

    db.Column('display_order', db.Integer),

    # Mixin Columns
    db.Column('notes', db.Text),
    db.Column('created_at', ArrowType),
    db.Column('modified_at', ArrowType),
)


#: `Budget` table
budgets = db.Table(
    'budgets',

    # Primary Key
    db.Column('id', db.Integer, primary_key=True),

    # Foreign Keys
    db.Column('user_id', db.Integer, db.ForeignKey('users.id'), nullable=False),

    # Budget Attributes
    db.Column('name', db.String(128), nullable=False),
    db.Column('currency', db.String(8), nullable=False),

    # Mixin Columns
    db.Column('notes', db.Text),
    db.Column('created_at', ArrowType),
    db.Column('modified_at', ArrowType),
)


#: `Category` table
categories = db.Table(
    'categories',

    # Primary Key
    db.Column('id', db.Integer, primary_key=True),

    # Foreign Keys
    db.Column('budget_id', db.Integer, db.ForeignKey('budgets.id'), nullable=False),
    db.Column('parent_id', db.Integer, db.ForeignKey('categories.id'), nullable=True),

    # Category Attributes
    db.Column('name', db.String(128), nullable=False),
    db.Column('system', db.Boolean, default=False),
    db.Column('hidden', db.Boolean, default=False),
    db.Column('display_order', db.Integer),
    db.Column('default_budget', AmountType),

    # Mixin Columns
    db.Column('notes', db.Text),
)


#: `BudgetEntry` table
budget_entries = db.Table(
    'budget_entries',

    # Primary Key
    db.Column('id', db.Integer, primary_key=True),

    # Foreign Keys
    db.Column('budget_id', db.Integer, db.ForeignKey('budgets.id'), nullable=False),
    db.Column('category_id', db.Integer, db.ForeignKey('categories.id'), nullable=True),

    # Budget Entry Attributes
    db.Column('month', db.Date),
    db.Column('amount', AmountType),
    db.Column('rollover', db.Boolean, default=False),

    # Mixin Columns
    db.Column('notes', db.Text),
)


#: `Transaction` table
transactions = db.Table(
    'transactions',

    # Primary Key
    db.Column('id', db.Integer, primary_key=True),

    # Foreign Keys
    db.Column('user_id', db.Integer, db.ForeignKey('users.id'), nullable=False),
    db.Column('account_id', db.Integer, db.ForeignKey('accounts.id'), nullable=False),
    db.Column('payee_id', db.Integer, db.ForeignKey('payees.id'), nullable=False),

    # Transaction Attributes
    db.Column('date', db.Date, nullable=False),
    db.Column('check', db.String(64)),
    db.Column('memo', db.String(255)),

    db.Column('currency', db.String(8), nullable=False),
    db.Column('foreign_currency', db.String(8)),
    db.Column('foreign_exchrate', AmountType(scale=6)),
)


#: `TransactionSplit` table
transaction_splits = db.Table(
    'transaction_splits',

    # Primary Key
    db.Column('id', db.Integer, primary_key=True),

    # Foreign Keys
    db.Column('transaction_id', db.Integer, db.ForeignKey('transactions.id'), nullable=False),
    db.Column('category_id', db.Integer, db.ForeignKey('categories.id'), nullable=True),
    db.Column('left_line_id', db.Integer, db.ForeignKey('transaction_lines.id'), nullable=False),
    db.Column('right_line_id', db.Integer, db.ForeignKey('transaction_lines.id'), nullable=False),

    # Transaction Split Attributes
    db.Column('type', db.Enum(TransactionType, values_callable=_enum_values), nullable=False),
    db.Column('memo', db.String(255)),
)


#: `TransactionLine` table
transaction_lines = db.Table(
    'transaction_lines',

    # Primary Key
    db.Column('id', db.Integer, primary_key=True),

    # Foreign Keys
    db.Column('transaction_id', db.Integer, db.ForeignKey('transactions.id'), nullable=False),
    db.Column('account_id', db.Integer, db.ForeignKey('accounts.id'), nullable=False),

    # Transaction Line Attributes
    db.Column('cleared', db.Boolean, default=False),
    db.Column('cleared_at', db.Date),
    db.Column('reconciled', db.Boolean, default=False),
    db.Column('reconciled_at', db.Date),
)


#: `TransactionEntry` table
transaction_entries = db.Table(
    'transaction_entries',

    # Primary Key
    db.Column('id', db.Integer, primary_key=True),

    # Foreign Keys
    db.Column('line_id', db.Integer, db.ForeignKey('transaction_lines.id'), nullable=False),
    db.Column('split_id', db.Integer, db.ForeignKey('transaction_splits.id'), nullable=False),

    # Ledger Entry Attributes
    db.Column('amount', AmountType, nullable=False),
    db.Column('currency', db.String(8), nullable=False),
)


#: `Payee` table
payees = db.Table(
    'payees',

    # Priamry Key
    db.Column('id', db.Integer, primary_key=True),

    # Foreign Keys
    db.Column('user_id', db.Integer, db.ForeignKey('users.id'), nullable=False),
    db.Column('category_id', db.Integer, db.ForeignKey('categories.id'), nullable=True),
    db.Column('account_id', db.Integer, db.ForeignKey('accounts.id'), nullable=True),

    # Payee Attributes
    db.Column('name', db.String(128), nullable=False, index=True),
    db.Column('role', db.Enum(PayeeRole, values_callable=_enum_values), nullable=False, default=PayeeRole.Expense),
    db.Column('system', db.Boolean, default=False),
    db.Column('hidden', db.Boolean, default=False),
    db.Column('memo', db.String(255)),
    db.Column('amount', AmountType),

    # Mixin Columns
    db.Column('created_at', ArrowType),
    db.Column('modified_at', ArrowType),
)
