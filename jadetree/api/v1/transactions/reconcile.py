# =============================================================================
#
# Jade Tree Personal Budgeting Application | jadetree.io
# Copyright (c) 2020 Asymworks, LLC.  All Rights Reserved.
#
# =============================================================================

from flask.views import MethodView

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
        return ledger_service.reconcile_account(
            db.session,
            auth.current_user(),
            account_id,
            **json_data,
        )
