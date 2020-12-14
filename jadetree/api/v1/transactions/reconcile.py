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
from .schema import ReconcileSchema, TransactionSchema


@blp.route('/reconcile/<int:account_id>')
class ReconcileView(MethodView):
    '''API Endpoint for All User Transactions'''
    @auth.login_required
    @blp.response(TransactionSchema(many=True))
    def get(self, account_id):
        '''Return list of cleared and unreconciled Transactions'''
        return ledger_service.load_reconcilable_lines(
            db.session,
            auth.current_user(),
            account_id,
            reverse=True,
        )

    @auth.login_required
    @blp.arguments(ReconcileSchema)
    @blp.response(TransactionSchema(many=True))
    def post(self, json_data, account_id):
        '''Reconcile the Account with a Statement'''
        txns = ledger_service.reconcile_account(
            db.session,
            auth.current_user(),
            account_id,
            **json_data,
        )

        emit(
            'create',
            {
                'class': 'Transaction',
                'items': [TransactionSchema(many=True).dump(txns)],
            },
            namespace='/',
            room=auth.current_user().uid_hash
        )

        return txns
