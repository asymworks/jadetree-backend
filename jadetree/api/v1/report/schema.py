"""Report API Schema Definitions.

Jade Tree Personal Budgeting Application | jadetree.io
Copyright (c) 2020 Asymworks, LLC.  All Rights Reserved.
"""

from marshmallow import Schema, fields


class NetWorthReportSchema(Schema):
    """Net Worth Information for a single month."""
    month = fields.Date()
    assets = fields.Decimal(places=4, as_string=True)
    liabilities = fields.Decimal(places=4, as_string=True)
    currency = fields.Str()
