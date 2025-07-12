import folium
from folium.plugins import HeatMap
from folium.plugins import TimestampedGeoJson
import datetime

import matplotlib.pyplot as plt
import matplotlib.image as mpimg

import numpy as np
from SPARQLWrapper import SPARQLWrapper, JSON

sparql = SPARQLWrapper("http://localhost:7200/repositories/gtfs-rj")

#-------------------------------------------------------------------------------

def plot_paradas_linha(route_short_name):
    # 1. Descobre o URI da linha pelo short_name
    query_route = f"""
    PREFIX gtfs: <http://vocab.gtfs.org/terms#/>
    SELECT ?route
    WHERE {{
      ?route a gtfs:Route ;
             gtfs:shortName "{route_short_name}" .
    }}
    """
    sparql.setQuery(query_route)
    sparql.setReturnFormat(JSON)
    results_route = sparql.query().convert()
    if not results_route["results"]["bindings"]:
        print(f'Linha {route_short_name} não encontrada.')
        return
    route_uri = results_route["results"]["bindings"][0]["route"]["value"]

    # 2. Busca todas as paradas de todas as viagens dessa linha
    query = f"""
    PREFIX gtfs: <http://vocab.gtfs.org/terms#/>
    PREFIX geo: <http://www.w3.org/2003/01/geo/wgs84_pos#/>
    SELECT DISTINCT ?lat ?lon
    WHERE {{
      ?trip gtfs:route <{route_uri}> .
      ?stop_time gtfs:trip ?trip ; gtfs:stop ?stop .
      ?stop geo:lat ?lat ; geo:long ?lon .
    }}
    """
    sparql.setQuery(query)
    sparql.setReturnFormat(JSON)
    results = sparql.query().convert()

    coords = []
    for r in results["results"]["bindings"]:
        lat = float(r["lat"]["value"])
        lon = float(r["lon"]["value"])
        coords.append([lat, lon])

    if not coords:
        print("Nenhuma parada encontrada para essa linha.")
        return

    lat_c = sum([c[0] for c in coords]) / len(coords)
    lon_c = sum([c[1] for c in coords]) / len(coords)
    m = folium.Map(location=[lat_c, lon_c], zoom_start=12, tiles="cartodbpositron")
    for i, (lat, lon) in enumerate(coords):
        folium.CircleMarker([lat, lon], radius=4, color="blue", fill=True, fill_opacity=0.7, popup=f"Parada {i+1}").add_to(m)
    m.save(f"../map/paradas_linha_{route_short_name}.html")
    print(f"Mapa salvo como paradas_linha_{route_short_name}.html")

#-------------------------------------------------------------------------------

def encontrar_estacao_mais_proxima(lat, lon):
    query = """
    PREFIX geo: <http://www.w3.org/2003/01/geo/wgs84_pos#/>
    PREFIX gtfs: <http://vocab.gtfs.org/terms#/>

    SELECT ?stop ?stop_lat ?stop_lon
    WHERE {
    ?stop a gtfs:Stop ;
            geo:lat ?stop_lat ;
            geo:long ?stop_lon .
    }
    """
    sparql.setQuery(query)
    sparql.setReturnFormat(JSON)
    results = sparql.query().convert()

    menor_dist = float('inf')
    estacao_mais_proxima = None
    for result in results["results"]["bindings"]:
        stop = result["stop"]["value"]
        stop_lat = float(result["stop_lat"]["value"])
        stop_lon = float(result["stop_lon"]["value"])
        dist = ((lat - stop_lat)**2 + (lon - stop_lon)**2)**0.5
        if dist < menor_dist:
            menor_dist = dist
            estacao_mais_proxima = (stop, stop_lat, stop_lon)
    return estacao_mais_proxima  # (uri, lat, lon)

def melhor_rota(lat_origem, lon_origem, lat_dest, lon_dest):
    estacao_origem = encontrar_estacao_mais_proxima(lat_origem, lon_origem)
    estacao_dest = encontrar_estacao_mais_proxima(lat_dest, lon_dest)
    if not estacao_origem or not estacao_dest:
        print("Não foi possível encontrar estações próximas.")
        return

    stop_uri_origem = f"<{estacao_origem[0]}>"
    stop_uri_dest = f"<{estacao_dest[0]}>"
    print(f'uri_origem: {stop_uri_origem}, uri_dest: {stop_uri_dest}')

    query = f"""
    PREFIX gtfs: <http://vocab.gtfs.org/terms#/>
    PREFIX geo: <http://www.w3.org/2003/01/geo/wgs84_pos#/>
    PREFIX xsd: <http://www.w3.org/2001/XMLSchema#/>

    SELECT ?trip ?route ?ordem ?lat ?lon
    WHERE {{
    ?trip gtfs:route ?route .
    ?stop_time1 gtfs:trip ?trip ; gtfs:stop {stop_uri_origem} ; gtfs:stop_sequence ?seq1_raw .
    ?stop_time2 gtfs:trip ?trip ; gtfs:stop {stop_uri_dest} ; gtfs:stop_sequence ?seq2_raw .

    BIND(xsd:integer(?seq1_raw) AS ?seq1)
    BIND(xsd:integer(?seq2_raw) AS ?seq2)

    FILTER(?seq2 > ?seq1)

    ?stop_time gtfs:trip ?trip ; gtfs:stop ?stop ; gtfs:stop_sequence ?ordem_raw .
    BIND(xsd:integer(?ordem_raw) AS ?ordem)

    FILTER(?ordem >= ?seq1 && ?ordem <= ?seq2)

    ?stop geo:lat ?lat ; geo:long ?lon .
    }}
    ORDER BY ?trip ?ordem
    """

    print(query)
    sparql.setQuery(query)
    sparql.setReturnFormat(JSON)
    results = sparql.query().convert()

    rotas = {}
    for result in results["results"]["bindings"]:
        route = result["route"]["value"]
        ordem = int(result["ordem"]["value"])
        lat = float(result["lat"]["value"])
        lon = float(result["lon"]["value"])
        rotas.setdefault(route, []).append((ordem, lat, lon))
    melhor_rota = min(rotas.values(), key=len) if rotas else []

    melhor_rota = sorted(melhor_rota, key=lambda x: x[0])

    base_time = datetime.datetime(2023, 1, 1, 12, 0, 0)
    features = []
    for i, (_, lat, lon) in enumerate(melhor_rota):
        timestamp = (base_time + datetime.timedelta(seconds=i)).isoformat() + "Z"
        features.append({
            "type": "Feature",
            "geometry": {"type": "Point", "coordinates": [lon, lat]},
            "properties": {"time": timestamp, "popup": f"Parada {i+1}"}
        })
    geojson = {"type": "FeatureCollection", "features": features}

    if melhor_rota:
        lat_c = sum([lat for _, lat, _ in melhor_rota]) / len(melhor_rota)
        lon_c = sum([lon for _, _, lon in melhor_rota]) / len(melhor_rota)
    else:
        lat_c, lon_c = -22.9, -43.2

    m = folium.Map(location=[lat_c, lon_c], zoom_start=13, tiles="cartodbpositron")
    TimestampedGeoJson(
        geojson,
        period="PT1S",
        add_last_point=True,
        auto_play=True,
        loop=False,
        max_speed=1,
        loop_button=True,
        date_options='YYYY/MM/DD HH:mm:ss',
        time_slider_drag_update=True
    ).add_to(m)
    m.save("../map/melhor_rota.html")
    print("Mapa animado salvo como melhor_rota.html")

#-------------------------------------------------------------------------------

def generate_heatmap_paradas_geral():
    query = """
    PREFIX geo: <http://www.w3.org/2003/01/geo/wgs84_pos#/>
    PREFIX xsd: <http://www.w3.org/2001/XMLSchema#>

    SELECT ?lat_group ?lon_group (COUNT(?stop) AS ?qtd_paradas)
    WHERE {
    ?stop geo:lat ?lat ; geo:long ?lon .
    BIND(xsd:float(?lat) AS ?lat_num)
    BIND(xsd:float(?lon) AS ?lon_num)
    BIND(ROUND(?lat_num * 100) / 100 AS ?lat_group)
    BIND(ROUND(?lon_num * 100) / 100 AS ?lon_group)
    }
    GROUP BY ?lat_group ?lon_group
    """
    sparql.setQuery(query)
    sparql.setReturnFormat(JSON)
    results = sparql.query().convert()

    lats, lons, counts = [], [], []
    for result in results["results"]["bindings"]:
        lats.append(float(result["lat_group"]["value"]))
        lons.append(float(result["lon_group"]["value"]))
        counts.append(int(result["qtd_paradas"]["value"]))

    print(lats[1:10])

    img = mpimg.imread('../mapa_rj.png')
    x_min, y_min = -43.7955, -23.0827
    x_max, y_max = -43.0990, -22.7469

    plt.figure(figsize=(10, 10))
    plt.imshow(img, extent=[x_min, x_max, y_min, y_max], aspect='auto')
    plt.scatter(lons, lats, s=[c*5 for c in counts], c=counts, cmap='hot', alpha=0.6)
    plt.axis('off')
    plt.tight_layout()
    plt.savefig('heatmap_paradas_geral.png', dpi=200, bbox_inches='tight')
    plt.close()

    return results

def generate_heatmap_paradas_geral_folium():
    query = """
    PREFIX geo: <http://www.w3.org/2003/01/geo/wgs84_pos#/>
    PREFIX xsd: <http://www.w3.org/2001/XMLSchema#>

    SELECT ?lat ?lon
    WHERE {
      ?stop geo:lat ?lat ; geo:long ?lon .
    }
    """
    sparql.setQuery(query)
    sparql.setReturnFormat(JSON)
    results = sparql.query().convert()

    coords = []
    for result in results["results"]["bindings"]:
        lat = float(result["lat"]["value"])
        lon = float(result["lon"]["value"])
        coords.append([lat, lon])

    if coords:
        lat_c = sum([c[0] for c in coords]) / len(coords)
        lon_c = sum([c[1] for c in coords]) / len(coords)
    else:
        lat_c, lon_c = -22.9, -43.2

    m = folium.Map(location=[lat_c, lon_c], zoom_start=11, tiles="cartodbpositron")
    HeatMap(coords, radius=8, blur=15, min_opacity=0.3).add_to(m)
    m.save("../map/heatmap_paradas_geral.html")
    print("Mapa salvo como heatmap_paradas_geral.html")

    return results

#-------------------------------------------------------------------------------

def generate_heatmap_paradas_linha(route_id="1234"):
    """
    Gera o heatmap das paradas de uma linha específica usando folium.
    """
    query = f"""
    PREFIX gtfs: <http://vocab.gtfs.org/terms#/>
    PREFIX geo: <http://www.w3.org/2003/01/geo/wgs84_pos#/>

    SELECT ?lat ?lon
    WHERE {{
        ?trip gtfs:route <http://vocab.gtfs.org/terms#/routes/O0636AAA0A> .
        ?stop_time gtfs:trip ?trip ; gtfs:stop ?stop .
        ?stop geo:lat ?lat ; geo:long ?lon .
    }}
    """
    sparql.setQuery(query)
    sparql.setReturnFormat(JSON)
    results = sparql.query().convert()

    coords = []
    for result in results["results"]["bindings"]:
        lat = float(result["lat"]["value"])
        lon = float(result["lon"]["value"])
        coords.append([lat, lon])

    if coords:
        lat_c = sum([c[0] for c in coords]) / len(coords)
        lon_c = sum([c[1] for c in coords]) / len(coords)
    else:
        lat_c, lon_c = -22.9, -43.2

    m = folium.Map(location=[lat_c, lon_c], zoom_start=11, tiles="cartodbpositron")
    HeatMap(coords, radius=10, blur=18, min_opacity=0.3).add_to(m)
    m.save(f"../map/heatmap_paradas_linha_{route_id}.html")
    print(f"Mapa salvo como heatmap_paradas_linha_{route_id}.html")

    return results