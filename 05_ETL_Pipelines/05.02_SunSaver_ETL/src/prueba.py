import os
import pandas as pd
import json
import stat
import logging
import requests
from dotenv import load_dotenv
from datetime import datetime, timezone
from typing import Dict, Any, Optional
import workspace_manager


logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)

logger = logging.getLogger(__name__)

load_dotenv()


def extract_clients_from_excel() -> Optional[str]:
    """
    Capa Bronze para archivos locales: Lee Excel de clientes y lo guarda en JSON.
    """
    try:
        # 1. Leer el archivo origen
        excel_path=workspace_manager.get_client_path()
        df = pd.read_excel(excel_path)
        
        # 2. Definir destino (usando tu workspace_manager)
        bronze_dir = workspace_manager.get_bronze_path()
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"clients_{timestamp}.json"
        full_path = os.path.join(bronze_dir, filename)

        # 3. Guardar como JSON (para que la capa Silver siempre lea el mismo formato)
        # Orient='records' crea una lista de diccionarios, ideal para JSON
        df.to_json(full_path, orient='records', date_format='iso', indent=4)

        # 4. Blindaje (Solo lectura como hiciste con la API)
        os.chmod(full_path, 0o444)

        logger.info(f"📁 Excel de clientes convertido y protegido en Bronze: {filename}")
        return full_path

    except Exception as e:
        logger.error(f"❌ Error al ingestar el archivo local: {e}")
        return None


if __name__ == "__main__":

    logger.info(f"Iniciando extracción e ingesta de cálculos de rendimiento...")
    extract_clients_from_excel()