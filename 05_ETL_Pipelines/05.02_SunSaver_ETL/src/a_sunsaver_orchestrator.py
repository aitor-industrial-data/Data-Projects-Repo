import pandas as pd
import sqlite3
import logging
import db_manager

logger = logging.getLogger(__name__)

def extract_from_bronze() -> pd.DataFrame:
    """
    Lee los datos crudos de la tabla raw_clients y los devuelve como DataFrame.
    """
    try:
        db_path = db_manager.get_db_path()
        
        # 1. Conexión a la DB (usando str por seguridad de tipos)
        with sqlite3.connect(str(db_path)) as conn:
            # 2. Leemos la tabla entera directamente a un DataFrame
            query = "SELECT * FROM raw_clients"
            df = pd.read_sql_query(query, conn)
            
        logger.info(f"📥 Silver: {len(df)} registros extraídos de Bronze para transformar.")
        return df

    except Exception as e:
        logger.error(f"❌ Error extrayendo de Bronze: {e}")
        return pd.DataFrame() # Devolvemos un DF vacío si falla

