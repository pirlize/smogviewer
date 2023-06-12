import pandas as pd
import json

# Φόρτωση δεδομένων από ένα αρχείο JSON
def load_data(file_name):
    with open(file_name) as f:
        data = json.load(f)
    return data

# Μετατροπή των δεδομένων σε DataFrame
def convert_to_df(data):
    df = pd.DataFrame(data['6_measurements'])
    return df

# Διαίρεση των δεδομένων σε ιστορικά και τρέχοντα
def split_data(df, timestamp_col, split_date):
    historical_data = df[df[timestamp_col] < split_date]
    current_data = df[df[timestamp_col] >= split_date]
    current_data = current_data.copy().sort_values(timestamp_col)
    return historical_data, current_data
