"""Jade Tree JSON Data Import/Export Service.

Jade Tree Personal Budgeting Application | jadetree.io
Copyright (c) 2020 Asymworks, LLC.  All Rights Reserved.
"""

from marshmallow import Schema, fields, pre_dump
from marshmallow_enum import EnumField

from jadetree.domain.types import (
    AccountRole,
    AccountSubtype,
    AccountType,
    PayeeRole,
    TransactionType,
)


class AccountSchema(Schema):
    """Export Schema for an `Account`."""
    id = fields.Int()
    name = fields.Str()
    type = EnumField(AccountType, by_value=True)
    subtype = EnumField(AccountSubtype, by_value=True)
    budget_id = fields.Int(allow_none=True)
    active = fields.Bool()
    iban = fields.Str(allow_none=True)
    opened = fields.DateTime()
    closed = fields.DateTime(allow_none=True)
    currency = fields.Str()
    display_order = fields.Int()
    notes = fields.Str(allow_none=True)


class BudgetCategoryBaseSchema(Schema):
    """Base Schema for Categories and Category Groups."""
    id = fields.Int()
    name = fields.Str()
    system = fields.Bool()
    hidden = fields.Bool()
    currency = fields.Str()
    notes = fields.Str(allow_none=True)
    display_order = fields.Int()
    parent_id = fields.Int()


class BudgetCategorySchema(BudgetCategoryBaseSchema):
    """Schema for Budget Category."""
    default_budget = fields.Decimal(places=4, as_string=True)


class BudgetCategoryGroupSchema(BudgetCategoryBaseSchema):
    """Schema for Budget Category Group."""
    children = fields.List(fields.Nested(BudgetCategorySchema))


class BudgetEntrySchema(Schema):
    """Export Schema for a `BudgetEntry`."""
    id = fields.Int()
    month = fields.Date(required=True)
    category_id = fields.Int(required=True)

    amount = fields.Decimal(required=True, places=4, as_string=True)
    rollover = fields.Bool()
    notes = fields.Str()


class BudgetSchema(Schema):
    """Export Schema for a `Budget`."""
    id = fields.Int()
    name = fields.Str(required=True)
    currency = fields.Str(required=True)
    categories = fields.List(fields.Nested(BudgetCategoryGroupSchema))
    entries = fields.List(fields.Nested(BudgetEntrySchema))
    notes = fields.Str()

    @pre_dump
    def pre_dump(self, obj, **kwargs):
        """Filter category list to only top-level."""
        return dict(
            id=obj.id,
            name=obj.name,
            currency=obj.currency,
            categories=[c for c in obj.categories if not c.parent],
            entries=obj.entries,
            notes=obj.notes,
        )


class PayeeSchema(Schema):
    """Export Schema for a `Payee`."""
    id = fields.Int()
    name = fields.Str(required=True)
    role = EnumField(PayeeRole, by_value=True)
    system = fields.Bool()
    hidden = fields.Bool()

    memo = fields.Str()
    amount = fields.Decimal(places=4, as_string=True)

    account_id = fields.Int(allow_none=True)


class TransactionLineSchema(Schema):
    """Export Schema for a `TransactionLine`."""
    id = fields.Int()
    account_id = fields.Int()
    account_type = EnumField(AccountType, by_value=True)

    role = EnumField(AccountRole, by_value=True)
    amount = fields.Decimal(places=4, as_string=True)
    currency = fields.Str()

    cleared = fields.Bool()
    cleared_at = fields.Date()
    reconciled = fields.Bool()
    reconciled_at = fields.Date()


class TransactionSplitSchema(Schema):
    """Export Schema for a `TransactionSplit`."""
    id = fields.Int()
    category_id = fields.Int()
    transfer_id = fields.Int(allow_none=True)
    left_line_id = fields.Int()
    right_line_id = fields.Int()

    amount = fields.Decimal(places=4, as_string=True)
    currency = fields.Str()

    type = EnumField(TransactionType, by_value=True)
    memo = fields.Str()


class TransactionSchema(Schema):
    """Export Schema for a `Transaction`."""
    id = fields.Int()
    account_id = fields.Int()
    payee_id = fields.Int()
    date = fields.Date()
    check = fields.Str()
    memo = fields.Str()
    currency = fields.Str()
    foreign_currency = fields.Str()
    foreign_exchrate = fields.Decimal(places=6, as_string=True)

    splits = fields.List(fields.Nested(TransactionSplitSchema))
    lines = fields.List(fields.Nested(TransactionLineSchema))


class UserDataSchema(Schema):
    """Export Schema for Jade Tree User Data."""
    accounts = fields.List(fields.Nested(AccountSchema))
    budgets = fields.List(fields.Nested(BudgetSchema))
    payees = fields.List(fields.Nested(PayeeSchema))
    transactions = fields.List(fields.Nested(TransactionSchema))
    version = fields.Int()


def export_data_json(user):
    """Export User Data into a JSON-serializable dictionary."""
    return UserDataSchema().dump(dict(
        accounts=user.accounts,
        budgets=user.budgets,
        payees=user.payees,
        transactions=user.transactions,
        version=1,
    ))
