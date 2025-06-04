import os
import csv
import datetime

def data_write(EEG_data, samples, timestamps):
    for sample, timestamp in zip(samples, timestamps):
        EEG_data.append([timestamp] + sample)

def save_data(EEG_data, save_path, username):
    filename = f"EEG_{datetime.datetime.now().strftime('%d_%m_%Y__%H_%M_%S')}.csv"
    os.makedirs(save_path, exist_ok=True)
    filepath = os.path.join(save_path, filename)
    with open(filepath, mode="w", newline="") as file:
        writer = csv.writer(file)
        writer.writerows(EEG_data)
    print(f"Datos guardados en {filepath}")