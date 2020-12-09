# =============================================================================
#
# Jade Tree Personal Budgeting Application | jadetree.io
# Copyright (c) 2020 Asymworks, LLC.  All Rights Reserved.
#
# =============================================================================

from flask.views import MethodView
from flask_socketio import emit

from jadetree.api.common import JTApiBlueprint, auth
from jadetree.database import db
from jadetree.service import account as account_service

from .schema import AccountCreateSchema, AccountSchema
from ..payee.schema import PayeeSchema
from ..transactions.schema import TransactionSchema

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
        acct, payee, init_txn = account_service.create_user_account(
            db.session,
            auth.current_user(),
            **json_data,
        )

        emit(
            'create',
            {
                'class': 'Account',
                'items': [AccountSchema().dump(acct)],
            },
            namespace='/api/v1',
            room=auth.current_user().uid_hash
        )

        emit(
            'create',
            {
                'class': 'Payee',
                'items': [PayeeSchema().dump(payee)],
            },
            namespace='/api/v1',
            room=auth.current_user().uid_hash
        )

        emit(
            'create',
            {
                'class': 'Transaction',
                'items': [TransactionSchema().dump(init_txn)],
            },
            namespace='/api/v1',
            room=auth.current_user().uid_hash
        )

        return acct


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
