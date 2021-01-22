# =============================================================================
#
# Jade Tree Personal Budgeting Application | jadetree.io
# Copyright (c) 2020 Asymworks, LLC.  All Rights Reserved.
#
# =============================================================================

import json

import pytest  # noqa: F401


def test_version_api_fields(app):
    with app.test_client() as client:
        rv = client.get('/api/v1/version')
        assert rv.status_code == 200

        data = json.loads(rv.data)
        assert 'app_name' in data
        assert 'app_version' in data
        assert 'api_title' in data
        assert 'api_version' in data
        assert 'db_version' in data


def test_version_api_needs_setup(app):
    with app.test_client() as client:
        rv = client.get('/api/v1/version')
        assert rv.status_code == 200

        data = json.loads(rv.data)
        assert 'needs_setup' in data
        assert data['needs_setup'] is True

        assert 'server_currency' not in data
        assert 'server_language' not in data
        assert 'server_locale' not in data
        assert 'server_mode' not in data


def test_version_api_after_setup(app):
    with app.test_client() as client:
        rv = client.get('/api/v1/version')
        assert rv.status_code == 200

        data = json.loads(rv.data)
        assert 'needs_setup' in data
        assert data['needs_setup'] is True

        # Setup Server
        setup_data = {
            'mode': 'personal',
            'email': 'test@jadetree.io',
            'password': 'hunter2JT',
            'name': 'Test User',
        }
        rv = client.post(
            '/api/v1/setup',
            content_type='application/json',
            data=json.dumps(setup_data),
        )
        assert rv.status_code == 204

        # Re-Check Version Result
        rv = client.get('/api/v1/version')
        assert rv.status_code == 200

        data = json.loads(rv.data)
        assert 'needs_setup' not in data

        assert 'server_currency' in data
        assert 'server_language' in data
        assert 'server_locale' in data
        assert 'server_mode' in data
        assert data['server_currency'] == app.config['DEFAULT_CURRENCY']
        assert data['server_language'] == app.config['DEFAULT_LANGUAGE']
        assert data['server_locale'] == app.config['DEFAULT_LOCALE']
        assert data['server_mode'] == 'personal'
