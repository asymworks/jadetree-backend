# =============================================================================
#
# Jade Tree Personal Budgeting Application | jadetree.io
# Copyright (c) 2020 Asymworks, LLC.  All Rights Reserved.
#
# =============================================================================

# Ledger Services

from babel.numbers import format_currency
from datetime import date
from decimal import Decimal

from jadetree.database.queries import q_txn_account_lines
from jadetree.domain.models import Account, Category, Transaction, \
    TransactionLine
from jadetree.domain.types import AccountRole, AccountType, TransactionType
from jadetree.exc import DomainError, NoResults, Unauthorized

from .payee import _load_payee
from .util import check_access, check_session, check_user

__all__ = (
    'create_transaction',
    'load_account_lines',
    'load_all_lines',
    'load_single_transaction',
)


def _load_transaction(session, user, transaction_id):
    '''
    '''
    check_session(session)
    check_user(user, needs_profile=True)

    t = session.query(Transaction).get(transaction_id)
    if t is None:
        raise NoResults('No transaction found for id {}'.format(transaction_id))

    if t.user != user:
        raise Unauthorized(
            'Transaction id {} does not belong to user {}'.format(
                transaction_id,
                user.email,
            )
        )

    return t


def _get_txn_type(session, user, acct, transfer_id, category_id, amount):
    '''Determine Transaction Type, Opposing Account, and Category'''
    ttype = None
    opp = None
    if transfer_id is not None:
        if transfer_id == acct.id:
            raise DomainError(
                'Opposing account may not be the same as the source account'
            )

        opp = session.query(Account).get(transfer_id)
        if opp is None:
            raise NoResults('No account found for id {}')

        if opp.user != user:
            raise Unauthorized(
                'Account id {} does not belong to user {}'.format(
                    transfer_id,
                    user.email,
                )
            )

        if opp.role != AccountRole.Personal:
            raise ValueError('Transfer account role must be Personal')
        if opp.type not in (AccountType.Asset, AccountType.Liability):
            raise ValueError(
                'Transfer account type must be Asset or Liability'
            )

        if category_id is not None:
            raise DomainError('Transfer transactions may not have a category')

        ttype = TransactionType.Transfer

    elif Account.inflow_sign(acct) * amount < 0:
        ttype = TransactionType.Outflow

    else:
        ttype = TransactionType.Inflow

    # Load Category
    category = None
    if category_id is not None:
        if acct.budget is None:
            raise DomainError(
                'Transactions from off-budget accounts may not be linked to '
                'Category Groups'
            )

        category = session.query(Category).get(category_id)
        if category is None:
            raise NoResults('No category found for id {}')

        if category.parent is None:
            raise DomainError('Transactions may not be linked to Category Groups')

        if category.budget.user != user:
            raise Unauthorized(
                'Category id {} does not belong to user {}'.format(
                    category_id,
                    user.email,
                )
            )

    # Load Expense or Income Account
    if opp is None:
        if acct.budget is None:
            # Off-Budget Account Transaction
            if ttype == TransactionType.Inflow:
                opp = session.query(Account).filter(
                    Account.user == user,
                    Account.role == AccountRole.System,
                    Account.type == AccountType.Income,
                    Account.name == '_ob_income'
                ).one_or_none()

            else:
                opp = session.query(Account).filter(
                    Account.user == user,
                    Account.role == AccountRole.System,
                    Account.type == AccountType.Expense,
                    Account.name == '_ob_expense'
                ).one_or_none()

        elif category and category.parent.name == '_income':
            # On-Budget Income (use category Budget)
            opp = session.query(Account).filter(
                Account.user == user,
                Account.budget == category.budget,
                Account.role == AccountRole.Budget,
                Account.type == AccountType.Income
            ).one_or_none()

        elif category and category.parent.name != '_income':
            # On-Budget Expense (use category Budget)
            opp = session.query(Account).filter(
                Account.user == user,
                Account.budget == category.budget,
                Account.role == AccountRole.Budget,
                Account.type == AccountType.Expense
            ).one_or_none()

        else:
            # Use Account Budget
            opp = session.query(Account).filter(
                Account.user == user,
                Account.budget == acct.budget,
                Account.role == AccountRole.Budget,
                Account.type == AccountType.Expense
            ).one_or_none()

        if opp is None:
            raise RuntimeError('Failed to load opposing account')

    # Return Type, Opposing Account, and Category
    return ttype, opp, category


def _get_trading(session, user, txn, exchange_rate=None):
    '''
    Look up the `~AccountType.Trading` account for a transaction. If the
    transaction does not require a trading account, the function returns None.
    '''
    trading_acct = None
    if txn.currency != user.currency:
        if exchange_rate is None or not isinstance(exchange_rate, Decimal):
            raise TypeError(
                'Exchange rate must be a Decimal number for foreign currency '
                'account balances'
            )

        if exchange_rate == 0:
            raise ValueError('Exchange rate must not be zero')

        txn.foreign_currency = txn.currency
        txn.foreign_exchrate = exchange_rate

        # Load Trading Account
        trading_acct = session.query(Account).filter(
            Account.user == user,
            Account.role == AccountRole.System,
            Account.type == AccountType.Trading,
        ).one_or_none()

        if trading_acct is None:
            raise RuntimeError('Failed to load currency trading account')

    return trading_acct


def _parse_splits(session, user, acct, amount, currency, splits):
    '''

    Returns a list of tuples of the form
    * line_ttype: `TransactionType`
    * line_opposing: `Account`
    * line_category: `Category`
    * line_amount: `Decimal`
    * line_memo: `str`

    :returns: list of parsed split items
    :rtype: list
    '''
    split_lines = []
    for line in splits:
        if 'amount' not in line:
            raise KeyError('Split dictionaries must contain the "amount" key')
        if not isinstance(line['amount'], Decimal):
            raise ValueError('Split amounts must be Decimal type')

        if 'category_id' not in line and 'transfer_id' not in line:
            raise KeyError(
                'Split dictionaries must contain either the "category_id" or '
                'the "transfer_id" key'
            )

        category_id = line.get('category_id', None)
        transfer_id = line.get('transfer_id', None)
        line_amt = line.get('amount')
        line_memo = line.get('memo', None)

        # Determine Transaction Type, Opposing Account, and Category
        ttype, opp, category = _get_txn_type(
            session, user, acct, transfer_id, category_id, line_amt
        )

        # Append to Split Information
        split_lines.append((ttype, opp, category, line_amt, line_memo))

    # Ensure split amounts sum to transaction total amount
    split_sum = sum([ln[3] for ln in split_lines])
    if split_sum != amount:
        raise ValueError(
            'Sum of transaction split amounts does not equal total '
            'transaction amount {} != {}'.format(
                format_currency(split_sum, currency),
                format_currency(amount, currency),
            )
        )

    # Return Lines
    return split_lines


def create_transaction(
    session, user, account_id, date, payee_id, amount, splits, currency=None,
    memo=None, check=None, exchange_rate=None
):
    '''
    '''
    check_session(session)
    check_user(user, needs_profile=True)

    # Load and Verify the Source Account
    a = session.query(Account).get(account_id)
    if a is None:
        raise NoResults('No account found for id {}'.format(account_id))

    if a.user != user:
        raise Unauthorized(
            'Account id {} does not belong to user {}'.format(
                account_id,
                user.email,
            )
        )

    # Must be relative to a Personal Asset or Liability Account
    if a.role != AccountRole.Personal:
        raise ValueError('Transaction account role must be Personal')
    if a.type not in (AccountType.Asset, AccountType.Liability):
        raise ValueError('Transaction account type must be Asset or Liability')

    # Default to account currency (NB: _not_ necessarily base currency)
    if currency is None:
        currency = a.currency

    # Load Payee
    payee = _load_payee(session, user, payee_id)

    # Create Transaction
    t = Transaction(
        user=user,
        account=a,
        date=date,
        payee=payee,
        currency=currency,
        memo=memo,
        check=check,
    )

    # Load Split Information and Create Transaction Lines
    split_lines = _parse_splits(session, user, a, amount, currency, splits)
    trading_acct = _get_trading(session, user, t, exchange_rate)

    # Add Lines
    for ln_ttype, ln_opp, ln_cat, ln_amt, ln_memo in split_lines:
        ln, entries, lines = t.add_split(
            opposing=ln_opp,
            amount=ln_amt,
            currency=t.currency,
            category=ln_cat,
            trading=trading_acct,
            memo=ln_memo,
            ttype=ln_ttype,
        )

    # Add to Session and Commit
    session.add(t)
    session.commit()

    return t


def _load_transaction_lines(session, q):
    '''
    '''
    all_cols = set([c.key for c in q.selectable.c])
    split_keys = set([c for c in all_cols if c.startswith('split_')])
    txn_keys = all_cols - set(split_keys)

    # Group Results by TransactionLine
    grouped = dict()
    id_list = []
    for rec in session.execute(q):
        row = dict(rec)
        line_id = row['line_id']
        line_item = dict([(k, row[k]) for k in txn_keys])
        split_item = dict([(k[6:], row[k]) for k in split_keys])

        if line_id in grouped:
            grouped[line_id]['splits'].append(split_item)
        else:
            grouped[line_id] = line_item
            grouped[line_id]['splits'] = [split_item]
            id_list.append(line_id)

    # Readout by Query Result Order
    return [grouped[id] for id in id_list]


def load_all_lines(session, user, order_by=None, reverse=False):
    '''
    Requires SQLite 3.25.0 or later to use Window Functions
    '''
    check_session(session)
    check_user(user, needs_profile=True)

    q = q_txn_account_lines(session, reverse=reverse) \
        .filter(Account.user == user)

    # Apply Ordering and Pagination
    if order_by is not None:
        q = q.order_by(None).order_by(order_by)

    # Return as LedgerTransactionLine items
    return _load_transaction_lines(session, q)


def load_account_lines(session, user, account_id, order_by=None, reverse=False):
    '''
    Requires SQLite 3.25.0 or later to use Window Functions
    '''
    check_session(session)
    check_user(user, needs_profile=True)

    a = session.query(Account).get(account_id)
    if a is None:
        raise NoResults('No account found for id {}'.format(account_id))

    if a.user != user:
        raise Unauthorized(
            'Account id {} does not belong to user {}'.format(
                account_id,
                user.email,
            )
        )

    # Load Ledger Information
    q = q_txn_account_lines(session, account_id, reverse=reverse)
    if order_by is not None:
        q = q.order_by(None).order_by(order_by)

    # Return as LedgerTransactionLine items
    return _load_transaction_lines(session, q)


def load_single_transaction(session, user, transaction_id):
    '''Load a single Transaction into the TransactionSchema interface'''
    t = _load_transaction(session, user, transaction_id)

    q = q_txn_account_lines(session) \
        .filter(Account.id == Transaction.account_id) \
        .filter(Transaction.id == t.id)

    # Return as LedgerTransactionLine items
    return _load_transaction_lines(session, q)


def load_reconcilable_lines(session, user, account_id, order_by=None, reverse=False):
    '''Load Transactions that are not yet reconciled'''
    check_session(session)
    check_user(user, needs_profile=True)

    a = session.query(Account).get(account_id)
    if a is None:
        raise NoResults('No account found for id {}'.format(account_id))

    if a.user != user:
        raise Unauthorized(
            'Account id {} does not belong to user {}'.format(
                account_id,
                user.email,
            )
        )

    # Load Ledger Information
    q = q_txn_account_lines(session, account_id, reverse=reverse, reconciled=False)
    if order_by is not None:
        q = q.order_by(None).order_by(order_by)

    # Return as LedgerTransactionLine items
    return _load_transaction_lines(session, q)


def update_transaction(session, user, transaction_id, **kwargs):
    '''
    '''
    check_session(session)
    check_user(user, needs_profile=True)

    txn = session.query(Transaction).get(transaction_id)
    if txn is None:
        raise NoResults('No transaction found for id {}'.format(transaction_id))

    check_access(user, txn)

    # FIXME: Context Manager
    # with session:

    if len(kwargs) == 0:
        return txn

    # Handle Updating Date
    if 'date' in kwargs:
        txn.date = kwargs.pop('date')

    # Handle Updating Payee
    if 'payee_id' in kwargs:
        payee_id = kwargs.pop('payee_id', None)
        txn.payee = _load_payee(session, user, payee_id)

    # Handle Updating Memo
    if 'memo' in kwargs:
        txn.memo = kwargs.pop('memo')

    # Handle Updating Check
    if 'check' in kwargs:
        txn.check = kwargs.pop('check')

    # Remaining updates will potentially require re-creating lines
    new_splits = None
    new_amount = None

    # Handle updating a Split Transaction
    if 'splits' in kwargs:
        for ln in txn.lines:
            if ln.reconciled:
                raise DomainError('Cannot modify a reconciled transaction')

        new_amount = kwargs.pop('amount', txn.amount)
        new_currency = kwargs.pop('currency', txn.currency)
        new_splits = kwargs.pop('splits')
        split_lines = _parse_splits(
            session, user, txn.account, new_amount, new_currency, new_splits
        )

        # Clear existing splits
        txn.lines.clear()
        txn.splits.clear()

        # Add new Split Lines
        trading_acct = _get_trading(session, user, txn, txn.foreign_exchrate)

        # Add Lines
        for ln_ttype, ln_opp, ln_cat, ln_amt, ln_memo in split_lines:
            ln, entries, lines = txn.add_split(
                opposing=ln_opp,
                amount=ln_amt,
                currency=txn.currency,
                category=ln_cat,
                trading=trading_acct,
                memo=ln_memo,
                ttype=ln_ttype,
            )

    # Ensure no unexpected arguments were passed
    if len(kwargs) > 0:
        raise TypeError(
            'Unexpected keyword arguments: {}'.format(', '.join(kwargs.keys()))
        )

    session.add(txn)
    session.commit()

    return txn


def clear_transaction(
    session, user, transaction_id, line_id=None, account_id=None, cleared=None
):
    '''Update the transaction cleared status.'''
    if line_id is None and account_id is None:
        raise TypeError('"line_id" or "account_id" must be set')
    if cleared is None:
        raise TypeError('"cleared" must be set to True or False')

    txn = _load_transaction(session, user, transaction_id)
    line = None
    if line_id is not None:
        for ln in txn.lines:
            if ln.id == line_id:
                line = ln
                break

        if line is None:
            raise DomainError('Line {} does not exist in Transaction {}'.format(
                line_id, transaction_id
            ))

        if account_id is not None and line.account.id != account_id:
            raise DomainError('Line {} is not linked to Account {}'.format(
                line_id, account_id
            ))

    else:
        for ln in txn.lines:
            if ln.account.id == account_id:
                line = ln
                break

        if line is None:
            raise DomainError(
                'Line for Account {} does not exist in Transaction {}'.format(
                    account_id, transaction_id
                )
            )

        if line_id is not None and line.account.id != account_id:
            raise DomainError('Line {} is not linked to Account {}'.format(
                line_id, account_id
            ))

    if line.reconciled:
        raise DomainError(
            'Cannot change the cleared status of a reconciled transaction'
        )

    if cleared and not line.cleared:
        line.cleared = True
        line.cleared_at = date.today()

    if not cleared:
        line.cleared = False
        line.cleared_at = None

    session.add(line)
    session.commit()

    return txn


def reconcile_account(
    session, user, account_id, statement_date, statement_balance
):
    '''Reconcile an Account with a Statement Date and Balance

    The statement balance must equal the sum of the amounts of the transaction
    lines on this Account that are cleared. If they do not match, a DomainError
    exception is raised. If the amounts do match, the cleared lines are marked
    as reconciled.

    Args:
        session (Session): SQLalchemy Database Session
        user (User): Jade Tree User
        account_id (int): Account Id
        statement_date (date): Statement Date
        statement_balance (Decimal): Statement Balance

    Returns:
        list: List of newly reconciled Transactions
    '''
    check_session(session)
    check_user(user, needs_profile=True)

    a = session.query(Account).get(account_id)
    if a is None:
        raise NoResults('No account found for id {}'.format(account_id))

    if a.user != user:
        raise Unauthorized(
            'Account id {} does not belong to user {}'.format(
                account_id,
                user.email,
            )
        )

    # Get Cleared Transactions
    txns = session.query(TransactionLine).join(
        Transaction, Transaction.id == TransactionLine.transaction_id,
    ).filter(
        TransactionLine.account == a,
        TransactionLine.cleared == True,        # noqa: E712
        Transaction.date <= statement_date,
    ).all()

    # Sum Transactions
    cleared_balance = sum([t.amount for t in txns])
    if cleared_balance != statement_balance:
        raise DomainError(
            'Statement balance of {} does not match cleared balance of {}'.format(
                format_currency(statement_balance, a.currency),
                format_currency(cleared_balance, a.currency),
            )
        )

    # Reconcile Transactions
    new_txns = [t for t in txns if not t.reconciled]
    for t in new_txns:
        t.reconciled = True
        t.reconciled_at = statement_date

    session.add_all(new_txns)
    session.commit()

    return new_txns
