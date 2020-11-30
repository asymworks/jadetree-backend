# =============================================================================
#
# Jade Tree Personal Budgeting Application | jadetree.io
# Copyright (c) 2020 Asymworks, LLC.  All Rights Reserved.
#
# =============================================================================

from marshmallow import Schema, fields


class UserSchema(Schema):
    '''User Model Schema'''
    id = fields.Int(dump_only=True)

    email = fields.Email(dump_only=True)
    name = fields.Str(allow_none=True)

    # Profile Settings
    language = fields.Str(allow_none=True)
    locale = fields.Str(allow_none=True)
    currency = fields.Str(allow_none=True)

    # Formatting Overrides (Dates)
    fmt_date_short = fields.Str(allow_none=True)
    fmt_date_long = fields.Str(allow_none=True)

    # Formatting Overrides (Numbers)
    fmt_decimal = fields.Str(allow_none=True)
    fmt_currency = fields.Str(allow_none=True)
    fmt_accounting = fields.Str(allow_none=True)

    # Registration Status
    active = fields.Bool(dump_only=True)
    confirmed = fields.Bool(dump_only=True)
    confirmed_at = fields.DateTime(dump_only=True, allow_none=True)
    profile_setup = fields.Bool(dump_only=True)
    profile_setup_at = fields.DateTime(dump_only=True, allow_none=True)
