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
                    _ingested_at_utc, 
                    raw_data
                FROM {table_name}
                ORDER BY _ingested_at_utc DESC
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
            ingested_at_utc = row['_ingested_at_utc']
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
                        'datetime_utc': v.get('datetime'),
                        'price_euro_mwh': float(v.get('value')),
                        'percentage': v.get('percentage'),
                        '_ingested_at_utc': ingested_at_utc
                    }
                    data_to_clean.append(entry)
        
        df = pd.DataFrame(data_to_clean)
        
        if not df.empty:
            # 1. Normalización de fechas
            df['datetime_utc'] = pd.to_datetime(df['datetime_utc'], errors='coerce', utc=True)
            
            # 2. Limpieza: Eliminar filas donde la fecha falló
            df = df.dropna(subset=['datetime_utc'])
            
            # 3. Manejo de Outliers (Límites lógicos para el mercado español)
            # El precio rara vez baja de -50 o sube de 1000 en condiciones normales
            lower_limit = -100
            upper_limit = 2000
            
            outliers = df[(df['price_euro_mwh'] < lower_limit) | (df['price_euro_mwh'] > upper_limit)]
            if not outliers.empty:
                logger.warning(f"🚨 Se detectaron {len(outliers)} valores fuera de rango. Filtrando...")
                df = df[(df['price_euro_mwh'] >= lower_limit) & (df['price_euro_mwh'] <= upper_limit)]

            # 4. Deduplicación
            # Mantenemos el registro más reciente según _ingested_at_utc
            df = df.sort_values('_ingested_at_utc', ascending=False)
            df = df.drop_duplicates(subset=['price_type', 'datetime_utc'], keep='first')
            
            # Ordenar para facilitar la lectura/carga
            df = df.sort_values(['price_type', 'datetime_utc']).reset_index(drop=True)

            # 5. Rellenamos los precios nulos con interpolación
            df['price_euro_mwh'] = df.groupby('price_type')['price_euro_mwh'].transform(lambda x: x.interpolate(method='linear').ffill().bfill())

            # 6. Creamos la columna unix_time
            df['unix_time'] = df['datetime_utc'].dt.tz_localize(None).astype('datetime64[s]').astype('int64')
            
            logger.info(f"✅ Transformación Silver completada: {len(df)} registros válidos.")
        
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
        df_sql['datetime_utc'] = pd.to_datetime(df_sql['datetime_utc'])
        df_sql['_ingested_at_utc'] = pd.to_datetime(df_sql['_ingested_at_utc'])

        # Ahora sí podemos usar .dt.strftime
        df_sql['datetime_utc'] = df_sql['datetime_utc'].dt.strftime('%Y-%m-%d %H:%M:%S')
        df_sql['_ingested_at_utc'] = df_sql['_ingested_at_utc'].dt.strftime('%Y-%m-%d %H:%M:%S')
        

        engine = create_engine(f"sqlite:///{db_path}")

        with engine.begin() as connection:
            # AJUSTE DE CLAVE PRIMARIA: 
            # Como tienes PVPC y SPOT, 'unix_time' por sí solo NO puede ser PK 
            # porque tendrías dos precios para el mismo segundo. Usamos clave compuesta.
            create_table_query = f"""
            CREATE TABLE IF NOT EXISTS {table_name} (
                unix_time           INTEGER NOT NULL,
                datetime_utc        TEXT NOT NULL,
                price_type          TEXT NOT NULL,
                price_euro_mwh      REAL,
                percentage          REAL,
                _ingested_at_utc    TEXT NOT NULL,
                PRIMARY KEY (datetime_utc, price_type)
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


def transform_energy_prices() -> bool:
    raw_prices = extract_raw_ree_from_db()
    if raw_prices.empty:
        return False          
    clean_prices = transform_prices_bronze_to_silver(raw_prices)
    if clean_prices.empty:
        return False         
    return load_ree_to_silver(clean_prices)


if __name__ == "__main__":
    transform_energy_prices()