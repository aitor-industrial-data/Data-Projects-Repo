
import os
import json
import stat
import pandas as pd
from typing import Optional
from pathlib import Path
from datetime import datetime, timezone
import config_paths
from logger_config import setup_logging


logger = setup_logging()


def extract_clients_from_excel() -> list[dict]:
    """
    Extrae datos de clientes desde Excel.
    """
    try:
        # 1. Localización de ruta
        BASE_DIR = Path(__file__).resolve().parent.parent
        excel_path = BASE_DIR / "data" / "clients_source.xlsx"
        
        # 2. Validación de existencia
        if not excel_path.exists():
            logger.error(f"❌ Archivo no encontrado: {excel_path}")
            return []

        # 3. Lectura de datos
        df = pd.read_excel(excel_path)
        
        # 4. Validación de contenido mínimo
        if df.empty:
            logger.warning(f"⚠️ El archivo {excel_path.name} está vacío.")
            return []

        # Convertimos los NaN de excel a None para que el JSON sea válido (escribirá 'null')
        # Usamos .where y pd.notnull para no alterar tipos de datos válidos
        df = df.astype(object).where(pd.notnull(df), None)
        
        logger.info(f"✅ Extracción exitosa: {len(df)} clientes detectados.")
        return df.to_dict(orient='records')

    except ImportError:
        logger.error("❌ Error: Falta instalar 'openpyxl'. Ejecuta: pip install openpyxl")
        return []
    except Exception as e:
        # Captura cualquier otro error (archivo corrupto, permisos, etc.)
        logger.error(f"❌ Error inesperado al extraer del Excel: {e}")
        return []



def ingest_clients_to_bronze(api_response: list[dict]) -> Optional[str]:
    """
    Capa Bronce: Carga los datos crudos del Excel y añade 
    metadatos de auditoría (_ingested_at_utc).
    """
    try:
        bronze_dir=config_paths.get_bronze_path()
        os.makedirs(bronze_dir, exist_ok=True)

        timestamp = datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')
        filename = f"clients_{timestamp}.json"
        full_path = os.path.join(bronze_dir, filename)

        # 2. Guardar el archivo JSON
        with open(full_path, 'w', encoding='utf-8') as f:
            json.dump(api_response, f, ensure_ascii=False, indent=4)

        # 3. BLINDAJE: Aplicar chmod 444 (Solo lectura)
        # Esto evita que nadie lo modifique
        permisos_lectura = stat.S_IRUSR | stat.S_IRGRP | stat.S_IROTH
        os.chmod(full_path, permisos_lectura)

        logger.info(f"🔒 Capa Bronze protegida: {filename}")
        
        # Devolvemos la ruta para que el siguiente script sepa qué leer
        return full_path

    except Exception as e:
        logger.error(f"❌ Error guardando Bronze en archivo: {e}")
        return None
        


def extract_clients() -> int:
    """
    Orquestador: Extrae de .xlsx, guarda en Bronze y actualiza el manifiesto.
    """
    try:
        # 1. Extracción
        raw_clients = extract_clients_from_excel()
        if not raw_clients:
            return 0
        
        total_clients = len(raw_clients)

        # 2. Ingesta a Bronze
        path_file = ingest_clients_to_bronze(raw_clients)
        if not path_file:
            return 0

        # Creamos la lista de "nuevas extracciones" 
        new_extractions = [{
            'source': 'clients_source.xlsx',
            'path': path_file,
            'status': 'pending',
            'created_at': datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S'),
            'updated_at': datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S')
        }]

        # 3. Gestión del MANIFIESTO
        bronze_dir = config_paths.get_bronze_path()
        manifest_path = os.path.join(bronze_dir, "_process_manifest_clients.json")

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
        logger.info(f"📄 Manifiesto clientes actualizado: {len(new_extractions)} nuevas tareas introducidas.")
        logger.info(f"datos totales procesados: {total_clients}")       
        return total_clients

    except Exception as e:
        logger.critical(f"❌ Error crítico en extract_energy_prices: {e}")
        return 0




if __name__ == "__main__":
    logger.info(f"Iniciando extraccion e ingesta de clientes en base de datos...")
    extract_clients()
    