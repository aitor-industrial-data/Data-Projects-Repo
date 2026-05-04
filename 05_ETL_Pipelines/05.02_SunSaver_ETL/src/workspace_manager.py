import os
import logging
from pathlib import Path
from dotenv import load_dotenv



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


def get_bronze_path() -> Path:
    """
    Retorna la ruta absoluta del directorio bronce y asegura que el directorio exista.
    """
    load_dotenv()

    # __file__ es "<raíz del proyecto>/src/sunsaver.db" -> .parent.parent es '<raíz del proyecto>'
    # Ajustamos para que BASE_DIR sea la raíz del proyecto
    BASE_DIR = Path(__file__).resolve().parent.parent
    
    _default_bronze = BASE_DIR / "data" / "bronze"
    _bronze_path_env = os.getenv("BRONZE_PATH")

    final_path = Path(_bronze_path_env) if _bronze_path_env else _default_bronze

    # Aseguramos que la carpeta /data exista
    final_path.parent.mkdir(parents=True, exist_ok=True)
    
    return final_path.resolve()

    

