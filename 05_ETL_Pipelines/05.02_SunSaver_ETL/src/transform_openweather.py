import pandas as pd
from datetime import datetime
import sqlite3
import json
import logging
from sqlalchemy import create_engine, text
import numpy as np

import db_manager

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)

logger = logging.getLogger(__name__)

def extract_from_db(table_name: str) -> pd.DataFrame:
    """
    Lee los datos de la tabla y los devuelve como DataFrame.
    """
    try:
        db_path = db_manager.get_db_path()
        
        # 1. Conexión a la DB (usando str por seguridad de tipos)
        with sqlite3.connect(str(db_path)) as conn:
            # 2. Leemos la tabla entera directamente a un DataFrame
            query = f"SELECT * FROM {table_name}"
            df = pd.read_sql_query(query, conn)
            
        logger.info(f"✅ Extracción exitosa: {len(df)} registros extraidos de DB")
        return df

    except Exception as e:
        logger.error(f"❌ Error extrayendo de DB: {e}")
        return pd.DataFrame() # Devolvemos un DF vacío si falla
    

def transform_weather_bronze_to_silver(df_raw: pd.DataFrame) -> pd.DataFrame:
    """
    Transforma los datos de weather de cada cliente de la capa Bronze a Silver aplicando
    limpieza de nulos, tipado de datos y validación de campos críticos.
    """
    try:
        if df_raw.empty:
            return pd.DataFrame()
        
        df = df_raw.copy()
        
        data_to_clean = []
    
        for index, row in df.iterrows():
            client_id = row['client_id']
            ingested_at = row['_ingested_at']

            # Convertimos el string de nuevo a diccionario
            raw_json = json.loads(row['raw_data'])
            
            # Extraemos la lista de los 40 pronósticos
            forecasts = raw_json.get('list', [])
            
            for f in forecasts:
                entry = {
                    'client_id': client_id,
                    'unix_time':f.get('dt'),
                    'forecast_time': f.get('dt_txt'),
                    'temp_celsius': f.get('main', {}).get('temp'),
                    'clouds_pct': f.get('clouds', {}).get('all'),
                    'rain_prob': f.get('pop'),
                    'wind_speed': f.get('wind', {}).get('speed'),
                    '_ingested_at': ingested_at
                }
                data_to_clean.append(entry)
                
        df = pd.DataFrame(data_to_clean)

        # ==========================================
        #          FASE DE LIMPIEZA
        # ==========================================

        # 1. TIPADO: Convertir a datetime para poder operar con fechas
        df['forecast_time'] = pd.to_datetime(df['forecast_time'], errors='coerce')
        df['_ingested_at'] = pd.to_datetime(df['_ingested_at'], errors='coerce')
        
        # 2. NULOS: Si no hay probabilidad de lluvia, es 0. 
        # Si no hay temperatura, llenamos con la anterior (ffill) o 0
        df['rain_prob'] = df['rain_prob'].fillna(0)
        df = df.dropna(subset=['client_id', 'forecast_time']) # Campos críticos

        # 3. DEDUPLICACIÓN (Vital en tu caso):
        # Como has lanzado el robot varias veces, tienes el mismo pronóstico repetido.
        # Ordenamos por fecha de ingesta y nos quedamos con la última versión de cada pronóstico.
        df = df.sort_values(by=['client_id', 'forecast_time', '_ingested_at'], ascending=[True, True, False])
        df = df.drop_duplicates(subset=['client_id', 'forecast_time'], keep='first')


        
        logger.info(f"✅ Limpieza Silver completada: {len(df)} registros listos.")
        return df
        
    except:
        return pd.DataFrame()

if __name__ == "__main__":

    logger.info(f"Iniciando extraccion e ingesta de weaather de capa bronze a silver...")
    raw_weather=extract_from_db('raw_weather')
    print(transform_weather_bronze_to_silver(raw_weather))
   
