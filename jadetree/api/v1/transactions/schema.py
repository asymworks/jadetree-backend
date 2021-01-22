# =============================================================================
#
# Jade Tree Personal Budgeting Application | jadetree.io
# Copyright (c) 2020 Asymworks, LLC.  All Rights Reserved.
#
# =============================================================================

from marshmallow import (
    Schema,
    ValidationError,
    fields,
    pre_dump,
    validates,
    validates_schema,
)
from marshmallow_enum import EnumField

from jadetree.domain.types import AccountRole, AccountType, TransactionType


class TransactionClearanceSchema(Schema):
    '''Schema for a Transaction Line Clearance Status'''
    line_id = fields.Int()
    account_id = fields.Int()

    cleared = fields.Bool()
    cleared_at = fields.Date(dump_only=True)

    @validates_schema
    def validate_schema(self, data, **kwargs):
        if 'line_id' not in data and 'account_id' not in data:
            raise ValidationError({
                'line_id': 'One of "line_id" and "account_id" is required',
            })
        if 'cleared' not in data and 'reconciled' not in data:
            raise ValidationError({
                'cleared': 'One of "cleared" and "reconciled" is required',
            })

    @pre_dump
    def pre_dump(self, data, **kwargs):
        data.line_id = data.id
        return data


class TransactionLineSchema(Schema):
    '''Schema for a Transaction Line'''
    id = fields.Int()
    account_id = fields.Int()
    account_type = EnumField(AccountType, by_value=True)

    role = EnumField(AccountRole, by_value=True)

    amount = fields.Decimal(places=4, as_string=True)
    currency = fields.Str()

    cleared = fields.Bool()
    cleared_at = fields.Date(dump_only=True)
    reconciled = fields.Bool()
    reconciled_at = fields.Date(dump_only=True)


class TransactionSplitSchema(Schema):
    '''Schema for a Transaction Split'''
    id = fields.Int(dump_only=True)
    category_id = fields.Int(allow_none=True)
    transfer_id = fields.Int(allow_none=True)
    left_line_id = fields.Int(dump_only=True)
    right_line_id = fields.Int(dump_only=True)

    amount = fields.Decimal(places=4, as_string=True)
    currency = fields.Str()

    type = EnumField(TransactionType, by_value=True)
    memo = fields.Str()


class TransactionSummarySchema(Schema):
    '''Summary Schema for a Transaction

    Contains the `Transaction` fields for the transaction metadata (account,
    date, payee, amount, etc). This is used for the transaction list query so
    that the database does not have to also load and join the `TransactionLine`
    and `TransactionSplit` objects for each transaction.
    '''
    id = fields.Int(dump_only=True)

    account_id = fields.Int()
    payee_id = fields.Int()

    date = fields.Date()
    check = fields.Str()
    memo = fields.Str()

    amount = fields.Decimal(places=4, as_string=True)
    currency = fields.Str()

    foreign_currency = fields.Str()
    foreign_exchrate = fields.Decimal(places=6, as_string=True)

    @validates('account_id')
    def validate_account_id(self, value):
        if self.context.get('account_id', value) != value:
            raise ValidationError('account_id must match with URI')


class TransactionSchema(TransactionSummarySchema):
    '''Full Schema for a Transaction

    Contains the full `Transaction` information including `TransactionLine` and
    `TransactionSplit` information.
    '''
    splits = fields.List(fields.Nested(TransactionSplitSchema))
    lines = fields.List(fields.Nested(TransactionLineSchema), dump_only=True)


class LedgerEntrySchema(Schema):
    '''Schema for a single Ledger Entry for an Account'''
    transaction_id = fields.Int(dump_only=True)
    account_id = fields.Int()
    line_id = fields.Int(dump_only=True)
    line_account_id = fields.Int(dump_only=True)

    date = fields.Date()
    payee_id = fields.Int()
    check = fields.Str()
    memo = fields.Str()

    amount = fields.Decimal(places=4, as_string=True)
    balance = fields.Decimal(places=4, as_string=True, dump_only=True)
    currency = fields.Str()

    transaction_currency = fields.Str()
    foreign_currency = fields.Str()
    foreign_exchrate = fields.Decimal(places=6, as_string=True)

    splits = fields.List(fields.Nested(TransactionSplitSchema))

    cleared = fields.Bool(dump_only=True)
    cleared_at = fields.Date(dump_only=True)
    reconciled = fields.Bool(dump_only=True)
    reconciled_at = fields.Date(dump_only=True)


class LedgerQuerySchema(Schema):
    '''Schema for querying Ledger Entries'''
    after_id = fields.Int()
    after_date = fields.Date()
    category_id = fields.Int()


class ReconcileSchema(Schema):
    '''Account Statement Reconciliation Information'''
    statement_date = fields.Date()
    statement_balance = fields.Decimal(places=4, as_string=True)
