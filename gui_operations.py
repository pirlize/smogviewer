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
    for id, parameter in enumerate(parameters.keys(), start=3):
        parameter_label = tk.Label(root, text=parameter)
        parameter_label.grid(row=id, column=0, sticky='w', padx=10, pady=5)

        df_from_db = read_from_db(f'SELECT * FROM measurements WHERE sensor_type_id={id} ORDER BY timestamp DESC LIMIT 1', conn)
        if not df_from_db.empty:
            value = df_from_db['value'].values[0]
        else:
            value = "No Data"

        value_label = tk.Label(root, text=f"{value} {parameters[parameter]}")
        value_label.grid(row=id, column=1, sticky='w', padx=10, pady=5)
        labels[parameter] = value_label 
    
    aqi_label = tk.Label(root, text="AQI")
    aqi_label.grid(row=len(parameters.keys())+3, column=0, sticky='w', padx=10, pady=5)
    aqi_value_label = tk.Label(root, text="No Data")
    aqi_value_label.grid(row=len(parameters.keys())+3, column=1, sticky='w', padx=10, pady=5)
    labels["AQI"] = aqi_value_label

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

    # AQI calculation
    pm25_df = read_from_db(f'SELECT * FROM measurements WHERE sensor_type_id={list(parameters.keys()).index("PM 2.5") + 3} ORDER BY timestamp DESC LIMIT 1', conn)
    pm10_df = read_from_db(f'SELECT * FROM measurements WHERE sensor_type_id={list(parameters.keys()).index("PM 10") + 3} ORDER BY timestamp DESC LIMIT 1', conn)
    if not pm25_df.empty and not pm10_df.empty:
        pm25_value = pm25_df['value'].values[0]
        pm10_value = pm10_df['value'].values[0]
        aqi_value = (pm25_value + pm10_value) / 2
        labels['AQI'].config(text = f"{aqi_value} AQI") 

    # Initiate the next update
    root.after(1000, lambda: update_labels(root, labels, parameters, conn, current_data_iter, table_name))



def plot_data(parameter, root, parameters, conn):
    # Get the selected time period from the dropdown menu
    time_period = root.children['time_period_dropdown'].get()
    
    if parameter == 'AQI':
        id_pm25 = list(parameters.keys()).index('PM 2.5') + 3
        id_pm10 = list(parameters.keys()).index('PM 10') + 3
        query_pm25 = construct_query(id_pm25, time_period)
        query_pm10 = construct_query(id_pm10, time_period)
        df_pm25 = read_from_db(query_pm25, conn)
        df_pm10 = read_from_db(query_pm10, conn)
        df_pm25['timestamp'] = pd.to_datetime(df_pm25['timestamp'])
        df_pm10['timestamp'] = pd.to_datetime(df_pm10['timestamp'])
        df_pm25.set_index('timestamp', inplace=True)
        df_pm10.set_index('timestamp', inplace=True)
        df_pm25 = df_pm25.resample('1H').mean()
        df_pm10 = df_pm10.resample('1H').mean()
        df = pd.DataFrame()
        df['value'] = (df_pm25['value'] + df_pm10['value']) / 2
    else:
        id_parameter = list(parameters.keys()).index(parameter) + 3
        query = construct_query(id_parameter, time_period)
        df = read_from_db(query, conn)
        df['timestamp'] = pd.to_datetime(df['timestamp'])
        df.set_index('timestamp', inplace=True)
        df = df.resample('1H').mean()

    fig = plt.Figure(figsize=(12, 6))
    ax = fig.add_subplot(111)
    ax.plot(df['value'])
    ax.set_title(f'{parameter} Over Time')
    ax.set_xlabel('Timestamp')
    ax.set_ylabel(f'{parameter} ({parameters[parameter][0] if parameter != "AQI" else "AQI"})')

    plot_window = tk.Toplevel(root)
    canvas = FigureCanvasTkAgg(fig, master=plot_window)  # pass plot_window as master
    canvas.draw()
    canvas.get_tk_widget().pack()


def construct_query(id, time_period):
    last_year = datetime.datetime.now().year - 1
    # Translate the selected time period into a SQL query
    if time_period == 'Last Year':
        query = f'SELECT * FROM measurements WHERE sensor_type_id={id} AND timestamp BETWEEN "{last_year}-01-01" AND "{last_year}-12-31"'
    elif time_period == 'Last Quarter':
        query = f'SELECT * FROM measurements WHERE sensor_type_id={id} AND timestamp BETWEEN "{last_year}-09-01" AND "{last_year}-12-31"'
    elif time_period == 'Last Month':
        query = f'SELECT * FROM measurements WHERE sensor_type_id={id} AND timestamp BETWEEN "{last_year}-11-01" AND "{last_year}-11-30"'
    elif time_period == 'Last Day':
        query = f'SELECT * FROM measurements WHERE sensor_type_id={id} AND timestamp BETWEEN "{last_year}-11-30" AND "{last_year}-11-31"'
    else:  # 'Live'
        query = f'SELECT * FROM measurements WHERE sensor_type_id={id}'

    return query

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

