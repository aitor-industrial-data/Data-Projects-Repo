import os
from pathlib import Path
from dotenv import load_dotenv

"""
PATH CONFIGURATION MANAGER
--------------------------
Author: Aitor Asin
Description: Centralizes filesystem logic and environment variable resolution.
             Ensures all required data directories (Bronze, Silver) are 
             automatically created during runtime.
"""

def _get_validated_path(env_var: str, default_subpath: str) -> Path:
    """
    Helper logic to resolve environment variables or fallback to project defaults.
    Automatically creates parent directories to prevent FileNotFoundError.
    """
    load_dotenv()
    
    # Project Root (Assumes this file is in /utils or similar)
    base_dir = Path(__file__).resolve().parent.parent
    
    env_val = os.getenv(env_var)
    if env_val:
        final_path = Path(env_val)
    else:
        final_path = base_dir / "data" / default_subpath

    # Infrastructure Safety: Ensure the directory structure exists
    final_path.parent.mkdir(parents=True, exist_ok=True)
    
    return final_path.resolve()


def get_db_path() -> Path:
    """
    Returns the absolute path to the SQLite database (Silver/Gold Layer).
    """
    return _get_validated_path("DB_PATH", "sunsaver.db")


def get_client_path() -> Path:
    """
    Returns the absolute path to the source Excel file for client data.
    """
    return _get_validated_path("CLIENTS_SOURCE_PATH", "clients_source.xlsx")


def get_bronze_path() -> Path:
    """
    Returns the absolute path to the Bronze directory (Immutable Raw Data).
    """
    # Note: For directories, we ensure the directory itself exists
    path = _get_validated_path("BRONZE_PATH", "bronze")
    path.mkdir(parents=True, exist_ok=True)
    return path


if __name__ == "__main__":
    # Quick debug to verify paths during development
    print(f"DB Path:     {get_db_path()}")
    print(f"Client Path: {get_client_path()}")
    print(f"Bronze Path: {get_bronze_path()}")