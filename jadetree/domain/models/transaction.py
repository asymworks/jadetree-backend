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

from ..types import AccountRole, AccountType, TransactionType
from .account import Account

__all__ = ('Transaction', 'TransactionLine', 'TransactionEntry', 'TransactionSplit')


@dataclass
class TransactionEntry:
    '''
    Holds the amount of currency associated with a `TransactionSplit` on a
    particular `Account`. For all account types other than Trading accounts,
    the `TransactionEntry` currency must match that of the account.
    '''
    amount: Decimal = None
    currency: str = None

    # Relationship Fields
    line: 'TransactionLine' = None
    split: 'TransactionSplit' = None

    # Helpers
    @property
    def is_inflow(self):
        if self.amount is None or self.line is None:
            return False
        return self.amount * Account.inflow_sign(self.line.account) > 0

    def __repr__(self):
        currency = 'XXX'
        if self.line is not None and self.line.account is not None:
            currency = self.line.account.currency
        return '<TransactionEntry {} {}>'.format(
            self.amount,
            currency
        )


@dataclass
class TransactionLine:
    '''
    Holds all the `TransactionEntry` items associated with a single account
    ledger line for a `Transaction` (i.e. the total amount of a transaction
    associated with a particular account for all splits).
    '''
    cleared: bool = None
    cleared_at: date = None
    reconciled: bool = None
    reconciled_at: date = None

    # Relationship Fields
    transaction: 'Transaction' = None
    account: 'Account' = None           # noqa: F821

    # Populated by ORM
    # entries: List[TransactionEntry]

    # Helpers
    @property
    def amount(self):
        '''Calculate the amount of this line in the account currency'''
        if self.transaction is None or self.transaction.currency is None:
            return Decimal()

        if self.account is None:
            return Decimal()

        line_amount = Decimal()
        line_currency = self.account.currency
        for entry in self.entries:
            line_amount = line_amount + entry.amount
            assert entry.currency == line_currency, \
                'Entry Currency differs from Line Currency'

        return line_amount

    @property
    def currency(self):
        '''Get the Account Currency for this line'''
        if self.account is None:
            return None

        return self.account.currency

    @property
    def role(self):
        '''Get the Account Role for this line'''
        if self.account is None:
            return None

        return self.account.role

    def __repr__(self):
        return '<TransactionLine {} {}>'.format(
            self.amount,
            self.currency
        )


@dataclass
class TransactionSplit:
    '''
    Connects `TransactionEntry` items for a single categorized amount of funds
    moving between two accounts. For transactions between two accounts with the
    same currency this will be two `TransactionEntry` objects; for currency
    exchanges involving the trading account there will be four (one pair for
    the left account and the trading account, and a second pair for the right
    account and the trading account).

    By convention the left account is the same for all `TransactionSplit`
    objects within a single `Transaction` while the right account may differ for
    each split.
    '''
    type: TransactionType = None
    memo: str = None

    # Relationship Fields
    transaction: 'Transaction' = None
    category: 'Category' = None             # noqa: F821
    left_line: 'TransactionLine' = None
    right_line: 'TransactionLine' = None

    # Populated by ORM
    # entries: List[TransactionEntry]

    # Helpers
    @property
    def amount(self):
        '''Calculate the amount of this split in the transaction currency'''
        if self.transaction is None or self.transaction.currency is None:
            return Decimal(0)

        if self.left_line is None:
            return Decimal(0)

        split_amount = Decimal()
        split_currency = self.left_line.account.currency
        for entry in self.entries:
            if entry.line == self.left_line:
                split_amount = split_amount + entry.amount
                assert entry.currency == split_currency, \
                    'Entry Currency differs from Line Currency'

        if split_currency == self.transaction.currency:
            return split_amount

        # If the Line Currency is the Foreign Currency
        if split_currency == self.transaction.foreign_currency:
            return split_amount * (self.transaction.foreign_exchrate or 1)

        # Else it must be in the User Base Currency
        assert split_currency == self.transaction.user.currency
        return split_amount / (self.transaction.foreign_exchrate or 1)

    @property
    def currency(self):
        '''Get the Transaction Currency for this Split'''
        if self.transaction is None:
            return None

        return self.transaction.currency

    @property
    def is_transfer(self):
        return self.left_account is not None and \
            self.right_account is not None and \
            self.left_account.role == AccountRole.Personal and \
            self.right_account.role == AccountRole.Personal

    @property
    def left_account(self):
        return self.left_line.account if self.left_line else None

    @property
    def right_account(self):
        return self.right_line.account if self.right_line else None

    def __repr__(self):
        return '<TransactionSplit {} -> {}>'.format(
            self.left_account.name if self.left_account else 'None',
            self.right_account.name if self.right_account else 'None'
        )


@dataclass
class Transaction:
    '''
    The `Transaction` object represents a single transfer of funds into or out
    of an `Account` to a single `Payee`, which can be in the same currency as
    the account or involve a foreign currency exchange, and the amount of which
    can be split into multiple `TransactionSplit` objects to distribute the
    funds between more than one category or transfer.
    '''
    date: date = None
    check: str = None
    memo: str = None

    currency: str = None
    foreign_currency: str = None
    foreign_exchrate: Decimal = None

    # Relationship Fields
    user: 'User' = None         # noqa: F821
    account: 'Account' = None   # noqa: F821
    payee: 'Payee' = None       # noqa: F821

    # Populated by ORM
    # lines: List[TransactionLine]
    # splits: List[TransactionSplit]

    # Domain Logic
    def _check_objects(self, fn_name):
        '''
        Verify that the :param:`~Transaction.user` and `~Transaction.account`
        are assigned, of the correct type, and that the source account is a
        :attr:`~AccountType.Personal` account.
        '''
        if self.user is None:
            raise DomainError(
                'Transaction.user must be assigned before calling '
                '{}'.format(fn_name)
            )

        if self.account is None:
            raise DomainError(
                'Transaction.account must be assigned before calling '
                '{}'.format(fn_name)
            )

        if self.account.role != AccountRole.Personal:
            raise DomainError(
                'Transactions must be associated with Personal accounts'
            )

    def _opposing_sign(self, opposing):
        '''
        Calculate the sign for the opposing line item in a double-entry pair
        of `TransactionLine` entries. The opposing line sign depends on the
        type of the opposing `Account` since it must satisfy the Accounting
        Equation for both `TransactionLine` items:

        .. math::

            Assets - Liabilities = Capital + Income - Expenses = Net Worth

        Therefore to keep the equation balanced, moving one unit of currency
        into an ``Asset`` account and increasing its balance by one must
        correspond to increasing a ``Liability``, ``Capital``, or ``Income``
        account by one unit, or decreasing an ``Expense`` or another ``Asset``
        account accordingly.

        :param opposing: opposing `Account` object for the transaction
        :type opposing: Account
        :returns: Sign of the `TransactionLine.amount` for the opposing line
        :rtype: int
        '''
        _acct = Account.account_signs(self.account)
        _opp = Account.account_signs(opposing)
        return -1 * _acct[0] * _acct[1] * _opp[0] * _opp[1]

    def add_split(
        self, opposing, amount, currency=None, category=None, memo=None,
        trading=None, ttype=None,
    ):
        '''
        Add a `TransactionSplit` to the transaction to represent a single split
        within the overall transaction.  If the currency is the same as the
        transaction account currency and the opposing account currency, this
        adds two `TransactionEntry` objects, one for each side of the
        double-entry transaction.

        If the currency is different than the transaction account currency or
        from the opposing account currency, a `~AccountType.Trading` account
        is used to convert from one currency to the other.  The currency must
        match the :attr:`Transaction.foreign_currency` attribute, and the
        :attr:`Transaction.foreign_exchrate` is used to convert to and from
        the base currency.

        :param opposing: Opposing account object
        :type opposing: Account
        :param amount: Transaction Line amount
        :type amount: Decimal
        :param currency: Type of currency the amount represents, as an ISO
            4217 code or another security code. Set to the same currency as
            the `Transaction.account` object if None.
        :type currency: str
        :param category: Budget category for the transaction
        :type category: Category
        :param memo: Memo for the transaction line
        :type memo: str
        :param trading: Currency trading account
        :type trading: Account
        :param ttype: Transaction Type override
        :type ttype: TransactionType
        :returns: tuple of (`TransactionSplit`, [new `TransactionEntry` items],
            [new `TransactionLine` items])
        :rtype: tuple
        '''
        self._check_objects(__name__)

        # Type check arguments
        if not isinstance(opposing, Account):
            raise TypeError('Opposing account must be an Account object')
        if not isinstance(amount, Decimal):
            raise TypeError('Amount must be a Decimal object')

        # Ensure accounts are active
        if not self.account.active:
            raise DomainError('Transaction source account is not active')
        if not opposing.active:
            raise DomainError('Transaction opposing account is not active')

        # Determine the Transaction Type
        if ttype is None:
            ttype = TransactionType.Inflow
            if amount * Account.inflow_sign(self.account) < 0:
                ttype = TransactionType.Outflow
            if opposing.role == AccountRole.Personal:
                ttype = TransactionType.Transfer

        # Transaction Line Currency defaults to Account Currency
        if not currency:
            currency = self.account.currency

        # Allow the first call to add_line() to set the currency
        if self.currency is None:
            self.currency = currency

        # Transaction lines must all have same currency
        if currency != self.currency:
            raise ValueError(
                'All Transaction Lines must be in the same currency'
            )

        # Foreign currency transactions must satisfy a couple extra conditions,
        # namely that there must only be two currencies in play, and one must
        # be the user base currency:
        # Case 1: Transaction Currency and both Accounts are the Base Currency
        # Case 2: Transaction and both Accounts are in the Foreign Currency
        # Case 3a: Transaction Currency is not the Base Currency, and both
        #          accounts are the Base Currency
        # Case 3b: Transaction Currency is the Base Currency, and both
        #          accounts are the Foreign Currency
        # Case 4a: Transaction Currency is the Base Currency and the left
        #          account is the foreign currency
        # Case 4b: Transaction Currency is the Base Currency and the right
        #          account is the foreign currency
        # Case 4c: Transaction Currency is not the Base Currency and the left
        #          account is the foreign currency
        # Case 4d: Transaction Currency is not the Base Currency and the left
        #          account is the foreign currency
        #
        # Once the cases are verified, we convert amounts (in transaction
        # currency) to the foreign currency for the left and right sides of
        # the transaction line.  The exchange rate is defined as base / foreign
        # (i.e. cost to buy one unit of foreign currency with base currency),
        # regardless of whether the transaction is in the base or foreign
        # currency

        l_amt = r_amt = amount              # Left and Right Amounts
        b_ccy = self.user.currency          # Base Currency
        l_ccy = self.account.currency       # Left Account Currency
        r_ccy = opposing.currency           # Right Account Currency
        t_ccy = self.currency               # Transaction Currency
        f_ccy = self.foreign_currency       # Foreign Currency

        is_foreign = l_ccy != b_ccy or r_ccy != b_ccy or t_ccy != b_ccy
        if is_foreign:
            if self.foreign_currency is None:
                raise DomainError(
                    'Transaction.foreign_currency must be assigned before '
                    'calling Transaction.add_split with a foreign currency'
                )

            if self.foreign_exchrate is None:
                raise DomainError(
                    'Transaction.foreign_exchrate must be assigned before '
                    'calling Transaction.add_split with a foreign currency'
                )

            # Case 2
            if l_ccy == t_ccy and r_ccy == t_ccy and t_ccy == f_ccy:
                # This is a no-op because the amounts are already in the
                # correct currency (albeit not the base currency)
                pass

            # Case 3a
            elif l_ccy == b_ccy and r_ccy == b_ccy and t_ccy == f_ccy:
                # Convert both sides to Base Currency
                l_amt = amount * self.foreign_exchrate
                r_amt = amount * self.foreign_exchrate

            # Case 3b
            elif l_ccy == f_ccy and r_ccy == f_ccy and t_ccy == b_ccy:
                # Convert both sides to Foreign Currency
                l_amt = amount / self.foreign_exchrate
                r_amt = amount / self.foreign_exchrate

            # Case 4a
            elif l_ccy == f_ccy and r_ccy == b_ccy and t_ccy == b_ccy:
                # Convert Left Side to Foreign Currency
                l_amt = amount / self.foreign_exchrate

            # Case 4b
            elif l_ccy == b_ccy and r_ccy == f_ccy and t_ccy == b_ccy:
                # Convert Right Side to Foreign Currency
                r_amt = amount / self.foreign_exchrate

            # Case 4c
            elif l_ccy == f_ccy and r_ccy == b_ccy and t_ccy == f_ccy:
                # Convert Right Side to Base Currency
                r_amt = amount * self.foreign_exchrate

            # Case 4d
            elif l_ccy == b_ccy and r_ccy == f_ccy and t_ccy == f_ccy:
                # Convert Left Side to Base Currency
                l_amt = amount * self.foreign_exchrate

            # Currency Matching Failure
            else:
                raise DomainError(
                    'Transaction Currency or the Transaction Foreign Currency '
                    'did not match the user base currency or one of the '
                    'account currencies. Ensure only two currencies are used '
                    'in a single transaction and one is the base currency.'
                )

        # Setup Return Lists
        split = None
        entries = []
        lines = []

        # Find a `TransactionLine` for the left and right accounts
        left_line = self.account_line(self.account)
        right_line = self.account_line(opposing)

        # Create the Transaction Lines if the do not exist
        if left_line is None:
            left_line = TransactionLine(
                transaction=self,
                account=self.account,
                cleared=False,
                cleared_at=None,
                reconciled=False,
                reconciled_at=None,
            )
            lines.append(left_line)

        if right_line is None:
            right_line = TransactionLine(
                transaction=self,
                account=opposing,
                cleared=False,
                cleared_at=None,
                reconciled=False,
                reconciled_at=None,
            )
            lines.append(right_line)

        # Create the Transaction Split and Entries
        split = TransactionSplit(
            transaction=self,
            category=category,
            left_line=left_line,
            right_line=right_line,
            type=ttype,
            memo=memo,
        )

        # Get the Opposing Line Sign
        opp_sign = self._opposing_sign(opposing)

        # Create the Ledger Entries
        entries = []
        if l_ccy == r_ccy:
            # Simple two-line transaction
            le = TransactionEntry(
                split=split,
                line=left_line,
                amount=l_amt,
                currency=l_ccy,
            )
            re = TransactionEntry(
                split=split,
                line=right_line,
                amount=opp_sign * r_amt,
                currency=r_ccy,
            )

            # Add to List
            entries = [le, re]

        else:
            # Multi-Currency Transaction
            if trading is None:
                raise ValueError(
                    'Trading account must be provided for a multi-currency '
                    'transaction'
                )

            if not isinstance(trading, Account):
                raise TypeError('Trading account must be an Account object')

            if trading.type != AccountType.Trading:
                raise DomainError('Trading account must be of type Trading')

            # Get Trading TransactionLine
            trading_line = self.account_line(trading)
            if trading_line is None:
                trading_line = TransactionLine(
                    transaction=self,
                    account=trading,
                    cleared=False,
                    cleared_at=None,
                    reconciled=False,
                    reconciled_at=None,
                )
                lines.append(trading_line)

            # Calculate Trading Sign
            trade_sign = self._opposing_sign(trading)

            # Create ledger entries
            le1 = TransactionEntry(
                split=split,
                line=left_line,
                amount=l_amt,
                currency=l_ccy,
            )
            re1 = TransactionEntry(
                split=split,
                line=trading_line,
                amount=+trade_sign * l_amt,
                currency=l_ccy,
            )
            le2 = TransactionEntry(
                split=split,
                line=trading_line,
                amount=-trade_sign * r_amt,
                currency=r_ccy,
            )
            re2 = TransactionEntry(
                split=split,
                line=right_line,
                amount=opp_sign * r_amt,
                currency=r_ccy,
            )

            # Add to Lines
            entries = [le1, re1, le2, re2]

        return split, entries, lines

    # Helpers
    def account_line(self, account):
        '''Find an `AccountLine` object for the given account'''
        for ln in self.lines:
            if ln.account == account:
                return ln
        return None

    @property
    def amount(self):
        '''
        Calculate the total amount for the Transaction in the transaction
        currency.
        '''
        self._check_objects(__name__)

        txn_amt = Decimal()
        for split in self.splits:
            txn_amt = txn_amt + split.amount

        return txn_amt

    @property
    def is_inflow(self):
        amt = self.amount()[0]
        if amt == 0 or self.account is None:
            return False
        return amt * Account.inflow_sign(self.account) > 0

    @property
    def is_outflow(self):
        amt = self.amount()[0]
        if amt == 0 or self.account is None:
            return False
        return amt * Account.inflow_sign(self.account) < 0

    @property
    def is_transfer(self):
        if len(self.splits) != 1:
            return False
        return self.splits[0].is_transfer

    @property
    def is_split(self):
        return len(self.splits) > 1

    def __repr__(self):
        return f'<Transaction {self.amount} {self.currency}>'
