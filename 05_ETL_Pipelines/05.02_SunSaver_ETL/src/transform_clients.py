import pandas as pd
import sqlite3
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
    

def transform_clients_bronze_to_silver(df_raw: pd.DataFrame) -> pd.DataFrame:
    """
    Transforma los datos de clientes de la capa Bronze a Silver aplicando
    limpieza de nulos, tipado de datos y validación de campos críticos.
    """
    try:
        if df_raw.empty:
            return pd.DataFrame()
        
        df = df_raw.copy()

        # 1. Definir columnas por tipo para procesamiento masivo
        numeric_cols = [
            'latitude', 'longitude', 'peak_power_kw', 'panel_area_m2', 
            'efficiency', 'loss_pct', 'angle', 'aspect', 
            'battery_capacity_kwh', 'soc_min_pct', 'installation_cost_eur'
        ]
        
        text_cols = [
            'client_id', 'name', 'panel_type', 'mounting', 'timezone', '_ingested_at'
        ]

        # 2. Forzar tipos de datos (Lo que no cuadre se convierte en NaN)
        for col in numeric_cols:
            df[col] = pd.to_numeric(df[col], errors='coerce')
            
        for col in text_cols:
            df[col] = df[col].astype(str).replace(['None', 'nan', 'NaN', 'null'], np.nan)
        
        # 3. Tratamiento específico para la fecha de ingesta (para poder comparar)
        df['_ingested_at'] = pd.to_datetime(df['_ingested_at'], errors='coerce')

        # 4. Borrar líneas si los campos CRÍTICOS son nulos
        # client_id, name, latitude, longitude, peak_power_kw
        critical_fields = ['client_id', 'name', 'latitude', 'longitude', 'peak_power_kw', '_ingested_at']
        df = df.dropna(subset=critical_fields)
        
        # ==========================================================
        # 5. ZONA DE LÓGICA DE NEGOCIO
        # ==========================================================
        
        # Redondear coordenadas a 6 decimales
        df['latitude'] = df['latitude'].round(6)
        df['longitude'] = df['longitude'].round(6)
        
        # Nombre en mayúsculas
        df['name'] = df['name'].str.upper().str.strip()

        # Validar coordenadas ( Lat -90 a 90, Lon -180 a 180)
        df = df[df['latitude'].between(-90, 90) & df['longitude'].between(-180, 180)]

        # Validar angle (0 a 90 grados) y aspect (0 a 360 grados)
        df.loc[~df['angle'].between(0, 90), 'angle'] = 30.0  # Valor por defecto
        df.loc[~df['aspect'].between(0, 360), 'aspect'] = 180.0 # Orientación Sur

        # Validar en porcentaje (0 a 100)
        df.loc[~df['loss_pct'].between(0, 90), 'loss_pct'] = 14.0  
        df.loc[~df['soc_min_pct'].between(0, 90), 'soc_min_pct'] = 20.0

        # Validar valores decimales (0 a 1)
        df.loc[~df['efficiency'].between(0, 1), 'efficiency'] = 0.15

        # Evitar valores negativos o absurdos
        df = df[df['peak_power_kw'] > 0] # Borra potencia negativa
        df.loc[df['panel_area_m2'] < 0, 'panel_area_m2'] = 0
        df.loc[df['battery_capacity_kwh'] < 0, 'battery_capacity_kwh'] = 0
        df.loc[df['installation_cost_eur'] < 0, 'installation_cost_eur'] = 0

        # ==========================================================

        # 6. Gestión de duplicados: nos quedamos con el más reciente
        # Ordenamos por fecha de ingesta (reciente primero) y quitamos duplicados por ID
        df = df.sort_values(by='_ingested_at', ascending=False)
        df = df.drop_duplicates(subset=['client_id'], keep='first')
        # Acortamos la fecha a formato legible (YYYY-MM-DD HH:MM:SS)
        df['_ingested_at'] = df['_ingested_at'].dt.strftime('%Y-%m-%d %H:%M:%S')

        # 7. Rellenar el resto de nulos con valores coherentes
        fill_values = {
            'panel_area_m2': 0.0,
            'efficiency': 0.15,       # Valor estándar de eficiencia (15%)
            'panel_type': 'unknown',
            'loss_pct': 14.0,         # Pérdida estándar habitual
            'angle': 30.0,            # Inclinación común
            'aspect': 180.0,          # Orientación Sur (habitual en instalaciones)
            'mounting': 'unknown',
            'battery_capacity_kwh': 0.0,
            'soc_min_pct': 20.0,      # Límite de descarga seguro común
            'installation_cost_eur': 0.0,
            'timezone': 'UTC'
        }
        
        df = df.fillna(value=fill_values)

        return df.reset_index(drop=True)
    
    except Exception as e:
        
        logger.error(f"❌ ERROR CRÍTICO en la transformación Silver: {e}")
       
        return pd.DataFrame()


    
def load_df_to_db(df: pd.DataFrame, table_name: str):
    """
    Inyecta un DataFrame en la base de datos SQLite definiendo client_id como PK.
    """
    db_path = db_manager.get_db_path()
    
    try:
        if df.empty:
            logger.warning(f"⚠️  El DataFrame para '{table_name}' está vacío. Cancelando inyección.")
            return False

        engine = create_engine(f"sqlite:///{db_path}")

        with engine.begin() as connection:
            # 1. Si queremos 'replace', eliminamos la tabla existente
            connection.execute(text(f"DROP TABLE IF EXISTS {table_name}"))

            # 2. Definimos el esquema manualmente para asegurar la Primary Key
            # Ajusta los tipos de datos según tus necesidades técnicas
            create_table_query = f"""
            CREATE TABLE IF NOT EXISTS {table_name} (
                    client_id               TEXT PRIMARY KEY,
                    name                    TEXT NOT NULL,
                    latitude                REAL NOT NULL,
                    longitude               REAL NOT NULL,
                    peak_power_kw           REAL NOT NULL,   
                    panel_area_m2           REAL NOT NULL,
                    efficiency              REAL NOT NULL,
                    panel_type              TEXT NOT NULL,
                    loss_pct                REAL NOT NULL,
                    angle                   REAL NOT NULL,
                    aspect                  REAL NOT NULL,
                    mounting                TEXT NOT NULL,
                    battery_capacity_kwh    REAL NOT NULL,
                    soc_min_pct             REAL NOT NULL,
                    installation_cost_eur   REAL NOT NULL,
                    timezone                TEXT NOT NULL,
                    _ingested_at            TEXT NOT NULL
                )
            """
            connection.execute(text(create_table_query))
            
            # 3. Inyectamos los datos. Usamos if_exists='append' porque la tabla ya existe
            df.to_sql(table_name, con=connection, if_exists='append', index=False)
        
        logger.info(f"✅ Ingesta exitosa: '{table_name}' (PK: client_id) con {len(df)} registros.")
        return True

    except Exception as e:
        logger.error(f"❌ Error al ingesta: {e}")
        return False


def transform_clients(raw_clients_table: str, clean_clients_table:str) -> bool:
    raw_clients=extract_from_db(raw_clients_table)
    clean_clients=transform_clients_bronze_to_silver(raw_clients)
    load_df_to_db(clean_clients, clean_clients_table)


if __name__ == "__main__":

    logger.info(f"Iniciando extraccion e ingesta de clientes de capa bronze a silver...")
    transform_clients('raw_clients', 'clean_clients')
    

    
        