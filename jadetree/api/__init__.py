# =============================================================================
#
# Jade Tree Personal Budgeting Application | jadetree.io
# Copyright (c) 2020 Asymworks, LLC.  All Rights Reserved.
#
# =============================================================================

from flask_cors import CORS

from .v1 import init_api as init_api_v1

__all__ = ('init_api', )


def init_api(app):
    '''Register the APIs with the Application'''
    init_api_v1(app)

    # Setup CORS for API
    CORS(app, resources={r'/api/*': {'origins': '*'}})

    # Notify Initialization Complete
    app.logger.debug('API and CORS Initialized')
