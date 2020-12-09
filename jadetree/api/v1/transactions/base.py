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
from jadetree.domain.types import AccountRole
from jadetree.service import ledger as ledger_service

from .schema import TransactionSummarySchema, TransactionSchema, \
    TransactionClearanceSchema

#: Authentication Service Blueprint
blp = JTApiBlueprint('transactions', __name__, description='Transaction Service')


@blp.route('/transactions')
class TransactionList(MethodView):
    '''API Endpoint for All User Transactions'''
    @auth.login_required
    @blp.response(TransactionSummarySchema(many=True))
    def get(self):
        '''Return list of all Transactions'''
        return auth.current_user().transactions

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
            namespace='/api/v1',
            room=auth.current_user().uid_hash
        )

        return txn


@blp.route('/transactions/<int:transaction_id>')
class TransactionDetail(MethodView):
    '''API Endpoint for Individual Transactions'''
    @auth.login_required
    @blp.response(TransactionSchema)
    def get(self, transaction_id):
        return ledger_service._load_transaction(
            db.session,
            auth.current_user(),
            transaction_id
        )

    @auth.login_required
    @blp.arguments(TransactionSchema, inject_context=True)
    @blp.response(TransactionSchema)
    def put(self, json_data, transaction_id):
        '''Update a Transaction'''
        txn = ledger_service.update_transaction(
            db.session,
            auth.current_user(),
            transaction_id,
            **json_data,
        )

        emit(
            'update',
            {
                'class': 'Transaction',
                'items': [TransactionSchema().dump(txn)],
            },
            namespace='/api/v1',
            room=auth.current_user().uid_hash
        )

        return txn

    @auth.login_required
    @blp.response(code=204)
    def delete(self, transaction_id):
        txn = ledger_service._load_transaction(
            db.session,
            auth.current_user(),
            transaction_id
        )

        emit(
            'delete',
            {
                'class': 'Transaction',
                'items': [TransactionSchema().dump(txn)],
            },
            namespace='/api/v1',
            room=auth.current_user().uid_hash
        )

        db.session.delete(txn)
        db.session.commit()


@blp.route('/transactions/<int:transaction_id>/clear')
class TransactionClearing(MethodView):
    '''API Endpoint for Clearing Transactions'''
    @auth.login_required
    @blp.response(TransactionClearanceSchema(many=True))
    def get(self, transaction_id):
        txn = ledger_service._load_transaction(
            db.session,
            auth.current_user(),
            transaction_id
        )

        return [ln for ln in txn.lines if ln.account.role == AccountRole.Personal]

    @auth.login_required
    @blp.arguments(TransactionClearanceSchema)
    @blp.response(TransactionClearanceSchema(many=True))
    def put(self, json_data, transaction_id):
        '''Clear or Un-Clear a Transaction Line'''
        txn = ledger_service.clear_transaction(
            db.session,
            auth.current_user(),
            transaction_id,
            **json_data
        )

        emit(
            'clear',
            {
                'class': 'Transaction',
                'items': [TransactionSchema().dump(txn)],
            },
            namespace='/api/v1',
            room=auth.current_user().uid_hash
        )

        return [ln for ln in txn.lines if ln.account.role == AccountRole.Personal]
