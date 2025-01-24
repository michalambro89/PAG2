import pandas as pd
from pymongo import MongoClient

# Ścieżka do pliku CSV
file_path = 'k_d_12_2023.csv'

# Kolumny w pliku CSV
columns = [
    "Kod stacji", "Nazwa stacji", "Rok", "Miesiąc", "Dzień",
    "Maksymalna temperatura dobowa", "Status TMAX",
    "Minimalna temperatura dobowa", "Status TMIN",
    "Średnia dobowa temperatura", "Status STD",
    "Temperatura minimalna przy gruncie", "Status TMNG",
    "Suma dobowa opadów", "Status SMDB",
    "Rodzaj opadu", "Wysokość pokrywy śnieżnej", "Status PKSN"
]

# Wczytaj dane z pliku CSV i dodaj kolumny
data = pd.read_csv(file_path, header=None, names=columns, encoding='windows-1250')

# Połączenie z MongoDB
client = MongoClient('mongodb+srv://wojciechiwanow7:haslo_maslo@cluster0.4jqzf.mongodb.net/')
db = client['weather_database']  # Nazwa bazy danych
collection = db['meteo_data']  # Nazwa kolekcji

# Konwersja DataFrame do listy słowników
data_dict = data.to_dict(orient='records')

# Wstawianie danych do MongoDB
collection.insert_many(data_dict)

print("Dane zostały pomyślnie zaimportowane do MongoDB!")
