"""Report API Schema Definitions.

Jade Tree Personal Budgeting Application | jadetree.io
Copyright (c) 2020 Asymworks, LLC.  All Rights Reserved.
"""

from marshmallow import Schema, ValidationError, fields, validate, validates_schema

import jadetree.api.common.fields as jtFields


class ReportFilterSchema(Schema):
    """Filter fields for a Report."""
    start_date = fields.Date('%Y-%m')
    end_date = fields.Date('%Y-%m')

    categories = jtFields.DelimitedList(fields.Integer(), validate=validate.Length(min=1))
    payees = jtFields.DelimitedList(fields.Integer(), validate=validate.Length(min=1))
    accounts = jtFields.DelimitedList(fields.Integer(), validate=validate.Length(min=1))

    @validates_schema
    def validate_dates(self, data, **kwargs):
        """Ensure the end date is not before the start date."""
        if 'end_date' in data and 'start_date' not in data:
            raise ValidationError('Both Start and End date must be provided')
        if 'start_date' in data and 'end_date' not in data:
            raise ValidationError('Both Start and End date must be provided')

        if 'start_date' in data and data['end_date'] < data['start_date']:
            raise ValidationError('Start date must not be after end date')

        accept_categories = True
        accept_payees = True
        if self.context:
            if 'accept_categories' in self.context and not self.context['accept_categories']:
                accept_categories = False
            if 'accept_payees' in self.context and not self.context['accept_payees']:
                accept_payees = False

        if 'categories' in data and not accept_categories:
            raise ValidationError('Categories may not be provided for this report type')

        if 'payees' in data and not accept_payees:
            raise ValidationError('Payees may not be provided for this report type')


class NetWorthReportSchema(Schema):
    """Net Worth Information for a single month."""
    month = fields.Date()
    assets = fields.Decimal(places=4, as_string=True)
    liabilities = fields.Decimal(places=4, as_string=True)
    currency = fields.Str()


class CategoryReportSchema(Schema):
    """Category spending report schema."""
    category_id = fields.Integer()
    amount = fields.Decimal(places=4, as_string=True)
    currency = fields.Str()


class PayeeReportSchema(Schema):
    """Payee spending report schema."""
    payee_id = fields.Integer()
    amount = fields.Decimal(places=4, as_string=True)
    currency = fields.Str()
