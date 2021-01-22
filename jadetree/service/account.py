# =============================================================================
#
# Jade Tree Personal Budgeting Application | jadetree.io
# Copyright (c) 2020 Asymworks, LLC.  All Rights Reserved.
#
# =============================================================================

# Account Services

from datetime import date
from decimal import Decimal

import arrow

from jadetree.database.queries import q_account_balances, q_account_list
from jadetree.domain.models import Account, Budget, Category, Payee, Transaction
from jadetree.domain.types import AccountRole, AccountType, PayeeRole, TransactionType
from jadetree.exc import NoResults, Unauthorized

from .user import get_initial_payee
from .util import check_session, check_user

__all__ = ('_load_account', 'create_user_account', 'get_user_account_list')


def create_user_account(
    session, user, name, type, currency, balance=None, balance_date=None,
    subtype=None, exchange_rate=None, budget_id=None, memo=None,
):
    '''
    Create an `Account` which belongs to a `User`, which can be either an
    `~AccountType.Asset` or `~AccountType.Liability` account type. The newly
    created account will have its account role set to `~AccountRole.Personal`
    and will be set up with the indicated currency. The ``subtype`` parameter
    may be provided to indicate the specific type of Asset or Liability
    account, but it is not required and is only used as a hint to the user
    interface.

    If the account is to be an on-budget account, the ``budget_id`` parameter
    should be set with the correct budget id; otherwise, the account will be
    set up as an off-budget account, and account transactions will not be
    linked to budget expense accounts.

    If the account has an existing balance, a new `Transaction` will be
    created to set the account's opening balance. If the account is off
    budget, the opposing account for the opening balance will be the user's
    Initial Capital system account.  For on-budget accounts which represent
    debt (Asset accounts with negative balance or Liability accounts with
    positive balance), a new budget expense account will be created for the
    opposing account for the opening balance. This expense account represents
    debt that must be "paid off" by moving income into the expense account.
    Otherwise, the opening balance is put into the budget's Income account.

    If the account has an opening balance and is not in the user's Base
    Currency, the ``exchange_rate`` parameter must be provided with the
    exchange rate on the ``balance_date``.

    A `Payee` will be automatically created for this account to transfer funds
    to and from the account. The `Payee` will be named "Transfer - Account"
    with the account name filled in for Account, and will have the
    `Payee.transfer` and `Payee.system` flags set to True.

    :param session: Database session
    :type session: ~sqlalchemy.orm.session.Session
    :param user:
    :type user: User
    :param name: Name of the new account
    :type name: str
    :param type: Type of the new account
    :type type: AccountType
    :param subtype: Sub-Type of the new account
    :type subtype: AccountSubtype
    :param currency: Type of currency the account holds, as an ISO 4217 code
        or another security code
    :type currency: str
    :param balance: Balance on the account
    :type balance: Decimal
    :param balance_date: Date of the account balance
    :type balance_date: date or Arrow
    :param exchange_rate: Exchange rate of the foreign currency (required if
        :param:`currency` is not the same as the user's base currency). The
        exchange rate should be given as ``Base/Foreign``, or the cost in the
        user's base currency to purchase one unit of the foreign currency.
    :type exchange_rate: Decimal
    :param budget_id: Budget to be linked to the account
    :type budget_id: int
    :param memo: Memo for the opening balance transaction
    :type memo: str
    :returns: New `Account` object
    :rtype: Account
    '''
    check_session(session)
    check_user(user, needs_profile=True)

    if type not in (AccountType.Asset, AccountType.Liability):
        raise ValueError('Account type must be Asset or Liability')

    b = None
    if budget_id is not None:
        b = session.query(Budget).get(budget_id)
        if b is None:
            raise NoResults(
                f'No budget found for id {budget_id}'
            )

    # FIXME: Add Context Manager
    # with session:

    # Create base account object
    a = Account(
        user=user,
        budget=b,
        name=name,
        role=AccountRole.Personal,
        type=type,
        subtype=subtype,
        currency=currency,
        display_order=len([a for a in user.accounts if a.role == AccountRole.Personal]),
    )

    # Create a Payee for this account
    p = Payee(
        user=user,
        account=a,
        category=None,
        name=name,
        role=PayeeRole.Transfer,
        system=True,
        hidden=False
    )

    # If the account has no balance, add and return
    if balance is None or balance == 0:
        session.add(a)
        session.add(p)
        session.commit()

        return a, p, None

    # Ensure balance date is provided
    if not isinstance(balance, Decimal):
        raise TypeError('Balance must be provided as a Decimal amount')
    if balance_date is None:
        raise ValueError('Balance date must be provided to create_user_account')
    if not isinstance(balance_date, (arrow.Arrow, date)):
        raise TypeError('Balance date must be an Arrow or date instance')
    if isinstance(balance_date, arrow.Arrow):
        balance_date = balance_date.date()

    # Otherwise find an Opening Balance account and add a Transaction
    balance_acct = None
    balance_cat = None
    if b is None:
        # Link to user Initial Capital account
        balance_acct = session.query(Account).filter(
            Account.user == user,
            Account.type == AccountType.Capital,
            Account.name == '_initial',
        ).one_or_none()

    else:
        # Link to the Budget Income Account or create a Debt account
        is_debt = (type == AccountType.Asset and balance < 0) or \
                  (type == AccountType.Liability and balance > 0)

        if is_debt:
            # Load or Create the Budget's Pre-JadeTree Debt account
            debt_grp = session.query(Category).filter(
                Category.budget == b,
                Category.parent == None,        # noqa: E711
                Category.name == '_debt',
            ).one_or_none()

            # Pre-created Group
            assert debt_grp is not None

            # Un-Hide the Debt Group
            if debt_grp.hidden:
                debt_grp.hidden = False
                session.add(debt_grp)

            # Create the Expense Category for the opening debt
            balance_cat = b.add_category(name, debt_grp)
            session.add(balance_cat)

            # Load the Budget's Expense Account
            balance_acct = session.query(Account).filter(
                Account.budget == b,
                Account.role == AccountRole.Budget,
                Account.type == AccountType.Expense,
            ).one_or_none()

        else:
            # Assign to Current-Month Income
            balance_cat = session.query(Category).filter(
                Category.budget == b,
                Category.parent != None,        # noqa: E711
                Category.name == '_cur_month',
                Category.system == True,
            ).one_or_none()

            # Load the Budget's Income account
            balance_acct = session.query(Account).filter(
                Account.budget == b,
                Account.role == AccountRole.Budget,
                Account.type == AccountType.Income,
            ).one_or_none()

    if balance_acct is None:
        raise RuntimeError('Failed to load initial balance account')

    # Create the Opening Balance Transaction
    t = Transaction(
        user=user,
        account=a,
        payee=get_initial_payee(session, user),
        date=balance_date,
        currency=currency,
    )

    # Set Foreign Currency Information
    trading_acct = None
    if currency != user.currency:
        if exchange_rate is None or not isinstance(exchange_rate, Decimal):
            raise TypeError(
                'Exchange rate must be a Decimal number for foreign currency '
                'account balances'
            )
        if exchange_rate == 0:
            raise ValueError('Exchange rate must not be zero')

        # Save Foreign Currency Information
        t.foreign_currency = currency
        t.foreign_exchrate = exchange_rate

        # Load Trading Account
        trading_acct = session.query(Account).filter(
            Account.user == user,
            Account.role == AccountRole.System,
            Account.type == AccountType.Trading,
        ).one_or_none()

        if trading_acct is None:
            raise RuntimeError('Failed to load currency trading account')

    # Add Transaction Split
    t.add_split(
        opposing=balance_acct,
        amount=balance,
        currency=currency,
        category=balance_cat,
        trading=trading_acct,
        ttype=TransactionType.System,
        memo=memo,
    )

    # Add to Session and Commit Batch
    session.add(a)
    session.add(p)
    session.add(t)
    session.commit()

    return a, p, t


def _load_account(session, user, account_id):
    '''
    '''
    check_session(session)
    check_user(user, needs_profile=True)

    a = session.query(Account).get(account_id)
    if a is None:
        raise NoResults(f'No account found for id {account_id}')

    if a.user != user:
        raise Unauthorized(
            'Account id {} does not belong to user {}'.format(
                account_id,
                user.email,
            )
        )

    return a


def get_account_balance(session, user, account_id):
    '''
    '''
    check_session(session)
    check_user(user)

    q = q_account_balances(session).filter(account_id=account_id)

    ret = session.execute(q).fetchone()
    if ret is None:
        return None

    return ret.balance


def get_user_account_list(session, user, budget_id=None):
    '''
    '''
    check_session(session)
    check_user(user)

    q = q_account_list(session, user.id)
    if budget_id is not None:
        q = q.filter(Account.budget_id == budget_id)

    ret = []
    for rec in session.execute(q):
        row = dict(rec)

        # Update Balance and Formatted Balance
        row['balance'] = Account.inflow_sign(rec['type']) * rec['balance']
        row['balance_fmt'] = user.format_decimal(row['balance'], row['currency'])

        # Append Result
        ret.append(row)

    return ret
