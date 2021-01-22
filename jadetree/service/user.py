# =============================================================================
#
# Jade Tree Personal Budgeting Application | jadetree.io
# Copyright (c) 2020 Asymworks, LLC.  All Rights Reserved.
#
# =============================================================================

# User Services

import re

from arrow import utcnow
from babel import Locale

from jadetree.domain.data import CURRENCY_LIST
from jadetree.domain.models import Account, Payee
from jadetree.domain.types import AccountRole, AccountType, PayeeRole
from jadetree.exc import DomainError

from .util import check_session, check_user
from .validator import RegexValidator

__all__ = ('setup_user', 'get_initial_payee')


def normalize_language(lang):
    return Locale.parse(lang).language


def normalize_locale(locale):
    return str(Locale.parse(locale))


def setup_user(
    session, user, language, locale, currency, **fmt_strings
):
    '''
    Setup the user's localization profile preferences, setting the language,
    locale string, base currency, as well as user-defined formatting string
    overrides.  Supported keys for the ``fmt_strings`` parameters are:

    * ``fmt_date_short``: Short date format string
    * ``fmt_date_long``: Long date format string
    * ``fmt_decimal``: Decimal number format string
    * ``fmt_currency``: Currency format string
    * ``fmt_accounting``: Accounting format string

    Format strings must comply with comply with `Unicode LDML`_.

    This function also creates four default `~AccountRole.System` accounts for
    the user, specifically:

    *   ``_initial``: `~AccountType.Capital` account used for initial balances
        for off-budget accounts
    *   ``_ob_income``: `~AccountType.Income` account used to track off-budget
        inflow transactions
    *   ``_ob_income``: `~AccountType.Expense` account used to track off-budget
        outflow transactions
    *   ``_trading``: `~AccountType.Trading` account used for multi-currency
        transactions

    .. _`Unicode LDML`:
        https://unicode.org/reports/tr35/#Number_Format_Patterns

    :param session: Database session
    :type session: ~sqlalchemy.orm.session.Session
    :param user:
    :type name: str
    :param language: ISO 3166 alpha-2 language code
    :type language: str
    :param locale: locale string with underscore separation (e.g. en_US)
    :type locale: str
    :param currency: ISO 4217 currency string, must be in `CURRENCY_LIST`
    :type currency: str
    :returns: User object
    :rtype: :class:`User`
    '''
    check_session(session)
    check_user(user)

    RegexValidator(
        r'^[a-z]{2}$',
        flags=re.I,
        message='Invalid language code'
    )(language)
    RegexValidator(
        r'^[a-z]{2}_\w+(_\w+){0,3}$',
        flags=re.I,
        message='Invalid locale string'
    )(locale)
    if currency.upper() not in CURRENCY_LIST:
        raise ValueError('Invalid currency code')
    if currency.upper() == 'XXX':
        raise DomainError(
            'User currency may not be the undefined currency XXX'
        )

    if not user.confirmed:
        raise DomainError(
            'User has not confirmed registration and may not update profile '
            'settings'
        )

    if user.profile_setup:
        raise DomainError(
            'User has already set up the profile settings'
        )

    # FIXME: Add Context Manager
    # with session:

    user.language = normalize_language(language)
    user.locale = normalize_locale(locale)
    user.currency = currency.upper()

    # Date Format Overrides
    for k in ('fmt_date_short', 'fmt_date_long'):
        setattr(user, k, fmt_strings.pop(k, None))

    # Number Format Overrides
    for k in ('fmt_decimal', 'fmt_currency', 'fmt_accounting'):
        setattr(user, k, fmt_strings.pop(k, None))

    # Update User
    user.profile_setup = True
    user.profile_setup_at = utcnow()

    # Create system accounts for the User
    a_initial = Account(
        user=user,
        name='_initial',
        role=AccountRole.System,
        type=AccountType.Capital,
        currency=currency
    )
    a_ob_income = Account(
        user=user,
        name='_ob_income',
        role=AccountRole.System,
        type=AccountType.Income,
        currency=currency
    )
    a_ob_expense = Account(
        user=user,
        name='_ob_expense',
        role=AccountRole.System,
        type=AccountType.Expense,
        currency=currency
    )
    a_trading = Account(
        user=user,
        name='_trading',
        role=AccountRole.System,
        type=AccountType.Trading,
        currency=currency
    )
    p_initial = Payee(
        user=user,
        name='Starting Balance',
        account=None,
        category=None,
        role=PayeeRole.Initial,
        system=True,
        hidden=False,
    )

    session.add(user)
    session.add_all((a_initial, a_ob_income, a_ob_expense, a_trading))
    session.add(p_initial)
    session.commit()

    return user


def update_user(session, user, **kwargs):
    '''
    Update user information from the provided dictionary values.

    :param session: Database session
    :type session: ~sqlalchemy.orm.session.Session
    :param user:
    :type user: User
    :returns: User object
    :rtype: :class:`User`
    '''
    check_session(session)
    check_user(user)

    raise NotImplementedError('update_user is not implemented yet')


def get_initial_payee(session, user):
    '''
    Return the "Starting Balance" `Payee` for the `User`

    :param session: Database session
    :type session: ~sqlalchemy.orm.session.Session
    :param user:
    :type user: User
    :returns: Starting Balance Payee object
    :rtype: :class:`Payee`
    '''
    return session.query(Payee).filter(
        Payee.user == user,
        Payee.role == PayeeRole.Initial,
    ).one()
