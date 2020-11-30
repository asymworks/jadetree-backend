# =============================================================================
#
# Jade Tree Personal Budgeting Application | jadetree.io
# Copyright (c) 2020 Asymworks, LLC.  All Rights Reserved.
#
# =============================================================================

from flask.views import MethodView

from jadetree.api.common import auth
from jadetree.database import db
from jadetree.exc import NoResults
from jadetree.service import budget as budget_service

from .base import blp
from .schema import BudgetEntrySchema, BudgetEntryUpdateSchema, \
    BudgetQueryArgsSchema


@blp.route('/budgets/<int:budget_id>/entries')
class BudgetEntryList(MethodView):
    '''API Endpoint for Budget Entry List'''
    @auth.login_required
    @blp.response(BudgetEntrySchema(many=True))
    def get(self, budget_id):
        '''Return all Budget Entries for a Budget'''
        if auth.current_user().budgets.count == 0:
            raise NoResults('No budget exists for this user')

        b = budget_service._load_budget(
            db.session,
            auth.current_user(),
            budget_id
        )

        # Inject budget currency into returned data
        return b.entries

    @auth.login_required
    @blp.arguments(BudgetEntrySchema)
    @blp.response(BudgetEntrySchema)
    def post(self, json_data, budget_id):
        '''Create a new Budget Entry'''
        if auth.current_user().budgets.count == 0:
            raise NoResults('No budget exists for this user')

        return budget_service.create_entry(
            db.session,
            auth.current_user(),
            budget_id,
            json_data,
        )


@blp.route('/budgets/<int:budget_id>/entries/<int:entry_id>')
class BudgetEntryItem(MethodView):
    '''API Endpoint for Budget Entry Item'''
    @auth.login_required
    @blp.response(BudgetEntrySchema)
    def get(self, entry_id, budget_id):
        '''Return a Budget Entry for a Budget'''
        if auth.current_user().budgets.count == 0:
            raise NoResults('No budget exists for this user')

        return budget_service._load_entry(
            db.session,
            auth.current_user(),
            budget_id,
            entry_id,
        )

    @auth.login_required
    @blp.arguments(BudgetEntryUpdateSchema)
    @blp.response(BudgetEntrySchema)
    def put(self, json_data, budget_id, entry_id):
        '''Update a Budget Entry for a Budget'''
        if auth.current_user().budgets.count == 0:
            raise NoResults('No budget exists for this user')

        return budget_service.update_entry(
            db.session,
            auth.current_user(),
            budget_id,
            entry_id,
            **json_data,
        )

    @auth.login_required
    @blp.response(code=204)
    def delete(self, budget_id, entry_id):
        '''Delete a Budget Entry for a Budget'''
        if auth.current_user().budgets.count == 0:
            raise NoResults('No budget exists for this user')

        budget_service.delete_entry(
            db.session,
            auth.current_user(),
            budget_id,
            entry_id,
        )


@blp.route('/budget/entries/ymc/<int:category_id>')
class BudgetEntryItemYMC(MethodView):
    '''
    '''
    @auth.login_required
    @blp.arguments(BudgetQueryArgsSchema, location='query')
    @blp.response(BudgetEntrySchema)
    def get(self, query_args, category_id):
        '''Return a Budget Entry for a Budget'''
        if auth.current_user().budgets.count == 0:
            raise NoResults('No budget exists for this user')

        budget_id = auth.current_user().budgets[0].id
        return budget_service._load_entry_ymc(
            db.session,
            auth.current_user(),
            budget_id,
            query_args['year'],
            query_args['month'],
            category_id,
        )
