# =============================================================================
#
# Jade Tree Personal Budgeting Application | jadetree.io
# Copyright (c) 2020 Asymworks, LLC.  All Rights Reserved.
#
# =============================================================================

from datetime import date

from flask.views import MethodView
from flask_smorest import abort

from jadetree.api.common import JTApiBlueprint, auth
from jadetree.database import db
from jadetree.exc import NoResults
from jadetree.service import budget as budget_service

from .schema import BudgetSchema, BudgetDataSchema, BudgetQueryArgsSchema, \
    BudgetUpdateSchema

#: Authentication Service Blueprint
blp = JTApiBlueprint('budget', __name__, description='Budget Service')


@blp.route('/budgets')
class BudgetList(MethodView):
    '''
    '''
    @auth.login_required
    @blp.response(BudgetSchema(many=True))
    def get(self):
        '''Return the list of User Budgets'''
        return auth.current_user().budgets

    @auth.login_required
    @blp.arguments(BudgetSchema)
    @blp.response(BudgetSchema)
    def post(self, json_data):
        '''Create a new Budget'''
        # TODO: Provide Category Templates
        from jadetree.service.budget.defaults import JADETREE_DEFAULT_CATEGORIES
        return budget_service.create_budget(
            db.session,
            auth.current_user(),
            json_data['name'],
            json_data['currency'],
            JADETREE_DEFAULT_CATEGORIES,
        )


@blp.route('/budgets/<int:budget_id>')
class BudgetItem(MethodView):
    '''API endpoint for a Budget Item'''
    @auth.login_required
    @blp.response(BudgetSchema)
    def get(self, budget_id):
        '''Return User Budget'''
        return budget_service._load_budget(
            db.session,
            auth.current_user(),
            budget_id,
        )

    @auth.login_required
    @blp.arguments(BudgetUpdateSchema)
    @blp.response(BudgetSchema)
    def put(self, json_data, budget_id):
        '''Update Budget Name or Notes'''
        if auth.current_user().budgets.count == 0:
            raise NoResults('No budget exists for this user')

        budget_id = auth.current_user().budgets[0].id
        return budget_service.update_budget(
            db.session,
            auth.current_user(),
            budget_id,
            **json_data,
        )


@blp.route('/budgets/<int:budget_id>/data')
class BudgetDataView(MethodView):
    '''API GET-only endpoint for monthly budget data'''
    @auth.login_required
    @blp.arguments(BudgetQueryArgsSchema, location='query')
    @blp.response(BudgetDataSchema)
    def get(self, query_args, budget_id):
        '''
        '''
        b = budget_service._load_budget(
            db.session,
            auth.current_user(),
            budget_id,
        )

        today = date.today()
        month = (today.year, today.month)
        if len(query_args) > 0:
            if 'year' not in query_args:
                return abort(400, message='Missing "year" query parameter')
            if 'month' not in query_args:
                return abort(400, message='Missing "month" query parameter')

            month = (query_args['year'], query_args['month'])

        data = budget_service.get_budget_month(
            db.session,
            auth.current_user(),
            b.id,
            month
        )

        # Convert categories into an array with category id's injected
        newCats = [dict(category_id=id, **c) for id, c in data['categories'].items()]
        data['categories'] = newCats
        data['currency'] = b.currency
        data['entries'] = [e for e in b.entries if (e.month.year, e.month.month) == month]

        return data
