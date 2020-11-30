# =============================================================================
#
# Jade Tree Personal Budgeting Application | jadetree.io
# Copyright (c) 2020 Asymworks, LLC.  All Rights Reserved.
#
# =============================================================================

from datetime import datetime
from decimal import Decimal

from jadetree.database.queries import q_budget_summary
from jadetree.domain.models import Category

from .budget import _load_budget
from ..util import check_session, check_user

__all__ = ('get_budget_data', 'get_budget_month', 'get_budget_summary')


def get_budget_data(session, user, budget_id):
    '''
    Return Budget Data for all months from the first transaction linked to
    the budget, to two months in the future
    '''
    check_session(session)
    check_user(user)

    # Check existance and authorization for budget id
    _load_budget(session, user, budget_id)

    # Load Categories and find Income Categories
    q_categories = session.query(Category).filter(
        Category.budget_id == budget_id,
        Category.parent_id != None      # noqa: E711
    )

    categories = dict()
    cat_ids = []
    cat_grp_ids = set()
    cat_cur_income = None
    cat_next_income = None
    for c in q_categories.all():
        cat_ids.append(c.id)
        cat_grp_ids.add(c.parent_id)
        categories[c.id] = c
        if c.name == '_cur_month':
            cat_cur_income = c.id
        if c.name == '_next_month':
            cat_next_income = c.id

    # Load Summary Items from Database (grouped and ordered by date)
    q_summary = q_budget_summary(session, budget_id)

    # Budget Summary Processing Data
    data = dict()
    cur_ym = None
    last_ym = None
    next_ym = None

    # Handle Budget-Level Month Summaries
    def _closeout_month():
        last_overspent = Decimal(0)
        last_available = Decimal(0)

        # Load Last-Month Summary Values
        if last_ym is not None and last_ym in data:
            last_overspent = data[last_ym]['overspent']
            last_available = data[last_ym]['available']

        # Calculate Income for Current Month (NB: Income is "negative outflow")
        cur_income = Decimal(0)
        if 'cur_income' in data[cur_ym]:
            cur_income = cur_income - data[cur_ym]['cur_income']
        if last_ym is not None and 'next_income' in data[last_ym]:
            cur_income = cur_income - data[last_ym]['next_income']

        # Add categories with no budget or spending this month to dictionary
        if last_ym is not None and last_ym in data:
            for id in data[last_ym]['categories'].keys():
                if id not in data[cur_ym]['categories'].keys():
                    # Set balance and rollover from previous month
                    balance = data[last_ym]['categories'][id]['carryover']
                    rollover = data[last_ym]['categories'][id]['rollover']

                    # Calculate overspend and carryover
                    overspend = Decimal(0) \
                        if balance > 0 or rollover \
                        else balance
                    carryover = Decimal(0) \
                        if balance < 0 and not rollover \
                        else balance

                    # Store current-month category information
                    data[cur_ym]['categories'][id] = dict(
                        parent_id=categories[id].parent_id,
                        budget=Decimal(0),
                        outflow=Decimal(0),
                        balance=balance,
                        rollover=rollover,
                        carryover=carryover,
                        overspend=overspend,
                        num_transactions=0,
                    )

        # Calculate Unbudgeted and Overspent for Current Month
        cur_cats = data[cur_ym]['categories']
        cur_budgeted = sum([itm['budget'] for itm in cur_cats.values()])
        cur_overspent = sum([itm['overspend'] for itm in cur_cats.values()])
        cur_available = last_available + last_overspent + cur_income - cur_budgeted

        # Store Month-End Information
        data[cur_ym]['last_available'] = last_available
        data[cur_ym]['last_overspent'] = last_overspent
        data[cur_ym]['overspent'] = cur_overspent
        data[cur_ym]['income'] = cur_income
        data[cur_ym]['budgeted'] = cur_budgeted
        data[cur_ym]['available'] = cur_available

    def _next_ym():
        if cur_ym[1] == 12:
            return (cur_ym[0] + 1, 1)
        else:
            return (cur_ym[0], cur_ym[1] + 1)

    def _diff_ym(x, y):
        return (x[0] - y[0]) * 12 + x[1] - y[1]

    # Process Categories per Month
    for rec in session.execute(q_summary):
        entry_id, cat, y, m, outflow, ntrans, budget, rollover, notes = rec
        outflow = outflow or Decimal(0)
        budget = budget or Decimal(0)

        # Force the Year and Month to be integers
        y = int(y)
        m = int(m)

        # Advance to Next Month?
        if (y, m) != cur_ym:
            if cur_ym is not None:
                _closeout_month()

            # Advance to next month, filling in gaps if required
            last_ym = cur_ym
            next_ym = (y, m)
            if last_ym is not None and int(_diff_ym(next_ym, last_ym)) > 1:
                # We need to fill in a gap
                cur_ym = _next_ym()
                while cur_ym != next_ym:
                    data[cur_ym] = dict(
                        categories=dict()
                    )
                    _closeout_month()
                    last_ym = cur_ym
                    cur_ym = _next_ym()

            else:
                cur_ym = next_ym

            # Setup Current Month
            data[cur_ym] = dict(
                categories=dict()
            )

        # Update Current Month
        assert cat not in data[cur_ym]['categories'], \
            'Duplicate category {} in {:04}-{:02}'.format(cat, y, m)

        if cat not in (cat_cur_income, cat_next_income):
            # Load prior-month category information for carryover
            last_carryover = Decimal(0)
            if last_ym in data and cat in data[last_ym]['categories']:
                last_carryover = data[last_ym]['categories'][cat]['carryover']

            # Calculate this-month balance = budget - outflow + carryover
            balance = budget - outflow + last_carryover

            # Calculate Overspend and Carryover
            overspend = Decimal(0) if balance > 0 or rollover else balance
            carryover = Decimal(0) if balance < 0 and not rollover else balance

            # Store current-month category information
            data[cur_ym]['categories'][cat] = dict(
                parent_id=categories[cat].parent_id,
                entry_id=entry_id,
                budget=budget,
                outflow=outflow,
                balance=balance,
                rollover=rollover,
                carryover=carryover,
                overspend=overspend,
                num_transactions=ntrans,
            )

            if notes:
                data[cur_ym]['categories'][cat]['notes'] = notes

        elif cat == cat_cur_income:
            data[cur_ym]['cur_income'] = outflow

        elif cat == cat_next_income:
            data[cur_ym]['next_income'] = outflow

    # Finish current month and append next month and a "future" month
    if cur_ym is not None:
        _closeout_month()

        # Add next month summary
        last_ym = cur_ym
        cur_ym = _next_ym()
        data[cur_ym] = dict(
            categories=dict()
        )
        _closeout_month()

        # Add future month summary
        last_ym = cur_ym
        cur_ym = 'future'
        data[cur_ym] = dict(
            categories=dict()
        )
        _closeout_month()

    return data


def get_budget_month(session, user, budget_id, month=None):
    '''
    Return the Budget Data for a single month

    Month must be None (meaning the current month on the server) or set to a
    2-tuple of (year, month).
    '''
    budget_data = get_budget_data(session, user, budget_id)

    if month is None:
        today = datetime.now().date()
        month = (today.year, today.month)

    # Generate Year/Month Index
    y, m = month
    ymint = y * 12 + m
    all_months = sorted([
        x[0] * 12 + x[1]
        for x in budget_data.keys()
        if x != 'future'
    ])

    if len(all_months) == 0 or ymint < all_months[0]:
        # No transactions have been posted yet
        return {
            'categories': dict(),
            'groups': dict(
                all=dict(
                    budget=Decimal(0),
                    outflow=Decimal(0),
                    balance=Decimal(0)
                )
            ),
            'last_available': Decimal(0),
            'last_overspent': Decimal(0),
            'overspent': Decimal(0),
            'income': Decimal(0),
            'budgeted': Decimal(0),
            'available': Decimal(0),
        }

    key = (y, m)
    if ymint > all_months[-1]:
        # Use the "future" month for all out months
        key = 'future'

    # Return Budget Month Data
    return budget_data[key]


def get_budget_summary(session, user, budget_id, month=None):
    '''
    Return the Budget Summary for the a single month

    Month must be None (meaning the current month on the server) or set to a
    2-tuple of (year, month).
    '''
    budget_data = get_budget_month(session, user, budget_id, month)
    budget_obj = _load_budget(session, user, budget_id)

    ret = {
        'id': budget_id,
        'name': budget_obj.name,
        'overspent': budget_data['overspent'],
        'income': budget_data['income'],
        'budgeted': budget_data['budgeted'],
        'available': budget_data['available'],
        'outflow': sum([c['outflow'] for c in budget_data['categories'].values()]),
        'overspent_categories': [],
    }

    for cid, c in budget_data['categories'].items():
        if c['overspend'] < 0:
            cat = session.query(Category).get(cid)
            ret['overspent_categories'].append({
                'id': cid,
                'name': cat.name,
                'parent_name': cat.parent.name if cat.parent else '',
                'budget': c['budget'],
                'outflow': c['outflow'],
                'overspend': c['overspend'],
            })

    return ret
