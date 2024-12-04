import arcpy
import csv
import json

# Ścieżki do danych wejściowych i wyjściowych
roads_layer = "drogi_i_sciezki"  # Warstwa linii
nodes_layer = "wiercholki"      # Warstwa punktów
output_csv = r"C:\Users\wojci\Desktop\studia\semestr_5\pag 2\Projekt-blok-1\projekt\listy_sasiedztwa.csv"

# Ścieżki do warstw potrzebnych do wagowania
warstwa_fontanny_pomniki = r"C:\Users\wojci\Desktop\studia\semestr_5\pag 2\Projekt-blok-1\projekt\2807_SHP\PL_PZGiK_341_BDOT10k_2807__OT_OIOR_P.shp"
warstwa_kompleks_zabytkow = r"C:\Users\wojci\Desktop\studia\semestr_5\pag 2\Projekt-blok-1\projekt\2807_SHP\PL_PZGiK_341_BDOT10k_2807__OT_KUZA_A.shp"
warstwa_kompleksy_rekreacyjne = r"C:\Users\wojci\Desktop\studia\semestr_5\pag 2\Projekt-blok-1\projekt\2807_SHP\PL_PZGiK_341_BDOT10k_2807__OT_KUSK_A.shp"
warstwa_rezerwaty = r"C:\Users\wojci\Desktop\studia\semestr_5\pag 2\Projekt-blok-1\projekt\2807_SHP\PL_PZGiK_341_BDOT10k_2807__OT_TCRZ_A.shp"
warstwa_parki_krajobrazowe = r"C:\Users\wojci\Desktop\studia\semestr_5\pag 2\Projekt-blok-1\projekt\2807_SHP\PL_PZGiK_341_BDOT10k_2807__OT_TCPK_A.shp"
warstwa_obszar_natura_2000 = r"C:\Users\wojci\Desktop\studia\semestr_5\pag 2\Projekt-blok-1\projekt\2807_SHP\PL_PZGiK_341_BDOT10k_2807__OT_TCON_A.shp"

# Funkcja do obliczania wagi krawędzi z procentową modyfikacją
def calculate_edge_weight(edge, point_layer, polygon_layers):
    weight = edge["length"]  # Podstawowa waga bazująca na długości

    # Utworzenie geometrii krawędzi jako punktów początkowego i końcowego
    start_geom = arcpy.PointGeometry(edge["start"])
    end_geom = arcpy.PointGeometry(edge["end"])

    # Uwzględnij odległości od warstwy punktowej
    with arcpy.da.SearchCursor(point_layer, ["SHAPE@"]) as cursor:
        for row in cursor:
            point_geom = row[0]  # Geometria punktu
            distance_to_start = start_geom.distanceTo(point_geom)
            distance_to_end = end_geom.distanceTo(point_geom)
            
            # Wpływ na wagę dla punktu w zasięgu 30 metrów
            if distance_to_start <= 30 or distance_to_end <= 30:
                closest_distance = min(distance_to_start, distance_to_end)
                # Procentowa redukcja wagi w zależności od odległości (bliżej = większa redukcja)
                reduction_factor = 1 - (30 - closest_distance) / 100  # Redukcja do 30% wagi
                weight *= reduction_factor

    # Uwzględnij przecięcia z warstwami poligonowymi
    for layer in polygon_layers:
        with arcpy.da.SearchCursor(layer, ["SHAPE@"]) as cursor:
            for row in cursor:
                polygon_geom = row[0]  # Geometria poligonu
                if start_geom.overlaps(polygon_geom) or end_geom.overlaps(polygon_geom):
                    weight *= 0.7  # Zmniejsz wagę o 30%, jeśli krawędź przechodzi przez poligon

    return weight


# Rozpoczynamy proces
print("Rozpoczynam tworzenie grafu na podstawie danych...")

# Pobierz wierzchołki i ich współrzędne
print("Pobieranie wierzchołków...")
nodes = {}
with arcpy.da.SearchCursor(nodes_layer, ["FID", "SHAPE@XY"]) as cursor:
    for idx, row in enumerate(cursor):
        nodes[row[0]] = arcpy.Point(row[1][0], row[1][1])  # ID wierzchołka -> obiekt Point
        if idx % 1000 == 0:
            print(f"Przetworzono {idx} wierzchołków...")
print(f"Łącznie załadowano {len(nodes)} wierzchołków.")

# Pobierz linie i ich punkty końcowe oraz długości
print("Pobieranie linii...")
edges = []
with arcpy.da.SearchCursor(roads_layer, ["FID", "SHAPE@LENGTH", "SHAPE@"]) as cursor:
    for idx, row in enumerate(cursor):
        line_id = row[0]
        line_length = row[1]
        line_shape = row[2]
        start_point = line_shape.firstPoint
        end_point = line_shape.lastPoint
        edges.append({
            "id": line_id,
            "start": arcpy.Point(start_point.X, start_point.Y),
            "end": arcpy.Point(end_point.X, end_point.Y),
            "length": line_length,
        })
        if idx % 1000 == 0:
            print(f"Przetworzono {idx} linii...")
print(f"Łącznie załadowano {len(edges)} linii.")

# Obliczanie wag krawędzi
print("Obliczanie wag krawędzi...")
polygon_layers = [
    warstwa_kompleks_zabytkow,
    warstwa_kompleksy_rekreacyjne,
    warstwa_rezerwaty,
    warstwa_parki_krajobrazowe,
    warstwa_obszar_natura_2000,
]

for idx, edge in enumerate(edges):
    edge["weight"] = calculate_edge_weight(edge, warstwa_fontanny_pomniki, polygon_layers)
    if idx % 100 == 0:  # Informacja co setną krawędź
        print(f"Przetworzono {idx + 1} krawędzi...")
print(f"Obliczono wagi dla wszystkich {len(edges)} krawędzi.")

# Tworzenie listy sąsiedztwa
print("Tworzenie listy sąsiedztwa...")
adjacency_list = {node_id: [] for node_id in nodes.keys()}

for idx, (node_id, node_coords) in enumerate(nodes.items()):
    for edge in edges:
        start_coords = edge["start"]
        end_coords = edge["end"]
        weight = edge["weight"]

        if node_coords.equals(start_coords):
            end_node = next((nid for nid, coord in nodes.items() if coord.equals(end_coords)), None)
            if end_node:
                adjacency_list[node_id].append((end_node, weight))
        elif node_coords.equals(end_coords):
            start_node = next((nid for nid, coord in nodes.items() if coord.equals(start_coords)), None)
            if start_node:
                adjacency_list[node_id].append((start_node, weight))
    if idx % 100 == 0:  # Informacja co setny wierzchołek
        print(f"Przetworzono {idx + 1} wierzchołków...")
print("Lista sąsiedztwa została utworzona.")

# Zapisz listę sąsiedztwa do pliku CSV
print(f"Zapisywanie listy sąsiedztwa do pliku: {output_csv}...")
with open(output_csv, mode='w', newline='', encoding='utf-8') as file:
    writer = csv.writer(file)
    writer.writerow(["Node", "Neighbors"])
    for node_id, neighbors in adjacency_list.items():
        neighbors_str = ";".join([f"{neighbor}:{weight}" for neighbor, weight in neighbors])
        writer.writerow([node_id, neighbors_str])

print(f"Lista sąsiedztwa została zapisana do pliku: {output_csv}")