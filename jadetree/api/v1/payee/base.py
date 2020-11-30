# =============================================================================
#
# Jade Tree Personal Budgeting Application | jadetree.io
# Copyright (c) 2020 Asymworks, LLC.  All Rights Reserved.
#
# =============================================================================

from flask.views import MethodView

from jadetree.api.common import JTApiBlueprint, auth
from jadetree.database import db
from jadetree.domain.types import TransactionType
from jadetree.service import payee as payee_service

from .schema import PayeeSchema, PayeeDetailSchema

#: Authentication Service Blueprint
blp = JTApiBlueprint('payee', __name__, description='Payee Service')


@blp.route('/payees')
class PayeeList(MethodView):
    '''API Endpoint for `Payee` Model'''
    @auth.login_required
    @blp.response(PayeeSchema(many=True))
    def get(self):
        '''Return list of Payees'''
        return auth.current_user().payees

    @auth.login_required
    @blp.arguments(PayeeSchema)
    @blp.response(PayeeSchema)
    def post(self, json_data):
        '''Create new Payee'''
        return payee_service.create_payee(
            db.session,
            auth.current_user(),
            **json_data,
        )


@blp.route('/payees/<int:payee_id>')
class PayeeItem(MethodView):
    '''API Endpoint for `Payee` Model'''
    @auth.login_required
    @blp.response(PayeeDetailSchema)
    def get(self, payee_id):
        '''Return list of Payees'''
        p = payee_service._load_payee(
            db.session,
            auth.current_user(),
            payee_id
        )

        # Get the most recent transaction line for the Payee
        p.last_category_id = None
        p.last_account_id = None
        p.last_amount = None
        p.last_memo = None
        p.last_type = None

        tl = payee_service.get_payee_last_txn(db.session, p.id)
        if tl is not None:
            if tl.type != TransactionType.Transfer:
                p.last_category_id = tl.category_id
                p.last_account_id = None
            else:
                p.last_category_id = None
                p.last_account_id = tl.opposing_id

            p.last_amount = tl.amount
            p.last_memo = tl.memo
            p.last_type = tl.type

        return p
