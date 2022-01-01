"""
Configy things go in here.
"""
import os

"""
Our Current transactions table looks something like this:
CREATE TABLE transactions (transaction_id integer primary key, import_datetime datetime, 
account_name text, event_datetime datetime, name text, amount_cents integer, category text);
"""

DB_NAME = 'main.db'

BASE_PATH = os.path.dirname(__file__)
DB_PATH = os.path.join(BASE_PATH, DB_NAME)

EXPORT_DEFINITIONS = {
    'cibc_cheq': {

        # csv spec could go here.

        'columns':
            [
                {'field_name': 'event_date'},  # date formant could go here.
                {'field_name': 'event_name'},
                {'field_name': 'debit_amount'},
                {'field_name': 'credit_amount'}
            ]
    }
}
