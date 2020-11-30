# =============================================================================
#
# Jade Tree Personal Budgeting Application | jadetree.io
# Copyright (c) 2020 Asymworks, LLC.  All Rights Reserved.
#
# =============================================================================

import http

from flask import g
from flask_httpauth import HTTPTokenAuth

from jadetree.database import db
from jadetree.exc import AuthError, Error
from jadetree.service import auth as auth_service

# Jade Tree API Authentication Helper
auth = HTTPTokenAuth()


@auth.verify_token
def verify_token(token):
    try:
        g._api_auth_error = None
        if not token:
            raise AuthError('Missing authentication token', status_code=401)
        return auth_service.load_user_by_token(db.session, token)
    except Exception as e:
        g._api_auth_error = e
        return None


@auth.error_handler
def error_handler(status):
    headers = {}
    payload = {
        'code': status,
        'status': http.HTTPStatus(status).value,
        'errors': { },
    }

    # TODO: Implement sane error handling across the API
    if g._api_auth_error:
        payload['class'] = g._api_auth_error.__class__.__name__
        payload['message'] = str(g._api_auth_error)

        if isinstance(g._api_auth_error, Error) and g._api_auth_error.status_code != 500:
            payload['code'] = g._api_auth_error.status_code
            payload['status'] = http.HTTPStatus(g._api_auth_error.status_code).value

    print(payload)
    return payload, payload['code'], headers
