import os
import json
import stat
import logging
import requests
from dotenv import load_dotenv
from datetime import datetime, timezone
from typing import Dict, Any, Optional

# Supongamos que tienes estas utilidades importadas
# import db_manager 

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)

logger = logging.getLogger(__name__)

load_dotenv()

def extract_weather(lat: float, lon: float) -> Dict[str, Any]:
    url = "https://api.openweathermap.org/data/2.5/forecast"
    API_KEY = os.getenv("WEATHER_API_KEY")
    
    if not API_KEY:
        logger.error("Falta WEATHER_API_KEY en el .env")
        return {}

    params = {
        'lat': lat,
        'lon': lon,
        'appid': API_KEY,
        'units': 'metric',
        'lang': 'en' 
    }

    try:
        response = requests.get(url, params=params, timeout=15)
        response.raise_for_status()
        all_data = response.json()

        if not all_data:
            raise ValueError("OpenWeather devolvió datos vacíos")

        return all_data
    except Exception as e:
        logger.error(f"❌ Error en extracción: {e}")
        raise


def ingest_openweather_to_bronze(api_response: dict, client_id: str) -> Optional[str]:
    """
    Capa Bronze: Guarda el JSON en un archivo físico, aplica chmod 444
    y devuelve la ruta del archivo para el rastro de auditoría (Lineage).
    """
    try:
        # 1. Definir rutas (Siguiendo tu estructura de carpetas)
        # Ajustado a tu ruta: ~/Documents/Data-Projects-Repo/
        bronze_dir = os.path.join("data", "bronze") 
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
    

if __name__ == "__main__":
    # 1. Extraer de la nube
    raw_data = extract_weather(42.8, -1.6) # Ejemplo Pamplona

    # 2. Guardar en Bronze y obtener el "puntero" (nombre del archivo)
    path_weather_raw = ingest_openweather_to_bronze(raw_data, "cliente_001")

    print(path_weather_raw)