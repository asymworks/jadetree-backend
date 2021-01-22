# =============================================================================
#
# Jade Tree Personal Budgeting Application | jadetree.io
# Copyright (c) 2020 Asymworks, LLC.  All Rights Reserved.
#
# =============================================================================

from sqlalchemy import and_
from sqlalchemy.orm import joinedload

from jadetree.database.tables import categories as categories_table
from jadetree.domain.models import Category
from jadetree.exc import DomainError, NoResults, Unauthorized

from ..util import check_session, check_user
from .budget import _load_budget

__all__ = (
    '_load_category',
    'create_budget_category_group',
    'create_budget_category',
    'delete_category',
    'get_category_tree',
    'move_category',
    'update_category',
)


def _load_category(session, user, budget_id, category_id):
    '''
    '''
    check_session(session)
    check_user(user, needs_profile=True)

    c = session.query(Category).get(category_id)
    if c is None:
        raise NoResults(f'No category found for id {category_id}')

    if c.budget.id != budget_id:
        raise NoResults(
            f'Category does not belong to budget {budget_id}'
        )

    if c.budget.user != user:
        raise Unauthorized(
            'Category id {} does not belong to user {}'.format(
                category_id,
                user.email,
            )
        )

    return c


def create_budget_category_group(session, user, budget_id, name, notes=None):
    '''
    Create a new Category Group for the Budget
    '''
    check_session(session)
    check_user(user, needs_profile=True)

    # Load Budget
    b = _load_budget(session, user, budget_id)

    # Add Category Group
    cg = b.add_category_group(
        name=name,
        system=False,
        hidden=False,
        display_order=len(b.groups),
        notes=notes,
    )

    # FIXME: Add Context Manager
    # with session:

    session.add(cg)
    session.commit()

    return cg


def create_budget_category(
    session, user, budget_id, parent_id, name, notes=None, default_budget=None
):
    '''
    Create a new Category for the Budget
    '''
    check_session(session)
    check_user(user, needs_profile=True)

    # Load Budget
    b = _load_budget(session, user, budget_id)

    # Load Category Group
    cg = session.query(Category).get(parent_id)
    if cg is None:
        raise NoResults(f'No category group found with id {parent_id}')

    if cg.parent is not None:
        raise DomainError(
            f'Category {parent_id} is not a Category Group'
        )

    # Add Category Group
    c = b.add_category(
        name=name,
        parent=cg,
        system=False,
        hidden=False,
        display_order=len(cg.children),
        default_budget=default_budget,
        notes=notes,
    )

    # FIXME: Add Context Manager
    # with session:

    session.add(c)
    session.commit()

    return c


def get_category_tree(session, user, budget_id):
    '''
    '''
    check_session(session)
    check_user(user, needs_profile=True)

    # Load Budget
    b = _load_budget(session, user, budget_id)

    # Load Query
    q = session.query(Category)\
        .options(joinedload(Category.children))\
        .filter(
            Category.budget == b,
            Category.parent == None         # noqa: E711
        ) \
        .order_by(Category.display_order)   # noqa: E123

    # Convert to dicts in display sort order
    ret = []
    for grp in q.all():
        ret.append(dict(
            id=grp.id,
            name=grp.name,
            system=grp.system,
            hidden=grp.hidden,
            order=grp.display_order,
            notes=grp.notes,
            children=[dict(
                id=cat.id,
                name=cat.name,
                system=cat.system,
                hidden=cat.hidden,
                order=cat.display_order,
                notes=cat.notes,
                default=cat.default_budget,
            ) for cat in sorted(
                list(grp.children),
                key=lambda x: x.display_order or 0
            )]
        ))

    # Return Category Tree
    return ret


def delete_category(session, user, budget_id, category_id):
    '''Delete a Category or Category Group'''
    check_session(session)
    check_user(user, needs_profile=True)

    # Load Category
    c = _load_category(session, user, budget_id, category_id)

    session.delete(c)
    session.commit()

    return c


def update_category(session, user, budget_id, category_id, **kwargs):
    '''Update a Category or Category Group'''
    check_session(session)
    check_user(user, needs_profile=True)

    # Load Category
    c = _load_category(session, user, budget_id, category_id)

    # Check if the Category is going to move and do that first
    if 'display_order' in kwargs or 'parent_id' in kwargs:
        new_order = kwargs.pop('display_order', c.display_order)
        new_parent = kwargs.pop('parent_id', c.parent_id)
        c = move_category(session, user, budget_id, category_id, new_order, new_parent)

    # Update Name/Visibility/Budget/Notes
    if 'name' in kwargs:
        c.name = kwargs.pop('name')

    if 'hidden' in kwargs:
        c.hidden = kwargs.pop('hidden')

    if 'default_budget' in kwargs:
        c.default_budget = kwargs.pop('default_budget')

    if 'notes' in kwargs:
        c.notes = kwargs.pop('notes')

    # Ensure no unexpected arguments were passed
    if len(kwargs) > 0:
        raise TypeError(
            'Unexpected keyword arguments: {}'.format(', '.join(kwargs.keys()))
        )

    session.add(c)
    session.commit()

    return c


def _update_positions(session, budget_id, parent_id, cur_position, new_position):
    '''
    Update the Display Ordering of categories around the new position. Use
    tailored SQL here for efficiency.
    '''
    if new_position > cur_position:
        # Move items between current and desired position Up
        stmt = categories_table \
            .update() \
            .values(
                display_order=categories_table.c.display_order - 1
            ).where(
                and_(
                    categories_table.c.budget_id == budget_id,
                    categories_table.c.parent_id == parent_id,
                    categories_table.c.display_order > cur_position,
                    categories_table.c.display_order <= new_position
                )
            )

        session.execute(stmt)

    else:
        # Move items between current and desired position Down
        stmt = categories_table \
            .update() \
            .values(
                display_order=categories_table.c.display_order + 1
            ).where(
                and_(
                    categories_table.c.budget_id == budget_id,
                    categories_table.c.parent_id == parent_id,
                    categories_table.c.display_order >= new_position,
                    categories_table.c.display_order < cur_position
                )
            )

        session.execute(stmt)


def move_category(session, user, budget_id, category_id, new_position, new_parent):
    '''
    Update the display ordering of a category within its parent or to another
    parent category.
    '''
    check_session(session)
    check_user(user, needs_profile=True)

    # Check existence and authorization for budget id
    b = _load_budget(session, user, budget_id)

    # Load Category
    cat = session.query(Category).get(category_id)
    if cat is None:
        raise NoResults(f'No category found with id {category_id}')

    cur_position = cat.display_order or 0
    cur_parent = cat.parent_id
    if new_position < 0:
        new_position = 0

    # New Position must be between 0 and number of sibling categories
    n_cats = session \
        .query(Category) \
        .filter(
            Category.budget == b,
            Category.parent_id == new_parent
        ) \
        .count()

    if new_position >= n_cats:
        new_position = n_cats

    # If the Parent is changing, this is a two-step process
    if new_parent != cur_parent:
        # Move to end position within current parent to update old siblings
        _update_positions(session, budget_id, cur_parent, cur_position, 99999)
        # Move to new position within new parent from end
        _update_positions(session, budget_id, new_parent, 99999, new_position)

    else:
        # Move to new position within current parent
        _update_positions(session, budget_id, cur_parent, cur_position, new_position)

    # Update Display Order and Parent for target category
    cat.display_order = new_position
    cat.parent_id = new_parent
    session.add(cat)
    session.commit()

    return cat
