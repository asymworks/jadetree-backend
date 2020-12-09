# =============================================================================
#
# Jade Tree Personal Budgeting Application | jadetree.io
# Copyright (c) 2020 Asymworks, LLC.  All Rights Reserved.
#
# =============================================================================

from datetime import date

from sqlalchemy import and_
from sqlalchemy.exc import IntegrityError

from jadetree.domain.models import BudgetEntry, Category
from jadetree.exc import DomainError, NoResults, Unauthorized

from .budget import _load_budget
from .category import _load_category
from ..util import check_session, check_user

__all__ = (
    '_load_entry', '_load_entry_ymc', 'create_entry', 'delete_entry',
    'update_entry',
)


def _load_entry(session, user, budget_id, entry_id):
    '''
    Load a Budget Entry by id and include authorization checks that the given
    user is allowed to access the budget.
    '''
    e = session.query(BudgetEntry).get(entry_id)
    if e is None:
        raise NoResults('No budget entry found for id {}'.format(entry_id))

    if e.budget.id != budget_id:
        raise NoResults(
            'Budget entry does not belong to budget {}'.format(budget_id)
        )

    if e.budget.user != user:
        raise Unauthorized(
            'Budget entry id {} does not belong to user {}'.format(
                entry_id,
                user.email,
            )
        )

    return e


def _load_entry_ymc(session, user, budget_id, year, month, category_id):
    '''
    Load a Budget Entry by year, month, and Category Id and include
    authorization checks that the given user is allowed to access the budget.
    '''
    check_session(session)
    check_user(user, needs_profile=True)

    # Check Access to Budget and Category
    b = _load_budget(session, user, budget_id)
    c = _load_category(session, user, budget_id, category_id)

    # Load Budget Entry
    d1 = date(year, month, 1)
    d2 = date(year, month + 1, 1)
    e = session.query(BudgetEntry).filter(
        and_(
            and_(
                BudgetEntry.month >= d1,
                BudgetEntry.month < d2,
            ),
            BudgetEntry.category == c,
            BudgetEntry.budget == b,
        )
    ).one_or_none()

    if e is None:
        return None

    return e


def create_entry(session, user, budget_id, entry_data):
    '''
    '''
    check_session(session)
    check_user(user, needs_profile=True)

    # Check existance and authorization for budget id
    b = _load_budget(session, user, budget_id)

    # Ensure required keys are present
    missing_keys = []
    for k in ('month', 'category_id', 'amount'):
        if k not in entry_data:
            missing_keys.push(k)
    if len(missing_keys) > 0:
        raise DomainError(
            'Missing parameters: {}'.format(', '.join(missing_keys))
        )

    # Load the Category
    c = session.query(Category).get(entry_data.pop('category_id', -1))
    if c is None:
        raise DomainError('Category {} does not exist', status_code=422)
    if c.budget != b:
        raise DomainError(
            'Category {} does not belong to budget {}'.format(c.id, budget_id),
            status_code=422
        )
    if c.parent is None:
        raise DomainError(
            'Budget entries may not be attached to Category Groups',
            status_code=422
        )

    # Update the Default Budget
    update_default = entry_data.pop('default', False)
    if update_default:
        c.default_budget = entry_data['amount']
        session.add(c)

    # Create the Budget Entry
    e = BudgetEntry(
        budget=b,
        category=c,
        **entry_data
    )

    session.add(e)
    session.commit()

    return e


def update_entry(session, user, budget_id, entry_id, **kwargs):
    '''
    '''
    check_session(session)
    check_user(user, needs_profile=True)

    # Check existance and authorization for budget entry id
    e = _load_entry(session, user, budget_id, entry_id)

    # Update Month/Year
    if 'month' in kwargs:
        e.month = kwargs.pop('month')

    # Update Amount and Rollover
    if 'amount' in kwargs:
        e.amount = kwargs.pop('amount')
    if 'rollover' in kwargs:
        e.rollover = kwargs.pop('rollover')

    # Update Notes
    if 'notes' in kwargs:
        e.notes = kwargs.pop('notes')

    # Update Category Default
    if 'default' in kwargs and kwargs.pop('default'):
        e.category.default_budget = e.amount
        session.add(e.category)

    # Check for unexpected keywords
    if len(kwargs):
        raise DomainError(
            'Unexpected parameters {}'.format(', '.join(kwargs.keys())),
            status_code=422,
        )

    # Commit Changes (DB may throw a uniqueness constraint error here)
    try:
        session.add(e)
        session.commit()

    except IntegrityError as exc:
        raise DomainError(exc.message, status_code=422, exc=exc)

    # Return Updated Item
    return e


def delete_entry(session, user, budget_id, entry_id):
    '''
    '''
    check_session(session)
    check_user(user, needs_profile=True)

    # Check existance and authorization for budget entry id
    e = _load_entry(session, user, budget_id, entry_id)

    # Delete Entry
    session.delete(e)
    session.commit()

    return e
