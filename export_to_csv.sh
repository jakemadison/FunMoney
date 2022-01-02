echo > main.csv;
sqlite3 main.db < export_csv.sql;
echo "all done."