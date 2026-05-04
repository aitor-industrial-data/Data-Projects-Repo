import requests
import stat
import pandas as pd
import logging
import os
from datetime import datetime, timedelta, timezone
from dotenv import load_dotenv
import json
from typing import Dict, Any, Optional
import sqlite3


import workspace_manager

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)

logger = logging.getLogger(__name__)


load_dotenv()

def extract_raw_json_from_ree() -> dict:
    """
    Extrae el objeto JSON original de la API de REE.
    """

    # Calculamos la fecha de mañana
    today = datetime.now().strftime("%Y-%m-%d") # para hacer pruebas con el precio de hoy (antes de 20:30 no hay precios de mañana)
    tomorrow = (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d")

    # Construimos la URL con la fecha de mañana
    url = (
        "https://apidatos.ree.es/es/datos/mercados/precios-mercados-tiempo-real"
        f"?start_date={tomorrow}T00:00&end_date={tomorrow}T23:59&time_trunc=hour"
    )

    headers = {"Accept": "application/json"}

    try:
        response = requests.get(url, params=headers, timeout=15)
        response.raise_for_status()
        all_data = response.json()

        if not all_data.get('included') or not all_data['included'][0]['attributes']['values']:
            logger.warning("⚠️ Los precios para mañana aún no han sido publicados.")
            return False
        
        logger.info(f"✅ Extracción completada: {len(all_data)} registros obtenidos.")
        return all_data
    
    except requests.exceptions.HTTPError as e:
        if response.status_code == 502:
            logger.warning("⚠️ Precios para mañana aún no publicados (REE devuelve 502 antes de las ~20:30h).")
        else:
            logger.error(f"❌ Error HTTP al obtener precios: {e}")
        return False

    except Exception as e:
        logger.error(f"❌ Error inesperado al obtener el JSON crudo: {e}")
        return False
    

def ingest_ree_to_bronze(api_response: dict) -> Optional[str]:
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
        filename = f"prices_{timestamp}.json"
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




def extract_energy_prices() -> bool:
    """
    Orquestador: Extrae de REE, guarda en Bronze y actualiza el manifiesto.
    """
    try:
        # 1. Extracción
        raw_prices = extract_raw_json_from_ree()
        if not raw_prices:
            return False

        # 2. Ingesta a Bronze
        path_file = ingest_ree_to_bronze(raw_prices)
        if not path_file:
            return False

        # Creamos la lista de "nuevas extracciones" 
        new_extractions = [{
            'source': 'REE',
            'path': path_file,
            'status': 'pending',
            'created_at': datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S'),
            'updated_at': datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S')
        }]

        # 3. Gestión del MANIFIESTO
        bronze_dir = workspace_manager.get_bronze_path()
        manifest_path = os.path.join(bronze_dir, "_process_manifest_ree.json")

        all_tasks = []
        if os.path.exists(manifest_path):
            try:
                with open(manifest_path, 'r', encoding='utf-8') as f:
                    all_tasks = json.load(f)
            except Exception:
                all_tasks = []

        # Unimos las nuevas a las existentes
        all_tasks.extend(new_extractions)

        # 4. Guardar archivo
        with open(manifest_path, 'w', encoding='utf-8') as f:
            json.dump(all_tasks, f, indent=4, ensure_ascii=False)
        
        # EL LOGGER QUE HAS PEDIDO:
        logger.info(f"📄 Manifiesto REE actualizado: {len(new_extractions)} nuevas tareas introducidas.")
        
        return True

    except Exception as e:
        logger.critical(f"❌ Error crítico en extract_energy_prices: {e}")
        return False


if __name__ == "__main__":
    extract_energy_prices()