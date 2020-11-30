#
# Load Base DB Information following database re-creation
#

import os, sys
root_path = os.path.dirname(os.path.abspath(__file__))
jt_path = os.path.abspath(os.path.join(root_path, '..'))
sys.path.append(jt_path)

from arrow import Arrow
from decimal import Decimal

from jadetree.factory import create_app
from jadetree.database import db
from jadetree.domain.models import User
from jadetree.domain.types import AccountType, AccountSubtype
from jadetree.service import account as account_service
from jadetree.service import auth as auth_service
from jadetree.service import budget as budget_service
from jadetree.service import user as user_service


YNAB4_MY_CATEGORIES = [
    {
        'name': 'Monthly Bills',
        'categories': [
            'Rent/Mortgage',
            'Phone',
            'Internet (FiOS)',
            'TV (Netflix, Sling, etc)',
            'Electricity',
            'Natural Gas',
            'Internet Services',
            'Patreon',
            'Pimsleur',
        ]
    },
    {
        'name': 'Yearly Expenses',
        'categories': [
            'Car Registration',
            'Car Insurance',
            'Renter\'s Insurance',
            'Life Insurance',
            'Amazon Prime',
            'DAN Insurance',
            'United CC Fee',
            'Safe Deposit Box',
            'CalTopo',
            'Strava Premium',
            'Digital Ocean',
            'Ars Technica++',
        ]
    },
    {
        'name': 'Everyday Expenses',
        'categories': [
            'Groceries',
            'Fuel',
            'Spending Money',
            'Restaurants',
            'Clothing',
            'Laundry',
            'Household Goods',
            'Fast Food',
            'Travel M&IE',
        ]
    },
    {
        'name': 'Rainy Day Funds',
        'categories': [
            'Emergency Fund',
            'Car Maintentance',
            'Medical',
            'Travel Fund',
            'Large Purchases',
            'Entertainment',
            'Gifts',
            'Work Stuff',
            'Charitable',
        ]
    },
    {
        'name': 'Savings Goals',
        'categories': [
            'Home Down Payment',
            'Investments',
        ]
    }
]


def create_user(app):
    with app.app_context():
        u = auth_service.register_user(db.session, 'test@jadetree.io', 'hunter2JT')
        u = auth_service.confirm_user(db.session, u.uid_hash)

        return u.id


def setup_user(app, uid):
    with app.app_context():
        u = db.session.query(User).get(uid)
        user_service.setup_user_profile(db.session, u, 'en', 'en_US', 'USD')


def create_budget(app, uid):
    with app.app_context():
        u = db.session.query(User).get(uid)
        b = budget_service.create_budget(
            user=u,
            name='Test Budget',
            session=db.session,
            categories=YNAB4_MY_CATEGORIES,
        )

        return b.id


if __name__ == '__main__':
    app = create_app()
    uid = create_user(app)

    # Setup Profile
    setup_user(app, uid)

    # Create Budget
    create_budget(app, uid)
