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

def extract_raw_weather_from_db(table_name: str = 'raw_weather') -> pd.DataFrame:
    """
    Extrae solo las ultimas lecturas de cada cliente y las devuelve como DataFrame.
    """
    try:
        db_path = db_manager.get_db_path()
        
        # 1. Conexión a la DB (usando str por seguridad de tipos)
        with sqlite3.connect(str(db_path)) as conn:
            # 2. Leemos la tabla entera directamente a un DataFrame
            query = f"""
            WITH RankedData AS (
                SELECT 
                    client_id, 
                    _ingested_at, 
                    raw_data,
                    ROW_NUMBER() OVER (
                        PARTITION BY client_id 
                        ORDER BY _ingested_at DESC
                    ) as rn
                FROM {table_name}
            )
            SELECT client_id, _ingested_at, raw_data
            FROM RankedData
            WHERE rn = 1
            """
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
                    'unix_time':int(f.get('dt')),
                    'forecast_time': f.get('dt_txt'),
                    'temp_celsius': f.get('main', {}).get('temp'),
                    'humidity_pct': f.get('main', {}).get('humidity'),
                    'clouds_pct': f.get('clouds', {}).get('all'),
                    'rain_prob_norm': f.get('pop'),
                    'wind_speed_mps': f.get('wind', {}).get('speed'),
                    'weather_id': f.get('weather', [{}])[0].get('id'),
                    'weather_main': f.get('weather', [{}])[0].get('main'),
                    'weather_description': f.get('weather', [{}])[0].get('description'),
                    'is_daylight': 1 if f.get('sys', {}).get('pod') == 'd' else 0,
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
        df['rain_prob_norm'] = df['rain_prob_norm'].fillna(0)
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
    

def load_weather_to_silver(df: pd.DataFrame, table_name: str = "clean_weather") -> bool:
    """
    Capa Silver: Almacena el histórico de predicciones/clima procesado.
    Usa una clave primaria compuesta para evitar duplicados exactos.
    """
    db_path = db_manager.get_db_path()
    
    try:
        if df.empty:
            logger.warning(f"⚠️ DataFrame para '{table_name}' vacío.")
            return False


        # Creamos una copia para no alterar el DataFrame original que viaja por el script
        df_sql = df.copy()
        
        # Convertimos los objetos Timestamp de Pandas a String (formato ISO)
        # Esto soluciona el error: "type 'Timestamp' is not supported"
        df_sql['forecast_time'] = df_sql['forecast_time'].dt.strftime('%Y-%m-%d %H:%M:%S')
        df_sql['_ingested_at'] = df_sql['_ingested_at'].dt.strftime('%Y-%m-%d %H:%M:%S')

        engine = create_engine(f"sqlite:///{db_path}")

        with engine.begin() as connection:
            # 1. Creamos la tabla si no existe (con clave compuesta)
            # Combinamos client_id y forecast_time para que no haya dos registros
            # del mismo cliente para la misma hora.
            create_table_query = f"""
            CREATE TABLE IF NOT EXISTS {table_name} (
                client_id               TEXT NOT NULL,
                unix_time               INTEGER NOT NULL,
                forecast_time           TEXT NOT NULL,
                temp_celsius            REAL,
                humidity_pct            REAL,
                clouds_pct              REAL,
                rain_prob_norm          REAL,
                wind_speed_mps          REAL,
                weather_id              INTEGER,
                weather_main            TEXT,
                weather_description     TEXT,
                is_daylight             INTEGER,
                _ingested_at            TEXT NOT NULL,
                PRIMARY KEY (client_id, unix_time)
            )
            """
            connection.execute(text(create_table_query))
            
            # 2. UPSERT (Update or Insert)
            # Convertimos el DF a una lista de diccionarios para usar SQL puro
            # Esto permite usar "INSERT OR REPLACE" que es lo que tú necesitas         
            # Usamos df_sql (la copia con strings) para el diccionario
            data = df_sql.to_dict(orient='records')

            upsert_query = text(f"""
                INSERT OR REPLACE INTO {table_name} 
                ({', '.join(df.columns)}) 
                VALUES ({', '.join([':' + col for col in df.columns])})
            """)
            
            connection.execute(upsert_query, data)
        
        logger.info(f"✅ Capa Silver actualizada: {len(df)} registros procesados.")
        return True

    except Exception as e:
        logger.error(f"❌ Error en carga Silver Weather: {e}")
        return False


def transform_openweather() -> bool:
    try:
        # 1. Extracción (Capa Bronze)
        raw_weather=extract_raw_weather_from_db()
        
        # 2. Transformación (Limpieza y tipos)
        clean_weather=transform_weather_bronze_to_silver(raw_weather)
        
        # 3. Carga (Capa Silver)
        load_weather_to_silver(clean_weather)
        
        return True

    except Exception as e:
        # Registramos el error con detalle para debuguear después
        logger.error(f"❌ Error crítico en el pipeline de transform_clients: {e}")
        return False
    
if __name__ == "__main__":

    logger.info(f"Iniciando extraccion e ingesta de weather de capa bronze a silver...")
    transform_openweather()
   
