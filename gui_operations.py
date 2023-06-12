import datetime
import tkinter as tk
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from tkinter import ttk
from db_operations import read_from_db
from ttkthemes import ThemedTk

# Αντιστοιχία αισθητήρων με τα ID τους
parameter_ids = {
    'O_3': 3, 
    'Environment Temperature': 4,  
    'Humidity': 5,  
    'Sensor Node Battery': 6, 
    'PM 1.0': 8, 
    'PM 2.5': 9, 
    'PM 10': 10,  
    'SO_2': 11, 
    'NO': 12,  
    'NO_2': 13, 
    'Pressure': 14
}

# Δημιουργία του παραθύρου της εφαρμογής
def create_window(window_title):
    root = ThemedTk(theme="arc")  # θέμα arc για καθαρή εμφάνιση
    root.title(window_title)
    
    # Dropdown menu για την επιλογή της χρονικής περιόδου
    time_period_label = tk.Label(root, text="Select Time Period")
    time_period_label.grid(row=0, column=0, sticky='w', padx=10, pady=10)

    # Επιλογές για χρονικές περιόδους
    choices = ['Last Year', 'Last Quarter', 'Last Month', 'Last Day', 'Live']
    
   # Δημιουργία του dropdown μενού για χρονικές περιόδους
    time_period = tk.StringVar() 
    time_period_dropdown = ttk.Combobox(root, textvariable = time_period, values = choices, name='time_period_dropdown')

    # Ορισμός της προεπιλεγμένης χρονικής περιόδου
    time_period_dropdown.current(0)
    time_period_dropdown.grid(row=0, column=1, sticky='e', padx=10, pady=10)

    return root

# Δημιουργία των ετικετών που εμφανίζουν τις τιμές των παραμέτρων
def create_labels(root, parameters, parameter_ids, conn):
    labels = {} # Λεξικό που θα αποθηκεύσει τις ετικέτες για κάθε παράμετρο
    for parameter in parameters.keys(): # Διατρέχουμε κάθε παράμετρο
        # Δημιουργία ετικέτας για την παράμετρο και τοποθέτηση στο grid του Tkinter
        parameter_label = tk.Label(root, text=parameter)
        parameter_label.grid(row=parameter_ids[parameter], column=0, sticky='w', padx=10, pady=5)
        
        # Διάβασμα της τελευταίας τιμής της παραμέτρου από τη βάση δεδομένων
        df_from_db = read_from_db(f'SELECT * FROM measurements WHERE sensor_type_id={parameter_ids[parameter]} ORDER BY timestamp DESC LIMIT 1', conn)
        # Εάν υπάρχει τιμή, την αναθέτουμε στη μεταβλητή value, διαφορετικά της αναθέτουμε την τιμή "No Data"
        if not df_from_db.empty:
            value = df_from_db['value'].values[0]
        else:
            value = "No Data"
            
        # Δημιουργία ετικέτας για την τιμή της παραμέτρου και τοποθέτηση στο grid του Tkinter
        value_label = tk.Label(root, text=f"{value} {parameters[parameter][0]}")
        value_label.grid(row=parameter_ids[parameter], column=1, sticky='w', padx=10, pady=5)
        
        # Αποθήκευση της ετικέτας τιμής στο λεξικό labels
        labels[parameter] = value_label 
        
    # Δημιουργία ετικετών για τον AQI (Air Quality Index)
    aqi_label = tk.Label(root, text="AQI")
    aqi_label.grid(row=len(parameters.keys())+3, column=0, sticky='w', padx=10, pady=5)
    aqi_value_label = tk.Label(root, text="No Data")
    aqi_value_label.grid(row=len(parameters.keys())+3, column=1, sticky='w', padx=10, pady=5)
    labels["AQI"] = aqi_value_label # Αποθήκευση της ετικέτας AQI στο λεξικό labels

    return labels

# Ενημέρωση των ετικετών με τις νεότερες τιμές των παραμέτρων
def update_labels(root, labels, parameters, conn, current_data_iter, table_name):
    try:
        record = next(current_data_iter) # Διάβασμα της επόμενης εγγραφής από τον iterator
        pd.DataFrame([record]).to_sql(table_name, conn, if_exists='append', index=False) # Προσθήκη της εγγραφής στη βάση δεδομένων
    except StopIteration: # Εάν έχουμε φτάσει στο τέλος του iterator, προσπερνάμε την ενημέρωση
        pass
     # Ενημέρωση της τιμής για κάθε παράμετρο
    for parameter in parameters.keys():
        id = parameter_ids[parameter] # Λήψη του id της παραμέτρου
        # Διάβασμα της τελευταίας τιμής της παραμέτρου από τη βάση δεδομένων
        df_from_db = read_from_db(f'SELECT * FROM measurements WHERE sensor_type_id={id} ORDER BY timestamp DESC LIMIT 1', conn)
        # Εάν υπάρχει τιμή, την αναθέτουμε στη μεταβλητή value, διαφορετικά της αναθέτουμε την τιμή "No Data"
        if not df_from_db.empty:
            value = df_from_db['value'].values[0]
        else:
            value = "No Data"
            
        # Ενημέρωση της ετικέτας τιμής της παραμέτρου στο γραφικό περιβάλλον
        labels[parameter].config(text = f"{value} {parameters[parameter][0]}")  
        
        # Έλεγχος εάν η τιμή υπερβαίνει το όριο και εμφάνιση προειδοποιητικού μηνύματος εάν υπερβαίνει
        limit = parameters[parameter][1]
        if limit is not None:  
            if value != "No Data" and float(value) > limit:  
                tk.messagebox.showwarning("Warning", f"{parameter} value exceeds the limit!")

    # Υπολογισμός και ενημέρωση της τιμής του AQI (Air Quality Index)
    pm25_df = read_from_db(f'SELECT * FROM measurements WHERE sensor_type_id={parameter_ids["PM 2.5"]} ORDER BY timestamp DESC LIMIT 1', conn)
    pm10_df = read_from_db(f'SELECT * FROM measurements WHERE sensor_type_id={parameter_ids["PM 10"]} ORDER BY timestamp DESC LIMIT 1', conn)
    if not pm25_df.empty and not pm10_df.empty:
        pm25_value = pm25_df['value'].values[0]
        pm10_value = pm10_df['value'].values[0]
        aqi_value = (pm25_value + pm10_value) / 2
        labels['AQI'].config(text = f"{aqi_value} AQI") 

    # Εκκίνηση της επόμενης ενημέρωσης μετά από 1 δευτερόλεπτο
    root.after(1000, lambda: update_labels(root, labels, parameters, conn, current_data_iter, table_name))


# Σχεδίαση των δεδομένων της επιλεγμένης παραμέτρου
def plot_data(parameter, root, parameters, parameter_ids, conn):
    # Λήψη της επιλεγμένης χρονικής περιόδου από το αναπτυσσόμενο μενού
    time_period = root.children['time_period_dropdown'].get()
    
    # Αν η επιλεγμένη παράμετρος είναι το AQI, πρέπει να διαχειριστούμε δύο σετ δεδομένων (PM2.5 και PM10)
    if parameter == 'AQI':
        # Κατασκευή των queries για τη βάση δεδομένων για τα PM2.5 και PM10
        id_pm25 = parameter_ids['PM 2.5']
        id_pm10 = parameter_ids['PM 10']
        query_pm25 = construct_query(id_pm25, time_period)
        query_pm10 = construct_query(id_pm10, time_period)
        # Διάβασμα των δεδομένων από τη βάση δεδομένων
        df_pm25 = read_from_db(query_pm25, conn)
        df_pm10 = read_from_db(query_pm10, conn)
        # Μετατροπή των σημείων χρόνου σε datetime και ρύθμιση τους ως δείκτες
        df_pm25['timestamp'] = pd.to_datetime(df_pm25['timestamp'])
        df_pm10['timestamp'] = pd.to_datetime(df_pm10['timestamp'])
        df_pm25.set_index('timestamp', inplace=True)
        df_pm10.set_index('timestamp', inplace=True)
        # Αναδιαμόρφωση των δεδομένων για να έχουμε μια τιμή ανά ώρα
        df_pm25 = df_pm25.resample('1H').mean()
        df_pm10 = df_pm10.resample('1H').mean()
        # Υπολογισμός του AQI ως τον μέσο όρο των PM2.5 και PM10
        df = pd.DataFrame()
        df['value'] = (df_pm25['value'] + df_pm10['value']) / 2
    else:
        # Για οποιαδήποτε άλλη παράμετρο, απλώς κατασκευάζουμε το query και διαβάζουμε τα δεδομένα από τη βάση δεδομένων
        id_parameter = parameter_ids[parameter]
        query = construct_query(id_parameter, time_period)
        df = read_from_db(query, conn)
        df['timestamp'] = pd.to_datetime(df['timestamp'])
        df.set_index('timestamp', inplace=True)
        df = df.resample('1H').mean()

    # Δημιουργία της γραφικής παράστασης
    fig = plt.Figure(figsize=(12, 6))
    ax = fig.add_subplot(111)
    ax.plot(df['value'])
    ax.set_title(f'{parameter} Over Time')
    ax.set_xlabel('Timestamp')
    ax.set_ylabel(f'{parameter} ({parameters[parameter][0] if parameter != "AQI" else "AQI"})')

    # Εμφάνιση της γραφικής παράστασης σε ένα νέο παράθυρο
    plot_window = tk.Toplevel(root)
    canvas = FigureCanvasTkAgg(fig, master=plot_window)  # περνάμε το plot_window ως master
    canvas.draw()
    canvas.get_tk_widget().pack()

# Κατασκευή query βάσει της επιλεγμένης χρονικής περιόδου
def construct_query(id, time_period):
    last_year = datetime.datetime.now().year - 1
    # Μεταφορά της επιλεγμένης χρονικής περιόδου σε SQL query
    if time_period == 'Last Year':
        query = f'SELECT * FROM measurements WHERE sensor_type_id={id} AND timestamp BETWEEN "{last_year}-01-01" AND "{last_year}-12-31"'
    elif time_period == 'Last Quarter':
        query = f'SELECT * FROM measurements WHERE sensor_type_id={id} AND timestamp BETWEEN "{last_year}-09-01" AND "{last_year}-12-31"'
    elif time_period == 'Last Month':
        query = f'SELECT * FROM measurements WHERE sensor_type_id={id} AND timestamp BETWEEN "{last_year}-11-01" AND "{last_year}-11-30"'
    elif time_period == 'Last Day':
        query = f'SELECT * FROM measurements WHERE sensor_type_id={id} AND timestamp BETWEEN "{last_year}-11-30" AND "{last_year}-11-31"'
    else:  # 'Live'
        query = f'SELECT * FROM measurements WHERE sensor_type_id={id} AND timestamp BETWEEN "{last_year}-12-01" AND "{last_year}-12-31"'

    return query

# δημιουργία κουμπιού που επιτρέπει στον χρήστη να επιλέγει και να ζητά ένα plot για μια συγκεκριμένη παράμετρο
def create_plot_button(root, parameters, conn):
    # Δημιουργία dropdown μενού με όλες τις παραμέτρους ως επιλογές
    parameter_list = list(parameters.keys()) + ['AQI']
    param_var = tk.StringVar(root)
    param_var.set(parameter_list[0])  # Ορίσμος προεπιλεγμένης επιλογής στην πρώτη παράμετρο
    
    param_label = tk.Label(root, text="Select Measurement")
    param_label.grid(row=1, column=0, sticky='w', padx=10, pady=10)

    parameter_dropdown = ttk.Combobox(root, textvariable=param_var, values=parameter_list)
    parameter_dropdown.grid(row=1, column=1, sticky='w', padx=10, pady=10)
    
    # Δημιουργία κουμπιού για τo plot δεδομένων. Η παράμετρος που πρόκειται να επιδειχθεί λαμβάνεται από το dropdown μενού.
    plot_button = ttk.Button(root, text="Plot Data", command=lambda: plot_data(param_var.get(), root, parameters, parameter_ids, conn))
    plot_button.grid(row=1, column=2, sticky='e', padx=10, pady=10)

