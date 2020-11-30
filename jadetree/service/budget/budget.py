# =============================================================================
#
# Jade Tree Personal Budgeting Application | jadetree.io
# Copyright (c) 2020 Asymworks, LLC.  All Rights Reserved.
#
# =============================================================================

# Budget Services

from sqlalchemy.exc import IntegrityError

from jadetree.domain.data import CURRENCY_LIST
from jadetree.domain.models import Account, Budget, Category
from jadetree.domain.types import AccountRole, AccountType
from jadetree.exc import DomainError, NoResults, Unauthorized

from ..util import check_session, check_user

__all__ = ('_load_budget', 'create_budget', 'update_budget')


def _load_budget(session, user, budget_id):
    '''
    Load a Budget by id and include authorization checks that the given user
    is allowed to access the budget.
    '''
    b = session.query(Budget).get(budget_id)
    if b is None:
        raise NoResults('No budget found for id {}'.format(budget_id))

    if b.user != user:
        raise Unauthorized(
            'Budget id {} does not belong to user {}'.format(
                budget_id,
                user.email,
            )
        )

    return b


def create_budget(session, user, name, currency=None, categories=None):
    '''
    The initial categories and expense accounts may be provided to this
    function. The structure of the ``categories`` parameter is interpreted
    as follows::

        category_map ::= [ <group_def> ]*
        group_def ::= {
            'name': 'group_name',
            'categories': <category_list> ? [],
            'system': <bool> ? False,
            'hidden': <bool> ? False
        }
        category_list ::= [ 'category_name' | <category_def> ]*
        category_def ::= {
            'name': 'category_name',
            'system': <bool> ? False,
            'hidden': <bool> ? False
        }

    Display ordering is automatically set based on the relative positions
    of the ``group_def`` and ``category_def`` entries within their lists.

    :param session: Database session
    :type session: ~sqlalchemy.orm.session.Session
    :param user:
    :type user: User
    :param name: Name of the new budget
    :type name: str
    :param currency: Type of currency the account holds, as an ISO 4217 code
        or another security code. If not provided, the user's Base Currency
        is used.
    :type currency: str or None
    :param categories: Initial categories and groups
    :type categories: list
    :returns: Budget Id
    :rtype: int
    '''
    check_session(session)
    check_user(user, needs_profile=True)

    if currency is None:
        currency = user.currency
    if currency.upper() not in CURRENCY_LIST:
        raise ValueError('Invalid currency code')
    if currency.upper() == 'XXX':
        raise DomainError(
            'Budget currency may not be the undefined currency XXX'
        )

    if categories is not None and not isinstance(categories, list):
        raise TypeError('Budget category list must be a list')

    # FIXME: Add Context Manager
    # with session:

    b = Budget(user=user, name=name, currency=currency)
    a_income = Account(
        user=user,
        budget=b,
        name='_income',
        role=AccountRole.Budget,
        type=AccountType.Income,
        currency=b.currency,
    )
    a_expense = Account(
        user=user,
        budget=b,
        name='_expense',
        role=AccountRole.Budget,
        type=AccountType.Expense,
        currency=b.currency,
    )
    g_income = Category(
        budget=b,
        name='_income',
        parent=None,
        system=True,
        hidden=True,
        display_order=0,
    )
    c_income_cur = Category(
        budget=b,
        name='_cur_month',
        parent=g_income,
        system=True,
        hidden=True,
    )
    c_income_next = Category(
        budget=b,
        name='_next_month',
        parent=g_income,
        system=True,
        hidden=True,
    )
    g_debt = Category(
        budget=b,
        name='_debt',
        parent=None,
        system=False,
        hidden=True,
        display_order=1,
    )

    if categories is not None:
        session.add_all(b.add_categories(categories, start_display_order=2))

    session.add_all((g_income, c_income_cur, c_income_next))
    session.add_all((g_debt, ))
    session.add_all((a_income, a_expense))
    session.add(b)
    session.commit()

    return b


def update_budget(session, user, budget_id, **kwargs):
    '''
    '''
    b = _load_budget(session, user, budget_id)

    if 'name' in kwargs:
        b.name = kwargs.pop('name')

    if 'notes' in kwargs:
        b.notes = kwargs.pop('notes')

    # Check for unexpected keywords
    if len(kwargs):
        raise DomainError(
            'Unexpected parameters {}'.format(', '.join(kwargs.keys())),
            status_code=422,
        )

    # Commit Changes
    try:
        session.add(b)
        session.commit()

    except IntegrityError as exc:
        raise DomainError(exc.message, status_code=422, exc=exc)

    # Return Updated Item
    return b
