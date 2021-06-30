"""Report API Base Methods.

Jade Tree Personal Budgeting Application | jadetree.io
Copyright (c) 2020 Asymworks, LLC.  All Rights Reserved.
"""

from flask.views import MethodView

from jadetree.api.common import JTApiBlueprint, auth
from jadetree.database import db
from jadetree.service.report import net_worth, spending_by_category, spending_by_payee

from .schema import (
    CategoryReportSchema,
    NetWorthReportSchema,
    PayeeReportSchema,
    ReportFilterSchema,
)

#: Authentication Service Blueprint
blp = JTApiBlueprint('report', __name__, description='Report Service')


@blp.route('/report/networth')
class NetWorthReport(MethodView):
    """API Endpoint for Net Worth report data."""
    @auth.login_required
    @blp.arguments(
        ReportFilterSchema(
            context=dict(
                accept_categories=False,
                accept_payees=False,
            ),
        ),
        location='query'
    )
    @blp.response(NetWorthReportSchema(many=True))
    def get(self, query_args):
        """Return the Net Worth Report Data."""
        return net_worth(db.session, auth.current_user(), filter=query_args)


@blp.route('/report/<int:budget_id>/category')
class CategorySpendingReport(MethodView):
    """API Endpoint for Per-Category Spending report data."""
    @auth.login_required
    @blp.arguments(ReportFilterSchema(), location='query')
    @blp.response(CategoryReportSchema(many=True))
    def get(self, query_args, budget_id):
        """Return the Net Worth Report Data."""
        return spending_by_category(db.session, auth.current_user(), budget_id, filter=query_args)


@blp.route('/report/<int:budget_id>/payee')
class PayeeSpendingReport(MethodView):
    """API Endpoint for Per-Payee Spending report data."""
    @auth.login_required
    @blp.arguments(ReportFilterSchema(), location='query')
    @blp.response(PayeeReportSchema(many=True))
    def get(self, query_args, budget_id):
        """Return the Net Worth Report Data."""
        return spending_by_payee(db.session, auth.current_user(), budget_id, filter=query_args)
