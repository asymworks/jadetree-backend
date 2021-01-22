# =============================================================================
#
# Jade Tree Personal Budgeting Application | jadetree.io
# Copyright (c) 2020 Asymworks, LLC.  All Rights Reserved.
#
# =============================================================================

import re

import pytest

from jadetree.domain.models import User


@pytest.mark.unit
def test_user_set_password_sets_uid_hash():
    u = User(email='test@jadetree.io')
    assert u.uid_hash is None
    assert u.pw_hash is None

    u.set_password('hunter2')
    assert u.uid_hash is not None
    assert u.pw_hash is not None


@pytest.mark.unit
def test_user_set_password_resets_pw_hash():
    u = User(email='test@jadetree.io')
    u.set_password('hunter2')
    assert u.uid_hash is not None
    assert u.pw_hash is not None

    pw1 = u.pw_hash

    u.set_password('passw0rd')
    assert u.pw_hash is not None
    assert u.pw_hash != pw1


@pytest.mark.unit
def test_user_set_password_resets_uid_hash():
    u = User(email='test@jadetree.io')
    u.set_password('hunter2')
    assert u.uid_hash is not None
    assert u.pw_hash is not None

    uid1 = u.uid_hash

    u.set_password('passw0rd')
    assert u.uid_hash is not None
    assert u.uid_hash != uid1


@pytest.mark.unit
def test_user_set_password_hashes():
    u = User(email='test@jadetree.io')
    u.set_password('hunter2')
    assert u.pw_hash[0:21] == 'pbkdf2:sha256:150000$'


@pytest.mark.unit
def test_user_uid_hash():
    u = User(email='test@jadetree.io')
    u.set_password('hunter2')
    assert len(u.uid_hash) == 32
    assert re.match(r'[0-9a-f]{32}', u.uid_hash) is not None
