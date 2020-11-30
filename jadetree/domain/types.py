# =============================================================================
#
# Jade Tree Personal Budgeting Application | jadetree.io
# Copyright (c) 2020 Asymworks, LLC.  All Rights Reserved.
#
# =============================================================================

import enum


class AccountType(enum.Enum):
    '''
    Per general accounting principles, :class:`Account` objects may represent
    one of five types of amounts:

    *   :attr:`AccountType.Asset` accounts hold money that the user owns
    *   :attr:`AccountType.Liability` accounts represent money that the user
        owes to a second party
    *   :attr:`AccountType.Income` accounts represent money paid to the user
        by a second party
    *   :attr:`AccountType.Expense` accounts represent money paid by the user
        to a second party
    *   :attr:`AccountType.Capital` accounts represent
    *   :attr:`AccountType.Trading` accounts are a special type of income
        accounts which track variable-priced assets (e.g. foreign currencies,
        securities, etc) and represent the unrealized gain (or loss) of the
        variable-priced assets relative to the base currency

    .. note::

        Jade Tree does not support all account types recognized by Generally
        Accepted Accounting Principles in the interest of being relatively
        uncomplex and geared towards personal budgeting. Capital accounts are
        supported by Jade Tree only for off-budget use (i.e. calculating net
        worth).

    '''
    Asset = 'A'         #: Asset Account
    Liability = 'L'     #: Liability Account
    Income = 'I'        #: Income Account
    Expense = 'E'       #: Expense Account
    Capital = 'C'       #: Capital Account
    Trading = 'T'       #: Trading Account


class AccountSubtype(enum.Enum):
    '''
    :class:`Account` objects which are :attr:`AccountType.Personal` type may
    have a sub-type assigned. These are informational only and may impact how
    the account is displayed, but does not affect functionality.

    By default, the Jade Tree interface will try to characterize each account
    as either an Asset Account (holds money owed to the user) or a Liability
    Account (represents money owed to other parties). Some account types will
    default to being "non-budget" accounts. The following lists the default
    mapping:

    +---------------------------------------+----------------------------+
    | :attr:`AccountSubtype.Checking`       | Asset                      |
    +---------------------------------------+----------------------------+
    | :attr:`AccountSubtype.Savings`        | Asset                      |
    +---------------------------------------+----------------------------+
    | :attr:`AccountSubtype.Cash`           | Asset                      |
    +---------------------------------------+----------------------------+
    | :attr:`AccountSubtype.Paypal`         | Asset                      |
    +---------------------------------------+----------------------------+
    | :attr:`AccountSubtype.Merchant`       | Asset                      |
    +---------------------------------------+----------------------------+
    | :attr:`AccountSubtype.CreditCard`     | Liability                  |
    +---------------------------------------+----------------------------+
    | :attr:`AccountSubtype.LineOfCredit`   | Liability                  |
    +---------------------------------------+----------------------------+
    | :attr:`AccountSubtype.Investment`     | Non-Budget                 |
    +---------------------------------------+----------------------------+
    | :attr:`AccountSubtype.Mortgage`       | Non-Budget                 |
    +---------------------------------------+----------------------------+
    | :attr:`AccountSubtype.Other`          | Non-Budget                 |
    +---------------------------------------+----------------------------+

    '''

    # Asset Accounts
    Checking = 'checking'               #: Checking Account
    Savings = 'savings'                 #: Savings Account
    Cash = 'cash'                       #: Cash Account
    Paypal = 'paypal'                   #: PayPal Account
    Merchant = 'merchant'               #: Merchant Account

    # Liability Accounts
    CreditCard = 'credit_card'          #: Credit Card Account
    LineOfCredit = 'loc'                #: Line of Credit Account

    # Non-Budget Accounts
    Investment = 'investment'           #: Investment Account
    Mortgage = 'mortgage'               #: Mortgage account
    OtherAsset = 'other'                #: Other Account Type


class AccountRole(enum.Enum):
    '''
    :class:`Account` objects may be further categorized into their role in the
    budgeting flow:

    *   :attr:`AccountRole.System` accounts are special internal accounts that
        Jade Tree uses for system operations (e.g. setting initial balances).
        System accounts are hidden from the user.
    *   :attr:`AccountRole.Personal` accounts are bank or other institutional
        accounts that belong to the user and are typically
        :attr:`~AccountType.Asset` or :attr:`~AccountType.Liability` accounts
    *   :attr:`AccountRole.Budget` accounts are `~AccountType.Income` or
        :attr:`~AccountType.Expense` accounts belonging to a `Budget`
    *   :attr:`AccountRole.Trading` accounts indicate trading accounts which
        are linked to :attr:`~AccountType.Asset` accounts with security type
        assets (note that Jade Tree has a special System Trading account that
        is used for foreign currency transactions)

    '''
    System = 'system'           #: System Account
    Personal = 'personal'       #: Personal Account
    Budget = 'budget'           #: Budget Account
    Trading = 'trading'         #: Trading Account


class PayeeRole(enum.Enum):
    '''
    '''
    Initial = 'initial'         #: Initial Balance Payee
    Transfer = 'transfer'       #: Transfer Payee
    Expense = 'expense'         #: General Expense Payee


class TransactionType(enum.Enum):
    '''
    :class:`jadetree.models.Transaction` objects may be one of four types:

    * :attr:`TransactionType.Inflow` transactions represent money flowing in
      to the user's assets, and will have a positive sign for
      :attr:`~jadetree.models.AccountType.Asset`,
      :attr:`~jadetree.models.AccountType.Income`, and
      :attr:`~jadetree.models.AccountType.Capital` account types, and a
      negative sign for :attr:`~jadetree.models.AccountType.Expense` and
      :attr:`~jadetree.models.AccountType.Liability` account types.
    * :attr:`TransactionType.Outflow` transactions represent money flowing in
      to the user's assets, and will have a positive sign for
      :attr:`~jadetree.models.AccountType.Expense` and
      :attr:`~jadetree.models.AccountType.Liability` account types, and a
      negative sign for :attr:`~jadetree.models.AccountType.Asset`,
      :attr:`~jadetree.models.AccountType.Income`, and
      :attr:`~jadetree.models.AccountType.Capital` account types.
    * :attr:`TransactionType.Transfer` transactions are special transactions
      between two Personal accounts. The signs of the splits indicate which
      direction money flows.
    * :attr:`TransactionType.System` transactions are special transactions
      between a Personal account and a System account.  The signs of the
      splits indicate which direction money flows.

    '''
    Inflow = 'inflow'           #: Deposit into a Personal Account
    Outflow = 'outflow'         #: Withdrawl from a Personal Account
    Transfer = 'transfer'       #: Transfer between two Personal Accounts
    System = 'system'           #: System Transaction
