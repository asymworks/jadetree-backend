"""Jade Tree Data Export Service.

Jade Tree Personal Budgeting Application | jadetree.io
Copyright (c) 2020 Asymworks, LLC.  All Rights Reserved.
"""

from jadetree.domain.models import Transaction, TransactionLine
from jadetree.domain.types import AccountSubtype, AccountType, TransactionType

# Export and Import Services


def export_transaction_qif(txn, account):
    """Export a Transaction as a QIF Record."""
    qif_lines = []
    qif_lines.append(f'D{txn.date.isoformat()}')
    if txn.check:
        qif_lines.append(f'N{txn.check}')
    if txn.memo:
        qif_lines.append(f'M{txn.memo}')

    qif_lines.append(f'XC{txn.currency}')
    if txn.foreign_currency:
        qif_lines.append(f'XF{txn.foreign_currency}:{txn.foreign_exchrate}')

    lines = txn.lines
    if txn.account != account:
        lines = [ln for ln in lines if ln.opposing == account]

    qif_lines.append('T{}'.format(sum([ln.amount for ln in lines])))
    if len(lines) == 1:
        if lines[0].type == TransactionType.Transfer:
            if lines[0].opposing == account:
                qif_lines.append(f'PTransfer:{txn.account.id}')
            else:
                qif_lines.append('PTransfer:{}'.format(lines[0].opposing.id))

        else:
            qif_lines.append(f'P{txn.payee.name}')
            qif_lines.append(f'XP{txn.payee.id}')
            qif_lines.append('L{}'.format(lines[0].category.path))

    else:
        qif_lines.append(f'P{txn.payee.name}')
        qif_lines.append(f'XP{txn.payee.id}')

        for ln in lines:
            if ln.type == TransactionType.Transfer:
                if ln.opposing == account:
                    qif_lines.append(f'XX:{txn.account.id}')
                else:
                    qif_lines.append('XX:{}'.format(lines[0].opposing.id))

            else:
                qif_lines.append(f'S{ln.category.path}')

            qif_lines.append(f'${ln.amount}')
            if ln.memo:
                qif_lines.append(f'E{ln.memo}')

    if txn.cleared and txn.reconciled:
        qif_lines.append('CR')
    elif txn.cleared:
        qif_lines.append('C*')
    qif_lines.append('^')

    return qif_lines


def export_account_qif(session, account):
    """Export Account Data as a QIF Record."""
    qif_lines = []

    # Account Information
    if account.subtype == AccountSubtype.Cash:
        qif_lines.append('!Type:Cash')
    elif account.subtype in (AccountSubtype.Checking, AccountSubtype.Savings):
        qif_lines.append('!Type:Bank')
    elif account.subtype == AccountSubtype.CreditCard:
        qif_lines.append('!Type:CCard')
    elif account.subtype == AccountSubtype.Investment:
        qif_lines.append('!Type:Invst')
    elif account.type == AccountType.Asset:
        qif_lines.append('!Type:Oth A')
    elif account.type == AccountType.Liability:
        qif_lines.append('!Type:Oth L')
    else:
        qif_lines.append('!Type:Account')
        qif_lines.append(f'XT{account.type.name}')
        if account.subtype:
            qif_lines.append(f'XS{account.subtype.name}')

    qif_lines.append(f'N{account.name}')
    qif_lines.append(f'XC{account.currency}')
    if account.active:
        qif_lines.append('XA')

    if account.iban:
        qif_lines.append(f'XI{account.iban}')

    if account.opened:
        qif_lines.append(f'XO{account.opened.isoformat()}')
    if account.closed:
        qif_lines.append(f'XX:{account.closed.isoformat()}')

    qif_lines.append('^')

    # Transaction Information
    txn_in = account.transactions
    txn_out = session.query(
        Transaction
    ).join(
        TransactionLine,
        TransactionLine.transaction_id == Transaction.id
    ).filter(
        TransactionLine.opposing == account
    ).all()

    for txn in sorted(txn_in + txn_out, key=lambda t: t.date.isoformat()):
        qif_lines.extend(export_transaction_qif(txn, account))

    return qif_lines


def export_budget_qif(budget):
    """Export Budget Data as QIF Records."""
    qif_lines = []

    # Budget Information
    qif_lines.append('!Type:Budget')
    qif_lines.append(f'N{budget.name}')
    qif_lines.append(f'XC{budget.currency}')
    qif_lines.append('^')

    # Category Information
    for category in budget.categories:
        qif_lines.append('!Type:Cat')
        qif_lines.append(f'N{category.path}')
        if category.system:
            qif_lines.append('XS')
        if category.hidden:
            qif_lines.append('XH')
        if category.display_order:
            qif_lines.append(f'XO:{category.display_order}')

        qif_lines.append('^')

        # Budget Entries
        for entry in category.entries:
            qif_lines.append(f'D{entry.month.isoformat()}')
            qif_lines.append(f'B{entry.amount}')
            if entry.rollover:
                qif_lines.append('XR')
            if entry.notes:
                qif_lines.append(f'M{entry.notes}')
            qif_lines.append('^')

    return qif_lines


def export_payees_qif(payees):
    """Export Payees as QIF Records."""
    qif_lines = []
    for payee in payees:
        qif_lines.append('!Type:Payee')
        qif_lines.append(f'I{payee.id}')
        qif_lines.append(f'N{payee.name}')
        qif_lines.append(f'R{payee.role.name}')
        if payee.category:
            qif_lines.append(f'L{payee.category.id}')
        if payee.account:
            qif_lines.append(f'A{payee.account.id}')
        if payee.system:
            qif_lines.append('XS')
        if payee.hidden:
            qif_lines.append('XH')
        if payee.memo:
            qif_lines.append(f'M{payee.memo}')
        if payee.amount:
            qif_lines.append(f'T{payee.amount}')
        qif_lines.append('^')

    return qif_lines
