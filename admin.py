"""
Adminy things go in here.
Most important is updating transactions.
"""

import csv
from datetime import datetime as dt

import transactions
from config import EXPORT_DEFINITIONS


def process_row(line, target_def):

    parsed_row = {}

    # todo: what about rows with not enough data?
    for each_def_col, each_col in zip(target_def['columns'], line):
        if each_def_col['field_name'] == 'event_date':
            date_format = each_def_col.get('format', '%Y-%m-%d')
            parsed_row['event_datetime'] = dt.strptime(each_col, date_format)

        if each_def_col['field_name'] == 'event_name':
            name_val = each_col.lower().strip().replace("'", "").replace(",", "")
            name_val = name_val.replace(
                "point of sale - interac retail purchase", ""
            ).replace(
                "point of sale", ""
            ).replace(
                "internet banking internet bill pay", ""
            )

            # remove all digits and leading/trailing whitespace
            name_val = ''.join(
                [i for i in name_val if not i.isdigit()]
            ).strip()

            # remove all extra whitespace
            parsed_row['name'] = ' '.join(name_val.split())

        # with cibc at least, we only ever have a single credit or single debit amount
        # we need to resolve this to a single amount
        if each_def_col['field_name'] == 'credit_amount':
            if each_col == 0 or each_col:
                parsed_row['amount_cents'] = int(float(each_col) * 100)

        # we'll store debits as negative rather than apply a label somewhere
        if each_def_col['field_name'] == 'debit_amount':
            if each_col == 0 or each_col:
                parsed_row['amount_cents'] = - int(float(each_col) * 100)

    return parsed_row


def add_transactions_from_csv(filepath, account_name):

    """
    Okay, here's some heavy lifting.  Take in the path of a file and I guess an account name?
    Use some kind of decently smart parsing to try and figure out important data:
    event time, amount (translate to cents), etc etc.

    Also try not to duplicate past transactions.  Use time of event + the amount of the event.
    That should get us pretty close.

    If min(date) of import is less than max(date) of DB i guess we don't have to care at all, just
    add them.
    :return:
    """

    try:
        target_def = EXPORT_DEFINITIONS[account_name]
    except KeyError:
        print(f'account name {account_name} not found in definitions')
        return

    # so, open the file, read in each line.
    parsed_data = []
    with open(filepath) as rf:
        reader = csv.reader(rf, delimiter=',')  # todo: config these
        for line in reader:
            # print(line)
            parsed_row = process_row(line, target_def)
            parsed_row['account_name'] = account_name
            parsed_data.append(parsed_row)

    # okay! we have some parsed data now :D

    # send them to get added to our existing transaction store.

    # print('Done reading, adding transactions')
    transactions.add_new_transactions(account_name, parsed_data)


def add_transactions_from_mint(filepath, max_date=None, min_date=None):

    """
    min_date: ignore dates lower than x.
    max_date: ignore dates greater than y.
    """

    if min_date:
        min_date = dt.strptime(min_date, '%Y-%m-%d')

    if max_date:
        max_date = dt.strptime(max_date, '%Y-%m-%d')

    # so, open the file, read in each line.
    parsed_data = []

    with open(filepath) as rf:
        reader = csv.reader(rf, delimiter=',')  # todo: config these
        for i, line in enumerate(reader):

            if i == 0:
                continue

            account_label = line[6]
            account_name = {
                'CIBC SMART ACCOUNT': 'cibc_cheq',
                'VISA CAD': 'cibc_cc',
                'Savings Account': 'cibc_sav',
                'USD Savings Acct': 'cibc_us',

                'Save': 'ws_save',

                'E Package Chequing XXXXXXXX5015': 'vc_cheq',
                'Jumpstart High Interest XXXXXXXX1324': 'vc_sav'

            }[account_label]

            # check the date:
            row_date = dt.strptime(line[0], '%m/%d/%Y')

            if min_date and row_date < min_date:
                continue

            if max_date and row_date > max_date:
                continue

            parsed_row = {
                'account_name': account_name,
                'event_datetime': row_date,

                # original desc sometimes has no info at all!  we'll use the altered description
                'name': line[1].lower().strip().replace("'", "").replace(",", "")
            }
            if line[4] == 'debit':
                amt = - int(float(line[3]) * 100)
            elif line[4] == 'credit':
                amt = int(float(line[3]) * 100)
            else:
                print(f'unkown type!! {line[4]}')
                continue

            parsed_row['amount_cents'] = amt
            parsed_row['category'] = line[5]

            # for now we're dropping labels and notes
            parsed_data.append(parsed_row)

    # okay! we have some parsed data now :D

    # send them to get added to our existing transaction store.
    print('Done reading, adding transactions')
    import db_controller
    # transactions.add_new_transactions(account_name, parsed_data)
    for num, t in enumerate(parsed_data):
        print(num)
        db_controller.insert_transaction(t)


def add_balances(filepath, account_name):

    parsed_events = []
    with open(filepath) as rf:
        reader = csv.reader(rf, delimiter=',')  # todo: config these
        pos = None
        for i, line in enumerate(reader):

            if i == 0:
                if line[-1] == 'Assets':
                    pos = True
                elif line[-1] == 'Debts':
                    pos = False
                continue

            # print(line)
            target_date = dt.strptime(line[0], '%B %Y')
            amount = line[-1].replace('$', '').replace(',', '')
            amount_cents = int(float(amount)*100)
            amount_cents = - amount_cents if not pos else amount_cents

            event = {
                'event_datetime': target_date,
                'account_name': account_name,
                'amount_cents': amount_cents
            }

            print(f'{target_date} -> {amount_cents}')
            parsed_events.append(event)

    transactions.add_balances_to_db(parsed_events)


def get_current_balances():

    bals = transactions.get_all_balances()

    for b in bals:
        print(b)


get_current_balances()

# '{account_name}',
# '{event_datetime}',
# {amount_cents}

print(transactions.get_latest_trans_date())


# import sys
# sys.exit(0)

transactions.add_balances_to_db(
    [
        # {'account_name': 'cibc_cheq', 'event_datetime': dt.now(), 'amount_cents': '1366942'},
        # {'account_name': 'cibc_sav', 'event_datetime': dt.now(), 'amount_cents': '400000'},
        # {'account_name': 'cibc_cc', 'event_datetime': dt.now(), 'amount_cents': '0'},
        #
        # {'account_name': 'vc_cheq', 'event_datetime': dt.now(), 'amount_cents': '55474'},
        # {'account_name': 'vc_sav', 'event_datetime': dt.now(), 'amount_cents': '1700488'},
        #
        #
        # # # #
        # {'account_name': 'wf_tfsa', 'event_datetime': dt.now(), 'amount_cents': '3751110'},
        # {'account_name': 'ws_sav', 'event_datetime': dt.now(), 'amount_cents': '2038189'},
        # {'account_name': 'ws_trade', 'event_datetime': dt.now(), 'amount_cents': '168476'},
        # # # #
        # {'account_name': 'morgan_stanley', 'event_datetime': dt.now(), 'amount_cents': '193968'},
        #
        # {'account_name': 'sunlife_rrsp', 'event_datetime': dt.now(), 'amount_cents': '11307328'},

    ]
)

print('\n\n')
add_transactions_from_csv(
    '/Users/themadisons/Downloads/cibc(24).csv',  # mac
    'cibc_cheq'
)
#
# add_transactions_from_csv(
#     '/Users/themadisons/Downloads/cibc(25).csv',  # mac
#     'cibc_cc'
# )
#
#
# add_transactions_from_csv(
#     '/Users/themadisons/Downloads/statement (22).csv',  # mac
#     'vc_cheq'
# )
