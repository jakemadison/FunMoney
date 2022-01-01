"""
Adminy things go in here.
Most important is updating transactions.
"""

import csv
from datetime import datetime as dt
from config import EXPORT_DEFINITIONS


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
            print(line)

            parsed_row = []

            # todo: what about rows with not enough data?
            for each_def_col, each_col in zip(target_def['columns'], line):
                if each_def_col['field_name'] == 'event_date':
                    val = dt.strptime(each_col, '%Y-%m-%d')

                if each_def_col['field_name'] == 'event_name':
                    val = each_col.lower().strip()

                if each_def_col['field_name'] == 'credit_amount':
                    val = int(float(each_col) * 100)

                # we'll store debits as negative rather than apply a label somewhere
                if each_def_col['field_name'] == 'debit_amount':
                    val = - int(float(each_col) * 100)

                parsed_row.append(
                    {
                        each_def_col['field_name']: val
                    }
                )
            parsed_data.append(parsed_row)


    for row in parsed_data:
        print(row)







add_transactions_from_csv(
    '/Users/themadisons/Downloads/cibc (4).csv',
    'cibc_cheq'
)
