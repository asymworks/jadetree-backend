# =============================================================================
#
# Jade Tree Personal Budgeting Application | jadetree.io
# Copyright (c) 2020 Asymworks, LLC.  All Rights Reserved.
#
# =============================================================================

from flask.views import MethodView
from flask_socketio import emit

from jadetree.api.common import auth
from jadetree.database import db
from jadetree.service import ledger as ledger_service

from .base import blp
from .schema import LedgerEntrySchema, TransactionSchema


@blp.route('/ledger')
class LedgerList(MethodView):
    '''API Endpoint for All User Transactions'''
    @auth.login_required
    @blp.response(LedgerEntrySchema(many=True))
    def get(self):
        '''Return list of all Transactions'''
        return ledger_service.load_all_lines(
            db.session,
            auth.current_user(),
            reverse=True,
        )

    @auth.login_required
    @blp.arguments(TransactionSchema, inject_context=True)
    @blp.response(TransactionSchema)
    def post(self, json_data):
        '''Create a new Transaction'''
        txn = ledger_service.create_transaction(
            db.session,
            auth.current_user(),
            **json_data,
        )

        emit(
            'create',
            {
                'class': 'Transaction',
                'items': [TransactionSchema().dump(txn)],
            },
            room=auth.current_user().uid_hash
        )

        return txn


@blp.route('/ledger/<int:account_id>')
class AccountLedgerList(MethodView):
    '''API Endpoint for Account Transactions'''
    @auth.login_required
    @blp.response(LedgerEntrySchema(many=True))
    def get(self, account_id):
        '''Return list of all Transactions'''
        return ledger_service.load_account_lines(
            db.session,
            auth.current_user(),
            account_id,
            reverse=True,
        )

    @auth.login_required
    @blp.arguments(TransactionSchema, inject_context=True)
    @blp.response(TransactionSchema)
    def post(self, json_data, account_id):
        '''Create a new Transaction within an account'''
        json_data['account_id'] = account_id
        txn = ledger_service.create_transaction(
            db.session,
            auth.current_user(),
            **json_data,
        )

        emit(
            'create',
            {
                'class': 'Transaction',
                'items': [TransactionSchema().dump(txn)],
            },
            room=auth.current_user().uid_hash
        )

        return txn
