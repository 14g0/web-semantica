import pandas as panda
from rdflib import Graph, Literal
from rdflib.namespace import RDF, FOAF, XSD, Namespace, DC

BASE_DIR = '../assets/gtfs-rio-de-janeiro'
FILE_NAMES = [
    'agency',
    # 'calendar',
    # 'calendar_dates',
    # 'fare_attributes',
    # 'fare_rules',
    # 'feed_info',
    'frequencies',
    'routes',
    'shapes',
    'stops',
    'stop_times',
    'trips'
]

GTFS_URI = Namespace("http://vocab.gtfs.org/terms#/")
TIME_URI = Namespace("http://www.w3.org/2006/time#/")
GEO_URI = Namespace("http://www.w3.org/2003/01/geo/wgs84_pos#/")
mainGraph = Graph()

#-------------------------------------------------------------------------------

def read_csv_file(printSteps: bool = False ):
    "Lê os arquivos csv GTFS do Rio de Janeiro e retorna um objeto de DataFrames do pandas."

    if(printSteps): print("Lendo arquivos CSV do GTFS do Rio de Janeiro...")
    return {
        file_name: panda.read_csv(f'{BASE_DIR}/{file_name}.csv') for file_name in FILE_NAMES
    }

#-------------------------------------------------------------------------------

def add_agency_to_rdf(df: panda.DataFrame):
    "Adiciona os dados da agência ao grafo RDF."
    
    for _, row in df.iterrows():
        agency_id = row['agency_id']
        agency_uri = GTFS_URI[f"agency/{agency_id}"]

        mainGraph.add((agency_uri, RDF.type, GTFS_URI.Agency))

        if 'agency_name' in row and not panda.isna(row['agency_name']):
            mainGraph.add((agency_uri, FOAF.name, Literal(row['agency_name'], datatype=XSD.string)))

        if 'agency_url' in row and not panda.isna(row['agency_url']):
            mainGraph.add((agency_uri, FOAF.page, Literal(row['agency_url'])))

        if 'agency_timezone' in row and not panda.isna(row['agency_timezone']):
            mainGraph.add((agency_uri, TIME_URI.timeZone, Literal(row['agency_timezone'], datatype=XSD.string)))

#-------------------------------------------------------------------------------
    
def add_frequencies_to_rdf(df: panda.DataFrame):
    "Adiciona os dados de frequências ao grafo RDF."

    for _, row in df.iterrows():
        if (
            'trip_id' in row and not panda.isna(row['trip_id']) and
            'start_time' in row and not panda.isna(row['start_time']) and
            'end_time' in row and not panda.isna(row['end_time']) and
            'headway_secs' in row and not panda.isna(row['headway_secs'])
        ):
            freq_uri = GTFS_URI[f"trips/{row['trip_id']}/frequencies/{row['start_time']}{row['end_time']}"]

            mainGraph.add((freq_uri, RDF.type, GTFS_URI.Frequency))
            mainGraph.add((freq_uri, GTFS_URI.startTime, Literal(row['start_time'], datatype=XSD.string)))
            mainGraph.add((freq_uri, GTFS_URI.endTime, Literal(row['end_time'], datatype=XSD.string)))
            mainGraph.add((freq_uri, GTFS_URI.headwaySeconds, Literal(str(row['headway_secs']), datatype=XSD.string)))

            if 'exact_times' in row and not panda.isna(row['exact_times']):
                valor_bool = str(row['exact_times']) == "1"
                mainGraph.add((freq_uri, GTFS_URI.headwaySeconds, Literal(valor_bool, datatype=XSD.boolean)))
            else:
                mainGraph.add((freq_uri, GTFS_URI.headwaySeconds, Literal(False, datatype=XSD.boolean)))
        else:
            print("Frequency doesn't contain all required fields")

#-------------------------------------------------------------------------------

def add_routes_to_rdf(df: panda.DataFrame):
    "Adiciona os dados das rotas ao grafo RDF."

    route_type_map = {
        "0": GTFS_URI.LightRail,
        "1": GTFS_URI.SubWay,
        "2": GTFS_URI.Rail,
        "3": GTFS_URI.Bus,
        "4": GTFS_URI.Ferry,
        "5": GTFS_URI.CableCar,
        "6": GTFS_URI.Gondola,
        "7": GTFS_URI.Funicular,
    }

    for _, row in df.iterrows():
        route_id = row['route_id']
        route_uri = GTFS_URI[f"routes/{route_id}"]

        mainGraph.add((route_uri, RDF.type, GTFS_URI.Route))

        if 'agency_id' in row and not panda.isna(row['agency_id']):
            agency_uri = GTFS_URI[f"agency/{row['agency_id']}"]
            mainGraph.add((route_uri, GTFS_URI.agency, agency_uri))

        if 'route_short_name' in row and not panda.isna(row['route_short_name']):
            mainGraph.add((route_uri, GTFS_URI.shortName, Literal(row['route_short_name'], datatype=XSD.string)))

        if 'route_long_name' in row and not panda.isna(row['route_long_name']):
            mainGraph.add((route_uri, GTFS_URI.longName, Literal(row['route_long_name'], datatype=XSD.string)))

        if 'route_desc' in row and not panda.isna(row['route_desc']):
            mainGraph.add((route_uri, DC.description, Literal(row['route_desc'], datatype=XSD.string)))

        if 'route_type' in row and not panda.isna(row['route_type']):
            route_type_uri = route_type_map.get(str(int(row['route_type'])))
            if route_type_uri:
                mainGraph.add((route_uri, GTFS_URI.routeType, route_type_uri))

        if 'route_url' in row and not panda.isna(row['route_url']):
            mainGraph.add((route_uri, FOAF.page, Literal(row['route_url'])))

        if 'route_color' in row and not panda.isna(row['route_color']):
            mainGraph.add((route_uri, GTFS_URI.color, Literal(row['route_color'], datatype=XSD.string)))

        if 'route_textColor' in row and not panda.isna(row['route_textColor']):
            mainGraph.add((route_uri, GTFS_URI.textColor, Literal(row['route_textColor'], datatype=XSD.string)))

#-------------------------------------------------------------------------------

def add_stops_to_rdf(df: panda.DataFrame):
    "Adiciona os dados das paradas ao grafo RDF."

    for _, row in df.iterrows():
        stop_id = row['stop_id']
        stop_uri = GTFS_URI[f"stops/{stop_id}"]

        mainGraph.add((stop_uri, DC.identifier, Literal(str(stop_id))))

        if 'location_type' in row and str(row['location_type']) == "1":
            mainGraph.add((stop_uri, RDF.type, GTFS_URI.Station))
        else:
            mainGraph.add((stop_uri, RDF.type, GTFS_URI.Stop))
            if 'parent_station' in row and not panda.isna(row['parent_station']):
                mainGraph.add((stop_uri, GTFS_URI.parentStation, Literal(str(row['parent_station']))))
            if 'zone_id' in row and not panda.isna(row['zone_id']):
                zone_uri = GTFS_URI[f"zones/{row['zone_id']}"]
                mainGraph.add((zone_uri, RDF.type, GTFS_URI.Zone))
                mainGraph.add((stop_uri, GTFS_URI.zone, zone_uri))

        if 'stop_code' in row and not panda.isna(row['stop_code']):
            mainGraph.add((stop_uri, GTFS_URI.code, Literal(str(row['stop_code']))))

        if 'stop_name' in row and not panda.isna(row['stop_name']):
            mainGraph.add((stop_uri, FOAF.name, Literal(str(row['stop_name']))))

        if 'stop_desc' in row and not panda.isna(row['stop_desc']):
            mainGraph.add((stop_uri, DC.description, Literal(str(row['stop_desc']))))

        if 'stop_lat' in row and not panda.isna(row['stop_lat']):
            mainGraph.add((stop_uri, GEO_URI.lat, Literal(str(row['stop_lat']))))

        if 'stop_lon' in row and not panda.isna(row['stop_lon']):
            mainGraph.add((stop_uri, GEO_URI.long, Literal(str(row['stop_lon']))))

        if 'stop_url' in row and not panda.isna(row['stop_url']):
            mainGraph.add((stop_uri, FOAF.page, Literal(str(row['stop_url']))))

        if 'wheelchair_boarding' in row and not panda.isna(row['wheelchair_boarding']):
            if str(row['wheelchair_boarding']) == "0":
                mainGraph.add((stop_uri, GTFS_URI.wheelchairAccessible, GTFS_URI.CheckParentStation))
            elif str(row['wheelchair_boarding']) == "1":
                mainGraph.add((stop_uri, GTFS_URI.wheelchairAccessible, GTFS_URI.WheelchairAccessible))
            elif str(row['wheelchair_boarding']) == "2":
                mainGraph.add((stop_uri, GTFS_URI.wheelchairAccessible, GTFS_URI.NotWheelchairAccessible))

#-------------------------------------------------------------------------------

def add_stop_times_to_rdf(df: panda.DataFrame):
    "Adiciona os dados de horários de parada (stop_times) ao grafo RDF."

    pickup_type_map = {
        "0": GTFS_URI.Regular,
        "1": GTFS_URI.NotAvailable,
        "2": GTFS_URI.MustPhone,
        "3": GTFS_URI.MustCoordinateWithDriver,
    }
    drop_off_type_map = pickup_type_map  # Mesmo mapeamento

    for _, row in df.iterrows():
        trip_id = row['trip_id']
        stop_id = row['stop_id']
        stop_time_uri = GTFS_URI[f"trip/{trip_id}/stop/{stop_id}"]

        mainGraph.add((stop_time_uri, RDF.type, GTFS_URI.StopTime))
        mainGraph.add((stop_time_uri, GTFS_URI.stop, GTFS_URI[f"stops/{stop_id}"]))
        mainGraph.add((stop_time_uri, GTFS_URI.trip, GTFS_URI[f"trips/{trip_id}"]))

        if 'arrival_time' in row and not panda.isna(row['arrival_time']):
            mainGraph.add((stop_time_uri, GTFS_URI.arrivalTime, Literal(row['arrival_time'], datatype=XSD.string)))

        if 'departure_time' in row and not panda.isna(row['departure_time']):
            mainGraph.add((stop_time_uri, GTFS_URI.departureTime, Literal(row['departure_time'], datatype=XSD.string)))

        if 'stop_sequence' in row and not panda.isna(row['stop_sequence']):
            mainGraph.add((stop_time_uri, GTFS_URI.stopSequence, Literal(int(row['stop_sequence']), datatype=XSD.nonNegativeInteger)))

        if 'stop_headsign' in row and not panda.isna(row['stop_headsign']):
            mainGraph.add((stop_time_uri, GTFS_URI.headsign, Literal(row['stop_headsign'], datatype=XSD.string)))

        if 'pickup_type' in row and not panda.isna(row['pickup_type']):
            pickup_uri = pickup_type_map.get(str(int(row['pickup_type'])))
            if pickup_uri:
                mainGraph.add((stop_time_uri, GTFS_URI.pickupType, pickup_uri))

        if 'shape_dist_traveled' in row and not panda.isna(row['shape_dist_traveled']):
            mainGraph.add((stop_time_uri, GTFS_URI.distanceTraveled, Literal(int(row['shape_dist_traveled']), datatype=XSD.nonNegativeInteger)))

#-------------------------------------------------------------------------------

def add_trips_to_rdf(df: panda.DataFrame):
    "Adiciona os dados das viagens (trips) ao grafo RDF."

    for _, row in df.iterrows():
        trip_id = row['trip_id']
        trip_uri = GTFS_URI[f"trips/{trip_id}"]

        mainGraph.add((trip_uri, RDF.type, GTFS_URI.Trip))

        if 'route_id' in row and not panda.isna(row['route_id']):
            route_uri = GTFS_URI[f"routes/{row['route_id']}"]
            mainGraph.add((trip_uri, GTFS_URI.route, route_uri))

        if 'service_id' in row and not panda.isna(row['service_id']):
            service_uri = GTFS_URI[f"services/{row['service_id']}"]
            mainGraph.add((trip_uri, GTFS_URI.service, service_uri))

        if 'trip_headsign' in row and not panda.isna(row['trip_headsign']):
            mainGraph.add((trip_uri, GTFS_URI.headsign, Literal(row['trip_headsign'], datatype=XSD.string)))

        if 'trip_short_name' in row and not panda.isna(row['trip_short_name']):
            mainGraph.add((trip_uri, GTFS_URI.shortName, Literal(row['trip_short_name'], datatype=XSD.string)))

        if 'direction_id' in row and not panda.isna(row['direction_id']):
            valor_bool = str(row['direction_id']) == "1"
            mainGraph.add((trip_uri, GTFS_URI.direction, Literal(valor_bool, datatype=XSD.boolean)))

        if 'shape_id' in row and not panda.isna(row['shape_id']):
            shape_uri = GTFS_URI[f"shapes/{row['shape_id']}"]
            mainGraph.add((shape_uri, RDF.type, GTFS_URI.Shape))
            mainGraph.add((trip_uri, GTFS_URI.shape, shape_uri))


#-------------------------------------------------------------------------------

def generate_rdf_graph(printSteps: bool = False):
    "Gera o grafo RDF a partir dos arquivos CSV do GTFS do Rio de Janeiro."

    if(printSteps): print("Gerando grafo RDF...")

    df_dict = read_csv_file(printSteps)

    add_agency_to_rdf(df_dict['agency'])
    add_frequencies_to_rdf(df_dict['frequencies'])
    add_routes_to_rdf(df_dict['routes'])
    add_stops_to_rdf(df_dict['stops'])
    add_stop_times_to_rdf(df_dict['stop_times'])
    add_trips_to_rdf(df_dict['trips'])

    if(printSteps): print("Grafo RDF gerado com sucesso!")

    mainGraph.serialize(destination='./gtfs.ttl', format='ttl')