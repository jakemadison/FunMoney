"""
Adminy things go in here.
Most important is updating transactions.
"""


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

    # so, open the file, read in each line.
    with open(filepath) as rf:
        for line in rf:
            print(line.strip())






