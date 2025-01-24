import redis
import pandas as pd

pool = redis.ConnectionPool(
    host='redis-17250.c304.europe-west1-2.gce.redns.redis-cloud.com',
    port=17250,
    password='OlabjT7aEhz6RYDMDgbfwro5GGyQQG45',
    decode_responses=True
)
db = redis.Redis(connection_pool=pool)

keys = db.keys("record:*") # W tym miejscu należy wprowadzić nazwę klucza, "record:*" dla danych hydrologicznych i "record_meteo:*" dla danych meteorologicznych
keys = sorted(keys, key=lambda x: int(x.split(":")[1]))

data = []
for key in keys:
    record = db.hgetall(key)
    data.append(record)

df = pd.DataFrame(data)

output_file = 'wyeksporotwane_dane3.csv' # W tym miejscu można wybrać nazwę pliku z zapisanymi danymi
df.to_csv(output_file, index=False, encoding='utf-8-sig', sep=';', header=False) # W celu dokładnego odtworzenia plików csv proszę ustawić:
# sep na ',' i encoding na 'windows-1250' dla danych meteorlogicznych, bądź sep na ';' i encoding na 'utf-8-sig' dla danych hydrologicznych
print(f"Dane zostały zapisane do pliku: {output_file}")