import functools
from db_operations import connect_db, write_to_db
from data_handling import load_data, convert_to_df, split_data
from gui_operations import create_window, create_labels, update_labels, create_plot_button, parameter_ids

file_name = 'node6Eleousa.json'
db_name = 'measurements.db'
table_name = 'measurements'
timestamp_col = 'timestamp'
split_date = '2022-12-01'
window_title = "Smog Atmosphere Monitor"

#Αισθητήρας, μονάδα μέτρησης, όριο
parameters = {
    'O_3': ['ppm', 0.10], 
    'Environment Temperature': ['℃', None],  
    'Humidity': ['%', None],  
    'Sensor Node Battery': ['%', None], 
    'PM 1.0': ['µg/m3', 2.0], 
    'PM 2.5': ['µg/m3', 5.0], 
    'PM 10': ['µg/m3', None],  
    'SO_2': ['ppm', 3.50], 
    'NO': ['ppm', None],  
    'NO_2': ['ppm', 2.00], 
    'Pressure': ['Pa', None]  
}

# Φόρτωση δεδομένων
data = load_data(file_name)

# Μετατροπή δεδομένων σε DataFrame
df = convert_to_df(data)

# Διαίρεση δεδομένων σε ιστορικά και τρέχοντα
historical_data, current_data = split_data(df, timestamp_col, split_date)

# Σορτάρισμα των current data by timestamp
current_data = current_data.sort_values(timestamp_col)

# Σύνδεση με τη βάση δεδομένων
conn = connect_db(db_name)

# Εγγραφή ιστορικών δεδομένων στη βάση
write_to_db(historical_data, table_name, conn)

# Έναρξη παράθυρου GUI
root = create_window(window_title)

# Δημιουργία ετικετών
labels = create_labels(root, parameters, parameter_ids, conn)

# Έναρξη της ενημέρωσης των ετικετών με τα τρέχοντα δεδομένα
current_data_iter = iter(current_data.itertuples(index=False))

# Μετατροπή της συνάρτησης σε μία που δεν απαιτεί καμία παράμετρο
update_labels_no_args = functools.partial(update_labels, root, labels, parameters, conn, current_data_iter, table_name)

# Έναρξη του κύκλου ενημέρωσης (1000 = ανά δευτερόλεπτο, 10000 = ανά 10'' και 100000 = ανά λεπτό)
root.after(1000, lambda: update_labels(root, labels, parameters, conn, current_data_iter, table_name))

# Δημιουργία κουμπιού για τo plot δεδομένων
create_plot_button(root, parameters, conn)

root.mainloop()
