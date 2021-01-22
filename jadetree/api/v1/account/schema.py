# =============================================================================
#
# Jade Tree Personal Budgeting Application | jadetree.io
# Copyright (c) 2020 Asymworks, LLC.  All Rights Reserved.
#
# =============================================================================

from marshmallow import Schema, fields
from marshmallow_enum import EnumField

from jadetree.domain.types import AccountSubtype, AccountType


class AccountCreateSchema(Schema):
    '''Schema for Account Creation'''
    name = fields.Str()
    type = EnumField(AccountType, by_value=True)
    subtype = EnumField(AccountSubtype, by_value=True)
    budget_id = fields.Int(allow_none=True)
    balance = fields.Decimal(places=4, as_string=True)
    balance_date = fields.Date()
    currency = fields.Str()


class AccountSchema(Schema):
    '''
    '''
    id = fields.Int()
    name = fields.Str()
    type = EnumField(AccountType, by_value=True)
    subtype = EnumField(AccountSubtype, by_value=True)
    budget_id = fields.Int(allow_none=True)
    balance = fields.Decimal(places=4, as_string=True)
    currency = fields.Str()
    display_order = fields.Int()
