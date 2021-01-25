"""Jade Tree Email Templates.

Jade Tree Personal Budgeting Application | jadetree.io
Copyright (c) 2020-2021 Asymworks, LLC.  All Rights Reserved.
"""

import re
from urllib.parse import urlencode, urljoin, urlparse, urlunparse

from flask import current_app

from jadetree.exc import ConfigError


def setup_frontend_urls(app):
    """Configure Application Frontend URLs.

    Sets up external URLs for Jade Tree based on values set in the application
    configuration. Any configuration keys with the pattern `FRONTEND_*_PATH`
    will be resolved to full URLs using `urlparse` and with the base server
    name loaded from `FRONTEND_HOST` or `SERVER_NAME`. The resulting paths are
    then stored in a new configuration key `_JT_FRONTEND_URLS` as a dictionary
    with the lower-cased name from the configuration as the key.

    As an example, if the application configuration has the given keys, the
    result will be as follows:

    ```
    # in application config
    FRONTEND_HOST = 'https://jadetree.my.domain'
    FRONTEND_LOGIN_PATH = '/login'
    FRONTEND_BUDGET_PATH = '/budget'
    FRONTEND_TRANSACTIONS_PATH = '/transactions'
    FRONTEND_LOGO_PATH = 'https://cdn.jadetree.my.domain/logo.svg',

    # in application factory
    def create_app():
        app = Flask(__name__)
        setup_frontend_urls(app)

        assert app.config['_JT_FRONTEND_URLS'] == {
            'budget': 'https://jadetree.my.domain/budget',
            'login': 'https://jadetree.my.domain/login',
            'logo': 'https://cdn.jadetree.my.domain/logo.svg',
            'transactions': 'https://jadetree.my.domain/transactions',
        }
    ```
    """
    base_url = app.config.get(
        'FRONTEND_HOST', app.config.get('SERVER_NAME', None)
    )
    if not base_url:
        raise ConfigError(
            (
                'Either FRONTEND_HOST or SERVER_NAME must be set to resolve '
                'frontend URLs.'
            ),
            config_key='FRONTEND_HOST',
        )

    frontend_urls = dict()
    RE_FRONTEND_PATH = re.compile(r'^FRONTEND_(.*)_PATH$')
    for k, v in app.config.items():
        m = RE_FRONTEND_PATH.match(k)
        if m:
            frontend_urls[m.group(1).lower()] = urljoin(base_url, v)

    if frontend_urls:
        app.config['_JT_FRONTEND_URLS'] = frontend_urls


def frontend_url(name, **query_args):
    """Build a URL for a Frontend Link.

    Builds a URL for the Jade Tree frontend using the Frontend URL list loaded
    from the application configuration. Any `query_args` parameters will be
    included as GET query arguments in the URL.

    Args:
        name: Name of the frontend URL in the configuration file, so if the
            `name` parameter is set to `login`, the URL will be created based
            on a configuration parameter named `FRONTEND_LOGIN_URL`.
        query_args: GET query arguments to include in the URL

    Returns:
        URL string

    Raises:
        KeyError: if the URL name is not in `app.config['_JT_FRONTEND_URLS']`
        ValueError: if the URL name is unset or an empty string
    """
    if not name:
        raise ValueError('URL name must be a valid string')
    if name not in current_app.config.get('_JT_FRONTEND_URLS', {}):
        raise KeyError(
            f'The FRONTEND_{name.upper()}_PATH configuration variable '
            'was not found'
        )

    url = current_app.config['_JT_FRONTEND_URLS'][name]
    parts = list(urlparse(url))
    if query_args:
        parts[4] = urlencode(query_args)

    return urlunparse(parts)


def jadetree_context():
    """Inject Jade Tree information into the Template Context."""
    return dict(
        frontend_urls=current_app.config.get('_JT_FRONTEND_URLS', {}),
        frontend_url=frontend_url,
    )


def init_templates(app):
    """Initialize the Templating Subsystem."""
    setup_frontend_urls(app)
    app.context_processor(jadetree_context)
    app.logger.debug('Template Context Initialized')
