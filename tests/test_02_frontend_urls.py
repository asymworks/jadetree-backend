"""Test the automatic frontend URL generation."""

import pytest  # noqa: F401

from jadetree.exc import ConfigError
from jadetree.templates import setup_frontend_urls


class MockApp:
    """Mock Application which implements Flask.config."""
    def __init__(self, config):
        """Initialize mock application configuration."""
        self.config = config


def test_frontend_url_requires_host(app_config, monkeypatch):
    """Check that FRONTEND_HOST or SERVER_NAME are required."""
    monkeypatch.delitem(app_config, 'FRONTEND_HOST', raising=False)
    monkeypatch.delitem(app_config, 'SERVER_NAME', raising=False)
    _app = MockApp(app_config)
    with pytest.raises(ConfigError) as exc_info:
        setup_frontend_urls(_app)

    assert 'FRONTEND_HOST' in str(exc_info.value)
    assert 'SERVER_NAME' in str(exc_info.value)


def test_frontend_url_no_keys(app_config, monkeypatch):
    """Check that _JT_FRONTEND_URLS is not set when no FRONTEND_*_URLs."""
    monkeypatch.setitem(app_config, 'FRONTEND_HOST', 'http://frontend.local')
    monkeypatch.setitem(app_config, 'SERVER_NAME', 'http://server.local')
    fe_keys = [
        k for k in app_config.keys()
        if k[:9] == 'FRONTEND_' and k[-5:] == '_PATH'
    ]
    for k in fe_keys:
        monkeypatch.delitem(app_config, k, raising=False)

    _app = MockApp(app_config)
    setup_frontend_urls(_app)

    assert '_JT_FRONTEND_URLS' not in _app.config


def test_frontend_url_relative(app_config, monkeypatch):
    """Check relative URLs using FRONTEND_HOST."""
    monkeypatch.setitem(app_config, 'FRONTEND_HOST', 'http://frontend.local')
    monkeypatch.setitem(app_config, 'SERVER_NAME', 'http://server.local')
    monkeypatch.setitem(app_config, 'FRONTEND_REL_PATH', '/relative')
    _app = MockApp(app_config)
    setup_frontend_urls(_app)

    assert '_JT_FRONTEND_URLS' in _app.config
    assert 'rel' in _app.config['_JT_FRONTEND_URLS']
    assert _app.config['_JT_FRONTEND_URLS']['rel'] == 'http://frontend.local/relative'


def test_frontend_url_server_name(app_config, monkeypatch):
    """Check relative URLs using SERVER_NAME."""
    monkeypatch.delitem(app_config, 'FRONTEND_HOST', raising=False)
    monkeypatch.setitem(app_config, 'SERVER_NAME', 'http://server.local')
    monkeypatch.setitem(app_config, 'FRONTEND_REL_PATH', '/relative')
    _app = MockApp(app_config)
    setup_frontend_urls(_app)

    assert '_JT_FRONTEND_URLS' in _app.config
    assert 'rel' in _app.config['_JT_FRONTEND_URLS']
    assert _app.config['_JT_FRONTEND_URLS']['rel'] == 'http://server.local/relative'


def test_frontend_url_absolute(app_config, monkeypatch):
    """Check absolute URLs using FRONTEND_HOST."""
    monkeypatch.setitem(app_config, 'FRONTEND_HOST', 'http://frontend.local')
    monkeypatch.setitem(app_config, 'FRONTEND_REL_PATH', '/relative')
    monkeypatch.setitem(app_config, 'FRONTEND_ABS_PATH', 'http://server2.local/absolute')
    _app = MockApp(app_config)
    setup_frontend_urls(_app)

    assert '_JT_FRONTEND_URLS' in _app.config
    assert 'abs' in _app.config['_JT_FRONTEND_URLS']
    assert 'rel' in _app.config['_JT_FRONTEND_URLS']
    assert _app.config['_JT_FRONTEND_URLS']['abs'] == 'http://server2.local/absolute'
    assert _app.config['_JT_FRONTEND_URLS']['rel'] == 'http://frontend.local/relative'
