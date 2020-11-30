# =============================================================================
#
# Jade Tree Personal Budgeting Application | jadetree.io
# Copyright (c) 2020 Asymworks, LLC.  All Rights Reserved.
#
# =============================================================================

from marshmallow import Schema, fields
from marshmallow_enum import EnumField

from jadetree.domain.types import PayeeRole, TransactionType


class PayeeSchema(Schema):
    '''
    Schema for a `Payee` object
    '''
    id = fields.Int()
    name = fields.Str(required=True)
    role = EnumField(PayeeRole, by_value=True)
    system = fields.Bool()
    hidden = fields.Bool()

    category_id = fields.Int()
    account_id = fields.Int()
    amount = fields.Decimal(places=4, as_string=True)
    memo = fields.Str()


class PayeeDetailSchema(PayeeSchema):
    '''
    Extended Schema for a `Payee` object including last transaction information
    '''
    last_category_id = fields.Int()
    last_account_id = fields.Int()
    last_amount = fields.Decimal(places=4, as_string=True)
    last_memo = fields.Str()
    last_type = EnumField(TransactionType, by_value=True)
