import requests, zipfile, io
import pandas as pd
import geopandas as gpd
import numpy as np
from shapely.geometry import Point
import re
import PyPDF2
# Pobranie danych źródłowych z portalu IMGW dla wybranego roku, miesiąca i zakresu danych
print("Pobieranie danych z portalu IMGW")

rok = input("Podaj rok: ")
miesiac = input("Podaj miesiąc: ")
if len(miesiac) == 1:
    miesiac = "0" + miesiac
zakres = input("Podaj zakres danych (1 - dobowy, 2 - miesięczny): ")

if zakres == "1":
    zakres = "dobowe"
else:
    zakres = "miesieczne"

# Zbudowanie adresu URL do pobrania pliku zip
if zakres == "dobowe":
    if rok == '2023':
        url_klimat = f"https://danepubliczne.imgw.pl/data/dane_pomiarowo_obserwacyjne/dane_meteorologiczne/dobowe/klimat/{rok}/{rok}_{miesiac}_k.zip"
        url_hydro = f"https://danepubliczne.imgw.pl/data/dane_pomiarowo_obserwacyjne/dane_hydrologiczne/dobowe/{rok}/codz_{rok}.zip"
    else:
        url_klimat = f"https://danepubliczne.imgw.pl/data/dane_pomiarowo_obserwacyjne/dane_meteorologiczne/dobowe/klimat/{rok}/{rok}_{miesiac}_k.zip"
        url_hydro = f"https://danepubliczne.imgw.pl/data/dane_pomiarowo_obserwacyjne/dane_hydrologiczne/dobowe/{rok}/codz_{rok}_{miesiac}.zip"
else:
    url_klimat = f"https://danepubliczne.imgw.pl/data/dane_pomiarowo_obserwacyjne/dane_meteorologiczne/miesieczne/klimat/{rok}/{rok}_m_k.zip"
    url_hydro = f"https://danepubliczne.imgw.pl/data/dane_pomiarowo_obserwacyjne/dane_hydrologiczne/miesieczne/{rok}/mies_{rok}.zip"

url_stacje_klimat = "https://danepubliczne.imgw.pl/data/dane_pomiarowo_obserwacyjne/dane_meteorologiczne/mapa_zawartosci_klimat.pdf"

klimat_list = []
hydro_list = []

# Pobranie i rozpakowanie danych meteorologicznych
try:
    r = requests.get(url_klimat)
    z = zipfile.ZipFile(io.BytesIO(r.content))
    z.extractall()
    print("Pobrano dane meteorologiczne")
    print("Plik z danymi meteorologicznymi:", z.namelist())
    klimat_list = z.namelist()
except Exception as e:
    print("Brak danych meteorologicznych", e)

# Pobranie i rozpakowanie danych hydrologicznych
try:
    r = requests.get(url_hydro)
    z = zipfile.ZipFile(io.BytesIO(r.content))
    z.extractall()
    print("Pobrano dane hydrologiczne")
    print("Plik z danymi hydrologicznymi:", z.namelist())
    hydro_list = z.namelist()
except Exception as e:
    print("Brak danych hydrologicznych", e)

try:
    r = requests.get(url_stacje_klimat)
    with open("mapa_zawartosci_klimat.pdf", "wb") as f:
        f.write(r.content)
except Exception as e:
    print("Brak pliku z mapą zawartości klimat", e)

# Wczytanie danych meteorologicznych i hydrologicznych
match zakres:
    case "dobowe":
        # Przetwarzanie danych meteorologicznych
        try:
            df_klimat = pd.read_csv(klimat_list[0], delimiter=",", encoding="cp1250", header=None)
            df_klimat.columns = [
                "Kod stacji", "Nazwa stacji", "Rok", "Miesiąc", "Dzień",
                "Maksymalna temperatura dobowa", "Status TMAX",
                "Minimalna temperatura dobowa", "Status TMIN",
                "Średnia dobowa temperatura", "Status STD",
                "Temperatura minimalna przy gruncie", "Status TMNG",
                "Suma dobowa opadów", "Status SMDB",
                "Rodzaj opadu", "Wysokość pokrywy śnieżnej", "Status PKSN"
            ]
            print("Wczytano dane meteorologiczne:")
            print(df_klimat.head())
        except Exception as e:
            print("Error reading meteorological data:", e)

        # Przetwarzanie danych hydrologicznych
        try:
            df_hydro = pd.read_csv(hydro_list[0], delimiter=";", encoding="utf-8-sig", header=None)
            df_hydro.columns = [
                "Kod stacji", "Nazwa stacji", "Nazwa rzeki/jeziora", "Rok hydrologiczny",
                "Wskaźnik miesiąca", "Dzień", "Stan wody", "Przepływ", "Temperatura wody", "Miesiąc kalendarzowy"
            ]
            print("Wczytano dane hydrologiczne:")
            print(df_hydro.head())
        except Exception as e:
            print("Error reading hydrological data:", e)

    case "miesieczne":
        # Przetwarzanie danych meteorologicznych
        try:
            df_klimat = pd.read_csv(klimat_list[0], delimiter=",", encoding="cp1250", header=None)
            df_klimat.columns = [
                "Kod stacji", "Nazwa stacji", "Rok", "Miesiąc",
                "Absolutna temperatura maksymalna", "Status TMAX",
                "Średnia temperatura maksymalna", "Status TMXS",
                "Absolutna temperatura minimalna", "Status TMIN",
                "Średnia temperatura minimalna", "Status TMNS",
                "Średnia temperatura miesięczna", "Status STM",
                "Minimalna temperatura przy gruncie", "Status TMNG",
                "Miesięczna suma opadów", "Status SUMM",
                "Maksymalna dobowa suma opadów", "Status OPMX",
                "Pierwszy dzień opadu maksymalnego", "Ostatni dzień opadu maksymalnego",
                "Maksymalna wysokość pokrywy śnieżnej", "Status PKSN",
                "Liczba dni z pokrywą śnieżną", "Liczba dni z opadem deszczu", "Liczba dni z opadem śniegu"
            ]
            print("Wczytano dane meteorologiczne:")
            print(df_klimat.head())
        except Exception as e:
            print("Error reading meteorological data:", e)

        # Przetwarzanie danych hydrologicznych
        try:
            df_hydro = pd.read_csv(hydro_list[0], delimiter=";", encoding="cp1250", header=None)
            df_hydro.columns = [
                "Kod stacji", "Nazwa stacji", "Nazwa rzeki/jeziora", "Rok hydrologiczny",
                "Wskaźnik miesiąca", "Wskaźnik ekstremum", "Stan wody", "Przepływ", "Temperatura wody", "Miesiąc kalendarzowy"
            ]
            print("Wczytano dane hydrologiczne:")
            print(df_hydro.head())
        except Exception as e:
            print("Error reading hydrological data:", e)

    case _:
        print("Nieznany zakres danych")

# Analiza statystyczna - dane meteorologiczne
if not df_klimat.empty:
    print("\nAnaliza statystyczna - dane meteorologiczne:")

    # Dobowe dane meteorologiczne
    if zakres == "dobowe" and "Średnia dobowa temperatura" in df_klimat.columns:
        print("Średnia temperatur dobowa:", df_klimat["Średnia dobowa temperatura"].mean())
        print("Mediana temperatur dobowa:", df_klimat["Średnia dobowa temperatura"].median())
        print("Średnia obcinana temperatur (10%):", df_klimat["Średnia dobowa temperatura"].clip(
            lower=df_klimat["Średnia dobowa temperatura"].quantile(0.1),
            upper=df_klimat["Średnia dobowa temperatura"].quantile(0.9)
        ).mean())
    # Miesięczne dane meteorologiczne
    elif zakres == "miesieczne" and "Średnia temperatura miesięczna" in df_klimat.columns:
        print("Średnia temperatura miesięczna:", df_klimat["Średnia temperatura miesięczna"].mean())
        print("Mediana temperatur miesięczna:", df_klimat["Średnia temperatura miesięczna"].median())
        print("Średnia obcinana temperatur miesięcznych (10%):", df_klimat["Średnia temperatura miesięczna"].clip(
            lower=df_klimat["Średnia temperatura miesięczna"].quantile(0.1),
            upper=df_klimat["Średnia temperatura miesięczna"].quantile(0.9)
        ).mean())
    else:
        print("Nie znaleziono odpowiednich danych meteorologicznych do analizy.")

# Analiza statystyczna - dane hydrologiczne
if not df_hydro.empty:
    print("\nAnaliza statystyczna - dane hydrologiczne:")
    if "Stan wody" in df_hydro.columns:
        print("Średni stan wody:", df_hydro["Stan wody"].mean())
        print("Mediana stanu wody:", df_hydro["Stan wody"].median())
        print("Średnia obcinana stanu wody (10%):", df_hydro["Stan wody"].clip(
            lower=df_hydro["Stan wody"].quantile(0.1),
            upper=df_hydro["Stan wody"].quantile(0.9)
        ).mean())
    else:
        print("Nie znaleziono odpowiednich danych hydrologicznych do analizy.")

# Wykonanie analiz geostatystycznych:  
# a. Średniej i mediany wartości pomiaru w podziale na daty w poszczególnych województwach i 
# powiatach. 
# b. Zmiany wartości średniej i mediany w zadanych interwałach czasu w województwach i 
# powiatach.  

# Wczytanie granic województw i powiatów
wojewodztwa = r'C:\Users\micha\Desktop\Studia GI\Studia GI 5\Programowanie Aplikacji Geoinformacyjnych 2\proj_2\Dane (1)\Dane\woj.shp'
powiaty = r'C:\Users\micha\Desktop\Studia GI\Studia GI 5\Programowanie Aplikacji Geoinformacyjnych 2\proj_2\Dane (1)\Dane\powiaty.shp'

# Wczytanie danych
gdf_woj = gpd.read_file(wojewodztwa).to_crs(epsg=4326)
gdf_pow = gpd.read_file(powiaty).to_crs(epsg=4326)

print("Wczytano dane o województwach i powiatach")
print(gdf_woj.columns)

# Wyrażenie regularne do wyłuskania kodu, nazwy i współrzędnych
pattern = r"(\d{4})\s+([A-ZĄĆĘŁŃÓŚŹŻa-ząęółńśćźż\s]+)\s+(\d{2})\s+(\d{2})\s+(\d{2})\s+(\d{2})"
print("Wczytywanie danych stacji klimatycznych")

# Geopandas DataFrame do przechowywania wyników
gdf_stacje = gpd.GeoDataFrame()

# Wczytanie pliku z danymi stacji klimatycznych
with open("mapa_zawartosci_klimat.pdf", "rb") as f:
    pdf = PyPDF2.PdfReader(f)
    for page in pdf.pages:
        text = page.extract_text()
        
        # Wyszukanie danych stacji klimatycznych
        matches = re.findall(pattern, text)
        
        # Przetwarzanie wyników
        for match in matches:
            kod_stacji = match[0]
            nazwa_stacji = match[1].strip()
            szer_geo = match[2:4]  # Szerokość: stopnie, minuty
            dlug_geo = match[4:6]  # Długość: stopnie, minuty
            
            # Przeliczenie szerokości i długości na format dziesiętny
            szer = float(szer_geo[0]) + float(szer_geo[1]) / 60
            dlug = float(dlug_geo[0]) + float(dlug_geo[1]) / 60
            
            # Dodanie danych do GeoDataFrame
            point = Point(szer, dlug)  # Geometria punktu (długość, szerokość)

            new_row = {
                "Kod_stac": kod_stacji,
                "Nazwa_stac": nazwa_stacji.encode('ascii', 'ignore').decode('ascii'),
                "Szer": dlug,
                "Dlug": szer,
                "Geometry": point
            }
            gdf_stacje = pd.concat([gdf_stacje, gpd.GeoDataFrame([new_row])], ignore_index=True)

# Zapis wyników do pliku (opcjonalnie)
gdf_stacje = gdf_stacje.set_geometry("Geometry")
print(gdf_stacje.crs)
gdf_stacje.crs = "EPSG:4326"
gdf_stacje.to_file("stacje_klimatyczne.shp", encoding='ISO-8859-1')

# Upewnij się, że kolumny 'Powiat' i 'Województwo' istnieją w gdf_stacje
gdf_stacje["Powiat"] = None
gdf_stacje["Województwo"] = None

for i in range(len(gdf_stacje)):
    for j in range(len(gdf_pow)):
        if gdf_stacje["Geometry"][i].within(gdf_pow["geometry"][j]):
            gdf_stacje["Powiat"][i] = gdf_pow["name"][j]
    for k in range(len(gdf_woj)):
        if gdf_stacje["Geometry"][i].within(gdf_woj["geometry"][k]):
            gdf_stacje["Województwo"][i] = gdf_woj["name"][k]

print("Wczytano dane stacji klimatycznych")
print(gdf_stacje.head())

