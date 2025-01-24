import redis
import pandas as pd

file_path = 'k_d_12_2023.csv' # W tym miejscu należy wprowadzić ścieżkę do pliku meteorologicznego k_d w formacie csv 
columns = [
    "Kod stacji", "Nazwa stacji", "Rok", "Miesiąc", "Dzień",
    "Maksymalna temperatura dobowa", "Status TMAX",
    "Minimalna temperatura dobowa", "Status TMIN",
    "Średnia dobowa temperatura", "Status STD",
    "Temperatura minimalna przy gruncie", "Status TMNG",
    "Suma dobowa opadów", "Status SMDB",
    "Rodzaj opadu", "Wysokość pokrywy śnieżnej", "Status PKSN"
]

df = pd.read_csv(file_path, header=None, names=columns, encoding='windows-1250')
print(df.head())

pool = redis.ConnectionPool(
    host='redis-17250.c304.europe-west1-2.gce.redns.redis-cloud.com',
    port=17250,
    password='OlabjT7aEhz6RYDMDgbfwro5GGyQQG45',
    decode_responses=True
)
db = redis.Redis(connection_pool=pool)

data_dict = df.to_dict(orient='records')

pipeline = db.pipeline()

for index, record in enumerate(data_dict):
    key = f"record_meteo:{index}"# W tym miejscu można zmienić nazwę klucza
    
    db.hset(key, mapping=record)

pipeline.execute()
print("Dane zostały zapisane w Redis.")