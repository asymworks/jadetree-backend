# =============================================================================
#
# Jade Tree Personal Budgeting Application | jadetree.io
# Copyright (c) 2020 Asymworks, LLC.  All Rights Reserved.
#
# =============================================================================

from flask.views import MethodView

from jadetree.api.common import JTApiBlueprint, auth
from jadetree.database import db
from jadetree.domain.types import AccountRole
from jadetree.service import ledger as ledger_service

from .schema import TransactionSchema, TransactionLineSchema

#: Authentication Service Blueprint
blp = JTApiBlueprint('transactions', __name__, description='Transaction Service')


@blp.route('/transactions')
class AllTransactionList(MethodView):
    '''API Endpoint for All User Transactions'''
    @auth.login_required
    @blp.response(TransactionSchema(many=True))
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
        return ledger_service.create_transaction(
            db.session,
            auth.current_user(),
            **json_data,
        )


@blp.route('/transactions/account/<int:account_id>')
class AccountTransactionList(MethodView):
    '''API Endpoint for Account Transactions'''
    @auth.login_required
    @blp.response(TransactionSchema(many=True))
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
        print(json_data)
        return {}


@blp.route('/transactions/<int:transaction_id>')
class TransactionDetail(MethodView):
    '''API Endpoint for Individual Transactions'''
    @auth.login_required
    @blp.response(TransactionSchema)
    def get(self, transaction_id):
        txns = ledger_service.load_single_transaction(
            db.session,
            auth.current_user(),
            transaction_id
        )

        assert len(txns) == 1
        return txns[0]

    @auth.login_required
    @blp.arguments(TransactionSchema, inject_context=True)
    @blp.response(TransactionSchema)
    def put(self, json_data, transaction_id):
        '''Update a Transaction'''
        return ledger_service.update_transaction(
            db.session,
            auth.current_user(),
            transaction_id,
            **json_data,
        )

    @auth.login_required
    @blp.response(code=204)
    def delete(self, transaction_id):
        t = ledger_service._load_transaction(
            db.session,
            auth.current_user(),
            transaction_id
        )

        db.session.delete(t)
        db.session.commit()


@blp.route('/transactions/<int:transaction_id>/clear')
class TransactionClearing(MethodView):
    '''API Endpoint for Clearing Transactions'''
    @auth.login_required
    @blp.response(TransactionLineSchema(many=True))
    def get(self, transaction_id):
        txn = ledger_service._load_transaction(
            db.session,
            auth.current_user(),
            transaction_id
        )

        return [ln for ln in txn.lines if ln.account.role == AccountRole.Personal]

    @auth.login_required
    @blp.arguments(TransactionLineSchema)
    @blp.response(TransactionLineSchema(many=True))
    def put(self, json_data, transaction_id):
        '''Update a Transaction'''
        txn = ledger_service.clear_transaction(
            db.session,
            auth.current_user(),
            transaction_id,
            **json_data
        )

        return [ln for ln in txn.lines if ln.account.role == AccountRole.Personal]
