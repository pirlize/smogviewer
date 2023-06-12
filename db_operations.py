import sqlite3
import pandas as pd

# Σύνδεση με τη βάση δεδομένων
def connect_db(db_name):
    conn = sqlite3.connect(db_name)
    return conn

# Εγγραφή δεδομένων στη βάση
def write_to_db(df, table_name, conn, if_exists='replace'):
    df.to_sql(table_name, conn, if_exists=if_exists, index=False)

# Ανάγνωση δεδομένων από τη βάση
def read_from_db(query, conn):
    df = pd.read_sql(query, conn)
    return df