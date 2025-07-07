import pandas as panda

BASE_DIR = './gtfs-rio-de-janeiro'
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

def read_csv_files(printSteps: bool = False ):
    "Lê os arquivos csv GTFS do Rio de Janeiro e retorna um objeto de DataFrames do pandas."

    if(printSteps): print("Lendo arquivos CSV do GTFS do Rio de Janeiro...")
    return {
        file_name: panda.read_csv(f'{BASE_DIR}/{file_name}.csv') for file_name in FILE_NAMES
    }


