# ==============================================================================
# extract_openweather.py
# ------------------------------------------------------------------------------
# RESPONSABILIDAD : Extraer los datos CRUDOS de la API de OpenWeatherMap.
# CAPA ETL        : EXTRACT
# FUENTE          : OpenWeatherMap Forecast API (5 días, intervalos de 3h)
# SALIDA          : list[dict] — datos crudos listos para guardar en bronce
# ------------------------------------------------------------------------------
# DISEÑO MULTI-CLIENTE:
#   La función principal extract_weather() acepta coordenadas como parámetros,
#   lo que permite llamarla para cualquier cliente con cualquier ubicación.
#   El orquestador es responsable de pasar las coordenadas de cada cliente.
# ------------------------------------------------------------------------------
# DEPENDENCIAS DE ENTORNO (.env):
#   WEATHER_API_KEY → Clave de acceso a la API de OpenWeather (única para todos
#                     los clientes — es una clave del sistema, no del cliente)
# ==============================================================================

import requests
import logging
import os
import sys
from typing import List, Dict, Any
from dotenv import load_dotenv

import db_manager


logger = logging.getLogger(__name__)

load_dotenv()


# ------------------------------------------------------------------------------
# VALIDACIÓN DE CONFIGURACIÓN
# Solo validamos la API KEY — las coordenadas vienen del cliente, no del .env.
# ------------------------------------------------------------------------------

API_KEY = os.getenv("WEATHER_API_KEY")
if not API_KEY:
    logger.error("Falta WEATHER_API_KEY en el .env")
    sys.exit(1)


# ------------------------------------------------------------------------------
# FUNCIÓN PRINCIPAL DE EXTRACCIÓN
# Acepta coordenadas como parámetros para soportar múltiples clientes.
# Se puede llamar con cualquier ubicación sin tocar el .env.
# ------------------------------------------------------------------------------

def extract_weather(lat: float, lon: float) -> List[Dict[str, Any]]:
    """
    Consulta la API de OpenWeather y devuelve la serie temporal de pronóstico.

    Parámetros:
        lat : Latitud de la ubicación del cliente.
        lon : Longitud de la ubicación del cliente.

    Retorna:
        list[dict] — Lista de hasta 40 registros (5 días x 8 intervalos de 3h).
        Cada dict contiene temperatura, nubes, viento, descripción y timestamp.

    Lanza:
        ValueError               — si la API devuelve una lista vacía.
        requests.HTTPError       — si la API devuelve un código de error HTTP.
        requests.ConnectionError — si no hay conexión con el servidor.
    """
    url = "https://api.openweathermap.org/data/2.5/forecast"

    params = {
        'lat':   lat,
        'lon':   lon,
        'appid': API_KEY,
        'units': 'metric',  # Temperatura en °C
        'lang':  'en'       # Descripciones en inglés para consistencia en DB
    }

    logger.info(f"🛰️  Consultando OpenWeather — coordenadas: ({lat}, {lon})")

    try:
        response = requests.get(url, params=params, timeout=15)
        response.raise_for_status()

        # La API devuelve un JSON con la clave "list" que contiene los registros
        all_data = response.json().get("list", [])

        if not all_data:
            logger.error("OpenWeather devolvió una lista vacía — sin datos para procesar")
            raise ValueError("OpenWeather devolvió una lista vacía")

        logger.info(f"✅ Extracción completada: {len(all_data)} registros obtenidos.")
        return all_data

    except requests.exceptions.RequestException as e:
        logger.error(f"❌ Error de conexión con OpenWeather: {e}")
        raise


# ==============================================================================
# REFERENCIA: ESTRUCTURA DEL DATO CRUDO (útil para desarrollar TRANSFORM)
# ==============================================================================
"""
Cada elemento de la lista devuelta tiene este formato:

{
    'dt': 1776351600,                        <- Unix timestamp del intervalo
    'main': {
        'temp': 23.75,                       <- Temperatura en °C
        'humidity': 32,                      <- Humedad relativa en %
        'pressure': 1018,                    <- Presión atmosférica en hPa
        ...
    },
    'weather': [
        {'description': 'clear sky', ...}   <- Descripción textual del tiempo
    ],
    'clouds': {'all': 0},                   <- Cobertura nubosa en %
    'wind':   {'speed': 3.89, 'gust': 5.1}, <- Velocidad y ráfaga en m/s
    'dt_txt': '2026-04-16 15:00:00'         <- Timestamp legible (UTC)
}

Accesos rápidos:
    temperatura = registro['main']['temp']
    nubes       = registro['clouds']['all']
    fecha       = registro['dt_txt']
"""


if __name__ == "__main__":
    raw_clients=db_manager.extract_from_db('raw_clients')
    print(raw_clients['latitude'])
    '''lati=42.776
    long=1.68
    print(extract_weather(lati,long))'''
