# =============================================================================
#
# Jade Tree Personal Budgeting Application | jadetree.io
# Copyright (c) 2020 Asymworks, LLC.  All Rights Reserved.
#
# =============================================================================

from flask import current_app
from flask.views import MethodView

from marshmallow import Schema, fields

from jadetree.api.common import JTApiBlueprint

#: Authentication Service Blueprint
blp = JTApiBlueprint('version', __name__, description='Version Service')


class VersionSchema(Schema):
    '''Schema for Jade Tree Version Information'''
    app_name = fields.Str()
    app_version = fields.Str()
    api_title = fields.Str()
    api_version = fields.Str()
    db_version = fields.Str(allow_none=True)
    needs_setup = fields.Bool()
    server_currency = fields.Str()
    server_language = fields.Str()
    server_locale = fields.Str()
    server_mode = fields.Str()


@blp.route('/version')
class VersionView(MethodView):
    '''Version Information API Call'''
    @blp.response(VersionSchema)
    def get(self):
        from . import api_v1

        ret = dict(
            app_name=current_app.config.get('APP_NAME', 'unknown'),
            app_version=current_app.config.get('APP_VERSION', 'unknown'),
            api_title=api_v1.spec.title,
            api_version=api_v1.spec.version,
            db_version=current_app.config.get('_JT_DB_CUR_REV', None),
        )

        if current_app.config.get('_JT_NEEDS_SETUP', False):
            ret['needs_setup'] = True

        else:
            ret['server_currency'] = current_app.config['DEFAULT_CURRENCY']
            ret['server_language'] = current_app.config['DEFAULT_LANGUAGE']
            ret['server_locale'] = current_app.config['DEFAULT_LOCALE']
            ret['server_mode'] = current_app.config['_JT_SERVER_MODE']

        return ret
