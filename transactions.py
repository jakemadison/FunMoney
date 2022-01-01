"""
Things for managing transactions can go here.
"""

import db_controller
from config import CAT_OVERRIDES


def guess_category(event):
    """
    Given an event_name and account, try and guess what the category might be.

    At some point, this is where our set of overrides should live.

    :param event:
    :return:
    """

    # is there an override for this one?
    if event['name'] in CAT_OVERRIDES:
        return CAT_OVERRIDES[event['name']]

    # is there an exact match in the DB for this event + account?
    db_res = db_controller.execute_on_db(
        f"""
            select category, count(1) as cnt from (
                    select category from transactions where 
                        name = '{event['name']}' and
                        account_name = '{event['account_name']}'
                )
                group by 1 
                order by 2 desc 
                limit 1;
        """
    )

    if db_res['result']:
        # return the most popular category for those results:
        return db_res['result'][0][0]

    # is there an exact match in the DB for this event?
    db_res = db_controller.execute_on_db(
        f"""
            select category, count(1) as cnt from (
                    select category from transactions where 
                        name = '{event['name']}'
                )
                group by 1 
                order by 2 desc 
                limit 1;
        """
    )

    if db_res['result']:
        # return the most popular category for those results:
        return db_res['result'][0][0]

    # is there a close enough match for this event + account?
    stripped_event_name = ''.join([i for i in event['name'] if not i.isdigit()])
    db_res = db_controller.execute_on_db(
        f"""
            select category, count(1) as cnt from (
                    select category from transactions where 
                        name = '{stripped_event_name}'
                        account_name = '{event['account_name']}'
                )
                group by 1 
                order by 2 desc 
                limit 1;
        """
    )

    if db_res['result']:
        # return the most popular category for those results:
        return db_res['result'][0][0]

    # is there a close enough match for this event?
    db_res = db_controller.execute_on_db(
        f"""
            select category, count(1) as cnt from (
                    select category from transactions where 
                        name = '{stripped_event_name}'
                )
                group by 1 
                order by 2 desc 
                limit 1;
        """
    )

    if db_res['result']:
        # return the most popular category for those results:
        return db_res['result'][0][0]

    # is there a close enough override?

    # maybe word associations?

    # Levenshtein distance?

    return 'idk'


def add_new_transactions_to_db(transaction_list):

    for transaction in transaction_list:
        transaction['category'] = guess_category(transaction)

        # one at a time is dumb but who cares.
        db_controller.insert_transaction(transaction)




def add_new_transactions(account_name, transaction_list):
    """
    Given a list of transactions, attempt to add those transactions to the DB.

    Try and be smart about it though and not duplicate transactions.  Use event_time + account + event_name.

    For now, just assume this is all the same account.
    :param account_name
    :param transaction_list:
    :return:
    """

    # what's the most recent transaction on here?
    most_recent = db_controller.get_most_recent_transaction(account_name)

    # if our earliest transaction is later than this, add everything
    print(most_recent)

    max_new_transaction = max([r['event_datetime'] for r in transaction_list])

    if not most_recent or most_recent['event_datetime'] < max_new_transaction:
        print('add all transactions from this batch!')
        add_new_transactions_to_db(transaction_list)
        print(f'added {len(transaction_list)} transactions')
        return

    # otherwise we have some overlap here..
    print('there is some overlap!')
    # for now, lets just do this the easy way and just skip everything that's < our max event
    valid_events = []

    # todo: are there ever valid cases where we have older transactions than max that we want to add?
    for each_transaction in transaction_list:
        if each_transaction['event_datetime'] < most_recent['event_datetime']:
            continue  # skip it

        if each_transaction['event_datetime'] == most_recent['event_datetime']:
            transactions_at_date = db_controller.get_transactions_for_date(
                account_name, each_transaction['event_datetime']
            )
            event_names_at_date = [r['name'] for r in transactions_at_date]

            print(f'found the following event names {event_names_at_date}')

            if each_transaction['name'] in event_names_at_date:
                continue  # skip it

        valid_events.append(each_transaction)

    add_new_transactions_to_db(valid_events)
    print(f'successfully added {len(valid_events)} to db')
