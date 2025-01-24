import pandas as pd
from pymongo import MongoClient

# Połączenie z MongoDB
client = MongoClient('mongodb+srv://wojciechiwanow7:haslo_maslo@cluster0.4jqzf.mongodb.net/')
db = client['weather_database']  # Nazwa bazy danych
collection = db['hydro_data']  # Nazwa kolekcji

# Pobierz dane z kolekcji MongoDB
cursor = collection.find()  # Pobiera wszystkie dokumenty z kolekcji

# Konwersja danych do DataFrame
data = pd.DataFrame(list(cursor))

# Usuń automatycznie generowane pole '_id' (jeśli nie jest potrzebne)
if '_id' in data.columns:
    data = data.drop(columns=['_id'])

# Wyświetlenie danych
print(data.head())

# Zapisanie danych do pliku CSV (opcjonalne)
output_file = 'odczytane_dane_hydro.csv'
data.to_csv(output_file, index=False, encoding='utf-8')
print(f"Dane zostały zapisane do pliku: {output_file}")
