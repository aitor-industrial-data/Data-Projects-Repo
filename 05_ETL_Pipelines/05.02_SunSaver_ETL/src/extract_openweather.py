# ==============================================================================
# extract_openweather.py
# ------------------------------------------------------------------------------
# RESPONSABILIDAD : Extraer los datos CRUDOS de la API de OpenWeatherMap.
# CAPA ETL        : EXTRACT
# FUENTE          : OpenWeatherMap Forecast API (5 días, intervalos de 3h)
# SALIDA          : list[dict] — datos crudos listos para guardar en bronce
# ------------------------------------------------------------------------------
# DISEÑO MULTI-CLIENTE:
#   La función principal extract_weather() acepta coordenadas como parámetros,
#   lo que permite llamarla para cualquier cliente con cualquier ubicación.
#   El orquestador es responsable de pasar las coordenadas de cada cliente.
# ------------------------------------------------------------------------------
# DEPENDENCIAS DE ENTORNO (.env):
#   WEATHER_API_KEY → Clave de acceso a la API de OpenWeather (única para todos
#                     los clientes — es una clave del sistema, no del cliente)
# ==============================================================================

import requests
import sqlite3
import logging
import os
import sys
import pandas as pd
import json
from datetime import datetime
from typing import Dict, Any
from dotenv import load_dotenv

import db_manager

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)

logger = logging.getLogger(__name__)

load_dotenv()


# ------------------------------------------------------------------------------
# FUNCIÓN PRINCIPAL DE EXTRACCIÓN
# Acepta coordenadas como parámetros para soportar múltiples clientes.
# Se puede llamar con cualquier ubicación sin tocar el .env.
# ------------------------------------------------------------------------------

def extract_weather(lat: float, lon: float)-> Dict[str, Any]:
   
    url = "https://api.openweathermap.org/data/2.5/forecast"

    API_KEY = os.getenv("WEATHER_API_KEY")
    if not API_KEY:
        logger.error("Falta WEATHER_API_KEY en el .env")
        sys.exit(1)

    params = {
        'lat':   lat,
        'lon':   lon,
        'appid': API_KEY,
        'units': 'metric',  # Temperatura en °C
        'lang':  'en'       # Descripciones en inglés para consistencia en DB
    }

    logger.info(f"🛰️  Consultando OpenWeather — coordenadas: ({lat}, {lon})")

    try:
        response = requests.get(url, params=params, timeout=15)
        response.raise_for_status()

        all_data = response.json()

        if not all_data:
            logger.error("OpenWeather devolvió una lista vacía — sin datos para procesar")
            raise ValueError("OpenWeather devolvió una lista vacía")

        logger.info(f"✅ Extracción completada: {len(all_data)} registros obtenidos.")
        return all_data

    except requests.exceptions.RequestException as e:
        logger.error(f"❌ Error de conexión con OpenWeather: {e}")
        raise


def ingest_openweather_to_bronze(api_response: dict, table_name: str, client_id: str) -> bool:
    """
    Capa Bronce: Carga los datos crudos de la API y añade 
    metadatos de auditoría (_ingested_at).
    """
    try:
        db_path = db_manager.get_db_path()

        # Convertimos el diccionario entero a un String de texto
        raw_json_str = json.dumps(api_response, ensure_ascii=False)
        ingested_at = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        # Creamos un DataFrame de una sola fila y dos columnas
        df = pd.DataFrame([{
            'client_id': client_id,
            '_ingested_at': ingested_at,
            'raw_data': raw_json_str
        }])
        

        with sqlite3.connect(str(db_path)) as conn:
            df.to_sql(table_name, conn, if_exists='append', index=False)

        logger.info(f"✅ Ingesta exitosa: {len(df)} registros añadidos a base de datos.")
        return True
    
    except Exception as e:
        logger.error(f"❌ Error en la ingesta Bronce: {e}")
        return False


def extract_all_clients_weather(client_table: str, weather_table: str) -> bool:
    try:

        db_path = db_manager.get_db_path()
            
        # 1. LEER CLIENTES: Traemos solo lo necesario de Silver
        with sqlite3.connect(str(db_path)) as conn:
            query = f"SELECT client_id, latitude, longitude FROM {client_table}"
            df_clients = pd.read_sql(query, conn)


        for index, row in df_clients.iterrows():
            client_id = row['client_id']
            lat = row['latitude']
            lon = row['longitude']

            try:
                # Extracción
                raw_weather=extract_weather(lat, lon)

                # Ingesta
                if raw_weather:
                    ingest_openweather_to_bronze(raw_weather, weather_table, client_id)
                else:
                    logger.warning(f"⚠️ No se obtuvieron datos para el cliente {client_id}")

            except Exception as e:
                # Si falla un cliente, logueamos y seguimos con el siguiente
                logger.error(f"❌ Error procesando cliente {client_id}: {e}")
                continue

        return True
    
    except Exception as e:
        # Este try captura errores críticos (ej: no hay conexión a la DB inicial)
        logger.critical(f"❌ Error crítico en extract_all_clients_weather: {e}")
        return False


if __name__ == "__main__":
    
    # Extre datos openweather de para cada client_id (clean_clients) de una tabla y lo inyecta en otra tabla (raw_weather)
    extract_all_clients_weather('clean_clients', 'raw_weather')


