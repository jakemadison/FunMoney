"""
Deal with SQLite3 here.
"""

import sqlite3

from config import DB_PATH


def execute_on_db(statement):

    conn = sqlite3.connect(DB_PATH)

    cur = conn.cursor()
    cur.execute(statement)
    result = cur.fetchall()
    print(f'resut is {result}')
    print(f'cursor desc is: {cur.description}')
    conn.commit()
    conn.close()

    return result


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


def add_new_transactions():
    pass


def update_category(target_id, new_category):

    """
    Update the category of a thing.
    :return:
    """
    statement = f"update transactions set category = '{new_category}' where transaction_id = {target_id}"
    execute_on_db(statement)

