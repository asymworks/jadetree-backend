"""Authorization API Base Methods.

Jade Tree Personal Budgeting Application | jadetree.io
Copyright (c) 2020 Asymworks, LLC.  All Rights Reserved.
"""

from flask import current_app
from flask.views import MethodView

from jadetree.api.common import JTApiBlueprint, auth
from jadetree.api.v1.user.schema import UserSchema
from jadetree.database import db
from jadetree.exc import Error
from jadetree.service import auth as auth_service

from .schema import (
    AuthTokenSchema,
    AuthUserSchema,
    ChangePasswordSchema,
    LoginSchema,
    RegisterUserSchema,
)

#: Authentication Service Blueprint
blp = JTApiBlueprint('auth', __name__, description='Authentication Service')


@blp.route('/auth/login')
class LoginView(MethodView):
    """User Login Endpoint."""
    @blp.response(AuthUserSchema(many=True))
    def get(self):
        """Return list of Registered Users.

        For Personal and Family server modes, return a list of user emails and
        names which will be accepted by the authorization endpoint without a
        password. if the server mode is Public, an empty list is returned.
        """
        if current_app.config['_JT_SERVER_MODE'] not in ('family', 'personal'):
            return []

        return auth_service.auth_user_list(db.session)

    @blp.arguments(LoginSchema)
    @blp.response(AuthTokenSchema)
    def post(self, args):
        """Log a user in to Jade Tree and return a Bearer Token."""
        return auth_service.login_user(
            db.session,
            args['email'],
            args['password'],
        )


@blp.route('/auth/logout')
class LogoutView(MethodView):
    """User Log Out Endpoint."""
    @auth.login_required
    @blp.response(code=204)
    def get(self):
        """Log a user out of all Login Sessions.

        This endpoint changes the User ID hash, which invalidates all
        previously-issued bearer tokens. All sessions must log in again with
        the user password to obtain new tokens.
        """
        auth_service.invalidate_uid_hash(
            db.session,
            auth.current_user().uid_hash
        )


@blp.route('/auth/register')
class RegisterView(MethodView):
    """Register a new User."""
    @blp.arguments(RegisterUserSchema)
    @blp.response(UserSchema)
    def post(self, args):
        """Register a new Jade Tree user.

        Registers a new user with the Jade Tree server. If the server mode is
        Public, the user will be created in an inactive state and the user must
        use a confirmation token and the `/auth/confirm` endpoint to complete
        their registration and validate their email address.

        If the server was set up in Personal mode, this endpoint is not
        available and an error is returned with code 410 (Gone).
        """
        if current_app.config.get('_JT_SERVER_MODE', None) == 'personal':
            message = "The '/setup' endpoint is not available after the " \
                'server has been set up'
            raise Error(message, status_code=410)

        return auth_service.register_user(
            db.session,
            args['email'],
            args['password'],
            args['name'],
        )


@blp.route('/auth/changePassword')
class ChangePasswordView(MethodView):
    """Change the User's Password."""
    @auth.login_required
    @blp.arguments(ChangePasswordSchema)
    @blp.response(AuthTokenSchema)
    def post(self, args):
        """Change the user's password and return a new bearer token."""
        return auth_service.change_password(
            db.session,
            auth.current_user().uid_hash,
            args['old_password'],
            args['new_password'],
            args['logout_sessions'],
        )
