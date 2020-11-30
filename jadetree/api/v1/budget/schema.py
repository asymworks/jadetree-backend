# =============================================================================
#
# Jade Tree Personal Budgeting Application | jadetree.io
# Copyright (c) 2020 Asymworks, LLC.  All Rights Reserved.
#
# =============================================================================

from marshmallow import Schema, fields, post_dump, pre_dump, validate


class CategoryBaseSchema(Schema):
    '''
    '''
    id = fields.Int()
    name = fields.Str()
    system = fields.Bool()
    hidden = fields.Bool()
    currency = fields.Str()
    notes = fields.Str(allow_none=True)
    display_order = fields.Int()
    parent_id = fields.Int()

    @post_dump(pass_original=True)
    def post_dump(self, data, original_data, **kwargs):
        '''Automatically inject Budget Currency'''
        if 'currency' not in data and original_data and original_data.budget:
            data['currency'] = original_data.budget.currency
        return data


class CategorySchema(CategoryBaseSchema):
    '''Schema for Budget Category'''
    default_budget = fields.Decimal(places=4, as_string=True)


class CategoryGroupSchema(CategoryBaseSchema):
    '''Schema for Budget Category Group'''
    children = fields.List(fields.Nested(CategorySchema))


class OverspentCategorySchema(Schema):
    '''
    '''
    id = fields.Int()
    name = fields.Str()
    parent_name = fields.Str()
    budget = fields.Decimal(places=4, as_string=True)
    outflow = fields.Decimal(places=4, as_string=True)
    overspend = fields.Decimal(places=4, as_string=True)


class BudgetSchema(Schema):
    '''
    '''
    id = fields.Int()
    name = fields.Str(required=True)
    currency = fields.Str(required=True)
    categories = fields.List(fields.Nested(CategoryGroupSchema))
    notes = fields.Str()

    @pre_dump
    def pre_dump(self, obj, **kwargs):
        '''
        Filter Category List to only those with no parent, so that child
        categories are not returned twice
        '''
        return dict(
            id=obj.id,
            name=obj.name,
            currency=obj.currency,
            categories=[c for c in obj.categories if not c.parent],
            notes=obj.notes,
        )


class BudgetUpdateSchema(Schema):
    '''
    '''
    name = fields.Str(allow_none=True)
    notes = fields.Str(allow_none=True)


class CategoryDetailSchema(Schema):
    '''
    '''
    entry_id = fields.Int()
    category_id = fields.Int()
    parent_id = fields.Int()
    budget = fields.Decimal(places=4, as_string=True)
    outflow = fields.Decimal(places=4, as_string=True)
    balance = fields.Decimal(places=4, as_string=True)
    rollover = fields.Bool()
    carryover = fields.Decimal(places=4, as_string=True)
    overspend = fields.Decimal(places=4, as_string=True)
    num_transactions = fields.Int()
    notes = fields.Str()


class BudgetEntrySchema(Schema):
    '''
    Schema for `BudgetEntry` containing a budget entry for a single category
    for a single month/year.
    '''
    id = fields.Int(dump_only=True)
    month = fields.Date(required=True)
    category_id = fields.Int(required=True)

    amount = fields.Decimal(required=True, places=4, as_string=True)
    currency = fields.Str()
    default = fields.Bool(default=False)
    rollover = fields.Bool()
    notes = fields.Str()

    @post_dump(pass_original=True)
    def post_dump(self, data, original_data, **kwargs):
        '''Automatically inject Budget Currency'''
        if 'currency' not in data and original_data.budget is not None:
            data['currency'] = original_data.budget.currency
        return data


class BudgetEntryUpdateSchema(Schema):
    '''Schema to update a `BudgetEntry`'''
    amount = fields.Decimal(places=4, as_string=True)
    default = fields.Bool(load_only=True, default=False)
    rollover = fields.Bool()
    notes = fields.Str(allow_none=True)


class BudgetDataSchema(Schema):
    '''Schema for Budget Data for a single Month'''
    categories = fields.List(fields.Nested(CategoryDetailSchema))
    entries = fields.List(fields.Nested(BudgetEntrySchema))
    last_available = fields.Decimal(places=4, as_string=True)
    last_overspent = fields.Decimal(places=4, as_string=True)
    overspent = fields.Decimal(places=4, as_string=True)
    income = fields.Decimal(places=4, as_string=True)
    budgeted = fields.Decimal(places=4, as_string=True)
    available = fields.Decimal(places=4, as_string=True)
    currency = fields.Str()


class BudgetQueryArgsSchema(Schema):
    '''Month/Year Query Arguments for Budget Detail View'''
    month = fields.Int(validate=validate.Range(min=1, max=12, error='Month must be between 1 and 12'))
    year = fields.Int(validate=validate.Range(min=1900), error='Year must be greater than 1900')
