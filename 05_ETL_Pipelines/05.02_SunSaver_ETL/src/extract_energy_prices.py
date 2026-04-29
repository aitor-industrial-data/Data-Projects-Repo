import requests
import pandas as pd
import logging
from datetime import datetime, timedelta
from dotenv import load_dotenv
import json
import sqlite3


import db_manager

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)

logger = logging.getLogger(__name__)


load_dotenv()


def extract_raw_json_from_ree() -> dict:
    """
    Extrae el objeto JSON original de la API de REE.
    """
    

    # Calculamos la fecha de mañana
    today=datetime.now().strftime("%Y-%m-%d")
    tomorrow = (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d")
    

    # Construimos la URL con la fecha de mañana
    url = (
        "https://apidatos.ree.es/es/datos/mercados/precios-mercados-tiempo-real"
        f"?start_date={today}T00:00&end_date={today}T23:59&time_trunc=hour"
        
    )

    headers = {"Accept": "application/json"}

    try:
        # 1. Petición a la API
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        
        # Este es el diccionario "crudo"
        raw_json = response.json()
        
        if not raw_json.get('included') or not raw_json['included'][0]['attributes']['values']:
            logger.warning("⚠️ Los precios para mañana aún no han sido publicados.")
            return False

        # Devolvemos el diccionario gigante tal cual
        logger.info(f"✅ Extracción completada: {len(raw_json)} registros obtenidos.")
        return raw_json

    except Exception as e:
        logger.error(f"❌ Error al obtener el JSON crudo: {e}")
        return None


def ingest_ree_to_bronze(api_response: dict, table_name: str = 'raw_prices') -> bool:
    """
    Capa Bronce para REE: Carga el JSON completo de precios en la base de datos.
    """
    if not api_response:
        logger.error("❌ No hay datos de REE para ingestar.")
        return False

    try:
        db_path = db_manager.get_db_path()

        # 1. Serializamos el JSON completo a una cadena de texto (Raw String)
        raw_json_str = json.dumps(api_response, ensure_ascii=False)
        ingested_at = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        # 2. Creamos el DataFrame de auditoría
        df = pd.DataFrame([{
            '_ingested_at': ingested_at,
            'raw_data': raw_json_str
        }])

        # 3. Inserción en SQLite
        with sqlite3.connect(str(db_path)) as conn:
            df.to_sql(table_name, conn, if_exists='append', index=False)

            # Aseguramos el índice para búsquedas rápidas por fecha de carga
            index_query = f"CREATE INDEX IF NOT EXISTS idx_ree_ingested_at ON {table_name} (_ingested_at);"
            conn.execute(index_query)

        logger.info(f"✅ Ingesta Bronce REE exitosa en tabla '{table_name}'.")
        return True
    
    except Exception as e:
        logger.error(f"❌ Error en la ingesta Bronce de REE: {e}")
        return False
    

def extract_energy_prices():
    raw_prices = extract_raw_json_from_ree()
    ingest_ree_to_bronze(raw_prices)


if __name__ == "__main__":
    extract_energy_prices()
    