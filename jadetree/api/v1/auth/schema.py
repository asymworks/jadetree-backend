# =============================================================================
#
# Jade Tree Personal Budgeting Application | jadetree.io
# Copyright (c) 2020 Asymworks, LLC.  All Rights Reserved.
#
# =============================================================================

from marshmallow import Schema, fields

from ..user.schema import UserSchema


class LoginSchema(Schema):
    '''Schema to Log In to Jade Tree API'''
    email = fields.Email(required=True)
    password = fields.Str()


class AuthTokenSchema(Schema):
    '''Schema for Authentication Token'''
    token = fields.Str()
    user = fields.Nested(UserSchema)


class AuthUserSchema(Schema):
    '''Schema for Authorized User List'''
    email = fields.Email()
    name = fields.Str()
