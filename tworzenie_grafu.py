import arcpy
import csv
import json

# Ścieżki do danych wejściowych i wyjściowych
roads_layer = r"C:\Users\micha\Desktop\Studia GI\Studia GI 5\Programowanie Aplikacji Geoinformacyjnych 2\proj_1\proj_custom_path\projekt\drogi_i_sciezki"  # Warstwa linii
nodes_layer = r"C:\Users\micha\Desktop\Studia GI\Studia GI 5\Programowanie Aplikacji Geoinformacyjnych 2\proj_1\proj_custom_path\projekt\wiercholki"      # Warstwa punktów
output_csv = r"C:\Users\micha\Desktop\Studia GI\Studia GI 5\Programowanie Aplikacji Geoinformacyjnych 2\proj_1\proj_custom_path\projekt\listy_sasiedztwa.csv"

print("Rozpoczynam tworzenie grafu na podstawie danych...")

# Pobierz wierzchołki i ich współrzędne
print("Pobieranie wierzchołków...")
nodes = {}
with arcpy.da.SearchCursor(nodes_layer, ["FID", "SHAPE@XY"]) as cursor:
    for idx, row in enumerate(cursor):
        nodes[row[0]] = row[1]  # ID wierzchołka -> współrzędne (x, y)
        if idx % 1000 == 0:
            print(f"Przetworzono {idx} wierzchołków...")
print(f"Łącznie załadowano {len(nodes)} wierzchołków.")

nodes_file = "nodes.json"
with open(nodes_file, 'w') as f:
    json.dump(nodes, f)
    print(f"Wierzchołki zostały zapisane do pliku: {nodes_file}")

# Pobierz linie i ich punkty końcowe oraz długości
print("Pobieranie linii...")
edges = []
with arcpy.da.SearchCursor(roads_layer, ["FID", "SHAPE@LENGTH", "SHAPE@"]) as cursor:
    for idx, row in enumerate(cursor):
        line_id = row[0]
        line_length = row[1]
        start_point = row[2].firstPoint
        end_point = row[2].lastPoint
        edges.append({
            "id": line_id,
            "start": (start_point.X, start_point.Y),  # Współrzędne startu
            "end": (end_point.X, end_point.Y),  # Współrzędne końca
            "length": line_length,
        })
        if idx % 1000 == 0:
            print(f"Przetworzono {idx} linii...")
print(f"Łącznie załadowano {len(edges)} linii.")

# Tworzenie listy sąsiedztwa
print("Tworzenie listy sąsiedztwa...")
adjacency_list = {node_id: [] for node_id in nodes.keys()}  # Słownik, gdzie klucz to ID wierzchołka, a wartość to lista sąsiednich wierzchołków z wagami

for node_id, node_coords in nodes.items():
    print(f"Przetwarzanie wierzchołka {node_id}...")
    for edge in edges:
        start_coords = edge["start"]
        end_coords = edge["end"]
        weight = edge["length"]

        if node_coords == start_coords:
            end_node = next((nid for nid, coord in nodes.items() if coord == end_coords), None)
            if end_node:
                adjacency_list[node_id].append((end_node, weight))
                print(f"Dodano sąsiedni wierzchołek {end_node} z wagą {weight} do wierzchołka {node_id}")
        elif node_coords == end_coords:
            start_node = next((nid for nid, coord in nodes.items() if coord == start_coords), None)
            if start_node:
                adjacency_list[node_id].append((start_node, weight))
                print(f"Dodano sąsiedni wierzchołek {start_node} z wagą {weight} do wierzchołka {node_id}")

print("Lista sąsiedztwa została utworzona.")

# Zapisz listę sąsiedztwa do pliku CSV
print(f"Zapisywanie listy sąsiedztwa do pliku: {output_csv}...")

with open(output_csv, mode='w', newline='', encoding='utf-8') as file:
    writer = csv.writer(file)
    writer.writerow(["Node", "Neighbors"])  # Nagłówki kolumn
    for node_id, neighbors in adjacency_list.items():
        # Sąsiedzi w formacie "node_id:weight"
        neighbors_str = ";".join([f"{neighbor}:{weight}" for neighbor, weight in neighbors])
        writer.writerow([node_id, neighbors_str])

print(f"Lista sąsiedztwa została zapisana do pliku: {output_csv}")




fontanny_pomniki_layer = r"C:\Users\micha\Desktop\Studia GI\Studia GI 5\Programowanie Aplikacji Geoinformacyjnych 2\proj_1\proj_custom_path\projekt\2807_SHP\PL.PZGiK.341.BDOT10k.2807__OT_OIOR_P.shp"
# wagowanie krawędzi na podstawie odległości od punktów z warstwy fontanny_pomniki_layer
# od 0 metrów do 20 metrów waga rozmyta od 0 do 1
# w tym celu stwóz nowy graf krawedzi, gdzie kazda krawedz ma nowe pole z waga odleglosci od fontann i pomników

# Pobierz punkty z warstwy fontanny_pomniki_layer
print("Pobieranie punktów...")
points = {}
with arcpy.da.SearchCursor(fontanny_pomniki_layer, ["FID", "SHAPE@XY"]) as cursor:
    for idx, row in enumerate(cursor):
        points[row[0]] = row[1]  # ID punktu -> współrzędne (x, y)
        if idx % 1000 == 0:
            print(f"Przetworzono {idx} punktów...")
print(f"Łącznie załadowano {len(points)} punktów.")

# Tworzenie listy sąsiedztwa z wagami
print("Tworzenie listy sąsiedztwa z wagami...")
weighted_adjacency_list = {node_id: [] for node_id in nodes.keys()}  # Słownik, gdzie klucz to ID wierzchołka, a wartość to lista sąsiednich wierzchołków z wagami

for node_id, node_coords in nodes.items():