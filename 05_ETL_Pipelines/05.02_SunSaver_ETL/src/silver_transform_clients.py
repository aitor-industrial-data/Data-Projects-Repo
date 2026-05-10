import pandas as pd
import os
import json
from sqlalchemy import create_engine, text
import numpy as np
from datetime import datetime, timezone

import config_paths
from logger_config import setup_logging


logger = setup_logging()
    

def extract_clients_from_json(file_path: str) -> pd.DataFrame:
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            raw_data_list = json.load(f) 
            
        ingested_at = datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S')
        
        df = pd.DataFrame(raw_data_list)
        
        df['_ingested_at_utc'] = ingested_at
        df['_source_file'] = os.path.basename(file_path)
        
        return df
    except Exception as e:
        logger.error(f"❌ Error leyendo JSON {file_path}: {e}")
        return pd.DataFrame()
    

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
            'latitude', 'longitude', 'nominal_load_kw', 'pv_peak_power_kw', 'panel_area_m2', 
            'efficiency', 'loss_pct', 'angle', 'aspect', 
            'battery_capacity_kwh', 'soc_min_pct', 'installation_cost_eur'
        ]
        
        text_cols = [
            'client_id', 'name', 'description', 'panel_type', 'mounting', 'timezone', '_ingested_at_utc'
        ]

        # 2. Forzar tipos de datos (Lo que no cuadre se convierte en NaN)
        for col in numeric_cols:
            df[col] = pd.to_numeric(df[col], errors='coerce')
            
        for col in text_cols:
            df[col] = df[col].astype(str).replace(['None', 'nan', 'NaN', 'null'], np.nan)
        
        # 3. Tratamiento específico para la fecha de ingesta (para poder comparar)
        df['_ingested_at_utc'] = pd.to_datetime(df['_ingested_at_utc'], errors='coerce')

        # 4. Borrar líneas si los campos CRÍTICOS son nulos
        critical_fields = ['client_id', 'name', 'latitude', 'longitude', 'pv_peak_power_kw', '_ingested_at_utc']
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

        # Validar angle (0 a 90 grados) y aspect (1 a 360 grados)
        # FIX BUG 3: aspect=0 es Norte (inusual) → se excluye el 0 usando between(1, 360)
        df.loc[~df['angle'].between(0, 90), 'angle'] = 30.0       # Valor por defecto
        df.loc[~df['aspect'].between(1, 360), 'aspect'] = 180.0   # Orientación Sur (era between(0,360) → 0 pasaba)

        # Validar en porcentaje (0 a 100)
        df.loc[~df['loss_pct'].between(0, 90), 'loss_pct'] = 14.0  
        df.loc[~df['soc_min_pct'].between(0, 90), 'soc_min_pct'] = 20.0

        # FIX BUG 1: Validar efficiency (0 a 1) — valores como 2, 21 se corrigen a 0.15
        # El .loc reemplaza inválidos por el default ANTES del fillna, así que NaN queda para fillna
        df.loc[df['efficiency'].notna() & ~df['efficiency'].between(0, 1), 'efficiency'] = 0.15

        # Evitar valores negativos o absurdos
        df = df[df['pv_peak_power_kw'] > 0]
        df.loc[df['panel_area_m2'] < 0, 'panel_area_m2'] = 0
        df.loc[df['battery_capacity_kwh'] < 0, 'battery_capacity_kwh'] = 0
        df.loc[df['installation_cost_eur'] < 0, 'installation_cost_eur'] = 0

        # ==========================================================

        # 6. Gestión de duplicados: nos quedamos con el más reciente
        df = df.sort_values(by='_ingested_at_utc', ascending=False)
        df = df.drop_duplicates(subset=['client_id'], keep='first')
        df['_ingested_at_utc'] = df['_ingested_at_utc'].dt.strftime('%Y-%m-%d %H:%M:%S')

        # 7. Rellenar el resto de nulos con valores coherentes
        fill_values = {
            'description': 'unknown',
            'nominal_load_kw': df['pv_peak_power_kw'] * 1.3,
            'panel_area_m2': 0.0,
            'efficiency': 0.15,
            'panel_type': 'unknown',
            'loss_pct': 14.0,
            'angle': 30.0,
            'aspect': 180.0,
            'mounting': 'unknown',
            'battery_capacity_kwh': 0.0,
            'soc_min_pct': 20.0,
            'installation_cost_eur': 0.0,
            'timezone': 'UTC'
        }
        
        df = df.fillna(value=fill_values)

        return df.reset_index(drop=True)
    
    except Exception as e:  
        logger.error(f"❌ ERROR CRÍTICO en la transformación Silver: {e}")
        return pd.DataFrame()


    
def load_clients_to_silver(df: pd.DataFrame, table_name: str = "clean_clients") -> bool:
    """
    Inyecta un DataFrame en la base de datos SQLite definiendo client_id como PK.
    """
    db_path = config_paths.get_db_path()
    
    try:
        if df.empty:
            logger.warning(f"⚠️  El DataFrame para '{table_name}' está vacío. Cancelando inyección.")
            return False

        engine = create_engine(f"sqlite:///{db_path}")

        with engine.begin() as connection:
            connection.execute(text(f"DROP TABLE IF EXISTS {table_name}"))

            create_table_query = f"""
            CREATE TABLE IF NOT EXISTS {table_name} (
                    client_id               TEXT NOT NULL PRIMARY KEY,
                    name                    TEXT NOT NULL,
                    description             TEXT NOT NULL,
                    latitude                REAL NOT NULL,
                    longitude               REAL NOT NULL,
                    nominal_load_kw         REAL NOT NULL,
                    pv_peak_power_kw        REAL NOT NULL,
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
                    _source_file            TEXT NOT NULL,
                    _ingested_at_utc        TEXT NOT NULL
                )
            """
            connection.execute(text(create_table_query))
            
            df.to_sql(table_name, con=connection, if_exists='append', index=False)
        
        logger.info(f"✅ Ingesta exitosa: '{table_name}' (PK: client_id) con {len(df)} registros.")
        return True

    except Exception as e:
        logger.error(f"❌ Error al ingesta: {e}")
        return False


def transform_clients() -> int:
    """
    Capa Silver: Lee las tareas 'pending' Y 'error' del manifiesto, las transforma
    y actualiza su estado. Devuelve el TOTAL de filas insertadas en la sesión.
    """
    bronze_dir = config_paths.get_bronze_path()
    manifest_path = os.path.join(bronze_dir, "_process_manifest_clients.json")
    
    # Acumulador para el rows_affected total de la sesión
    session_rows = 0 
    
    try:
        if not os.path.exists(manifest_path):
            logger.info("No existe el manifiesto de control. Nada que procesar.")
            return 0

        with open(manifest_path, 'r', encoding='utf-8') as f:
            all_tasks = json.load(f)

        
        actionable_tasks = [t for t in all_tasks if t['status'] in ('pending', 'error')]

        if not actionable_tasks:
            logger.info("✅ No hay tareas pendientes en el manifiesto.")
            return 0

        pending_count = sum(1 for t in actionable_tasks if t['status'] == 'pending')
        retry_count   = sum(1 for t in actionable_tasks if t['status'] == 'error')
        logger.info(f"🚀 {pending_count} tareas nuevas + {retry_count} reintentos. Iniciando transformación...")

        session_ok    = 0
        session_error = 0

        for task in actionable_tasks:
            path_file = task['path']
            
            try:
                logger.info(f"Procesando archivo: {os.path.basename(path_file)}")
                df_raw = extract_clients_from_json(path_file)
                
                if df_raw.empty:
                    logger.warning(f"⚠️ El archivo {os.path.basename(path_file)} está vacío o corrupto.")
                    task['status'] = 'error'
                    task['error'] = 'Archivo vacío o corrupto'
                    task['updated_at'] = datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S')
                    session_error += 1
                    continue

                # Transformación (donde aplicas tus filtros de latitud, eficiencia, etc.)
                df_silver = transform_clients_bronze_to_silver(df_raw)
                
                if not df_silver.empty:
                    # Capturamos cuántas filas han sobrevivido a la limpieza
                    current_file_rows = len(df_silver)
                    
                    load_success = load_clients_to_silver(df_silver)
                    
                    if load_success:
                        task['status'] = 'success'
                        task.pop('error', None) 
                        task['updated_at'] = datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S')
                        
                        # Sumamos al contador de la sesión
                        session_rows += current_file_rows
                        session_ok += 1
                        logger.info(f"✅ {os.path.basename(path_file)} cargado: {current_file_rows} filas.")
                    else:
                        task['status'] = 'error'
                        task['error'] = 'Fallo la carga en DB'
                        task['updated_at'] = datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S')
                        session_error += 1
                else:
                    task['status'] = 'error'
                    task['error'] = 'DataFrame vacío tras transformación'
                    task['updated_at'] = datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S')
                    session_error += 1

            except Exception as e:
                logger.error(f"❌ Error procesando tarea {os.path.basename(path_file)}: {e}")
                task['status'] = 'error'
                task['error'] = str(e)
                task['updated_at'] = datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S')
                session_error += 1
                continue 

        # Guardar el manifiesto con los estados actualizados
        with open(manifest_path, 'w', encoding='utf-8') as f:
            json.dump(all_tasks, f, indent=4, ensure_ascii=False)

        # Resumen final en logs
        total_ok = sum(1 for t in all_tasks if t['status'] == 'success')
        logger.info(
            f"💾 Sesión: ✅ {session_ok} ok | ❌ {session_error} errores. "
            f"Total filas afectadas: {session_rows}"
        )

        logger.info(f"Datos totales procesados: {session_rows}")
        return session_rows

    except Exception as e:
        logger.error(f"❌ Error crítico en transform_clients: {e}")
        return 0



if __name__ == "__main__":
    logger.info("Iniciando extraccion e ingesta de clientes de capa bronze a silver...")
    transform_clients()