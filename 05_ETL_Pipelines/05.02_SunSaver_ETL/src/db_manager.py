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


    

