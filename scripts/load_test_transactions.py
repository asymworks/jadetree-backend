#
# Load Base DB Information following database re-creation
#

import os, sys
root_path = os.path.dirname(os.path.abspath(__file__))
jt_path = os.path.abspath(os.path.join(root_path, '..'))
sys.path.append(jt_path)

from datetime import date
from decimal import Decimal

from jadetree.factory import create_app
from jadetree.database import db
from jadetree.domain.models import Account, Budget, BudgetEntry, Category, \
    Payee, User
from jadetree.domain.types import AccountRole, AccountType, AccountSubtype, \
    PayeeRole, TransactionType
from jadetree.service import user as user_service
from jadetree.service import account as account_service
from jadetree.service import budget as budget_service
from jadetree.service import ledger as ledger_service


def create_accounts(app, user_id, budget_id):
    with app.app_context():
        u = db.session.query(User).get(user_id)
        a_ck = account_service.create_user_account(
            session=db.session,
            user=u,
            budget_id=budget_id,
            name='Checking',
            type=AccountType.Asset,
            subtype=AccountSubtype.Checking,
            currency='USD',
            balance=Decimal('10000'),
            balance_date=date(2020, 1, 1)
        )
        a_sv = account_service.create_user_account(
            session=db.session,
            user=u,
            budget_id=budget_id,
            name='Savings',
            type=AccountType.Asset,
            subtype=AccountSubtype.Savings,
            currency='USD',
            balance=Decimal('42000'),
            balance_date=date(2020, 1, 1)
        )
        a_cc = account_service.create_user_account(
            session=db.session,
            user=u,
            budget_id=budget_id,
            name='Visa',
            type=AccountType.Liability,
            subtype=AccountSubtype.CreditCard,
            currency='USD',
            balance=Decimal('2000'),
            balance_date=date(2020, 1, 1)
        )

        return a_ck, a_sv, a_cc


def create_transactions(u, b, a_ck, a_sv, a_cc):
    c_groceries = db.session.query(Category).filter(Category.name=='Groceries').one()
    c_household = db.session.query(Category).filter(Category.name=='Household Goods').one()
    c_rent = db.session.query(Category).filter(Category.name=='Rent/Mortgage').one()
    c_fuel = db.session.query(Category).filter(Category.name=='Fuel').one()
    c_money = db.session.query(Category).filter(Category.name=='Spending Money').one()

    p_vons = Payee(user=u, name='Vons')
    p_target = Payee(user=u, name='Target')
    p_lazyacres = Payee(user=u, name='Lazy Acres')
    p_traderjoes = Payee(user=u, name='Trader Joes')
    p_exxon = Payee(user=u, name='Exxon Mobil')
    p_landlord = Payee(user=u, name='Landlord')

    be_groc_jan = BudgetEntry(budget=b, category=c_groceries, month=date(2020, 1, 1), amount=Decimal(200))
    be_groc_feb = BudgetEntry(budget=b, category=c_groceries, month=date(2020, 2, 1), amount=Decimal(200))

    be_sm_jan = BudgetEntry(budget=b, category=c_money, month=date(2020, 1, 1), amount=Decimal(50))
    be_sm_feb = BudgetEntry(budget=b, category=c_money, month=date(2020, 2, 1), amount=Decimal(60))

    db.session.add_all([be_groc_jan, be_groc_feb, be_sm_jan, be_sm_feb])
    db.session.add_all([p_vons, p_lazyacres, p_target])
    db.session.commit()

    # Grocery Purchases
    ledger_service.create_transaction(
        session=db.session,
        user=u,
        account_id=a_cc.id,
        category_id=c_groceries.id,
        date=date(2020, 1, 2),
        amount=Decimal(50),
        payee_id=p_vons.id,
    )

    ledger_service.create_transaction(
        session=db.session,
        user=u,
        account_id=a_cc.id,
        category_id=c_groceries.id,
        date=date(2020, 1, 9),
        amount=Decimal(70),
        payee_id=p_lazyacres.id,
    )

    ledger_service.create_transaction(
        session=db.session,
        user=u,
        account_id=a_cc.id,
        category_id=c_groceries.id,
        date=date(2020, 1, 16),
        amount=Decimal(45),
        payee_id=p_vons.id,
    )

    ledger_service.create_transaction(
        session=db.session,
        user=u,
        account_id=a_cc.id,
        category_id=c_groceries.id,
        date=date(2020, 1, 23),
        amount=Decimal(55),
        payee_id=p_traderjoes.id,
    )

    ledger_service.create_transaction(
        session=db.session,
        user=u,
        account_id=a_cc.id,
        category_id=c_fuel.id,
        date=date(2020, 1, 23),
        amount=Decimal(20),
        payee_id=p_exxon.id,
    )

    ledger_service.create_transaction(
        session=db.session,
        user=u,
        account_id=a_cc.id,
        category_id=c_groceries.id,
        date=date(2020, 2, 4),
        amount=Decimal(60),
        payee_id=p_vons.id,
    )

    ledger_service.create_transaction(
        session=db.session,
        user=u,
        account_id=a_cc.id,
        category_id=c_household.id,
        date=date(2020, 2, 5),
        amount=Decimal(80),
        payee_id=p_target.id,
    )

    # Split Purchase
    ledger_service.create_split_transaction(
        session=db.session,
        user=u,
        account_id=a_cc.id,
        date=date(2020, 1, 24),
        amount=Decimal(50),
        payee_id=p_target.id,
        splits=[
            { 'amount': Decimal(30), 'category_id': c_household.id },
            { 'amount': Decimal(20), 'category_id': c_groceries.id },
        ]
    )

    # Transfer to Savings
    ledger_service.create_transaction(
        session=db.session,
        user=u,
        account_id=a_ck.id,
        transfer_id=a_sv.id,
        payee_id=a_sv.payee.id,
        date=date(2020, 1, 17),
        amount=Decimal(50),
    )

    # Rent Payment
    ledger_service.create_transaction(
        session=db.session,
        user=u,
        account_id=a_ck.id,
        category_id=c_rent.id,
        date=date(2020, 1, 31),
        amount=Decimal(-2000),
        payee_id=p_landlord.id,
        memo='February 2020 Rent',
    )


if __name__ == '__main__':
    app = create_app('../config/dev.py')
    with app.app_context():
        u = db.session.query(User).one()
        b = db.session.query(Budget).one()
        a_ck, a_sv, a_cc = create_accounts(app, u.id, b.id)

        a_ck = db.session.query(Account).filter(Account.role==AccountRole.Personal, Account.name=='Checking').one()
        a_sv = db.session.query(Account).filter(Account.role==AccountRole.Personal, Account.name=='Savings').one()
        a_cc = db.session.query(Account).filter(Account.role==AccountRole.Personal, Account.name=='Visa').one()

        c_groceries = db.session.query(Category).filter(Category.name=='Groceries').one()
        c_household = db.session.query(Category).filter(Category.name=='Household Goods').one()
        c_rent = db.session.query(Category).filter(Category.name=='Rent/Mortgage').one()
        c_fuel = db.session.query(Category).filter(Category.name=='Fuel').one()
        c_money = db.session.query(Category).filter(Category.name=='Spending Money').one()

        p_vons = Payee(user=u, name='Vons')
        p_target = Payee(user=u, name='Target')
        p_lazyacres = Payee(user=u, name='Lazy Acres')
        p_traderjoes = Payee(user=u, name='Trader Joes')
        p_exxon = Payee(user=u, name='Exxon Mobil')
        p_landlord = Payee(user=u, name='Landlord')

        be_groc_jan = BudgetEntry(budget=b, category=c_groceries, month=date(2020, 1, 1), amount=Decimal(200))
        be_groc_feb = BudgetEntry(budget=b, category=c_groceries, month=date(2020, 2, 1), amount=Decimal(200))

        be_sm_jan = BudgetEntry(budget=b, category=c_money, month=date(2020, 1, 1), amount=Decimal(50))
        be_sm_feb = BudgetEntry(budget=b, category=c_money, month=date(2020, 2, 1), amount=Decimal(60))

        db.session.add_all([be_groc_jan, be_groc_feb, be_sm_jan, be_sm_feb])
        db.session.add_all([p_vons, p_lazyacres, p_target, p_traderjoes, p_exxon, p_landlord])
        db.session.commit()

        # Grocery Purchases
        ledger_service.create_transaction(
            session=db.session,
            user=u,
            account_id=a_cc.id,
            category_id=c_groceries.id,
            date=date(2020, 1, 2),
            amount=Decimal(50),
            payee_id=p_vons.id,
        )

        ledger_service.create_transaction(
            session=db.session,
            user=u,
            account_id=a_cc.id,
            category_id=c_groceries.id,
            date=date(2020, 1, 9),
            amount=Decimal(70),
            payee_id=p_lazyacres.id,
        )

        ledger_service.create_transaction(
            session=db.session,
            user=u,
            account_id=a_cc.id,
            category_id=c_groceries.id,
            date=date(2020, 1, 16),
            amount=Decimal(45),
            payee_id=p_vons.id,
        )

        ledger_service.create_transaction(
            session=db.session,
            user=u,
            account_id=a_cc.id,
            category_id=c_groceries.id,
            date=date(2020, 1, 23),
            amount=Decimal(55),
            payee_id=p_traderjoes.id,
        )

        ledger_service.create_transaction(
            session=db.session,
            user=u,
            account_id=a_cc.id,
            category_id=c_fuel.id,
            date=date(2020, 1, 23),
            amount=Decimal(20),
            payee_id=p_exxon.id,
        )

        ledger_service.create_transaction(
            session=db.session,
            user=u,
            account_id=a_cc.id,
            category_id=c_groceries.id,
            date=date(2020, 2, 4),
            amount=Decimal(60),
            payee_id=p_vons.id,
        )

        ledger_service.create_transaction(
            session=db.session,
            user=u,
            account_id=a_cc.id,
            category_id=c_household.id,
            date=date(2020, 2, 5),
            amount=Decimal(80),
            payee_id=p_target.id,
        )

        # Split Purchase
        ledger_service.create_split_transaction(
            session=db.session,
            user=u,
            account_id=a_cc.id,
            date=date(2020, 1, 24),
            amount=Decimal(50),
            payee_id=p_target.id,
            splits=[
                { 'amount': Decimal(30), 'category_id': c_household.id },
                { 'amount': Decimal(20), 'category_id': c_groceries.id },
            ]
        )

        # Transfer to Savings
        ledger_service.create_transaction(
            session=db.session,
            user=u,
            account_id=a_ck.id,
            transfer_id=a_sv.id,
            payee_id=a_sv.payee.id,
            date=date(2020, 1, 17),
            amount=Decimal(50),
        )

        # Rent Payment
        ledger_service.create_transaction(
            session=db.session,
            user=u,
            account_id=a_ck.id,
            category_id=c_rent.id,
            date=date(2020, 1, 31),
            amount=Decimal(-2000),
            payee_id=p_landlord.id,
            memo='February 2020 Rent',
        )
