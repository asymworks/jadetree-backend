# =============================================================================
#
# Jade Tree Personal Budgeting Application | jadetree.io
# Copyright (c) 2020 Asymworks, LLC.  All Rights Reserved.
#
# =============================================================================


def check_transaction_entries(tsplit, entries):
    '''
    Validate a list of TransactionEntry objects are equivalent, meaning they
    contain the same items but do not necessarily share ordering.
    '''
    assert tsplit.entries is not None
    assert isinstance(tsplit.entries, list)
    assert len(tsplit.entries) == len(entries)
    for i in range(len(tsplit.entries)):
        assert (
            tsplit.entries[i].line.account,
            tsplit.entries[i].amount,
            tsplit.entries[i].currency,
        ) in entries
