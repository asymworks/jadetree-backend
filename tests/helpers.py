"""Jade Tree Test Helpers.

Jade Tree Personal Budgeting Application | jadetree.io
Copyright (c) 2020 Asymworks, LLC.  All Rights Reserved.
"""

import json

import jwt

from jadetree.service.auth import JWT_SUBJECT_BEARER_TOKEN, load_user_by_email


def check_transaction_entries(tsplit, entries):
    """Check that a list of Transaction Entries are equivalent.

    Validate a list of TransactionEntry objects are equivalent, meaning they
    contain the same items but do not necessarily share ordering.
    """
    assert tsplit.entries is not None
    assert isinstance(tsplit.entries, list)
    assert len(tsplit.entries) == len(entries)
    for i in range(len(tsplit.entries)):
        assert (
            tsplit.entries[i].line.account,
            tsplit.entries[i].amount,
            tsplit.entries[i].currency,
        ) in entries


def check_login(rv, email, session):
    """Check that a login was successful for a user.

    Loads the user by email and ensures that the database UID hash matches the hash
    in the web token returned in rv.

    Args:
        rv: Return value from `Werkzeug.test.Client.open`
        email: User email address that should be logged in
        session: Database Session

    Returns:
        Bearer token returned by the API
    """
    user = load_user_by_email(session, email)
    assert user is not None
    assert user.email == email

    # Check Return Value
    assert rv.status_code == 200

    data = json.loads(rv.data)
    assert 'token' in data
    assert 'user' in data

    payload = jwt.decode(data['token'], verify=False)

    assert payload is not None
    assert 'iat' in payload
    assert 'iss' in payload
    assert 'aud' in payload
    assert 'sub' in payload
    assert 'uid' in payload

    assert payload['sub'] == JWT_SUBJECT_BEARER_TOKEN
    assert payload['uid'] == user.uid_hash

    return data['token']


def check_unauthorized(rv, message='Invalid credentials'):
    """Check that a login was rejected with invalid credentials."""
    assert rv.status_code == 401

    data = json.loads(rv.data)
    assert 'class' in data
    assert 'status' in data
    assert 'code' in data
    assert 'message' in data

    assert data['class'] == 'AuthError'
    assert data['code'] == 401
    assert data['status'] == 'Unauthorized'
    assert message in data['message']
