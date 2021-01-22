# =============================================================================
#
# Jade Tree Personal Budgeting Application | jadetree.io
# Copyright (c) 2020 Asymworks, LLC.  All Rights Reserved.
#
# =============================================================================

import sys

import click
from flask.cli import AppGroup

__all__ = ('init_cli', )


def init_shell():       # pragma: no cover
    '''Initialize the Shell Context'''
    import datetime
    from decimal import Decimal

    import arrow
    import sqlalchemy as sa

    from jadetree.database import db
    from jadetree.domain.models import (
        Account,
        Budget,
        BudgetEntry,
        Category,
        Payee,
        Transaction,
        TransactionEntry,
        TransactionLine,
        TransactionSplit,
        User,
    )
    from jadetree.domain.types import (
        AccountRole,
        AccountSubtype,
        AccountType,
        PayeeRole,
        TransactionType,
    )
    from jadetree.service import (
        account as account_service,
        auth as auth_service,
        budget as budget_service,
        export as export_service,
        ledger as ledger_service,
        payee as payee_service,
        user as user_service,
    )

    return {
        'arrow': arrow,
        'datetime': datetime,
        'sa': sa,
        'Decimal': Decimal,

        'db': db,
        'session': db.session,

        'Account': Account,
        'Budget': Budget,
        'BudgetEntry': BudgetEntry,
        'Category': Category,
        'Payee': Payee,
        'Transaction': Transaction,
        'TransactionEntry': TransactionEntry,
        'TransactionLine': TransactionLine,
        'TransactionSplit': TransactionSplit,
        'User': User,

        'AccountRole': AccountRole,
        'AccountType': AccountType,
        'AccountSubtype': AccountSubtype,
        'PayeeRole': PayeeRole,
        'TransactionType': TransactionType,

        'account_service': account_service,
        'auth_service': auth_service,
        'budget_service': budget_service,
        'export_service': export_service,
        'ledger_service': ledger_service,
        'payee_service': payee_service,
        'user_service': user_service,
    }


export_cli = AppGroup('export')


@export_cli.command('accounts')
@click.argument('user_id')
def export_accounts(user_id):
    from jadetree.database import db
    from jadetree.domain.models import User
    from jadetree.domain.types import AccountRole
    from jadetree.service import export

    for acct in db.session.query(User).get(user_id).accounts:
        if acct.role == AccountRole.Personal:
            for line in export.export_account_qif(db.session, acct):
                sys.stdout.write(line + '\n')


@export_cli.command('budgets')
@click.argument('user_id')
def export_budgets(user_id):
    from jadetree.database import db
    from jadetree.domain.models import User
    from jadetree.service import export

    for budget in db.session.query(User).get(user_id).budgets:
        for line in export.export_budget_qif(budget):
            sys.stdout.write(line + '\n')


@export_cli.command('payees')
@click.argument('user_id')
def export_payees(user_id):
    from jadetree.database import db
    from jadetree.domain.models import User
    from jadetree.service import export

    payees = db.session.query(User).get(user_id).payees
    for line in export.export_payees_qif(payees):
        sys.stdout.write(line + '\n')


def init_cli(app):
    '''Register the CLI Commands with the Application'''
    app.shell_context_processor(init_shell)
    app.cli.add_command(export_cli)

    # Notify Initialization Complete
    app.logger.debug('CLI Initialized')
