# =============================================================================
#
# Jade Tree Personal Budgeting Application | jadetree.io
# Copyright (c) 2020 Asymworks, LLC.  All Rights Reserved.
#
# =============================================================================

from flask import current_app
from flask.views import MethodView

from jadetree.api.common import JTApiBlueprint, auth
from jadetree.database import db
from jadetree.service import auth as auth_service

from .schema import LoginSchema, AuthTokenSchema, AuthUserSchema

#: Authentication Service Blueprint
blp = JTApiBlueprint('auth', __name__, description='Authentication Service')


@blp.route('/auth/login')
class LoginView(MethodView):
    '''Log a user in to the Jade Tree API and return a bearer token'''
    @blp.response(AuthUserSchema(many=True))
    def get(self):
        '''
        For Personal and Family server modes, return a list of user emails and
        names which will be accepted by the authorization endpoint withoug a
        password.
        '''
        if current_app.config['_JT_SERVER_MODE'] not in ('family', 'personal'):
            return []

        return auth_service.auth_user_list(db.session)

    @blp.arguments(LoginSchema)
    @blp.response(AuthTokenSchema)
    def post(self, args):
        return auth_service.login_user(
            db.session,
            args['email'],
            args['password'],
        )


@blp.route('/auth/logout')
class LogoutView(MethodView):
    '''Log a user out of all login sessions'''
    @auth.login_required
    @blp.response(code=204)
    def get(self):
        auth_service.invalidate_uid_hash(
            db.session,
            auth.current_user().uid_hash
        )
