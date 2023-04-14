"""
Things for managing transactions can go here.
"""
import textblob as textblob

import db_controller
from config import CAT_OVERRIDES
from textblob.classifiers import NaiveBayesClassifier
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.naive_bayes import MultinomialNB
from sklearn.pipeline import make_pipeline
from sklearn.metrics import accuracy_score

import cmd

# todo: don't rebuild model everytime.  Pickle it or something
MODEL = None


def build_classifier():

    """
    Accuracy on first pass 66%.
    - Use original descriptions in import
    - import the entire mint set
    - recheck accuracy

    :return:
    """

    statement = """
        select name, category from transactions where category is not null and category != 'idk' 
        order by random()
        limit 7000
        ;
    """
    db_res = db_controller.execute_on_db(statement)

    training_data = db_res['result']

    print(len(training_data))
    train = training_data[:-100]
    test = training_data[-100:]
    print(f'data: {len(training_data)}, train: {len(train)}, test: {len(test)}')
    # print(test)

    print('building classifier')
    classifier = NaiveBayesClassifier(train)
    print('done building classifier')

    print('assessing classifier')
    acc = round(classifier.accuracy(test), 2) * 100
    print(f'classifier accuracy: {acc}%')

    # return
    print('getting undetermined categories for matching...')
    statement = """
        select trim(name) from transactions where category is null or category = 'idk';
    """

    db_res = db_controller.execute_on_db(statement)

    targets = [r[0] for r in db_res['result']]

    print(f'iterating over {len(targets)} targets')

    for target in targets:
        cl_result = classifier.classify(target)
        prob_dist = classifier.prob_classify(target)
        prob_pos = round(prob_dist.prob(str(cl_result)), 2) * 100
        print(f'I think that: "{target}" should be a {cl_result} ({prob_pos}%)')


def play_with_sklearn_model():

    model = make_pipeline(TfidfVectorizer(), MultinomialNB())

    statement = """
        select name, category from transactions where category is not null and category != 'idk' 
        order by random()
        limit 70000
        ;
    """
    db_res = db_controller.execute_on_db(statement)

    training_data = db_res['result']

    print(len(training_data))
    train = training_data[:-100]
    test = training_data[-100:]
    print(f'data: {len(training_data)}, train: {len(train)}, test: {len(test)}')
    # print(test)

    print('building classifier')
    train_data = [t[0] for t in train]
    train_target = [t[1] for t in train]
    model.fit(train_data, train_target)
    print('done building classifier')

    print('assessing classifier')

    preds = model.predict([t[0] for t in test])

    acc = accuracy_score(
        [t[1] for t in test], preds
    )*100

    print(f'classifier accuracy: {acc}%')

    print('getting undetermined categories for matching...')
    statement = """
        select trim(name) from transactions where category is null or category = 'idk';
    """

    db_res = db_controller.execute_on_db(statement)

    targets = [r[0] for r in db_res['result']]

    print(f'iterating over {len(targets)} targets')

    for target in targets:
        cl_result = model.predict([target])[0]
        prob_pos = round(max(model.predict_proba([target])[0]*100), 2)
        print(f'I think that: "{target}" should be {cl_result} ({prob_pos}%)')


def init_model():

    global MODEL

    MODEL = make_pipeline(TfidfVectorizer(), MultinomialNB())

    statement = """
        select name, category from transactions where category is not null and category != 'idk' 
        order by random()
        ;
    """
    db_res = db_controller.execute_on_db(statement)

    training_data = db_res['result']

    print(len(training_data))
    train = training_data[:-100]
    test = training_data[-10:]
    print(f'data: {len(training_data)}, train: {len(train)}, test: {len(test)}')
    # print(test)

    print('building classifier')
    train_data = [t[0] for t in train]
    train_target = [t[1] for t in train]
    MODEL.fit(train_data, train_target)
    print('done building classifier')

    print('assessing model')
    preds = MODEL.predict([t[0] for t in test])

    acc = accuracy_score(
        [t[1] for t in test], preds
    ) * 100

    print(f'model accuracy: {acc}%')


def guess_category(event):

    """
    Use our model to try and guess a category.

    :param event:
    :return:
    """
    if MODEL is None:
        init_model()

    # print(event)

    target = event['name']
    cl_result = MODEL.predict(
        [target]
    )[0]

    prob_pos = round(
        max(
            MODEL.predict_proba(
                [event['name']]
            )[0]*100
        ),
        2
    )

    print(f'I think that: "{target}" should be {cl_result}  -- ({prob_pos}%)', end=' ')
    cat = input('Enter or replace with:')
    if cat != '':
        cl_result = cat

    return cl_result


def re_categorize():
    query = """
        select * from transactions where category='Uncategorized';
    """
    result = db_controller.execute_on_db(query)

    for r in result['result']:
        dict_r = dict(zip(result['schema'], r))
        # print(dict_r)
        cl_res = guess_category(dict_r)
        t_id = dict_r['transaction_id']
        updoot = f"update transactions set category = '{cl_res}' where transaction_id = {t_id};"
        db_controller.execute_on_db(updoot)


def foo_category(event):
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
                        name = '{stripped_event_name}' and
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

    # statement = """
    #     select distinct(category) from transactions;
    # """
    # all_cats = db_controller.execute_on_db(statement)

    for transaction in transaction_list:
        # one at a time is dumb but who cares.
        transaction['category'] = guess_category(transaction)
        db_controller.insert_transaction(transaction)


def matches_duplicate_transaction(target_transaction, sample_transactions):
    for each_transaction in sample_transactions:
        if (
                each_transaction['name'] == target_transaction['name'] and
                each_transaction['event_datetime'] == target_transaction['event_datetime'] and
                each_transaction['amount_cents'] == target_transaction['amount_cents'] and
                each_transaction['account_name'] == target_transaction['account_name']
        ):
            return True

    return False


def add_new_transactions(account_name, transaction_list, force_add=False):
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

    min_new_transaction = min([r['event_datetime'] for r in transaction_list])

    if force_add or not most_recent or min_new_transaction > most_recent['event_datetime']:
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

        # print(each_transaction, end=' ->')
        # if the transaction is earlier than our latest event, skip it.
        if each_transaction['event_datetime'] < most_recent['event_datetime']:
            # print('too young')
            continue  # skip it

        if each_transaction['event_datetime'] == most_recent['event_datetime']:
            transactions_at_date = db_controller.get_transactions_for_date(
                account_name, each_transaction['event_datetime']
            )

            print(f'found the following events {transactions_at_date}')
            if matches_duplicate_transaction(each_transaction, transactions_at_date):
                continue  # skip it

        valid_events.append(each_transaction)

    add_new_transactions_to_db(valid_events)
    print(f'successfully added {len(valid_events)} to db')


def add_balances_to_db(balances_list):

    for balance in balances_list:
        statement = """
            insert into balances (account_name, event_datetime, amount_cents) 
            values (
                '{account_name}',
                '{event_datetime}',
                {amount_cents}
            );
        """
        insert = statement.format(**balance)
        print(f'running {insert}')

        db_controller.execute_on_db(
            statement.format(**balance)
        )


def get_all_balances():
    statement = """
    select 
        account_name, amount_cents/100 as amount, most_recent,
        (sum(amount_cents) over ())/100 as total_amount  
    from
        (select 
            account_name, 
            amount_cents,
            event_datetime,
            max(event_datetime) over (partition by account_name) as most_recent
            
            from balances) b  
            where event_datetime = most_recent;
    """
    res = db_controller.execute_on_db(statement)
    return res['result']


def get_latest_trans_date():
    statement = """
        select account_name, max(event_datetime) from transactions group by 1 order by 1;
    """
    res = db_controller.execute_on_db(statement)
    return res['result']