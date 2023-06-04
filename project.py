import functools
from db_operations import connect_db, write_to_db
from data_handling import load_data, convert_to_df, split_data
from gui_operations import create_window, create_labels, update_labels, create_plot_button

file_name = 'node6Eleousa.json'
db_name = 'measurements.db'
table_name = 'measurements'
timestamp_col = 'timestamp'
split_date = '2022-12-01'
window_title = "Smog Atmosphere Monitor"

parameters = {
    'O_3': ['ppm', 120], 
    'Environment Temperature': ['℃', None],  
    'Humidity': ['%', None],  
    'Sensor Node Battery': ['%', None], 
    'PM 1.0': ['µg/m3', 25], 
    'PM 2.5': ['µg/m3', 50], 
    'PM 10': ['µg/m3', None],  
    'SO_2': ['ppm', 350], 
    'NO': ['ppm', None],  
    'NO_2': ['ppm', 200], 
    'Pressure': ['Pa', None]  
}

data = load_data(file_name)

df = convert_to_df(data)

historical_data, current_data = split_data(df, timestamp_col, split_date)

# Sort the current data by timestamp
current_data = current_data.sort_values(timestamp_col)

conn = connect_db(db_name)

write_to_db(historical_data, table_name, conn)

root = create_window(window_title)

labels = create_labels(root, parameters, conn)

current_data_iter = iter(current_data.itertuples(index=False))

# Convert the function to one that doesn't require any arguments
update_labels_no_args = functools.partial(update_labels, root, labels, parameters, conn, current_data_iter, table_name)

# Initiate the update cycle
root.after(1000, lambda: update_labels(root, labels, parameters, conn, current_data_iter, table_name))

create_plot_button(root, parameters, conn)

root.mainloop()
