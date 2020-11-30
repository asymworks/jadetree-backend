# =============================================================================
#
# Jade Tree Personal Budgeting Application | jadetree.io
# Copyright (c) 2020 Asymworks, LLC.  All Rights Reserved.
#
# =============================================================================

# Payee Services

from jadetree.domain.models import Payee, Transaction, TransactionSplit
from jadetree.domain.types import PayeeRole
from jadetree.exc import DomainError, NoResults, Unauthorized

from .account import _load_account
from .budget import _load_category
from .util import check_session, check_user

__all__ = ('get_payee_list', '_load_payee', 'get_payee_last_txn')


def get_payee_list(session, user):
    '''
    :param session: Database session
    :type session: ~sqlalchemy.orm.session.Session
    :param user:
    :type user: User
    :returns: List of `Payee` objects for the user that are in the
        `PayeeRole.Expense` or `Payee.Transfer` role and that have the
        `Payee.visible` flag set to True
    :rtype: list
    '''
    q = session\
        .query(Payee) \
        .filter(
            Payee.user == user,
            Payee.role.in_((PayeeRole.Expense, PayeeRole.Transfer)),
            Payee.hidden == False) \
        .order_by(Payee.role, Payee.name)       # noqa: E712

    # Return Payee List
    return q.all()


def _load_payee(session, user, payee_id):
    '''
    '''
    check_session(session)
    check_user(user, needs_profile=True)

    p = session.query(Payee).get(payee_id)
    if p is None:
        raise NoResults('No payee found for id {}'.format(payee_id))

    if p.user != user:
        raise Unauthorized(
            'Payee id {} does not belong to user {}'.format(
                payee_id,
                user.email,
            )
        )

    return p


def create_payee(
    session, user, name, role=PayeeRole.Expense, system=False, hidden=False,
    category_id=None, account_id=None, amount=None, memo=None
):
    '''
    Create a new Payee
    '''
    check_session(session)
    check_user(user, needs_profile=True)

    if account_id is not None and role != PayeeRole.Transfer:
        raise DomainError(
            'Payee account ID may only be specified for Transfer payees'
        )

    if account_id is None and role == PayeeRole.Transfer:
        raise DomainError(
            'Payee account ID must be specified for Transfer payees'
        )

    category = None
    if category_id is not None:
        category = _load_category(session, user, category_id)

    account = None
    if account_id is not None:
        account = _load_account(session, user, account_id)

    p = Payee(
        user=user,
        name=name,
        role=role,
        system=system,
        hidden=hidden,
        category=category,
        account=account,
        amount=amount,
        memo=memo,
    )

    session.add(p)
    session.commit()

    return p


def get_payee_last_txn(session, payee_id):
    '''
    '''
    return session\
        .query(TransactionSplit) \
        .join(Transaction, Transaction.id == TransactionSplit.transaction_id) \
        .filter(Transaction.payee_id == payee_id) \
        .order_by(Transaction.date.desc()) \
        .first()
