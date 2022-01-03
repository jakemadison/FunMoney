"""
Deal with SQLite3 here.
"""

import sqlite3

from config import DB_PATH


def execute_on_db(statement):

    conn = sqlite3.connect(DB_PATH, detect_types=sqlite3.PARSE_DECLTYPES)
    # conn.row_factory = sqlite3.Row

    cur = conn.cursor()
    cur.execute(statement)

    result = cur.fetchall()
    # print(f'result is {result}')

    if cur.description is None:
        schema = ''
    else:
        schema = [f[0] for f in cur.description]

    # print(f'cursor desc is: {schema}')

    conn.commit()
    conn.close()

    return {
        'schema': schema,
        'result': result
    }


def get_transactions(num_days=None):
    """
    Get transactions for n days.  If None, get them all.

    :param num_days:
    :return:
    """
    if num_days is None:
        statement = """
            select * from transactions;
        """

    result = execute_on_db(statement)
    return result


def update_category(target_id, new_category):

    """
    Update the category of a thing.
    :return:
    """
    statement = f"update transactions set category = '{new_category}' where transaction_id = {target_id}"
    execute_on_db(statement)


def get_transactions_by_name(event_name, account=None):

    if account is None:
        statement = f"select * from transactions where name='{event_name}';"
    else:
        statement = f"select * from transactions where account_name='{account}' and name='{event_name}';"

    db_result = execute_on_db(statement)
    if not db_result['result']:
        return []

    dict_res = []
    for row in db_result['result']:
        dict_res.append(
            dict(zip(db_result['schema'], row))
        )

    return dict_res


def get_transactions_for_date(account_name, target_datetime):

    statement = f"select * from transactions where account_name = '{account_name}' and event_datetime = '{target_datetime}';"
    db_result = execute_on_db(statement)

    if not db_result['result']:
        return []

    dict_res = []
    for row in db_result['result']:
        dict_res.append(
            dict(zip(db_result['schema'], row))
        )
    return dict_res


def get_most_recent_transaction(account_name):
    """
    Just return it as a dict if it exists.
    :param account_name:
    :return:
    """

    statement = f"select * from transactions where account_name = '{account_name}' order by event_datetime desc limit 1"
    result = execute_on_db(statement)

    if not result['result']:
        return []

    return dict(
        zip(
            result['schema'],
            result['result'][0]
        )
    )


def insert_transaction(transaction):
    """
    CREATE TABLE transactions (transaction_id integer primary key, import_datetime datetime,
    account_name text, event_datetime datetime, name text, amount_cents integer, category text);
    :param transaction:
    :return:
    """
    statement = """
        insert into transactions (import_datetime, account_name, event_datetime, name, amount_cents, category) 
        values (
            datetime(),
            '{account_name}',
            '{event_datetime}',
            '{name}',
            {amount_cents},
            '{category}' 
        );
    """
    insert = statement.format(**transaction)
    # print(f'running {insert}')
    try:
        execute_on_db(
            statement.format(**transaction)
        )
    except Exception:
        print(f'insert was {insert}')
        raise
