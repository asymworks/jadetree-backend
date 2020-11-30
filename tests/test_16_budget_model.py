# =============================================================================
#
# Jade Tree Personal Budgeting Application | jadetree.io
# Copyright (c) 2020 Asymworks, LLC.  All Rights Reserved.
#
# =============================================================================

import pytest

from jadetree.domain.models import Budget, Category
from jadetree.exc import DomainError


def test_budget_can_add_category_group_simple():
    b = Budget()
    g = b.add_category_group('Test Group')

    assert isinstance(g, Category)
    assert g.name == 'Test Group'
    assert g.budget == b
    assert g.parent is None
    assert g.system is False
    assert g.hidden is False


def test_budget_can_add_category_group_system():
    b = Budget()
    g = b.add_category_group('Test Group', system=True)

    assert isinstance(g, Category)
    assert g.name == 'Test Group'
    assert g.budget == b
    assert g.parent is None
    assert g.system is True
    assert g.hidden is False


def test_budget_can_add_category_group_hidden():
    b = Budget()
    g = b.add_category_group('Test Group', hidden=True)

    assert isinstance(g, Category)
    assert g.name == 'Test Group'
    assert g.budget == b
    assert g.parent is None
    assert g.system is False
    assert g.hidden is True


def test_budget_add_category_group_throws_invalid_name():
    b = Budget()

    with pytest.raises(ValueError) as exc_data:
        b.add_category_group('Test|Group')

    assert 'pipe' in str(exc_data.value)


def test_budget_can_add_category_simple():
    b = Budget()
    g = b.add_category_group('Test Group')
    c = b.add_category('Test Category', g)

    assert isinstance(c, Category)
    assert c.name == 'Test Category'
    assert c.budget == b
    assert c.parent == g
    assert c.system is False
    assert c.hidden is False


def test_budget_can_add_category_system():
    b = Budget()
    g = b.add_category_group('Test Group')
    c = b.add_category('Test Category', g, system=True)

    assert isinstance(c, Category)
    assert c.name == 'Test Category'
    assert c.budget == b
    assert c.parent == g
    assert c.system is True
    assert c.hidden is False


def test_budget_can_add_category_hidden():
    b = Budget()
    g = b.add_category_group('Test Group')
    c = b.add_category('Test Category', g, hidden=True)

    assert isinstance(c, Category)
    assert c.name == 'Test Category'
    assert c.budget == b
    assert c.parent == g
    assert c.system is False
    assert c.hidden is True


def test_budget_add_category_throws_invalid_name():
    b = Budget()
    g = b.add_category_group('Test Group')

    with pytest.raises(ValueError) as exc_data:
        b.add_category('Test|Category', g)

    assert 'pipe' in str(exc_data.value)


def test_budget_add_category_throws_no_parent():
    b = Budget()
    with pytest.raises(DomainError) as exc_data:
        b.add_category('Test Category', None)

    assert 'must belong' in str(exc_data.value)


def test_budget_add_category_throws_invalid_parent():
    b = Budget()
    with pytest.raises(TypeError) as exc_data:
        b.add_category('Test Category', 'Group')

    assert 'type Category' in str(exc_data.value)


def test_budget_add_category_throws_parent_not_group():
    b = Budget()
    g = b.add_category_group('Test Group')
    c = b.add_category('Test Category 1', g)
    with pytest.raises(DomainError) as exc_data:
        b.add_category('Test Category 2', c)

    assert 'must be a Category Group' in str(exc_data.value)


def test_budget_add_categories_empty():
    b = Budget()
    itms = b.add_categories({})

    assert len(b.categories) == 0
    assert len(itms) == 0


def test_budget_add_categories_simple_groups():
    b = Budget()
    itms = b.add_categories([
        { 'name': 'Group 1' },
        { 'name': 'Group 2' },
    ])

    assert len(b.categories) == 2
    assert len(itms) == 2

    cat_info = [(c.name, c.parent.name if c.parent else None, c.system, c.hidden) for c in b.categories]

    assert ('Group 1', None, False, False) in cat_info
    assert ('Group 2', None, False, False) in cat_info


def test_budget_add_categories_complex_groups():
    b = Budget()
    itms = b.add_categories([
        {
            'name': 'Group 1',
            'system': True,
            'hidden': False,
        },
        {
            'name': 'Group 2',
            'system': False,
            'hidden': True,
        }
    ])

    assert len(b.categories) == 2
    assert len(itms) == 2

    cat_info = [(c.name, c.parent.name if c.parent else None, c.system, c.hidden) for c in b.categories]

    assert ('Group 1', None, True, False) in cat_info
    assert ('Group 2', None, False, True) in cat_info


def test_budget_add_categories_throws_bad_list():
    b = Budget()

    with pytest.raises(TypeError) as exc_data:
        b.add_categories([
            {
                'name': 'Group 1',
                'categories': 'Test Category',
                'system': True,
                'hidden': False,
            },
            {
                'name': 'Group 2',
                'categories': [],
                'system': False,
                'hidden': True,
            },
        ])

    assert 'list or tuple' in str(exc_data.value)


def test_budget_add_categories_simple_list():
    b = Budget()
    itms = b.add_categories([
        {
            'name': 'Group 1',
            'categories': ['Category 1', 'Category 2'],
        },
        {
            'name': 'Group 2',
            'categories': ['Category 3'],
        },
    ])

    assert len(b.categories) == 5
    assert len(itms) == 5

    cat_info = [(c.name, c.parent.name if c.parent else None, c.system, c.hidden) for c in b.categories]

    assert ('Group 1', None, False, False) in cat_info
    assert ('Group 2', None, False, False) in cat_info
    assert ('Category 1', 'Group 1', False, False) in cat_info
    assert ('Category 2', 'Group 1', False, False) in cat_info
    assert ('Category 3', 'Group 2', False, False) in cat_info


def test_budget_add_categories_complex_list_1():
    b = Budget()
    itms = b.add_categories([
        {
            'name': 'Group 1',
            'categories': [
                'Category 1',
                {
                    'name': 'Category 2'
                }
            ],
        },
        {
            'name': 'Group 2',
            'categories': ['Category 3'],
        },
    ])

    assert len(b.categories) == 5
    assert len(itms) == 5

    cat_info = [(c.name, c.parent.name if c.parent else None, c.system, c.hidden) for c in b.categories]

    assert ('Group 1', None, False, False) in cat_info
    assert ('Group 2', None, False, False) in cat_info
    assert ('Category 1', 'Group 1', False, False) in cat_info
    assert ('Category 2', 'Group 1', False, False) in cat_info
    assert ('Category 3', 'Group 2', False, False) in cat_info


def test_budget_add_categories_complex_list_2():
    b = Budget()
    itms = b.add_categories([
        {
            'name': 'Group 1',
            'categories': [
                'Category 1',
                {
                    'name': 'Category 2',
                    'system': True,
                    'hidden': False,
                },
            ],
        },
        {
            'name': 'Group 2',
            'categories': ['Category 3'],
        },
    ])

    assert len(b.categories) == 5
    assert len(itms) == 5

    cat_info = [(c.name, c.parent.name if c.parent else None, c.system, c.hidden) for c in b.categories]

    assert ('Group 1', None, False, False) in cat_info
    assert ('Group 2', None, False, False) in cat_info
    assert ('Category 1', 'Group 1', False, False) in cat_info
    assert ('Category 2', 'Group 1', True, False) in cat_info
    assert ('Category 3', 'Group 2', False, False) in cat_info


def test_budget_add_categories_complex():
    b = Budget()
    itms = b.add_categories([
        {
            'name': 'Group 1',
            'categories': [
                'Category 1',
                {
                    'name': 'Category 2',
                    'system': True,
                    'hidden': False,
                }
            ],
        },
        {
            'name': 'Group 2',
            'categories': ['Category 3'],
            'system': False,
            'hidden': True,
        },
    ])

    assert len(b.categories) == 5
    assert len(itms) == 5

    cat_info = [(c.name, c.parent.name if c.parent else None, c.system, c.hidden) for c in b.categories]

    assert ('Group 1', None, False, False) in cat_info
    assert ('Group 2', None, False, True) in cat_info
    assert ('Category 1', 'Group 1', False, False) in cat_info
    assert ('Category 2', 'Group 1', True, False) in cat_info
    assert ('Category 3', 'Group 2', False, False) in cat_info


def test_budget_add_categories_without_name_key():
    b = Budget()

    with pytest.raises(KeyError) as exc_data:
        b.add_categories([
            {
                'name': 'Group 1',
                'categories': [
                    'Category 1',
                    {
                        'system': True,
                        'hidden': False,
                    }
                ],
            },
            {
                'name': 'Group 2',
                'categories': ['Category 3'],
            },
        ])

    assert '"name" key' in str(exc_data.value)


def test_budget_add_categories_with_invalid_category_name_key():
    b = Budget()

    with pytest.raises(TypeError) as exc_data:
        b.add_categories([
            {
                'name': 'Group 1',
                'categories': [
                    'Category 1',
                    {
                        'name': 4,
                    }
                ],
            },
            {
                'name': 'Group 2',
                'categories': ['Category 3'],
            },
        ])

    assert 'name must be a string' in str(exc_data.value)


def test_budget_add_categories_with_invalid_category_name_entry():
    b = Budget()

    with pytest.raises(TypeError) as exc_data:
        b.add_categories([
            {
                'name': 'Group 1',
                'categories': [
                    'Category 1',
                    4
                ],
            },
            {
                'name': 'Group 2',
                'categories': ['Category 3'],
            },
        ])

    assert 'name or a dictionary' in str(exc_data.value)
