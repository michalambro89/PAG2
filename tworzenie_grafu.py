import arcpy
import csv

# Ścieżki do danych wejściowych i wyjściowych
roads_layer = r"C:\Users\micha\Desktop\Studia GI\Studia GI 5\Programowanie Aplikacji Geoinformacyjnych 2\proj_1\proj_custom_path\projekt\drogi_i_sciezki"  # Warstwa linii
nodes_layer = r"C:\Users\micha\Desktop\Studia GI\Studia GI 5\Programowanie Aplikacji Geoinformacyjnych 2\proj_1\proj_custom_path\projekt\wiercholki"      # Warstwa punktów
output_csv = r"C:\Users\micha\Desktop\Studia GI\Studia GI 5\Programowanie Aplikacji Geoinformacyjnych 2\proj_1\proj_custom_path\projekt\listy_sasiedztwa_6.csv"

# Ścieżki do warstw potrzebnych do wagowania
warstwa_fontanny_pomniki = "fontanny_i_pomniki"

# Układ współrzędnych EPSG:2180 (Polska, układ 1992)
spatial_reference = arcpy.SpatialReference(2180)

def are_coordinates_equal(coord1, coord2, tolerance=0.001):
    return abs(coord1[0] - coord2[0]) <= tolerance and abs(coord1[1] - coord2[1]) <= tolerance

# Funkcja obliczająca wagę
def fuzzylinear(distance, max_distance):
    return 1 if distance >= max_distance else distance / max_distance

def calculate_edge_weight(edge, point_layer, max_distance=3000):
    """Oblicz wagę krawędzi na podstawie odległości do punktów."""
    start_geom = arcpy.PointGeometry(arcpy.Point(*edge["start"]), spatial_reference)
    end_geom = arcpy.PointGeometry(arcpy.Point(*edge["end"]), spatial_reference)
    corrected_weight = edge["length"]

    with arcpy.da.SearchCursor(point_layer, ["SHAPE@"]) as cursor:
        for row in cursor:
            point_geom = row[0]
            distance_to_start = start_geom.distanceTo(point_geom)
            distance_to_end = end_geom.distanceTo(point_geom)
            if distance_to_start <= max_distance:
                corrected_weight *= fuzzylinear(distance_to_start, max_distance)
                break
            elif distance_to_end <= max_distance:
                corrected_weight *= fuzzylinear(distance_to_end, max_distance)
                break
    return corrected_weight

# Pobranie wierzchołków i ich współrzędnych
print("Pobieranie wierzchołków...")
nodes = {}
with arcpy.da.SearchCursor(nodes_layer, ["FID", "SHAPE@XY"]) as cursor:
    nodes = {fid: (coord[0], coord[1]) for fid, coord in cursor}
print(f"Załadowano {len(nodes)} wierzchołków.")

# Pobranie linii i ich punktów końcowych
print("Pobieranie linii...")
edges = []
with arcpy.da.SearchCursor(roads_layer, ["FID", "SHAPE@LENGTH", "SHAPE@"]) as cursor:
    for row in cursor:
        line_id, line_length, line_shape = row
        start_point = (line_shape.firstPoint.X, line_shape.firstPoint.Y)
        end_point = (line_shape.lastPoint.X, line_shape.lastPoint.Y)
        edges.append({
            "id": line_id,
            "start": start_point,
            "end": end_point,
            "length": line_length,
        })
print(f"Załadowano {len(edges)} linii.")

# Przygotowanie mapowania krawędzi
print("Budowa mapy krawędzi...")
edge_map = {}
for idx, edge in enumerate(edges):
    weight = calculate_edge_weight(edge, warstwa_fontanny_pomniki)
    rounded_start = (round(edge["start"][0], 3), round(edge["start"][1], 3))
    rounded_end = (round(edge["end"][0], 3), round(edge["end"][1], 3))
    edge_map.setdefault(rounded_start, []).append((rounded_end, weight))
    edge_map.setdefault(rounded_end, []).append((rounded_start, weight))
    if idx % 100 == 0:
        print(f"Przetworzono {idx + 1} krawędzi...")
print("Wagi krawędzi zostały obliczone.")

# Tworzenie listy sąsiedztwa
print("Tworzenie listy sąsiedztwa...")
adjacency_list = {node_id: [] for node_id in nodes.keys()}
for idx, (node_id, coord) in enumerate(nodes.items()):
    rounded_coord = (round(coord[0], 3), round(coord[1], 3))
    if rounded_coord in edge_map:
        for neighbor, weight in edge_map[rounded_coord]:
            neighbor_id = next(
                (nid for nid, ncoord in nodes.items() if are_coordinates_equal(ncoord, neighbor)),
                None
            )
            if neighbor_id is not None:
                adjacency_list[node_id].append((neighbor_id, weight))
    if idx % 100 == 0:
        print(f"Przetworzono {idx + 1} wierzchołków...")

# Zapisanie listy sąsiedztwa do pliku CSV
print(f"Zapisywanie listy sąsiedztwa do pliku: {output_csv}...")
with open(output_csv, mode='w', newline='', encoding='utf-8') as file:
    writer = csv.writer(file)
    writer.writerow(["Node", "Neighbors"])
    for node_id, neighbors in adjacency_list.items():
        neighbors_str = ";".join([f"{neighbor}:{weight}" for neighbor, weight in neighbors])
        writer.writerow([node_id, neighbors_str])
 
print("Proces zakończony.")