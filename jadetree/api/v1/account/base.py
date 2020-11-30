# =============================================================================
#
# Jade Tree Personal Budgeting Application | jadetree.io
# Copyright (c) 2020 Asymworks, LLC.  All Rights Reserved.
#
# =============================================================================

from flask.views import MethodView

from jadetree.api.common import JTApiBlueprint, auth
from jadetree.database import db
from jadetree.service import account as account_service

from .schema import AccountCreateSchema, AccountSchema

#: Authentication Service Blueprint
blp = JTApiBlueprint('account', __name__, description='Account Service')


@blp.route('/accounts')
class AccountsList(MethodView):
    '''API Endpoint for `Account` Model'''
    @auth.login_required
    @blp.response(AccountSchema(many=True))
    def get(self):
        '''Return list of User Accounts'''
        return account_service.get_user_account_list(
            db.session,
            auth.current_user(),
        )

    @auth.login_required
    @blp.arguments(AccountCreateSchema)
    @blp.response(AccountSchema)
    def post(self, json_data):
        '''Create a new User Account'''
        return account_service.create_user_account(
            db.session,
            auth.current_user(),
            **json_data,
        )


@blp.route('/accounts/<int:account_id>')
class AccountItem(MethodView):
    '''API Endpoint for `Account` Model'''
    @auth.login_required
    @blp.response(AccountSchema)
    def get(self, account_id):
        '''Return User Account'''
        return account_service._load_account(
            db.session,
            auth.current_user(),
            account_id,
        )
