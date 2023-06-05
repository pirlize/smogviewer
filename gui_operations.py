import datetime
import tkinter as tk
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from tkinter import ttk
from db_operations import read_from_db
from ttkthemes import ThemedTk

def create_window(window_title):
    root = ThemedTk(theme="arc")  # arc is a nice clean theme
    root.title(window_title)
    
    # Dropdown menu to select time period
    time_period_label = tk.Label(root, text="Select Time Period")
    time_period_label.grid(row=0, column=0, sticky='w', padx=10, pady=10)

    # Choices for time periods
    choices = ['Last Year', 'Last Quarter', 'Last Month', 'Last Day', 'Live']
    
    # Create the dropdown menu
    time_period = tk.StringVar() 
    time_period_dropdown = ttk.Combobox(root, textvariable = time_period, values = choices, name='time_period_dropdown')

    # Set the default time period
    time_period_dropdown.current(0)
    time_period_dropdown.grid(row=0, column=1, sticky='e', padx=10, pady=10)

    return root

def create_labels(root, parameters, conn):
    labels = {}
    for idx, parameter in enumerate(parameters.keys(), start=1):
        ttk.Label(root, text=parameter).grid(row=idx, column=0, sticky="W", padx=20, pady=10)
        df_from_db = read_from_db(f'SELECT * FROM measurements WHERE sensor_type_id={idx+2} ORDER BY timestamp DESC LIMIT 1', conn)

        if not df_from_db.empty:
            value = df_from_db['value'].values[0]
        else:
            value = "No Data"

        value_label = ttk.Label(root, text=f"{value} {parameters[parameter]}")
        value_label.grid(row=idx, column=1, sticky="E", padx=20)
        labels[parameter] = value_label
    return labels


def update_labels(root, labels, parameters, conn, current_data_iter, table_name):
    try:
        record = next(current_data_iter)
        pd.DataFrame([record]).to_sql(table_name, conn, if_exists='append', index=False)
    except StopIteration:
        pass
    for id, parameter in enumerate(parameters.keys(), start=3):
        df_from_db = read_from_db(f'SELECT * FROM measurements WHERE sensor_type_id={id} ORDER BY timestamp DESC LIMIT 1', conn)
        if not df_from_db.empty:
            value = df_from_db['value'].values[0]
        else:
            value = "No Data"

        labels[parameter].config(text = f"{value} {parameters[parameter][0]}")  
        
        limit = parameters[parameter][1]
        if limit is not None:  
            if value != "No Data" and float(value) > limit:  
                tk.messagebox.showwarning("Warning", f"{parameter} value exceeds the limit!")

    # Initiate the next update
    root.after(1000, lambda: update_labels(root, labels, parameters, conn, current_data_iter, table_name))



def plot_data(parameter, root, parameters, conn):
    # Get the selected time period from the dropdown menu
    time_period = root.children['time_period_dropdown'].get()
    
    id = list(parameters.keys()).index(parameter) + 3
    last_year = datetime.datetime.now().year - 1
    # Translate the selected time period into a SQL query
    if time_period == 'Last Year':
        query = f'SELECT * FROM measurements WHERE sensor_type_id={id} AND timestamp BETWEEN "{last_year}-01-01" AND "{last_year}-12-31"'
    elif time_period == 'Last Quarter':
        query = f'SELECT * FROM measurements WHERE sensor_type_id={id} AND timestamp BETWEEN "{last_year}-09-01" AND "{last_year}-12-31"'
    elif time_period == 'Last Month':
        query = f'SELECT * FROM measurements WHERE sensor_type_id={id} AND timestamp BETWEEN "{last_year}-11-01" AND "{last_year}-11-31"'
    elif time_period == 'Last Day':
        query = f'SELECT * FROM measurements WHERE sensor_type_id={id} AND timestamp BETWEEN "{last_year}-11-30" AND "{last_year}-11-31"'
    else:  # 'Live'
        query = f'SELECT * FROM measurements WHERE sensor_type_id={id}'
    
    df = read_from_db(query, conn)
    #df = read_from_db(f'SELECT * FROM measurements WHERE sensor_type_id={id}', conn)

    df['timestamp'] = pd.to_datetime(df['timestamp'])

    df.set_index('timestamp', inplace=True)

    fig = plt.Figure(figsize=(12, 6))
    ax = fig.add_subplot(111)
    ax.plot(df['value'])
    ax.set_title(f'{parameter} Over Time')
    ax.set_xlabel('Timestamp')
    ax.set_ylabel(f'{parameter} ({parameters[parameter][0]})')

    plot_window = tk.Toplevel(root)
    canvas = FigureCanvasTkAgg(fig, master=plot_window)  # pass plot_window as master
    canvas.draw()
    canvas.get_tk_widget().pack()

def create_plot_button(root, parameters, conn):
    # Create a dropdown menu with all parameters as options
    parameter_list = list(parameters.keys()) + ['AQI']
    param_var = tk.StringVar(root)
    param_var.set(parameter_list[0])  # Set the default option to the first parameter
    
    param_label = tk.Label(root, text="Select Measurement")
    param_label.grid(row=1, column=0, sticky='w', padx=10, pady=10)

    parameter_dropdown = ttk.Combobox(root, textvariable=param_var, values=parameter_list)
    parameter_dropdown.grid(row=1, column=1, sticky='w', padx=10, pady=10)
    
    # Create button to plot data. The parameter to be plotted is fetched from the dropdown menu.
    plot_button = ttk.Button(root, text="Plot Data", command=lambda: plot_data(param_var.get(), root, parameters, conn))
    plot_button.grid(row=1, column=2, sticky='e', padx=10, pady=10)

