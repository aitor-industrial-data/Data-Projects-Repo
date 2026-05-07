import pandas as pd
import os
import json
from datetime import datetime, timezone
from sqlalchemy import create_engine, text

import workspace_manager
from logger_config import setup_logging


logger = setup_logging()


def extract_raw_weather_from_json(file_path: str, client_id: str) -> pd.DataFrame:
    """
    Lee un archivo JSON físico y lo prepara como el DataFrame.
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            raw_data_dict = json.load(f)
            
        # Obtenemos la fecha de creación del archivo para auditoría
        ingested_at = datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S')
        
        df = pd.DataFrame([{
            'client_id': client_id,
            '_ingested_at_utc': ingested_at,
            '_source_file': os.path.basename(file_path),
            'raw_data': json.dumps(raw_data_dict)
             
        }])
        
        return df
    
    except Exception as e:
        logger.error(f"❌ Error leyendo JSON {file_path}: {e}")
        return pd.DataFrame()
    
    
    
def transform_weather_bronze_to_silver(df_raw: pd.DataFrame) -> pd.DataFrame:
    try:
        if df_raw.empty:
            return pd.DataFrame()
        
        all_clients_data = []
    
        for index, row in df_raw.iterrows():
            client_id = row['client_id']
            ingested_at_utc = row['_ingested_at_utc']
            source_file = row['_source_file']
            raw_json = json.loads(row['raw_data'])
            forecasts = raw_json.get('list', [])
            
            client_forecasts = []
            for f in forecasts:
                client_forecasts.append({
                    'forecast_time_utc': f.get('dt_txt'),
                    'temp_celsius': f.get('main', {}).get('temp'),
                    'humidity_pct': f.get('main', {}).get('humidity'),
                    'clouds_pct': f.get('clouds', {}).get('all'),
                    'rain_prob_norm': f.get('pop'),
                    'wind_speed_mps': f.get('wind', {}).get('speed'),
                    'weather_id': f.get('weather', [{}])[0].get('id'),
                    'weather_main': f.get('weather', [{}])[0].get('main'),
                    'weather_description': f.get('weather', [{}])[0].get('description'),
                    'pod': f.get('sys', {}).get('pod')
                })
            
            df_client = pd.DataFrame(client_forecasts)
            
            # --- 1. TIPADO (Dentro del bucle para poder operar) ---
            df_client['forecast_time_utc'] = pd.to_datetime(df_client['forecast_time_utc'])
            
            # --- 3. DEDUPLICACIÓN (Si la API enviara duplicados en el mismo JSON) ---
            df_client = df_client.drop_duplicates(subset=['forecast_time_utc'], keep='last')
            
            # --- INTERPOLACIÓN ---
            df_client.set_index('forecast_time_utc', inplace=True)
            df_resampled = df_client.resample('1h').asfreq()
            
            
            num_cols = ['temp_celsius', 'humidity_pct', 'clouds_pct', 'rain_prob_norm', 'wind_speed_mps']
            df_resampled[num_cols] = df_resampled[num_cols].interpolate(method='linear')
            df_resampled[num_cols] = df_resampled[num_cols].round(3) # redondeo
            
            cat_cols = ['weather_id', 'weather_main', 'weather_description', 'pod']
            df_resampled[cat_cols] = df_resampled[cat_cols].ffill()
            
            # --- RECONSTRUCCIÓN ---
            df_resampled = df_resampled.reset_index()
            df_resampled['client_id'] = client_id
            df_resampled['_ingested_at_utc'] = ingested_at_utc
            df_resampled['_source_file'] = source_file
            df_resampled['unix_time'] = (df_resampled['forecast_time_utc'] - pd.Timestamp("1970-01-01")) // pd.Timedelta("1s")
            df_resampled['is_daylight'] = df_resampled['pod'].apply(lambda x: 1 if x == 'd' else 0)

            
            
            all_clients_data.append(df_resampled)
                
        # Unificamos todos los clientes
        df_final = pd.concat(all_clients_data, ignore_index=True)

        # --- 2. NULOS Y LIMPIEZA FINAL (Fuera del bucle) ---
        df_final['rain_prob_norm'] = df_final['rain_prob_norm'].fillna(0)
        df_final['_ingested_at_utc'] = pd.to_datetime(df_final['_ingested_at_utc'], errors='coerce')
        
        # Eliminar si faltan campos críticos tras la interpolación
        df_final = df_final.dropna(subset=['client_id', 'forecast_time_utc'])
        
        # ELIMINAR COLUMNAS TEMPORALES
        if 'pod' in df_final.columns:
            df_final = df_final.drop(columns=['pod'])

    
        logger.info(f"✅ Limpieza Silver completada: {len(df_final)} registros listos.")
        return df_final
        
    except Exception as e:
        logger.error(f"❌ Error en transformación: {e}")
        return pd.DataFrame()
    

def load_weather_to_silver(df: pd.DataFrame, table_name: str = "clean_weather") -> bool:
    """
    Capa Silver: Almacena el histórico de predicciones/clima procesado.
    Usa una clave primaria compuesta para evitar duplicados exactos.
    """
    db_path = workspace_manager.get_db_path()
    
    try:
        if df.empty:
            logger.warning(f"⚠️ DataFrame para '{table_name}' vacío.")
            return False


        # Creamos una copia para no alterar el DataFrame original que viaja por el script
        df_sql = df.copy()
        
        # Convertimos los objetos Timestamp de Pandas a String (formato ISO)
        # Esto soluciona el error: "type 'Timestamp' is not supported"
        df_sql['forecast_time_utc'] = df_sql['forecast_time_utc'].dt.strftime('%Y-%m-%d %H:%M:%S')
        df_sql['_ingested_at_utc'] = df_sql['_ingested_at_utc'].dt.strftime('%Y-%m-%d %H:%M:%S')

        engine = create_engine(f"sqlite:///{db_path}")

        with engine.begin() as connection:
            # 1. Creamos la tabla si no existe (con clave compuesta)
            # Combinamos client_id y forecast_time para que no haya dos registros
            # del mismo cliente para la misma hora.
            create_table_query = f"""
            CREATE TABLE IF NOT EXISTS {table_name} (
                client_id               TEXT NOT NULL,
                unix_time               INTEGER NOT NULL,
                forecast_time_utc       TEXT NOT NULL,
                temp_celsius            REAL,
                humidity_pct            REAL,
                clouds_pct              REAL,
                rain_prob_norm          REAL,
                wind_speed_mps          REAL,
                weather_id              INTEGER,
                weather_main            TEXT,
                weather_description     TEXT,
                is_daylight             INTEGER,
                _source_file             TEXT,
                _ingested_at_utc        TEXT NOT NULL,
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
    """
    Capa Silver: Lee las tareas 'pending' Y 'error' del manifiesto, las transforma
    y actualiza su estado a 'success' o 'error' tras la carga en la DB.
    Las tareas con 'error' se reintentan automáticamente en cada ejecución.
    """
    bronze_dir = workspace_manager.get_bronze_path()
    manifest_path = os.path.join(bronze_dir, "_process_manifest_openweather.json")
    
    try:
        # 1. Verificar si existe el manifiesto
        if not os.path.exists(manifest_path):
            logger.info("☕ No existe el manifiesto de control. Nada que procesar.")
            return True
 
        # 2. Leer todas las tareas
        with open(manifest_path, 'r', encoding='utf-8') as f:
            all_tasks = json.load(f)
 
        # 3. Filtrar pendientes Y errores anteriores (reintento automático)
        actionable_tasks = [t for t in all_tasks if t['status'] in ('pending', 'error')]
 
        if not actionable_tasks:
            logger.info("✅ No hay tareas pendientes en el manifiesto.")
            return True
 
        pending_count = sum(1 for t in actionable_tasks if t['status'] == 'pending')
        retry_count   = sum(1 for t in actionable_tasks if t['status'] == 'error')
        logger.info(f"🚀 {pending_count} tareas nuevas + {retry_count} reintentos. Iniciando transformación...")
 
        # Contadores de la sesión actual (no históricos)
        session_ok    = 0
        session_error = 0
 
        # 4. Procesar cada tarea
        for task in actionable_tasks:
            client_id = task['client_id']
            path_file = task['path']
            
            try:
                logger.info(f"⚙️ Procesando: {client_id} (Archivo: {os.path.basename(path_file)})")
 
                # A. Leer el JSON físico
                df_raw = extract_raw_weather_from_json(path_file, client_id)
                
                if df_raw.empty:
                    logger.warning(f"⚠️ El archivo para {client_id} está vacío o corrupto.")
                    task['status'] = 'error'
                    task['error'] = 'Archivo vacío o corrupto'
                    task['updated_at'] = datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S')
                    session_error += 1
                    continue
 
                # B. Transformación (Limpieza, interpolación e ingeniería de variables)
                df_silver = transform_weather_bronze_to_silver(df_raw)
                
                # C. Carga a DB y actualización de estado
                if not df_silver.empty:
                    load_success = load_weather_to_silver(df_silver)
                    
                    if load_success:
                        task['status'] = 'success'
                        task.pop('error', None)  # Limpiar error previo si el reintento tuvo éxito
                        task['updated_at'] = datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S')
                        logger.info(f"✅ {client_id} cargado en Silver correctamente.")
                        session_ok += 1
                    else:
                        task['status'] = 'error'
                        task['error'] = 'Falló la carga en DB'
                        task['updated_at'] = datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S')
                        logger.error(f"❌ Falló la carga en DB para {client_id}.")
                        session_error += 1
                else:
                    task['status'] = 'error'
                    task['error'] = 'DataFrame vacío tras transformación Silver'
                    task['updated_at'] = datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S')
                    logger.error(f"❌ Transformación devolvió DataFrame vacío para {client_id}.")
                    session_error += 1
 
            except Exception as e:
                logger.error(f"❌ Error procesando tarea de {client_id}: {e}")
                task['status'] = 'error'
                task['error'] = str(e)
                task['updated_at'] = datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S')
                session_error += 1
                continue
 
        # 5. Persistir los cambios de estado en el archivo JSON
        with open(manifest_path, 'w', encoding='utf-8') as f:
            json.dump(all_tasks, f, indent=4, ensure_ascii=False)
 
        # Resumen de sesión actual + estado global del manifiesto
        total_ok      = sum(1 for t in all_tasks if t['status'] == 'success')
        total_error   = sum(1 for t in all_tasks if t['status'] == 'error')
        total_pending = sum(1 for t in all_tasks if t['status'] == 'pending')
        logger.info(
            f"💾 Sesión: ✅ {session_ok} ok | ❌ {session_error} errores  —  "
            f"Manifiesto total: ✅ {total_ok} | ❌ {total_error} | ⏳ {total_pending}"
        )
 
        return session_error == 0
 
    except Exception as e:
        logger.error(f"❌ Error crítico en el pipeline de transformación: {e}")
        return False

    
if __name__ == "__main__":
    logger.info(f"Iniciando extraccion e ingesta de weather de capa bronze a silver...")
    transform_openweather()

    
    
   
