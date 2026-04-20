# ==============================================================================
# extract_pvgis.py
# ------------------------------------------------------------------------------
# RESPONSABILIDAD : Extraer los datos CRUDOS de la API de PVGIS (JRC Europa).
# CAPA ETL        : EXTRACT
# FUENTE          : PVGIS API v5.2 — Serie horaria de producción fotovoltaica
# SALIDA          : dict — JSON completo de la API, listo para guardar en bronce
# ------------------------------------------------------------------------------
# NOTA SOBRE LA SALIDA:
#   A diferencia de OpenWeather (que devuelve list[dict]), PVGIS devuelve un
#   dict con la estructura completa: inputs, outputs y metadata. Se guarda el
#   dict completo en bronce para no perder ningún dato de la respuesta original.
#   El transform extraerá outputs.hourly para procesar los registros horarios.
# ------------------------------------------------------------------------------
# DISEÑO MULTI-CLIENTE:
#   La función principal extract_pvgis() acepta todos los parámetros de la
#   instalación como argumentos, lo que permite llamarla para cualquier cliente.
#   El orquestador es responsable de pasar los datos de cada cliente.
#   No hay variables globales de configuración — todo viene del cliente.
# ------------------------------------------------------------------------------
# DEPENDENCIAS DE ENTORNO (.env):
#   No hay dependencias — todos los parámetros vienen de la tabla clients.
# ==============================================================================

import requests
import logging
from typing import Dict, Any

logger = logging.getLogger(__name__)


# ------------------------------------------------------------------------------
# FUNCIÓN PRINCIPAL DE EXTRACCIÓN
# Acepta todos los parámetros de la instalación explícitamente para soportar
# múltiples clientes con diferentes configuraciones.
# ------------------------------------------------------------------------------

def extract_pvgis(client: dict) -> Dict[str, Any]:
    """
    Consulta la API de PVGIS y devuelve el JSON completo de producción solar.

    Parámetros:
        lat          : Latitud de la instalación del cliente.
        lon          : Longitud de la instalación del cliente.
        outputformat : 'json'

    Retorna:
        dict — JSON completo de la API con claves: inputs, outputs, meta.
        Los registros horarios están en: retorno['outputs']['tmy_hourly']

    Lanza:
        ValueError               — si la API devuelve una respuesta sin datos horarios.
        requests.HTTPError       — si la API devuelve un código de error HTTP.
        requests.ConnectionError — si no hay conexión con el servidor.
    """
    url = "https://re.jrc.ec.europa.eu/api/v5_2/tmy"

    params = {
        'lat':           client["latitude"],
        'lon':           client["longitude"],
        'outputformat':  'json'      
    }

    
    logger.info(f"🛰️  Consultando PVGIS")

    try:
        response = requests.get(url, params=params, timeout=15)
        response.raise_for_status()

        # La API devuelve un JSON
        all_data = response.json()
    
        if not all_data:
            logger.error("PVGIS devolvió un diccionario vacío— sin datos para procesar")
            raise ValueError("PVGIS devolvió una diccionario vacío")

        logger.info(f"✅ Extracción completada: {len(all_data['outputs']['tmy_hourly'])} registros obtenidos.")
        return all_data

    except requests.exceptions.RequestException as e:
        logger.error(f"❌ Error de conexión con PVGIS: {e}")
        raise






