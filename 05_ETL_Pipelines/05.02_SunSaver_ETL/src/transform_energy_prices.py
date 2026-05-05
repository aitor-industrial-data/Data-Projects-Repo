import pandas as pd
import os
from datetime import datetime, timezone
import sqlite3
import json
import logging
from sqlalchemy import create_engine, text

import workspace_manager

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)

logger = logging.getLogger(__name__)


def extract_raw_ree_from_json(file_path: str) -> pd.DataFrame:
    """
    Lee un archivo JSON físico y lo prepara como el DataFrame.
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            raw_data_dict = json.load(f)
            
        ingested_at = datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S')
        
        df = pd.DataFrame([{
            '_ingested_at_utc': ingested_at,
            '_source_file': os.path.basename(file_path),
            'raw_data': json.dumps(raw_data_dict)
        }])
        
        return df
    
    except Exception as e:
        logger.error(f"❌ Error leyendo JSON {file_path}: {e}")
        return pd.DataFrame()


def transform_prices_bronze_to_silver(df_raw: pd.DataFrame) -> pd.DataFrame:
    """
    Transforma los datos de precios PVPC de REE de la capa Bronze a Silver.
    El PVPC ya viene por hora de la API, se limpia y carga directamente.
    """
    try:
        if df_raw.empty:
            logger.warning("⚠️ DataFrame de entrada vacío.")
            return pd.DataFrame()
        
        data_to_clean = []
        
        for index, row in df_raw.iterrows():
            source_file = row['_source_file']
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
                        '_source_file': source_file,
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

            # 3. PVPC: ya viene por hora, solo deduplicar
            df = df.sort_values('_ingested_at_utc', ascending=False)
            df = df.drop_duplicates(subset=['price_type', 'datetime_utc'], keep='first')

            # 4. Rellenar nulos con interpolación
            df = df.sort_values(['price_type', 'datetime_utc']).reset_index(drop=True)
            df['price_euro_mwh'] = df.groupby('price_type')['price_euro_mwh'].transform(
                lambda x: x.interpolate(method='linear').ffill().bfill().round(4)
            )

            # 5. Columna unix_time (inicio de hora, alineado con weather y fact)
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
    db_path = workspace_manager.get_db_path()
    
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
                _source_file        TEXT,
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
    """
    Capa Silver: Lee las tareas 'pending' Y 'error' del manifiesto de REE,
    las transforma y actualiza su estado a 'success' o 'error'.
    Las tareas con 'error' se reintentan automáticamente en cada ejecución.
    """
    bronze_dir = workspace_manager.get_bronze_path()
    manifest_path = os.path.join(bronze_dir, "_process_manifest_ree.json")
 
    try:
        # 1. Verificar si existe el manifiesto
        if not os.path.exists(manifest_path):
            logger.info("☕ No existe el manifiesto de REE. Nada que procesar.")
            return True
 
        # 2. Leer todas las tareas
        with open(manifest_path, 'r', encoding='utf-8') as f:
            all_tasks = json.load(f)
 
        # 3. Filtrar pendientes Y errores anteriores (reintento automático)
        actionable_tasks = [t for t in all_tasks if t['status'] in ('pending', 'error')]
 
        if not actionable_tasks:
            logger.info("✅ No hay precios de REE pendientes en el manifiesto.")
            return True
 
        pending_count = sum(1 for t in actionable_tasks if t['status'] == 'pending')
        retry_count   = sum(1 for t in actionable_tasks if t['status'] == 'error')
        logger.info(f"🚀 {pending_count} tareas nuevas + {retry_count} reintentos REE. Iniciando transformación...")
 
        session_ok    = 0
        session_error = 0
 
        # 4. Procesar cada tarea (archivo JSON)
        for task in actionable_tasks:
            path_file = task['path']
 
            try:
                logger.info(f"⚙️ Procesando archivo: {os.path.basename(path_file)}")
 
                df_raw = extract_raw_ree_from_json(path_file)
 
                if df_raw.empty:
                    logger.warning(f"⚠️ El archivo {os.path.basename(path_file)} está vacío o corrupto.")
                    task['status'] = 'error'
                    task['error'] = 'Archivo vacío o corrupto'
                    task['updated_at'] = datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S')
                    session_error += 1
                    continue
 
                df_silver = transform_prices_bronze_to_silver(df_raw)
 
                if not df_silver.empty:
                    load_success = load_ree_to_silver(df_silver)
 
                    if load_success:
                        task['status'] = 'success'
                        task.pop('error', None)
                        task['updated_at'] = datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S')
                        logger.info(f"✅ Archivo {os.path.basename(path_file)} cargado en Silver correctamente.")
                        session_ok += 1
                    else:
                        task['status'] = 'error'
                        task['error'] = 'Falló la carga en DB'
                        task['updated_at'] = datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S')
                        logger.error(f"❌ Falló la carga en DB para el archivo {os.path.basename(path_file)}.")
                        session_error += 1
                else:
                    task['status'] = 'error'
                    task['error'] = 'DataFrame vacío tras transformación Silver'
                    task['updated_at'] = datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S')
                    logger.error(f"❌ Transformación devolvió DataFrame vacío para {os.path.basename(path_file)}.")
                    session_error += 1
 
            except Exception as e:
                logger.error(f"❌ Error procesando tarea de precios: {e}")
                task['status'] = 'error'
                task['error'] = str(e)
                task['updated_at'] = datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S')
                session_error += 1
                continue
 
        # 5. Persistir los cambios de estado en el archivo JSON
        with open(manifest_path, 'w', encoding='utf-8') as f:
            json.dump(all_tasks, f, indent=4, ensure_ascii=False)
 
        total_ok      = sum(1 for t in all_tasks if t['status'] == 'success')
        total_error   = sum(1 for t in all_tasks if t['status'] == 'error')
        total_pending = sum(1 for t in all_tasks if t['status'] == 'pending')
        logger.info(
            f"💾 Sesión: ✅ {session_ok} ok | ❌ {session_error} errores  —  "
            f"Manifiesto total: ✅ {total_ok} | ❌ {total_error} | ⏳ {total_pending}"
        )
 
        return session_error == 0
 
    except Exception as e:
        logger.error(f"❌ Error crítico en el pipeline de transformación de REE: {e}")
        return False


if __name__ == "__main__":
    transform_energy_prices()