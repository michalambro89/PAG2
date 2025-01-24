import redis
import pandas as pd

file_path = 'codz_2023.csv' # W tym miejscu należy wprowadzić ścieżkę do pliku hydrologicznego  w formacie csv 
columns = [
    "Kod stacji", "Nazwa stacji", "Nazwa rzeki/jeziora", "Rok hydrologiczny",
    "Wskaźnik miesiąca", "Dzień", "Stan wody", "Przepływ", "Temperatura wody", "Miesiąc kalendarzowy"
]

df = pd.read_csv(file_path, sep=';', header=None, names=columns, encoding='UTF-8')
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
    key = f"record:{index}"# W tym miejscu można zmienić nazwę klucza
    
    db.hset(key, mapping=record)

pipeline.execute()

print("Dane zostały zapisane w Redis.")
