import requests
import logging
import os
import sys
from typing import Dict, Any
from dotenv import load_dotenv 

logger = logging.getLogger(__name__)

load_dotenv()

try:
    LAT = float(os.getenv("SITE_LATITUDE"))
    LON = float(os.getenv("SITE_LONGITUDE"))
    PEAK_POWER = float(os.getenv("PV_PEAK_POWER_KW"))
    LOSS = float(os.getenv("PV_SYSTEM_LOSS_PCT"))
    MOUNTING_PLACE = os.getenv("PV_MOUNTING_PLACE")
    YEAR = int(os.getenv("PV_YEAR"))

except (ValueError, TypeError) as e:
    logger.error(f"❌ ERROR CRÍTICO DE CONFIGURACIÓN: {e}")
    logger.error("El Robot ETL no puede continuar con datos inválidos o ausentes en el .env.")
    # Detenemos la ejecución por completo
    sys.exit(1)




def get_pvgis_data(lat: float = None, lon: float = None, peakpower: float = None, loss: float = None, mountingplace: str = None, year: int = None) -> Dict[str, Any]:
    """
    Obtiene la SERIE HORARIA de producción fotovoltaica desde PVGIS.
    """
    target_lat = lat if lat is not None else LAT
    target_lon = lon if lon is not None else LON
    target_pw = peakpower if peakpower is not None else PEAK_POWER
    target_loss = loss if loss is not None else LOSS
    target_mount = mountingplace if mountingplace is not None else MOUNTING_PLACE
    target_year = year if year is not None else YEAR

    url = "https://re.jrc.ec.europa.eu/api/v5_2/seriescalc"
    params = {
        'lat': target_lat,
        'lon': target_lon,
        'peakpower': target_pw,
        'loss': target_loss,
        'mountingplace': target_mount,
        'startyear': target_year,
        'endyear': target_year,
        'outputformat': 'json'
    }

    logger.info(f"🛰️ Consultando PVGIS Horario para el año {target_year}...")

    try:
        response = requests.get(url, params=params, timeout=15)
        response.raise_for_status() 
        
        all_data = response.json()
        
        hourly_data = all_data.get("outputs", {}).get("hourly", [])
        
        logger.info(f"✅ Datos obtenidos: {len(hourly_data)} registros horarios.")
        
        return all_data if hourly_data else None

    except requests.exceptions.RequestException as e:
        logger.error(f"❌ Error en EXTRACT PVGIS: {e}")
        raise

