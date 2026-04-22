import pandas as pd
from pathlib import Path


def extract_clients_from_csv():
    # 1. Localizamos la raíz del proyecto de forma dinámica
    # Si este script está en /src, subimos un nivel para encontrar /data
    BASE_DIR = Path(__file__).resolve().parent.parent
    csv_path = BASE_DIR / "data" / "clients_source.csv"
    
    if not csv_path.exists():
        print(f"❌ Error: No encuentro el archivo en {csv_path}")
        return []

    # 2. Leemos con Pandas
    df = pd.read_csv(csv_path)
    
    # 3. Convertimos a lista de diccionarios para la función de ingesta
    return df.to_dict(orient='records')
