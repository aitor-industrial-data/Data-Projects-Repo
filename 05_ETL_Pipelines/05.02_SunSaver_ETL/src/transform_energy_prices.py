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
        
        with sqlite3.connect(str(db_path)) as conn:
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
        return pd.DataFrame()



def transform_prices_bronze_to_silver(df_raw: pd.DataFrame) -> pd.DataFrame:
    """
    Transforma los datos de precios de REE de la capa Bronze a Silver.
    - PVPC: ya viene por hora de la API → se carga tal cual.
    - Spot: viene cada 15 min → se agrupa a la hora (media) para alinearse
      con el resto de capas (weather por hora, PVPC por hora).
    """
    try:
        if df_raw.empty:
            logger.warning("⚠️ DataFrame de entrada vacío.")
            return pd.DataFrame()
        
        data_to_clean = []
        
        for index, row in df_raw.iterrows():
            ingested_at_utc = row['_ingested_at_utc']
            raw_json = json.loads(row['raw_data'])
            series_list = raw_json.get('included', [])
            
            for series in series_list:
                price_type = series.get('type')
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
            df = df.dropna(subset=['datetime_utc'])
            
            # 2. Manejo de Outliers
            lower_limit = -100
            upper_limit = 2000
            outliers = df[(df['price_euro_mwh'] < lower_limit) | (df['price_euro_mwh'] > upper_limit)]
            if not outliers.empty:
                logger.warning(f"🚨 Se detectaron {len(outliers)} valores fuera de rango. Filtrando...")
                df = df[(df['price_euro_mwh'] >= lower_limit) & (df['price_euro_mwh'] <= upper_limit)]

            # 3. Separar PVPC y Spot para tratarlos de forma independiente
            df_pvpc = df[df['price_type'] != 'Precio mercado spot'].copy()
            df_spot_raw = df[df['price_type'] == 'Precio mercado spot'].copy()

            # --- PVPC: ya viene por hora, solo deduplicar ---
            df_pvpc = df_pvpc.sort_values('_ingested_at_utc', ascending=False)
            df_pvpc = df_pvpc.drop_duplicates(subset=['price_type', 'datetime_utc'], keep='first')

            # --- SPOT: agrupar a la hora (media de los 4 cuartos de hora) ---
            # Truncamos al inicio de la hora para hacer el groupby
            df_spot_raw['hour_utc'] = df_spot_raw['datetime_utc'].dt.floor('h')
            # Cogemos el _ingested_at_utc más reciente de cada grupo
            spot_ingested = (
                df_spot_raw.groupby('hour_utc')['_ingested_at_utc']
                .max()
                .reset_index()
            )
            spot_avg = (
                df_spot_raw.groupby('hour_utc')['price_euro_mwh']
                .mean()
                .round(4)
                .reset_index()
            )
            df_spot = spot_avg.merge(spot_ingested, on='hour_utc')
            df_spot.rename(columns={'hour_utc': 'datetime_utc'}, inplace=True)
            df_spot['price_type'] = 'Precio mercado spot'
            df_spot['percentage'] = None  # la media por hora pierde el % individual

            logger.info(
                f"📊 Spot agrupado a hora: {len(df_spot_raw)} registros de 15 min "
                f"→ {len(df_spot)} registros horarios"
            )

            # 4. Reunificar ambas series
            df = pd.concat([df_pvpc, df_spot], ignore_index=True)

            # 5. Rellenar nulos con interpolación por serie
            df = df.sort_values(['price_type', 'datetime_utc']).reset_index(drop=True)
            df['price_euro_mwh'] = df.groupby('price_type')['price_euro_mwh'].transform(
                lambda x: x.interpolate(method='linear').ffill().bfill().round(4)
            )

            # 6. Columna unix_time (inicio de hora, alineado con weather y fact)
            df['unix_time'] = (
                df['datetime_utc']
                .dt.tz_localize(None)
                .astype('datetime64[s]')
                .astype('int64')
            )
            
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
        
        df_sql['datetime_utc'] = pd.to_datetime(df_sql['datetime_utc'])
        df_sql['_ingested_at_utc'] = pd.to_datetime(df_sql['_ingested_at_utc'])
        df_sql['datetime_utc'] = df_sql['datetime_utc'].dt.strftime('%Y-%m-%d %H:%M:%S')
        df_sql['_ingested_at_utc'] = df_sql['_ingested_at_utc'].dt.strftime('%Y-%m-%d %H:%M:%S')

        engine = create_engine(f"sqlite:///{db_path}")

        with engine.begin() as connection:
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