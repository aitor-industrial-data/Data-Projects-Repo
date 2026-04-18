import os
import sqlite3
import logging
import json
from dotenv import load_dotenv

logger = logging.getLogger(__name__)

load_dotenv()

DB_PATH = os.getenv("DB_PATH", "data/default_project.db")

def create_tables():
    """Crea todas las tablas necesarias si no existen."""
    try:
        with sqlite3.connect(DB_PATH) as conn:
            cursor = conn.cursor()
            
            # Tabla de Clima
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS weather_forecast (
                    unix_timestamp INTEGER PRIMARY KEY,
                    forecast_time TEXT,
                    temperature REAL,
                    cloud_coverage INTEGER,
                    condition_desc TEXT,
                    wind_speed REAL,
                    wind_gust REAL,
                    source TEXT
                )
            ''')

            # Tabla de PVGIS
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS solar_generation (
                    unix_timestamp INTEGER PRIMARY KEY,
                    timestamp TEXT,
                    power_kw REAL,
                    irradiance_wm2 REAL,
                    temp_c REAL,
                    sun_height_deg REAL,
                    source TEXT
                )
            ''')

            # Tabla de Precios
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS energy_prices (
                    unix_timestamp INTEGER PRIMARY KEY,
                    price REAL,
                    currency TEXT
                )
            ''')
            
            logger.info("🗄️  Estructura de tablas verificada/creada correctamente.")
            
    except sqlite3.Error as e:
        logger.error(f"❌ Error al crear las tablas: {e}")


def save_bronze_to_db(data, table_name: str):
    """Guarda datos crudos en la capa bronce. Acepta dict (PVGIS) o list[dict] (OpenWeather, ESIOS)."""
    if not data:
        logger.warning(f"No hay datos para guardar en {table_name}.")
        return

    try:
        with sqlite3.connect(DB_PATH) as conn:
            cursor = conn.cursor()
            cursor.execute(f"""
                CREATE TABLE IF NOT EXISTS {table_name} (
                    id          INTEGER PRIMARY KEY AUTOINCREMENT,
                    ingested_at TEXT DEFAULT (datetime('now')),
                    raw_data    TEXT
                )
            """)

            if isinstance(data, dict):
                values = [(json.dumps(data),)]
            elif isinstance(data, list):
                values = [(json.dumps(record),) for record in data]
            else:
                logger.error(f"Tipo de dato no soportado: {type(data)}")
                return

            cursor.executemany(
                f"INSERT INTO {table_name} (raw_data) VALUES (?)", values
            )

        logger.info(f"✅ {len(values)} registros insertados en {table_name}.")

    except sqlite3.Error as e:
        logger.error(f"Error al insertar en {table_name}: {e}")


def read_bronze_from_db(table_name: str, latest_only: bool = False):
    """
    Lee datos crudos de la capa bronce y los deserializa.

    - Si la tabla guardó un dict (PVGIS):     devuelve dict
    - Si la tabla guardó list[dict] (OpenWeather, ESIOS): devuelve list[dict]

    Parámetros:
        table_name  : nombre de la tabla bronce (ej: 'bronze_weather')
        latest_only : si True, devuelve solo los registros de la última ingesta
    """
    try:
        with sqlite3.connect(DB_PATH) as conn:
            cursor = conn.cursor()

            if latest_only:
                # Cogemos solo los registros de la ingesta más reciente
                cursor.execute(f"""
                    SELECT raw_data FROM {table_name}
                    WHERE ingested_at = (SELECT MAX(ingested_at) FROM {table_name})
                """)
            else:
                cursor.execute(f"SELECT raw_data FROM {table_name}")

            rows = cursor.fetchall()

        if not rows:
            logger.warning(f"⚠️ No hay datos en {table_name}.")
            return None

        # Deserializamos cada fila de JSON a Python
        records = [json.loads(row[0]) for row in rows]

        # Si solo hay 1 registro y es un dict (PVGIS), devolvemos el dict directamente
        if len(records) == 1 and isinstance(records[0], dict):
            logger.info(f"✅ 1 registro leído de {table_name} (dict).")
            return records[0]

        # Si hay varios registros (OpenWeather, ESIOS), devolvemos la lista
        logger.info(f"✅ {len(records)} registros leídos de {table_name} (list[dict]).")
        return records

    except sqlite3.Error as e:
        logger.error(f"❌ Error al leer de {table_name}: {e}")
        return None


def save_to_db(data_list, table_name):
    """Inserta una lista de diccionarios en la tabla especificada."""
    if not data_list:
        logger.warning(f"⚠️ No hay datos para guardar en {table_name}.")
        return
    
    try:
        with sqlite3.connect(DB_PATH) as conn:
            cursor = conn.cursor()
            
            keys = data_list[0].keys()
            columns = ', '.join(keys)
            placeholders = ', '.join(['?' for _ in keys])
            
            sql = f"INSERT OR REPLACE INTO {table_name} ({columns}) VALUES ({placeholders})"
            values = [tuple(d.values()) for d in data_list]
            
            cursor.executemany(sql, values)
            
        logger.info(f"✅ {len(data_list)} registros procesados en la tabla {table_name}.")
        
    except sqlite3.Error as e:
        logger.error(f"❌ Error al insertar datos en {table_name}: {e}")