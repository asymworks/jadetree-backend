"""Jade Tree Reports Service.

Jade Tree Personal Budgeting Application | jadetree.io
Copyright (c) 2020 Asymworks, LLC.  All Rights Reserved.
"""

import datetime

from jadetree.database.queries import q_report_net_worth

from .util import check_session, check_user


def net_worth(session, user):
    """Report the user's net worth in assets and liabilities per month."""
    check_session(session)
    check_user(user)

    q = q_report_net_worth(session, user.id)
    data = []
    for y, m, assets, liabilities in q.all():
        data.append(dict(
            month=datetime.date(year=int(y), month=int(m), day=1),
            assets=assets,
            liabilities=liabilities,
            currency=user.currency,
        ))

    return data
