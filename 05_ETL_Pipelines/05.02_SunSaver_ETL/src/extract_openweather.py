import requests
import logging
import os
import sys
from typing import List, Dict, Any
from dotenv import load_dotenv 

logger = logging.getLogger(__name__)

load_dotenv()

API_KEY = os.getenv("WEATHER_API_KEY")
if not API_KEY:
    logger.error("Falta WEATHER_API_KEY en el .env")
    sys.exit(1)


_lat_raw = os.getenv("SITE_LATITUDE")
_lon_raw = os.getenv("SITE_LONGITUDE")

if _lat_raw is None or _lon_raw is None:
    logger.error("Faltan SITE_LATITUDE o SITE_LONGITUDE en el .env")
    sys.exit(1)

try:
    LAT = float(_lat_raw)
    LON = float(_lon_raw)
except ValueError as e:
    logger.error(f"Coordenadas con formato inválido: {e}")
    sys.exit(1)


def get_weather_forecast(lat: float = None, lon: float = None) -> List[Dict[str, Any]]:

    """
    get_weather_forecast: Obtiene la serie temporal de 5 días (cada 3 horas) desde OpenWeather.

    """
    # Usamos las variables cargadas fuera si no se pasan por argumento
    target_lat = lat if lat is not None else LAT
    target_lon = lon if lon is not None else LON

    url = "https://api.openweathermap.org/data/2.5/forecast"
    
    params = {
        'lat': target_lat,
        'lon': target_lon,
        'appid': API_KEY,
        'units': 'metric',
        'lang': 'en'
    }

    logger.info(f"🛰️  Consultando OpenWeather ({target_lat}, {target_lon})")

    try:
        response = requests.get(url, params=params, timeout=15)
        response.raise_for_status() 
        # print(response.json()) # Para visualizar por primera vez los datos que llegan.
        all_data = response.json().get("list", [])
        
        logger.info(f"✅ Datos obtenidos: {len(all_data)}.")
        return all_data if all_data else None

    except requests.exceptions.RequestException as e:
        logger.error(f"❌ Error en EXTRACT: {e}")
        raise



# ==============================================================================
# ESTRUCTURA REAL DEL DATO OBTENIDO (Para manipular en TRANSFORM)
# ==============================================================================
"""
Cada elemento [0],[1],... de la lista all_data tiene este formato exacto:

[{
    'dt': 1776351600, 
    'main': {
        'temp': 23.75, 
        'humidity': 32, 
        'pressure': 1018,
        ...
    }, 
    'weather': [
        {'description': 'clear sky', ...}
    ], 
    'clouds': {'all': 0}, 
    'wind': {'speed': 3.89, ...}, 
    'dt_txt': '2026-04-16 15:00:00'
},...

ATAJOS DE ACCESO:
temp = all_data[0]['main']['temp']
nubes = all_data[0]['clouds']['all']
fecha = all_data[0]['dt_txt']
"""