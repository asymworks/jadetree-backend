# =============================================================================
#
# Jade Tree Personal Budgeting Application | jadetree.io
# Copyright (c) 2020 Asymworks, LLC.  All Rights Reserved.
#
# =============================================================================

from jadetree.api.common import JTApi

from .account import blp as account_api
from .auth import blp as auth_api
from .budget import blp as budget_api
from .payee import blp as payee_api
from .setup import blp as setup_api
from .transactions import blp as transaction_api
from .user import blp as user_api
from .version import blp as version_api

from .socketio import init_api_socketio

__all__ = ('init_api', )

#: Global Api Objects
api_v1 = JTApi()


def init_api(app):
    '''Register the API with the Application'''
    api_v1.init_app(app, spec_kwargs=dict(
        title='Jade Tree',
        version='v1',
        openapi_version='3.0.2')
    )

    api_v1.register_blueprint(account_api, url_prefix='/api/v1')
    api_v1.register_blueprint(auth_api, url_prefix='/api/v1')
    api_v1.register_blueprint(budget_api, url_prefix='/api/v1')
    api_v1.register_blueprint(payee_api, url_prefix='/api/v1')
    api_v1.register_blueprint(setup_api, url_prefix='/api/v1')
    api_v1.register_blueprint(transaction_api, url_prefix='/api/v1')
    api_v1.register_blueprint(user_api, url_prefix='/api/v1')
    api_v1.register_blueprint(version_api, url_prefix='/api/v1')

    # Initialize SocketIO Handlers
    init_api_socketio('/api/v1')

    # Notify Initialization Complete
    app.logger.debug('API v1 Initialized')
