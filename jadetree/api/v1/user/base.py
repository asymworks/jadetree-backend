# =============================================================================
#
# Jade Tree Personal Budgeting Application | jadetree.io
# Copyright (c) 2020 Asymworks, LLC.  All Rights Reserved.
#
# =============================================================================

from flask.views import MethodView

from jadetree.api.common import JTApiBlueprint, auth
from jadetree.database import db
from jadetree.service import user as user_service

from .schema import UserSchema

#: Authentication Service Blueprint
blp = JTApiBlueprint('user', __name__, description='User Profile Service')


@blp.route('/user')
class UserView(MethodView):
    '''API Endpoint for `User` Model'''
    @auth.login_required
    @blp.response(UserSchema)
    def get(self):
        '''Return Current User Information'''
        return auth.current_user()

    @auth.login_required
    @blp.arguments(UserSchema)
    @blp.response(UserSchema)
    def put(self, json_data):
        '''Update User Information'''
        u = auth.current_user()
        if not u.profile_setup:
            return user_service.setup_user(db.session, u, **json_data)

        return user_service.update_user(db.session, u, **json_data)
