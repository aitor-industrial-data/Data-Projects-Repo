import os
import sqlite3
import logging
from dotenv import load_dotenv


logger = logging.getLogger(__name__)

load_dotenv()

DB_PATH = os.getenv("DB_PATH", "data/default_project.db")

def create_tables():
    """Crea todas las tablas necesarias si no existen."""

    try:
        conn = sqlite3.connect(DB_PATH)
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
                wind_gust REAL
            )
        ''')

        # Tabla de PVGIS
        cursor.execute('''
            CREATE TABLE solar_generation (
                timestamp DATETIME PRIMARY KEY,
                power_kw FLOAT,
                irradiance_wm2 FLOAT,
                temp_c FLOAT,
                sun_height_deg FLOAT,
                source TEXT
            );
        ''')

        # Tabla de Precios
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS energy_prices (
                unix_timestamp INTEGER PRIMARY KEY,
                price REAL,
                currency TEXT
            )
        ''')
        
        conn.commit()
        conn.close()
        logger.info("🗄️ Estructura de tablas verificada/creada correctamente.")
    except sqlite3.Error as e:
        logger.error(f"❌ Error al crear las tablas: {e}")


def save_to_db(data_list, table_name):
    """Inserta una lista de diccionarios en la tabla especificada."""
    if not data_list:
        logger.warning(f"⚠️ No hay datos para guardar en {table_name}.")
        return
    
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        keys = data_list[0].keys()
        columns = ', '.join(keys)
        placeholders = ', '.join(['?' for _ in keys])
        
        sql = f"INSERT OR REPLACE INTO {table_name} ({columns}) VALUES ({placeholders})"
        values = [tuple(d.values()) for d in data_list]
        
        cursor.executemany(sql, values)
        conn.commit()
        conn.close()
        
        # Cambiamos print por logger.info
        logger.info(f"💾 {len(data_list)} registros procesados en la tabla {table_name}.")
        
    except sqlite3.Error as e:
        logger.error(f"❌ Error al insertar datos en {table_name}: {e}")