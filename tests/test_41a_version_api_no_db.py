# =============================================================================
#
# Jade Tree Personal Budgeting Application | jadetree.io
# Copyright (c) 2020 Asymworks, LLC.  All Rights Reserved.
#
# =============================================================================

import json
import pytest   # noqa: F401


def test_version_api_needs_db_init(app_without_database):
    with app_without_database.test_client() as client:
        rv = client.get('/api/v1/version')
        # Check that a failure is sent indicating the database needs
        # to be initialized
        assert rv.status_code == 500

        data = json.loads(rv.data)
        assert 'class' in data
        assert 'status' in data
        assert 'code' in data
        assert 'message' in data

        assert data['class'] == 'Error'
        assert data['code'] == 500
        assert data['status'] == 'Internal Server Error'
        assert 'Database is not initialized' in data['message']
