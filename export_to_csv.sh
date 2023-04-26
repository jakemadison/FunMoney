touch main.csv;
touch balances.csv;

echo > main.csv;
echo > balances.csv;

sqlite3 main.db < export_csv.sql;

python3 ./interpolate_balances.py balances.csv

echo "all done."