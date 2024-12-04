import arcpy
import csv
import json
import heapq

# Funkcja do ładowania wierzchołków z pliku JSON
def load_nodes(file_path):
    with open(file_path, 'r') as f:
        nodes = json.load(f)
    return {int(k): v for k, v in nodes.items()}  # Konwersja kluczy na int

# Funkcja do ładowania listy sąsiedztwa z pliku CSV
def load_adjacency_list(csv_path):
    adjacency_list = {}
    with open(csv_path, 'r') as csvfile:
        reader = csv.reader(csvfile)
        next(reader)  # Pomijamy nagłówek
        for row in reader:
            node = int(row[0])
            neighbors = {}
            if row[1].strip():  # Sprawdzenie, czy kolumna 'Neighbors' nie jest pusta
                for neighbor in row[1].split(";"):
                    if ":" in neighbor:  # Sprawdzenie poprawności formatu
                        neighbor_id, weight = neighbor.split(":")
                        neighbors[int(neighbor_id)] = float(weight)
                    else:
                        print(f"Ostrzeżenie: niepoprawny format sąsiada '{neighbor}' dla wierzchołka {node}.")
            adjacency_list[node] = neighbors
    return adjacency_list

# Funkcja do tworzenia warstwy
def create_path_layer(path, nodes, adjacency_list, output_fc, roads_layer):
    """
    Tworzy warstwę liniową w układzie EPSG:2180 i dodaje ją do aktywnej mapy, łącząc wierzchołki rzeczywistymi drogami.
    """
    # Układ odniesienia EPSG:2180 (Polska, układ 1992)
    spatial_reference = arcpy.SpatialReference(2180)

    # Ścieżka do pliku geobazy tymczasowej
    output_fc = f"{arcpy.env.scratchGDB}/AStarPath"

    # Usuń istniejący plik, jeśli istnieje
    if arcpy.Exists(output_fc):
        arcpy.Delete_management(output_fc)
    
    # Utwórz nową warstwę liniową
    arcpy.CreateFeatureclass_management(
        out_path=arcpy.env.scratchGDB,  # Zapisz w geobazie tymczasowej
        out_name="AStarPath",
        geometry_type="POLYLINE",
        spatial_reference=spatial_reference
    )

    # Przygotowanie kursorów
    with arcpy.da.InsertCursor(output_fc, ["SHAPE@"]) as cursor:
        # Przechodzimy przez kolejne pary wierzchołków na ścieżce
        for i in range(1, len(path)):
            current_node = path[i-1]
            next_node = path[i]

            # Używamy krawędzi z listy sąsiedztwa, aby pobrać współrzędne
            if next_node in adjacency_list[current_node]:
                # Uzyskujemy współrzędne wierzchołków
                point1 = arcpy.Point(*nodes[current_node])
                point2 = arcpy.Point(*nodes[next_node])
                
                # Tworzymy kursor szukający po współrzędnych punktów odpowiedniej drogi. Trzeba wziac geometrie calej drogi, gdyz bedziemy tworzyc nowa linie miedzy punktami na podstawie tej geometrii drogi
                with arcpy.da.SearchCursor(roads_layer, ["SHAPE@"]) as road_cursor:
                    for row in road_cursor:
                        line = row[0]
                        start = row.firstPoint
                        end = row.lastPoint
                        if (start.X == point1.X and start.Y == point1.Y and end.X == point2.X and end.Y == point2.Y) or (start.X == point2.X and start.Y == point2.Y and end.X == point1.X and end.Y == point1.Y):
                            cursor.insertRow([line])
                            print(f"Dodano linię między wierzchołkami {current_node} i {next_node}")
                            break

    # Dodaj warstwę do projektu
    aprx = arcpy.mp.ArcGISProject("CURRENT")
    map_view = aprx.activeMap
    layer_name = "AStarPath"

    # Sprawdzenie, czy warstwa o tej nazwie już istnieje w mapie
    existing_layer = None
    for layer in map_view.listLayers():
        if layer.name == layer_name:
            existing_layer = layer
            break

    # Jeśli warstwa już istnieje, usuń ją przed dodaniem nowej
    if existing_layer:
        map_view.removeLayer(existing_layer)

    # Dodaj nową warstwę do mapy
    map_view.addDataFromPath(output_fc)
    print(f"Ścieżka została dodana jako nowa warstwa: {output_fc}")

# Funkcja heurystyki: oblicza odległość euklidesową
def heuristic(node, target, nodes):
    x1, y1 = nodes[node]
    x2, y2 = nodes[target]
    return ((x2 - x1) ** 2 + (y2 - y1) ** 2) ** 0.5

# Algorytm A*
def a_star(start, target, nodes, adjacency_list):
    # Inicjalizacja
    open_list = []  # Lista otwarta (priorytetowa)
    heapq.heappush(open_list, (0 + heuristic(start, target, nodes), 0, start))  # (f, g, wierzchołek)
    
    came_from = {}  # Słownik do śledzenia ścieżki
    g_score = {node: float('inf') for node in nodes}  # Koszt dojścia do wierzchołka
    g_score[start] = 0  # Koszt startowy
    f_score = {node: float('inf') for node in nodes}  # Koszt całkowity f = g + h
    f_score[start] = heuristic(start, target, nodes)  # Funkcja f na początek

    while open_list:
        # Pobierz wierzchołek z najmniejszym f_score
        _, current_g, current = heapq.heappop(open_list)

        # Jeśli osiągnięto cel
        if current == target:
            path = []
            while current in came_from:
                path.append(current)
                current = came_from[current]
            path.append(start)
            path.reverse()
            return path

        # Sprawdzenie sąsiadów
        for neighbor, weight in adjacency_list[current].items():
            tentative_g_score = current_g + weight

            if tentative_g_score < g_score[neighbor]:
                came_from[neighbor] = current
                g_score[neighbor] = tentative_g_score
                f_score[neighbor] = tentative_g_score + heuristic(neighbor, target, nodes)
                heapq.heappush(open_list, (f_score[neighbor], tentative_g_score, neighbor))

    return None  # Brak ścieżki

# Ścieżki do danych wejściowych i wyjściowych
roads_layer = r"C:\Users\micha\Desktop\Documents\ArcGIS\Projects\MyProject5\MyProject5.gdb\drogi_Merge"  # Warstwa linii
nodes_layer = r"C:\Users\micha\Desktop\Studia GI\Studia GI 5\Programowanie Aplikacji Geoinformacyjnych 2\proj_1\proj_custom_path\projekt\wiercholki"      # Warstwa punktów
output_csv = r"C:\Users\micha\Desktop\Studia GI\Studia GI 5\Programowanie Aplikacji Geoinformacyjnych 2\proj_1\proj_custom_path\projekt\listy_sasiedztwa.csv"

nodes_file = r"C:\Users\micha\Desktop\Studia GI\Studia GI 5\Programowanie Aplikacji Geoinformacyjnych 2\proj_1\proj_custom_path\projekt\nodes.json"   
adjacency_file = r"C:\Users\micha\Desktop\Studia GI\Studia GI 5\Programowanie Aplikacji Geoinformacyjnych 2\proj_1\proj_custom_path\projekt\listy_sasiedztwa.csv"
output_feature_class = "in_memory\\AStarPath"

try:
    # Załaduj dane
    print("Ładowanie wierzchołków...")
    nodes = load_nodes(nodes_file)
    print(f"Załadowano {len(nodes)} wierzchołków.")

    print("Ładowanie listy sąsiedztwa...")
    adjacency_list = load_adjacency_list(adjacency_file)
    print(f"Załadowano listę sąsiedztwa dla {len(adjacency_list)} wierzchołków.")

    # Wybór startowego i docelowego wierzchołka
    start_node = 3662  # Przykładowy start
    target_node = 39339  # Przykładowy cel

    # Uruchom algorytm A*
    print(f"Rozpoczynanie algorytmu A* dla wierzchołków {start_node} i {target_node}...")
    path = a_star(start_node, target_node, nodes, adjacency_list)

    if path:
        print("Znaleziono ścieżkę:", path)
        create_path_layer(path, nodes, adjacency_list, output_feature_class, roads_layer)
    else:
        print("Brak ścieżki między tymi wierzchołkami.")
except Exception as e:
    print(f"Wystąpił błąd: {e}")






