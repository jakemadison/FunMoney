.headers on
.mode csv
.output main.csv
select * from transactions;

.output balances.csv
select date(event_datetime), account_name, amount_cents from balances order by event_datetime;

.output daily_transactions.csv
select date(event_datetime), account_name, sum(amount_cents) from transactions group by 1,2 order by event_datetime;

-- .output daily_balances.csv
-- select * from daily_balances;
