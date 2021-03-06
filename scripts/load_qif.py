#
# Load a QIF file into an Account
#

import argparse
import os
import sys

root_path = os.path.dirname(os.path.abspath(__file__))
jt_path = os.path.abspath(os.path.join(root_path, '..'))
sys.path.append(jt_path)

from datetime import date
from decimal import Decimal

from arrow import Arrow

from jadetree.database import db
from jadetree.domain.models import Account, Budget, BudgetEntry, Category, Payee, User
from jadetree.domain.types import AccountRole, AccountType, PayeeRole, TransactionType
from jadetree.service import (
    account as account_service,
    budget as budget_service,
    ledger as ledger_service,
    user as user_service,
)

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Import QIF Files into Jade Tree')
    parser.add_argument('account', metavar='ACCOUNT', type=str, nargs=1, help='account name for import')
    parser.add_argument('qif_file', metavar='QIF_FILE', type=str, nargs=1, help='QIF Files for Input')
    parser.add_argument('-r', '--rules', type=str, nargs=1, help='import rules file')

    args = parser.parse_args()
    
