import pandas as pd
from pymongo import MongoClient

# Ścieżka do pliku CSV
file_path = 'codz_2023.csv'

# Kolumny w pliku CSV
columns = [
    "Kod stacji", "Nazwa stacji", "Nazwa rzeki/jeziora", "Rok hydrologiczny",
    "Wskaźnik miesiąca", "Dzień", "Stan wody", "Przepływ", "Temperatura wody", "Miesiąc kalendarzowy"
]

# Wczytaj dane z pliku CSV i dodaj kolumny
data = pd.read_csv(file_path, sep=';', header=None, names=columns, encoding='UTF-8')

# Wyświetl pierwsze kilka wierszy, aby upewnić się, że dane są poprawnie wczytane
print(data.head())

# Połączenie z MongoDB
client = MongoClient('mongodb+srv://wojciechiwanow7:haslo_maslo@cluster0.4jqzf.mongodb.net/')
db = client['weather_database']  # Nazwa bazy danych
collection = db['hydro_data']  # Nazwa kolekcji

# Konwersja DataFrame do listy słowników
data_dict = data.to_dict(orient='records')

# Wstawianie danych do MongoDB
collection.insert_many(data_dict)

print("Dane zostały pomyślnie zaimportowane do MongoDB!")
