# =============================================================================
#
# Jade Tree Personal Budgeting Application | jadetree.io
# Copyright (c) 2020 Asymworks, LLC.  All Rights Reserved.
#
# =============================================================================

from flask.views import MethodView

from jadetree.api.base import JTApiBlueprint

#: Authentication Service Blueprint
blp = JTApiBlueprint('export', __name__, description='Export Service')


@blp.route('/export')
class VersionView(MethodView):
    '''Export Data API Call'''
    def get(self):
        return 'Test'
