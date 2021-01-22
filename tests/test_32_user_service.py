# =============================================================================
#
# Jade Tree Personal Budgeting Application | jadetree.io
# Copyright (c) 2020 Asymworks, LLC.  All Rights Reserved.
#
# =============================================================================

import pytest  # noqa: F401

from jadetree.domain.types import AccountRole, AccountType
from jadetree.exc import DomainError
from jadetree.service import user as user_service


def test_user_profile_setup_sets_up_profile(session, user_without_profile):
    u = user_service.setup_user(
        session=session,
        user=user_without_profile,
        language='en',
        locale='en_US',
        currency='USD'
    )

    assert u.profile_setup is True
    assert u.profile_setup_at is not None
    assert u.language == 'en'
    assert u.locale == 'en_US'
    assert u.currency == 'USD'
    assert u.fmt_date_short is None
    assert u.fmt_date_long is None
    assert u.fmt_decimal is None
    assert u.fmt_currency is None
    assert u.fmt_accounting is None


def test_user_profile_setup_sets_up_accounts(session, user_with_profile):
    accts = {a.name: a for a in user_with_profile.accounts}

    assert len(accts) == 4

    assert '_initial' in accts
    assert accts['_initial'].role == AccountRole.System
    assert accts['_initial'].type == AccountType.Capital
    assert accts['_initial'].currency == user_with_profile.currency

    assert '_ob_income' in accts
    assert accts['_ob_income'].role == AccountRole.System
    assert accts['_ob_income'].type == AccountType.Income
    assert accts['_ob_income'].currency == user_with_profile.currency

    assert '_ob_expense' in accts
    assert accts['_ob_expense'].role == AccountRole.System
    assert accts['_ob_expense'].type == AccountType.Expense
    assert accts['_ob_expense'].currency == user_with_profile.currency

    assert '_trading' in accts
    assert accts['_trading'].role == AccountRole.System
    assert accts['_trading'].type == AccountType.Trading
    assert accts['_trading'].currency == user_with_profile.currency


def test_user_profile_setup_normalizes_language(session, user_without_profile):
    u = user_service.setup_user(
        session=session,
        user=user_without_profile,
        language='En',
        locale='en_US',
        currency='USD'
    )

    assert u.language == 'en'
    assert u.locale == 'en_US'
    assert u.currency == 'USD'


def test_user_profile_setup_normalizes_locale(session, user_without_profile):
    u = user_service.setup_user(
        session=session,
        user=user_without_profile,
        language='en',
        locale='EN_us_PoSiX',
        currency='USD'
    )

    assert u.language == 'en'
    assert u.locale == 'en_US_PoSiX'
    assert u.currency == 'USD'


def test_user_profile_setup_normalizes_currency(session, user_without_profile):
    u = user_service.setup_user(
        session=session,
        user=user_without_profile,
        language='en',
        locale='en_CA',
        currency='cad'
    )

    assert u.language == 'en'
    assert u.locale == 'en_CA'
    assert u.currency == 'CAD'


def test_user_profile_setup_throws_not_confirmed(session, user_without_profile):
    u = user_without_profile
    u.confirmed = False
    with pytest.raises(DomainError, match='User has not confirmed'):
        user_service.setup_user(session, user_without_profile, 'en', 'en_US', 'USD')


def test_user_profile_setup_throws_bad_language(session, user_without_profile):
    with pytest.raises(ValueError, match='Invalid language code'):
        user_service.setup_user(session, user_without_profile, 'eng', 'en_US', 'USD')


def test_user_profile_setup_throws_bad_locale(session, user_without_profile):
    with pytest.raises(ValueError, match='Invalid locale string'):
        user_service.setup_user(session, user_without_profile, 'en', 'en-US', 'USD')


def test_user_profile_setup_throws_bad_currency(session, user_without_profile):
    with pytest.raises(ValueError, match='Invalid currency code'):
        user_service.setup_user(session, user_without_profile, 'en', 'en_US', 'US$')


def test_user_profile_setup_throws_invalid_currency(session, user_without_profile):
    with pytest.raises(DomainError, match='undefined currency'):
        user_service.setup_user(session, user_without_profile, 'en', 'en_US', 'XXX')


def test_user_profile_setup_custom_date_fmt(session, user_without_profile):
    u = user_service.setup_user(
        session=session,
        user=user_without_profile,
        language='en',
        locale='en_US',
        currency='USD',
        fmt_date_short='shortdate',
        fmt_date_long='longdate',
    )

    assert u.fmt_date_short == 'shortdate'
    assert u.fmt_date_long == 'longdate'
    assert u.fmt_decimal is None
    assert u.fmt_currency is None
    assert u.fmt_accounting is None


def test_user_profile_setup_custom_number_fmt(session, user_without_profile):
    u = user_service.setup_user(
        session=session,
        user=user_without_profile,
        language='en',
        locale='en_US',
        currency='USD',
        fmt_decimal='decimal',
        fmt_currency='currency',
        fmt_accounting='accounting',
    )

    assert u.fmt_date_short is None
    assert u.fmt_date_long is None
    assert u.fmt_decimal == 'decimal'
    assert u.fmt_currency == 'currency'
    assert u.fmt_accounting == 'accounting'


def test_user_profile_setup_throws_already_setup(session, user_with_profile):
    with pytest.raises(DomainError, match='already set up the profile'):
        user_service.setup_user(session, user_with_profile, 'en', 'en_US', 'USD')
