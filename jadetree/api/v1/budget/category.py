# =============================================================================
#
# Jade Tree Personal Budgeting Application | jadetree.io
# Copyright (c) 2020 Asymworks, LLC.  All Rights Reserved.
#
# =============================================================================

from flask.views import MethodView

from jadetree.api.common import auth
from jadetree.database import db
from jadetree.service import budget as budget_service

from .base import blp
from .schema import CategorySchema, CategoryGroupSchema


@blp.route('/budgets/<int:budget_id>/categories')
class BudgetCategoryList(MethodView):
    '''API Endpoint for Budget Category Tree'''
    @auth.login_required
    @blp.response(CategoryGroupSchema(many=True))
    def get(self, budget_id):
        '''Return Category Tree for the User Budget'''
        b = budget_service._load_budget(
            db.session,
            auth.current_user(),
            budget_id,
        )
        return [cg for cg in b.categories if cg.parent is None]

    @auth.login_required
    @blp.arguments(CategorySchema)
    @blp.response(CategorySchema)
    def post(self, json_data, budget_id):
        '''Create a new Category or Category Group'''
        print(json_data)
        if 'parent_id' in json_data and json_data['parent_id'] is not None:
            return budget_service.create_budget_category(
                db.session,
                auth.current_user(),
                budget_id,
                **json_data
            )

        else:
            return budget_service.create_budget_category_group(
                db.session,
                auth.current_user(),
                budget_id,
                **json_data
            )


@blp.route('/budgets/<int:budget_id>/categories/<int:category_id>')
class BudgetCategoryItem(MethodView):
    '''API Endpoint for Budget Category Tree'''
    @auth.login_required
    @blp.response(CategorySchema)
    def get(self, budget_id, category_id):
        '''Return Category Data'''
        return budget_service._load_category(
            db.session,
            auth.current_user(),
            budget_id,
            category_id,
        )

    @auth.login_required
    @blp.response(code=204)
    def delete(self, budget_id, category_id):
        '''Delete a Category or Category Group'''
        budget_service.delete_category(
            db.session,
            auth.current_user(),
            budget_id,
            category_id,
        )

    @auth.login_required
    @blp.arguments(CategorySchema)
    @blp.response(CategorySchema)
    def put(self, json_data, budget_id, category_id):
        '''Update a Category or Category Group'''
        return budget_service.update_category(
            db.session,
            auth.current_user(),
            budget_id,
            category_id,
            **json_data,
        )
