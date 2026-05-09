import requests
import stat
import os
from datetime import datetime, timedelta, timezone
from dotenv import load_dotenv
import json
from typing import Optional, Union

import workspace_manager
from logger_config import setup_logging

# ── Logging ───────────────────────────────────────────────────────────────────
logger = setup_logging()

# ── Configuración ─────────────────────────────────────────────────────────────
load_dotenv()

def extract_raw_json_from_ree() -> Union[dict, bool]:
    """
    Extrae precios PVPC (id=1001) de mañana de la API de Red Eléctrica.
    Retorna el diccionario de datos o False si no hay disponibilidad o hay error.
    """
    tomorrow = (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d")

    try:
        url = (
            "https://apidatos.ree.es/es/datos/mercados/precios-mercados-tiempo-real"
            f"?start_date={tomorrow}T00:00&end_date={tomorrow}T23:59"
            "&time_trunc=hour&geo_trunc=electric_system"
            "&geo_limit=peninsular&geo_ids=8741"
        )
        headers = {
            "Accept": "application/json",
            "Origin": "https://www.ree.es",
            "Referer": "https://www.ree.es/",
        }
        
        response = requests.get(url, headers=headers, timeout=15)
        response.raise_for_status()
        all_data = response.json()

        # Filtrar solo el ID 1001 (PVPC)
        pvpc_item = next(
            (item for item in all_data.get("included", [])
             if item.get("id") == "1001"),
            None
        )

        if pvpc_item and pvpc_item["attributes"].get("values"):
            logger.info(f"✅ PVPC extraído correctamente para {tomorrow}")
            all_data["included"] = [pvpc_item]
            return all_data

        # Si llegamos aquí, REE no tiene los precios publicados todavía
        logger.warning(f"⚠️ REE no devolvió precios para {tomorrow}. (Probable: antes de las 20:30h)")
        return False

    except requests.exceptions.HTTPError as e:
        code = response.status_code
        if code in (500, 502, 503, 504):
            logger.error(f"⚠️ Servidor REE no disponible ({code}). Precios aún no publicados.")
        else:
            logger.error(f"❌ Error HTTP en REE: {e}")
        return False

    except Exception as e:
        logger.error(f"❌ Error inesperado conectando con REE: {e}")
        return False

def ingest_ree_to_bronze(api_response: dict) -> Optional[str]:
    """
    Capa Bronze: Guarda el JSON original con permisos de solo lectura.
    """
    try:
        bronze_dir = workspace_manager.get_bronze_path()
        os.makedirs(bronze_dir, exist_ok=True)

        timestamp = datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')
        filename = f"prices_{timestamp}.json"
        full_path = os.path.join(bronze_dir, filename)

        with open(full_path, 'w', encoding='utf-8') as f:
            json.dump(api_response, f, ensure_ascii=False, indent=4)

        # Blindaje chmod 444
        os.chmod(full_path, stat.S_IRUSR | stat.S_IRGRP | stat.S_IROTH)
        logger.info(f"🔒 Archivo Bronze blindado: {filename}")
        
        return full_path

    except Exception as e:
        logger.error(f"❌ Error en persistencia Bronze: {e}")
        return None

def extract_energy_prices() -> Union[int, bool]: 
    """
    Orquestador del módulo REE.
    RETORNA: 
        - int: Cantidad de registros (filas) si todo es correcto.
        - False: Si el proceso debe marcarse como fallido/incompleto en el orquestador principal.
    """
    try:
        # 1. Extracción con validación de disponibilidad
        raw_prices = extract_raw_json_from_ree()
        
        
        # SI REE NO DA DATOS, DEVOLVEMOS FALSE
        # Esto hará que el orquestador principal marque 'PARTIAL SUCCESS' y registre el fallo
        if raw_prices is False:
            return False 

        # 2. Conteo de volumen de datos
        try:
            total_hours = len(raw_prices["included"][0]["attributes"]["values"])
        except (KeyError, IndexError):
            logger.error("❌ Formato de datos de REE irreconocible.")
            return False

        # 3. Persistencia en Bronze
        path_file = ingest_ree_to_bronze(raw_prices)
        if not path_file:
            return False

        # 4. Actualización del Manifiesto de Procesamiento
        new_extraction = {
            'source': 'REE',
            'path': path_file,
            'status': 'pending',
            'created_at': datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S'),
            'updated_at': datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S')
        }

        bronze_dir = workspace_manager.get_bronze_path()
        manifest_path = os.path.join(bronze_dir, "_process_manifest_ree.json")

        all_tasks = []
        if os.path.exists(manifest_path):
            try:
                with open(manifest_path, 'r', encoding='utf-8') as f:
                    all_tasks = json.load(f)
            except Exception:
                all_tasks = []

        all_tasks.append(new_extraction)

        with open(manifest_path, 'w', encoding='utf-8') as f:
            json.dump(all_tasks, f, indent=4, ensure_ascii=False)
        
        logger.info(f"📊 ETL REE: {total_hours} registros inyectados en Bronze.")
        return total_hours 

    except Exception as e:
        logger.critical(f"❌ Fallo catastrófico en extract_energy_prices: {e}")
        return False

if __name__ == "__main__":
    # Ejecución manual para pruebas
    extract_energy_prices()