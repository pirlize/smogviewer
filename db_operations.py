import sqlite3
import pandas as pd

def connect_db(db_name):
    conn = sqlite3.connect(db_name)
    return conn

def write_to_db(df, table_name, conn, if_exists='replace'):
    df.to_sql(table_name, conn, if_exists=if_exists, index=False)

def read_from_db(query, conn):
    df = pd.read_sql(query, conn)
    return df



