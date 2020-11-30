# =============================================================================
#
# Jade Tree Personal Budgeting Application | jadetree.io
# Copyright (c) 2020 Asymworks, LLC.  All Rights Reserved.
#
# =============================================================================

from dataclasses import dataclass
from datetime import date
from decimal import Decimal

from jadetree.exc import DomainError

from ..mixins import NotesMixin, TimestampMixin

__all__ = ('Budget', 'Category', 'BudgetEntry')


@dataclass
class BudgetEntry(NotesMixin):
    '''
    '''
    month: date = None
    amount: Decimal = None
    rollover: bool = None

    # Relationship Fields
    budget: 'Budget' = None
    category: 'Category' = None

    # Helpers
    def __repr__(self):
        return '<BudgetEntry "{}" {}-{}>'.format(
            self.category,
            self.month.year,
            self.month.month
        )


@dataclass
class Category(NotesMixin):
    '''
    '''
    name: str = None
    system: bool = None
    hidden: bool = None
    display_order: int = None
    default_budget: Decimal = None

    # Relationship Fields
    budget: 'Budget' = None
    parent: 'Category' = None

    # Domain Logic
    @property
    def is_group(self):
        '''
        Return True if the object is a Category Group, which is indicated by
        having no parent category object.
        '''
        return self.parent is None

    @property
    def path(self):
        '''
        Return the full Category Path, which is the Category Name prefixed
        with the Category Group Name and a pipe, as in "Group|Category".
        Category names may not contain the pipe to ensure the group name and
        expense category name may be split. If the path does not include the
        pipe, the name refers to a Category Group.
        '''
        if self.parent is None:
            return self.name
        return '{}:{}'.format(self.parent.name, self.name)

    @classmethod
    def validate_name(cls, name, system=False):
        if '|' in name:
            raise ValueError(
                'Category and Category Group names may not include the pipe '
                'character ("|")'
            )

        if name[0] == '_' and not system:
            raise ValueError(
                'Category and Category Group names may not start with the '
                'underscore character ("_")'
            )

    # Helpers
    def __repr__(self):
        if self.parent is None:
            return '<Category Group "{}">'.format(self.path)
        return '<Category "{}">'.format(self.path)


@dataclass
class Budget(NotesMixin, TimestampMixin):
    '''
    '''
    name: str = None
    currency: str = None

    # Relationship Fields
    user: 'User' = None                                             # noqa: F821

    # Populated by ORM
    # accounts: List['Account'] = field(default_factory=list)       # noqa: F821
    # categories: List['Category'] = field(default_factory=list)    # noqa: F821
    # groups: List['CategoryGroup'] = field(default_factory=list)   # noqa: F821

    # Domain Logic
    def add_categories(self, category_map, start_display_order=None):
        '''
        Add a list of categories and category groups to the budget. The schema
        is as follows::

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
                'hidden': <bool> ? False,
                'default': <decimal> ? None
            }

        Display ordering is automatically set based on the relative positions
        of the ``group_def`` and ``category_def`` entries within their lists.

        '''
        ret = []
        gi = start_display_order or len(self.groups)
        for g_itm in category_map:
            if not isinstance(g_itm, dict):
                raise TypeError('Category Group items must be dictionaries')
            if 'name' not in g_itm or not isinstance(g_itm['name'], str):
                raise TypeError(
                    'Category Group items must have the "name" key set to a '
                    'string'
                )

            g_name = g_itm['name']
            g_system = g_itm.get('system', False)
            g_hidden = g_itm.get('hidden', False)
            categories = g_itm.get('categories', [])

            if not isinstance(categories, (tuple, list)):
                raise TypeError(
                    'The Category list for a Category Group must be a list or '
                    'tuple'
                )

            ci = 0
            cg = self.add_category_group(g_name, g_system, g_hidden, gi)
            ret.append(cg)
            for itm in categories:
                if not isinstance(itm, (str, dict)):
                    raise TypeError(
                        'Category items with a Category Group must be a '
                        'string with the category name or a dictionary with '
                        'the "name" key included'
                    )

                c_name = itm
                c_system = False
                c_hidden = False
                c_default = None
                if isinstance(itm, dict):
                    if 'name' not in itm:
                        raise KeyError(
                            'Category items specified as a dictionary must '
                            'have the "name" key set with a string value'
                        )

                    c_name = itm['name']
                    c_system = itm.get('system', False)
                    c_hidden = itm.get('hidden', False)
                    c_default = itm.get('default', None)

                if not isinstance(c_name, str):
                    raise TypeError('Category name must be a string')

                ret.append(
                    self.add_category(
                        c_name,
                        cg,
                        c_system,
                        c_hidden,
                        ci,
                        c_default,
                    )
                )

                # Increment Category Counter
                ci = ci + 1

            # Increment Group Counter
            gi = gi + 1

        return ret

    def add_category(
        self, name, parent, system=False, hidden=False, display_order=None,
        default_budget=None, notes=None,
    ):
        '''
        '''
        if parent is None:
            raise DomainError(
                'Budget category must belong to a Category Group'
            )

        if not isinstance(parent, Category):
            raise TypeError('"parent" parameter must be of type Category')

        if parent.parent is not None:
            raise DomainError(
                'Budget category parents must be a Category Group'
            )

        Category.validate_name(name, system)

        c = Category(
            budget=self,
            parent=parent,
            name=name,
            system=system,
            hidden=hidden,
            display_order=display_order,
            default_budget=default_budget,
            notes=notes,
        )

        return c

    def add_category_group(
        self, name, system=False, hidden=False, display_order=None, notes=None
    ):
        '''
        '''
        Category.validate_name(name, system)

        cg = Category(
            budget=self,
            parent=None,
            name=name,
            notes=notes,
            system=system,
            hidden=hidden,
            display_order=display_order,
        )

        return cg

    # Helpers
    def __repr__(self):
        return '<Budget "{}">'.format(self.name)
