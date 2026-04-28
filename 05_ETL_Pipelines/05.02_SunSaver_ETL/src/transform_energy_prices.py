import pandas as pd
import sqlite3
import json
import logging
from sqlalchemy import create_engine, text

import db_manager

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)

logger = logging.getLogger(__name__)

def extract_raw_ree_from_db(table_name: str = 'raw_prices') -> pd.DataFrame:
    """
    Extrae solo la ultima lectura y la devuelve como DataFrame.
    """
    try:
        db_path = db_manager.get_db_path()
        
        # 1. Conexión a la DB (usando str por seguridad de tipos)
        with sqlite3.connect(str(db_path)) as conn:
            # 2. Leemos la tabla entera directamente a un DataFrame
            query = f"""
                SELECT  
                    _ingested_at, 
                    raw_data
                FROM {table_name}
                ORDER BY _ingested_at DESC
                LIMIT 1
                """
            df = pd.read_sql_query(query, conn)
            
        logger.info(f"✅ Extracción exitosa: {len(df)} registros extraidos de DB")
        return df

    except Exception as e:
        logger.error(f"❌ Error extrayendo de DB: {e}")
        return pd.DataFrame() # Devolvemos un DF vacío si falla



def transform_prices_bronze_to_silver(df_raw: pd.DataFrame) -> pd.DataFrame:
    """
    Transforma los datos de precios de REE de la capa Bronze a Silver.
    Extrae las series PVPC y Spot del JSON crudo.
    """
    try:
        if df_raw.empty:
            logger.warning("⚠️ DataFrame de entrada vacío.")
            return pd.DataFrame()
        
        data_to_clean = []
        
        for index, row in df_raw.iterrows():
            ingested_at = row['_ingested_at']
            # Cargamos el JSON de la columna raw_data
            raw_json = json.loads(row['raw_data'])
            
            # La API de REE devuelve los datos en la lista 'included'
            series_list = raw_json.get('included', [])
            
            for series in series_list:
                price_type = series.get('type')  # 'PVPC' o 'Precio mercado spot'
                values = series.get('attributes', {}).get('values', [])
                
                for v in values:
                    entry = {
                        'price_type': price_type,
                        'datetime': v.get('datetime'),
                        'price_euro_mwh': float(v.get('value')),
                        'percentage': v.get('percentage'),
                        '_ingested_at': ingested_at
                    }
                    data_to_clean.append(entry)
        
        df = pd.DataFrame(data_to_clean)
        
        if not df.empty:
            # Convertimos la columna datetime a formato fecha/hora real de Pandas
            df['datetime'] = pd.to_datetime(df['datetime'], errors='coerce')
            # Limpieza básica: eliminamos duplicados si los hubiera
            df = df.drop_duplicates(subset=['price_type', 'datetime'])
            
            logger.info(f"✅ Transformación Silver completada: {len(df)} registros.")
        
        return df

    except Exception as e:
        logger.error(f"❌ Error en la transformación Silver de precios: {e}")
        return pd.DataFrame()
    

def load_ree_to_silver(df: pd.DataFrame, table_name: str = "clean_prices") -> bool:
    db_path = db_manager.get_db_path()
    
    try:
        if df.empty:
            logger.warning(f"⚠️ DataFrame para '{table_name}' vacío.")
            return False

        df_sql = df.copy()
        
        # ASEGURAMOS CONVERSIÓN A DATETIME antes de usar .dt
        # Esto soluciona el error que comentas
        df_sql['datetime'] = pd.to_datetime(df_sql['datetime'])
        df_sql['_ingested_at'] = pd.to_datetime(df_sql['_ingested_at'])

        # Ahora sí podemos usar .dt.strftime
        df_sql['datetime'] = df_sql['datetime'].dt.strftime('%Y-%m-%d %H:%M:%S')
        df_sql['_ingested_at'] = df_sql['_ingested_at'].dt.strftime('%Y-%m-%d %H:%M:%S')

        engine = create_engine(f"sqlite:///{db_path}")

        with engine.begin() as connection:
            # AJUSTE DE CLAVE PRIMARIA: 
            # Como tienes PVPC y SPOT, 'unix_time' por sí solo NO puede ser PK 
            # porque tendrías dos precios para el mismo segundo. Usamos clave compuesta.
            create_table_query = f"""
            CREATE TABLE IF NOT EXISTS {table_name} (
                datetime            TEXT NOT NULL,
                price_type          TEXT NOT NULL,
                price_euro_mwh      REAL,
                percentage          REAL,
                _ingested_at        TEXT NOT NULL,
                PRIMARY KEY (datetime, price_type)
            )
            """
            connection.execute(text(create_table_query))
            
            # 2. UPSERT (INSERT OR REPLACE)
            data = df_sql.to_dict(orient='records')
            
            columns = df_sql.columns.tolist()
            placeholders = ", ".join([f":{col}" for col in columns])
            col_names = ", ".join(columns)

            upsert_query = text(f"""
                INSERT OR REPLACE INTO {table_name} ({col_names}) 
                VALUES ({placeholders})
            """)
            
            connection.execute(upsert_query, data)
        
        logger.info(f"✅ Capa Silver actualizada: {len(df)} registros.")
        return True

    except Exception as e:
        logger.error(f"❌ Error en carga Silver REE: {e}")
        return False



if __name__ == "__main__":
    raw_prices=extract_raw_ree_from_db()
    clean_prices=transform_prices_bronze_to_silver(raw_prices)
    load_ree_to_silver(clean_prices)