"""
Add in all missing days for all accounts along with their current balance.




"""

import sys
import csv
import datetime as dt

dt_fmt = '%Y-%m-%d'
target = sys.argv[1]

parsed_data = {}
tracked_accounts = []
min_date = None
max_date = None

interpolate_with_balances = True

# do a single pass to parse the data:
with open(target) as f:
    reader = csv.reader(f)
    for i, line in enumerate(reader):
        # skip header
        if i == 0:
            continue

        e_date, account, balance = line
        parsed_date = dt.datetime.strptime(e_date, dt_fmt)

        # init on first line
        if i == 1:
            min_date = parsed_date

        if account not in tracked_accounts:
            tracked_accounts.append(account)

        if e_date not in parsed_data:
            parsed_data[e_date] = {}

        parsed_data[e_date][account] = balance
        # max_date = parsed_date


# now do a pass to read in daily_transactions.csv
daily_transaction_data = {}
with open('daily_transactions.csv') as f:
    reader = csv.reader(f)
    for i, line in enumerate(reader):
        # skip header
        if i == 0:
            continue

        e_date, account, amount = line

        if e_date not in daily_transaction_data:
            daily_transaction_data[e_date] = {}
        daily_transaction_data[e_date][account] = amount


export_rows = []
curr_date = min_date
curr_acct_balance = {}

max_date = dt.datetime.now().date()

# now do the actual work of interpolating:
while curr_date.date() <= max_date:
    for account in tracked_accounts:
        # look up from parsed:
        day_node = parsed_data.get(curr_date.strftime(dt_fmt), {})
        days_balance = day_node.get(account)

        # fall back to current tracking:
        if days_balance is None:
            days_balance = curr_acct_balance.get(account)

        # skip this row
        if days_balance is None:
            continue

        if interpolate_with_balances:
            # now modify by the sum of transactions on that day:
            transaction_modifier = daily_transaction_data.get(curr_date.strftime(dt_fmt), {}).get(account)
            if transaction_modifier is not None:
                days_balance = int(days_balance) + int(transaction_modifier)

        row = [
            curr_date.strftime(dt_fmt),
            account,
            days_balance
        ]
        export_rows.append(row)
        curr_acct_balance[account] = days_balance

    curr_date += dt.timedelta(days=1)


# write out to file
with open('interpolated_daily_bal.csv', 'w') as f:
    writer = csv.writer(f)
    for i, row in enumerate(export_rows):
        writer.writerow(row)





