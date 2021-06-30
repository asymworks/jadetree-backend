"""Report API Base Methods.

Jade Tree Personal Budgeting Application | jadetree.io
Copyright (c) 2020 Asymworks, LLC.  All Rights Reserved.
"""

from flask.views import MethodView

from jadetree.api.common import JTApiBlueprint, auth
from jadetree.database import db
from jadetree.service.report import net_worth

from .schema import NetWorthReportSchema, ReportFilterSchema

#: Authentication Service Blueprint
blp = JTApiBlueprint('report', __name__, description='Report Service')


@blp.route('/report/networth')
class PayeeList(MethodView):
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
