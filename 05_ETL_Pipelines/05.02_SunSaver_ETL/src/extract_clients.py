
import sqlite3
import pandas as pd
from pathlib import Path
import logging
from datetime import datetime
import db_manager

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)

logger = logging.getLogger(__name__)


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

        logger.info(f"✅ Extracción exitosa: {len(df)} clientes detectados.")
        return df.to_dict(orient='records')

    except ImportError:
        logger.error("❌ Error: Falta instalar 'openpyxl'. Ejecuta: pip install openpyxl")
        return []
    except Exception as e:
        # Captura cualquier otro error (archivo corrupto, permisos, etc.)
        logger.error(f"❌ Error inesperado al extraer del Excel: {e}")
        return []



def ingest_clients_to_bronze(client_list: list[dict], table_name: str) -> bool:
    """
    Capa Bronce: Carga los datos crudos del Excel y añade 
    metadatos de auditoría (_ingested_at).
    """
    try:
        db_path = db_manager.get_db_path()
        
        # 1. Convertimos a DataFrame
        df = pd.DataFrame(client_list)

        # 2. Añadimos el metadato de auditoría (Estándar de ingeniería)
        # Usamos el guion bajo para indicar que es un campo de control
        df['_ingested_at'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

        # 3. Volcado a SQLite
        with sqlite3.connect(str(db_path)) as conn:
            # Usamos 'replace' para asegurar que la estructura de la tabla 
            # coincida siempre con el Excel + nuestra columna de auditoría
            df.to_sql(table_name, conn, if_exists='append', index=False)
            
        logger.info(f"✅ Ingesta exitosa: {len(df)} registros añadidos a base de datos")
        return True
    
    except Exception as e:
        logger.error(f"❌ Error en la ingesta Bronce: {e}")
        return False


def extract_clients (table_name: str) -> bool:
    #extrae e inyecta clientes en capa bronce de db
    clients=extract_clients_from_excel()
    ingest_clients_to_bronze(clients, table_name)


if __name__ == "__main__":
    logger.info(f"Iniciando extraccion e ingesta de clientes en base de datos...")
    extract_clients('raw_clients')
    