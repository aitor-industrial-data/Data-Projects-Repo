import os
import sqlite3
import logging
import pandas as pd
from pathlib import Path
from dotenv import load_dotenv

import db_manager


logger = logging.getLogger(__name__)


def get_db_path() -> Path:
    """
    Retorna la ruta absoluta a la base de datos y asegura que el directorio exista.
    """
    load_dotenv()

    # __file__ es "<raíz del proyecto>/src/sunsaver.db" -> .parent.parent es '<raíz del proyecto>'
    # Ajustamos para que BASE_DIR sea la raíz del proyecto
    BASE_DIR = Path(__file__).resolve().parent.parent
    
    _default_db = BASE_DIR / "data" / "sunsaver.db"
    _db_path_env = os.getenv("DB_PATH")

    final_path = Path(_db_path_env) if _db_path_env else _default_db

    # Aseguramos que la carpeta /data exista
    final_path.parent.mkdir(parents=True, exist_ok=True)
    
    return final_path.resolve()



def extract_from_db(table_name: str) -> pd.DataFrame:
    """
    Lee los datos de la tabla y los devuelve como DataFrame.
    """
    try:
        db_path = db_manager.get_db_path()
        
        # 1. Conexión a la DB (usando str por seguridad de tipos)
        with sqlite3.connect(str(db_path)) as conn:
            # 2. Leemos la tabla entera directamente a un DataFrame
            query = f"SELECT * FROM {table_name}"
            df = pd.read_sql_query(query, conn)
            
        logger.info(f"✅ Extracción exitosa: {len(df)} registros extraidos de DB")
        return df

    except Exception as e:
        logger.error(f"❌ Error extrayendo de DB: {e}")
        return pd.DataFrame() # Devolvemos un DF vacío si falla