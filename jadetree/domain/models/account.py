# =============================================================================
#
# Jade Tree Personal Budgeting Application | jadetree.io
# Copyright (c) 2020 Asymworks, LLC.  All Rights Reserved.
#
# =============================================================================

from dataclasses import dataclass
from datetime import date
from decimal import Decimal

from ..mixins import NotesMixin, TimestampMixin
from ..types import AccountRole, AccountSubtype, AccountType

__all__ = ('Account', )


@dataclass
class Account(NotesMixin, TimestampMixin):
    '''
    Accounts are the basic model for collections of transactions,
    representing money flowing into and out of the account. The sum of all
    transactions linked to an account represents its balance.

    Accounts are defined to contain a single type of currency, and each
    transaction attached to the account must resolve to that currency type.
    If a transaction is performed in a foreign currency, there must be an
    exchange rate attached to the transaction to convert to the account's
    native currency type.  Currencies are identified by their three-letter
    `ISO 4217`_ code.

    .. _`ISO 4217`: https://www.iso.org/iso-4217-currency-codes.html

    .. py:attribute:: name
        :type: str

        Account name, which must be unique within a user's accounts

    .. py:attribute:: role
        :type: :class:`AccountRole`

        Account role (System, Personal, or Trading)

    .. py:attribute:: type
        :type: :class:`AccountType`

        Account type (Asset, Liability, Capital, Income, Expense, or Trading)

    .. py:attribute:: subtype
        :type: :class:`AccountSubtype`

        Account subtype for Personal Asset and Liability accounts

    .. py:attribute:: currency
        :type: str

        Currency code for the type of currency held by the account. This is
        normally a three-digit ISO 4217 code (e.g. 'USD'), but can be any
        string up to eight characters long to represent other types of non-
        monetary securities.

    .. py:attribute:: active
        :type: bool

        Flag indicating whether the account is active and can participate in
        transactions.

    .. py:attribute:: iban
        :type: str

        International Bank Account Number for the account. Not currently used
        by Jade Tree but may be used in the future for automatic transaction
        loading.

    .. py:attribute:: opened
        :type: `~datetime.date`

        Date the account was opened.

    .. py:attribute:: closed
        :type: `~datetime.date`

        Date the account was closed.

    .. py:attribute:: user
        :type: `User`

        User which owns the account.

    .. py:attribute:: budget
        :type: `Budget`

        Budget linked to this account. Accounts must be linked to a budget in
        order to have transactions categorized against budget categories.

    '''
    name: str = None
    role: AccountRole = None
    type: AccountType = None
    subtype: AccountSubtype = None

    currency: str = None
    active: bool = None
    iban: str = None

    opened: date = None
    closed: date = None

    display_order: int = None

    # Relationship Fields
    user: 'User' = None             # noqa: F821
    budget: 'Budget' = None         # noqa: F821
    payee: 'Payee' = None           # noqa: F821

    # Populated by ORM
    # transaction_lines: List['TransactionLine']

    # Domain Logic
    @staticmethod
    def account_signs(account_or_type):
        '''
        Calculate the inflow and side signs for an `Account` or `AccountType`
        instance. The signs are determined from the Accounting Equation:

        .. math::

            Assets - Liabilities = Capital + Income - Expenses = Net Worth

        The inflow sign is defined as the sign of a change in account balance
        that represents an increase in net worth, meaning a positive value
        for `~AccountType.Asset`, `~AccountType.Capital`, and
        `~AccountType.Income` account types, and a negative value for
        `~AccountType.Liablity` and `~AccountType.Expense` accounts.

        The side sign is defined as +1 for `~AccountType.Asset` and
        `~AccountType.Liability` account types on the left side of the
        equation, and -1 for `~AccountType.Capital`, `~AccountType.Income`,
        and `~AccountType.Expense` accounts.  The side sign is used when
        calculating transaction line amounts for the opposing side of a
        transaction to ensure an increase in net worth on one side also
        corresponds to an increase in net worth on the other side.

        :param account_or_type: `Account` object or `AccountType` value
        :type account_or_type: `Account` or `AccountType`
        :returns: tuple of (inflow_sign, side_sign) where ``inflow_sign`` and
            ``side_sign`` are integers equal to either +1 or -1.
        :rtype: tuple
        '''
        atype = account_or_type
        if isinstance(account_or_type, Account):
            atype = account_or_type.type
        inflow_sign = 1
        side_sign = 1
        if atype in (AccountType.Liability, AccountType.Expense):
            inflow_sign = -1
        if atype not in (AccountType.Asset, AccountType.Liability):
            side_sign = -1
        return inflow_sign, side_sign

    @staticmethod
    def inflow_sign(account_or_type):
        '''
        Determine the sign of a change in account balance that represents an
        increase in net worth, meaning a positive value for
        `~AccountType.Asset`, `~AccountType.Capital`, and
        `~AccountType.Income` account types, and a negative value for
        `~AccountType.Liablity` and `~AccountType.Expense` accounts.

        :param account_or_type: `Account` object or `AccountType` value
        :type account_or_type: `Account` or `AccountType`
        :returns: +1 or -1 depending on whether the account balance must
            increase or decrease to signify an increase in net worth
        :rtype: tuple
        '''
        return Account.account_signs(account_or_type)[0]

    @property
    def balance(self):
        ret = Decimal(0)
        for line in self.transaction_lines:
            for entry in line.entries:
                ret = ret + entry.amount

        return ret * self.sign

    @property
    def sign(self):
        return Account.account_signs(self.type)[0]

    # Helpers
    def __repr__(self):
        return f'<{self.type.name} Account "{self.name}">'
