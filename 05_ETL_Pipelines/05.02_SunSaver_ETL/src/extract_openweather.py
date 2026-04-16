import requests
import logging
import os
from typing import Dict, Any


# Solo declaramos, NO configuramos basicConfig aquí
logger = logging.getLogger(__name__)

def get_weather_forecast(lat: float, lon: float) -> Dict[str, Any]:

    """
    get_weather_forecast: Obtiene la serie temporal de 5 días (cada 3 horas) desde OpenWeather.

    """
    

    api_key = os.getenv("WEATHER_API_KEY")
    url = "https://api.openweathermap.org/data/2.5/forecast"
    
    params = {
        'lat': lat,
        'lon': lon,
        'appid': api_key,
        'units': 'metric',
        'lang': 'en'
    }

    logger.info(f"🛰️ Consultando OpenWeather ({lat}, {lon})")

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