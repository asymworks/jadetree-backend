# =============================================================================
#
# Jade Tree Personal Budgeting Application | jadetree.io
# Copyright (c) 2020 Asymworks, LLC.  All Rights Reserved.
#
# =============================================================================

from functools import wraps
import http

from flask_smorest import Api, Blueprint, abort  # noqa

from jadetree.exc import Error, NoResults, Unauthorized

from .auth import auth


class JTApi(Api):
    '''
    Extend Flask-Smorest Api class with authentication and error handling
    information
    '''
    def init_app(self, app, *, spec_kwargs=None):
        super().init_app(app, spec_kwargs=spec_kwargs)
        self.spec.components.security_scheme(
            'bearerAuth', {
                'type': 'http',
                'scheme': 'bearer',
                'bearerFormat': 'JWT',
            }
        )

        self._app.register_error_handler(Error, self._jt_error)
        self._app.register_error_handler(NoResults, self._no_results)
        self._app.register_error_handler(Unauthorized, self._unauthorized)

    def _jt_error(self, error):
        headers = {}
        payload = {
            'code': error.status_code,
            'status': http.HTTPStatus(error.status_code).phrase,
            'class': error.__class__.__name__,
            'message': str(error),
            'errors': { },
        }

        return payload, payload['code'], headers

    def _no_results(self, error):
        headers = {}
        payload = {
            'code': 404,
            'status': http.HTTPStatus(404).phrase,
            'class': error.__class__.__name__,
            'message': str(error),
            'errors': { },
        }

        return payload, payload['code'], headers

    def _unauthorized(self, error):
        headers = {}
        payload = {
            'code': 403,
            'status': http.HTTPStatus(403).phrase,
            'class': error.__class__.__name__,
            'message': str(error),
            'errors': { },
        }

        return payload, payload['code'], headers


class JTApiBlueprint(Blueprint):
    '''
    Extend Flask-Smorest Blueprint class with authentication helpers
    '''
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._prepare_doc_cbks.append(self._prepare_auth_doc)

    def arguments(self, schema, *args, **kwargs):
        '''Inject request data into the schema context'''
        if isinstance(schema, type):
            schema = schema()

        inject_context = kwargs.pop('inject_context', False)
        decorator_orig = super().arguments(schema, *args, **kwargs)

        def decorator(func):
            func = decorator_orig(func)

            @wraps(func)
            def wrapper(*args, **kwargs):
                if inject_context:
                    for k, v in kwargs.items():
                        schema.context[k] = v

                return func(*args, **kwargs)

            return wrapper

        return decorator

    @staticmethod
    def login_required(func):
        # Note: we don't use "role" and "optional" parameters in the app,
        # we always call login_required with not parameter
        func = auth.login_required(func)
        getattr(func, '_apidoc', {})['auth'] = True
        return func

    @staticmethod
    def _prepare_auth_doc(doc, doc_info, **kwargs):
        if doc_info.get('auth', False):
            doc.setdefault('responses', {})['401'] = http.HTTPStatus(401).name
            doc['security'] = [{'bearerAuth': []}]
        return doc
