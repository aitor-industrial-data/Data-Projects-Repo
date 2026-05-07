import os
import json
import stat
import sqlite3
import requests
import pandas as pd
from dotenv import load_dotenv
from datetime import datetime, timezone
from typing import Dict, Any, Optional

import workspace_manager
from logger_config import setup_logging


logger = setup_logging()

load_dotenv()

def extract_weather(lat: float, lon: float) -> Dict[str, Any]:
    url = "https://api.openweathermap.org/data/2.5/forecast"
    API_KEY = os.getenv("WEATHER_API_KEY")
    
    if not API_KEY:
        logger.error("Falta WEATHER_API_KEY en el .env")
        return {}

    headers = {
        'lat': lat,
        'lon': lon,
        'appid': API_KEY,
        'units': 'metric',
        'lang': 'en' 
    }

    try:
        response = requests.get(url, params=headers, timeout=15)
        response.raise_for_status()
        all_data = response.json()

        if not all_data:
            raise ValueError("OpenWeather devolvió datos vacíos")

        return all_data
    except Exception as e:
        logger.error(f"❌ Error en extracción de openweather: {e}")
        raise


def ingest_openweather_to_bronze(api_response: dict, client_id: str) -> Optional[str]:
    """
    Capa Bronze: Guarda el JSON en un archivo físico, aplica chmod 444
    y devuelve la ruta del archivo para el rastro de auditoría (Lineage).
    """
    try:
        # 1. Definir rutas (Siguiendo tu estructura de carpetas)
        # Ajustado a tu ruta: ~/Documents/Data-Projects-Repo/
        bronze_dir=workspace_manager.get_bronze_path()
        os.makedirs(bronze_dir, exist_ok=True)

        timestamp = datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')
        filename = f"weather_{client_id}_{timestamp}.json"
        full_path = os.path.join(bronze_dir, filename)

        # 2. Guardar el archivo JSON
        with open(full_path, 'w', encoding='utf-8') as f:
            json.dump(api_response, f, ensure_ascii=False, indent=4)

        # 3. BLINDAJE: Aplicar chmod 444 (Solo lectura)
        # Esto evita que nadie (ni el ratón en DBBrowser) lo modifique
        permisos_lectura = stat.S_IRUSR | stat.S_IRGRP | stat.S_IROTH
        os.chmod(full_path, permisos_lectura)

        logger.info(f"🔒 Capa Bronze protegida: {filename}")
        
        # Devolvemos la ruta para que el siguiente script sepa qué leer
        return full_path

    except Exception as e:
        logger.error(f"❌ Error guardando Bronze en archivo: {e}")
        return None


def extract_openweather(client_table: str = 'clean_clients') -> bool:
    """
    Obtiene el clima, genera archivos Bronze y actualiza el manifiesto de control.
    Devuelve True si se generaron nuevas tareas, False en caso contrario.
    """
    try:
        db_path = workspace_manager.get_db_path()
            
        # 1. LEER CLIENTES
        with sqlite3.connect(str(db_path)) as conn:
            query = f"SELECT client_id, latitude, longitude FROM {client_table}"
            df_clients = pd.read_sql(query, conn)

        new_extractions = []
        manifest_path = os.path.join("data", "bronze", "_process_manifest_openweather.json")

        # 2. BUCLE DE EXTRACCIÓN
        for _, row in df_clients.iterrows():
            client_id = row['client_id']
            lat = row['latitude']
            lon = row['longitude']

            try:
                raw_weather = extract_weather(lat, lon)

                if raw_weather:
                    path_file = ingest_openweather_to_bronze(raw_weather, client_id)
                    
                    new_extractions.append({
                        'source': 'openweather',
                        'client_id': client_id,
                        'path': path_file,
                        'status': 'pending',
                        'created_at': datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S'),
                        'updated_at': datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S')
                    })
                else:
                    logger.warning(f"⚠️ Sin datos para el cliente {client_id}")

            except Exception as e:
                logger.error(f"❌ Error procesando cliente {client_id}: {e}")
                continue
            
        # 3. PERSISTENCIA EN EL MANIFIESTO
        if new_extractions:
            all_tasks = []
            
            if os.path.exists(manifest_path):
                try:
                    with open(manifest_path, 'r', encoding='utf-8') as f:
                        all_tasks = json.load(f)
                except Exception:
                    all_tasks = []

            # Unimos las tareas nuevas a las existentes
            all_tasks.extend(new_extractions)

            pending_count = len([t for t in all_tasks if t['status'] == 'pending'])

            with open(manifest_path, 'w', encoding='utf-8') as f:
                json.dump(all_tasks, f, indent=4, ensure_ascii=False)
            
            logger.info(f"📄 Manifiesto openweather actualizado: {len(new_extractions)} nuevas tareas introducidas.")

            return True # Indicamos que hay trabajo nuevo para el Transform
            
        return False # No hubo extracciones nuevas
    
    except Exception as e:
        logger.critical(f"❌ Error crítico en extract_openweather: {e}")
        return False


if __name__ == "__main__":
    
    extract_openweather()
   
   
    