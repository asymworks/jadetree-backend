"""Authorization API Schema Definitions.

Jade Tree Personal Budgeting Application | jadetree.io
Copyright (c) 2020 Asymworks, LLC.  All Rights Reserved.
"""

from marshmallow import Schema, fields

from jadetree.api.common import JTPasswordValidator
from jadetree.api.v1.user.schema import UserSchema


class LoginSchema(Schema):
    """Schema to Log In to Jade Tree API."""
    email = fields.Email(required=True)
    password = fields.Str()


class AuthTokenSchema(Schema):
    """Schema to return a new Authentication Token."""
    token = fields.Str()
    user = fields.Nested(UserSchema)


class AuthUserSchema(Schema):
    """Schema for the list of Authorized Users."""
    email = fields.Email()
    name = fields.Str()


class RegisterUserSchema(Schema):
    """Schema to register a new User."""
    email = fields.Email(required=True)
    password = fields.Str(required=True, validate=JTPasswordValidator())
    name = fields.Str(require=True)


class RegistrationEmailSchema(Schema):
    """Schema holding an Email Address."""
    email = fields.Email(required=True)


class RegistrationTokenSchema(Schema):
    """Schema holding a JSON Web Token."""
    token = fields.Str()


class ChangePasswordSchema(Schema):
    """Schema to change a User Password.

    The user's previous password must be provided to change the password via
    the `changePassword` endpoint. If the previous password was forgotten, the
    `resetPassword` endpoint must be used instead.

    If the `logout_sessions` flag is set to true (the default), the user's hash
    will be changed, invalidating currently issued login tokens and causing any
    any other sessions to have to log in again. Set this to `False` to disable
    this behavior.
    """
    old_password = fields.Str(required=True)
    new_password = fields.Str(required=True, validate=JTPasswordValidator())
    logout_sessions = fields.Bool(missing=True)
