# =============================================================================
#
# Jade Tree Personal Budgeting Application | jadetree.io
# Copyright (c) 2020 Asymworks, LLC.  All Rights Reserved.
#
# =============================================================================

from flask import current_app
from flask.views import MethodView

from marshmallow import Schema, ValidationError, fields, validates, \
    validates_schema

from jadetree.api.common import JTApiBlueprint
from jadetree.database import db
from jadetree.exc import Error
from jadetree.setup import JT_SERVER_MODES, setup_jadetree

#: Authentication Service Blueprint
blp = JTApiBlueprint('setup', __name__, description='Server Setup Service')


class SetupSchema(Schema):
    '''Schema for Jade Tree Server Setup'''
    mode = fields.Str(required=True)
    email = fields.Email(required=True)
    password = fields.Str(required=True)
    name = fields.Str(required=True)

    # Validate server mode strings
    @validates('mode')
    def validate_mode(self, value):
        if value not in JT_SERVER_MODES:
            raise ValidationError(
                "'mode' must be one of: {}".format(
                    ', '.join(["'" + m + "'" for m in JT_SERVER_MODES])
                )
            )

    # Validate against configuration-forced values
    @validates_schema
    def validate_config(self, data, **kwargs):
        err_msg = "Field '{}' must be set to '{}' (forced by configuration)"

        # Check Server Mode Data
        server_mode = current_app.config.get('SERVER_MODE', None)
        if server_mode is not None:
            if data['mode'] != server_mode:
                raise ValidationError(err_msg.format('mode', server_mode), 'mode')

        # Check User Data
        user_keys = ('email', 'name')
        for key in user_keys:
            config_val = current_app.config.get(
                'USER_{}'.format(key.upper()),
                None
            )
            if config_val is not None and data[key] != config_val:
                raise ValidationError(err_msg.format(key, config_val), key)


@blp.route('/setup')
class SetupView(MethodView):
    '''Server Setup API Call'''
    @blp.response(SetupSchema)
    def get(self):
        if not current_app.config.get('_JT_NEEDS_SETUP', False):
            message = "The '/setup' endpoint is not available after the " \
                'server has been set up'
            raise Error(message, status_code=410)

        ret = dict()

        # Load Forced Server Mode
        server_mode = current_app.config.get('SERVER_MODE', None)
        if server_mode is not None:
            ret['mode'] = server_mode

        # Load Forced User Information
        user_keys = ('email', 'name')
        for key in user_keys:
            config_val = current_app.config.get(
                'USER_{}'.format(key.upper()),
                None
            )
            if config_val is not None:
                ret[key] = config_val

        return ret

    @blp.arguments(SetupSchema)
    @blp.response(code=204)
    def post(self, json_data):
        if not current_app.config.get('_JT_NEEDS_SETUP', False):
            message = "The '/setup' endpoint is not available after the " \
                'server has been set up'
            raise Error(message, status_code=410)

        setup_jadetree(db.session, **json_data)
