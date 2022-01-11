.headers on
.mode csv
.output main.csv
select * from transactions;

.output balances.csv
select * from balances;