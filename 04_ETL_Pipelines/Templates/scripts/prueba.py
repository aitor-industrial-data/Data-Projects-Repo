################################################################################
# etl_master_template.py
# AUTOR: Aitor | Ingeniero Técnico Industrial | Data Engineer
# PROYECTO: Plantilla Maestra ETL (Extracción API -> Transformación -> Carga BD)
################################################################################

import os
import time
import requests
import logging
from typing import List, Dict, Any
from datetime import datetime

from dotenv import load_dotenv
from sqlalchemy import create_engine, Column, Integer, String, Float, Boolean, text
from sqlalchemy.orm import declarative_base, sessionmaker
from sqlalchemy.exc import SQLAlchemyError

# ==============================================================================
# 0. CONFIGURACIÓN INICIAL Y LOGGING 
# ==============================================================================
load_dotenv() 

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)

API_URL = os.getenv("ETL_API_URL", "https://api.example.com/placeholder") 
TARGET_DB_URI = os.getenv("ETL_DB_URI", "sqlite:///default_local.db")

try:
    BATCH_SIZE = int(os.getenv("ETL_BATCH_SIZE", 500))
except ValueError:
    BATCH_SIZE = 500

API_KEY = os.getenv("ETL_API_KEY")
HEADERS = {
    "Authorization": f"Bearer {API_KEY}",
    "Content-Type": "application/json",
    "User-Agent": "DataEngineer-ETL-Aitor/1.0"
}

# ==============================================================================
# 1. DEFINICIÓN DEL MODELO DE DATOS 
# ==============================================================================
Base = declarative_base()

class TargetModel(Base):
    __tablename__ = 'cryptoprices' # Ajustar según proyecto
    id = Column(Integer, primary_key=True, autoincrement=True)
    coin_id = Column(String)
    symbol = Column(String)
    name = Column(String)
    current_price = Column(Float)
    last_updated = Column(String)

# ==============================================================================
# 2. FASE EXTRACT 
# ==============================================================================
def extract_from_api(url: str, max_pages: int = None) -> List[Dict[str, Any]]:
    """Extrae datos manejando paginación y cortesía (Rate Limit)."""
    logger.info(f"Iniciando extracción desde: {url}")
    all_data = []
    page = 1
    
    try:
        # --- OPCIÓN: Lógica Paginada (Activa por defecto) ---
        while True:
            if max_pages and page > max_pages:
                break

            params = {"page": page, "per_page": 100} 
            response = requests.get(url, params=params, headers=HEADERS, timeout=15)
            
            if response.status_code == 429:
                wait = int(response.headers.get("Retry-After", 60))
                logger.warning(f"Rate limit (429). Esperando {wait}s...")
                time.sleep(wait)
                continue

            response.raise_for_status()
            page_data = response.json()

            if not page_data: break
                
            all_data.extend(page_data)
            logger.info(f"Página {page} extraída. Registros actuales: {len(all_data)}")
            
            page += 1
            time.sleep(1.5) # Pausa de cortesía industrial

        return all_data

    except requests.exceptions.RequestException as e:
        logger.error(f"Error en EXTRACT: {e}")
        raise

# ==============================================================================
# 3. FASE TRANSFORM 
# ==============================================================================
def transform_data(raw_data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Limpia y mapea los datos brutos al modelo de destino."""
    logger.info("Iniciando fase de transformación...")
    clean_data = []

    for item in raw_data:
        try:
            clean_item = {
                'coin_id': str(item.get('id', '')).strip(),
                'symbol': str(item.get('symbol', '')).strip().upper(),
                'name': str(item.get('name', '')).strip(),
                'current_price': round(float(item.get('current_price', 0) or 0), 2),
                'last_updated': str(item.get('last_updated', ''))
            }
            clean_data.append(clean_item)
        except Exception as e:
            continue

    logger.info(f"Transformación finalizada. Registros válidos: {len(clean_data)}")
    return clean_data

# ==============================================================================
# 4. FASE LOAD 
# ==============================================================================
def load_to_db(clean_data: List[Dict[str, Any]], db_uri: str) -> None:
    """Carga con gestión de batches e información de progreso."""
    logger.info("Iniciando fase de carga...")
    engine = create_engine(db_uri, echo=False)
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    session = Session()

    try:
        # Opcional: session.query(TargetModel).delete() # Limpiar tabla antes de cargar
        
        total = len(clean_data)
        for i, data_dict in enumerate(clean_data, 1):
            session.add(TargetModel(**data_dict))
            
            if i % BATCH_SIZE == 0 or i == total:
                session.commit()
                progreso = (i / total) * 100
                logger.info(f"Progreso de carga: {progreso:.1f}% ({i}/{total})")

    except SQLAlchemyError as e:
        session.rollback()
        logger.critical(f"Error en LOAD: {e}")
        raise
    finally:
        session.close()

# ==============================================================================
# ORQUESTADOR PRINCIPAL
# ==============================================================================
if __name__ == "__main__":
    logger.info("=== INICIANDO PIPELINE ETL (MODO DESARROLLO) ===")
    start_time = datetime.now()
    
    # CONTROL DE FASES: "EXTRACT", "TRANSFORM" o "LOAD"
    FASE_OBJETIVO = "LOAD" 

    try:
        # --- 1. EXTRACT ---
        raw_data = extract_from_api(API_URL, max_pages=5)
        
        if raw_data:
            print(f"\n[DEBUG] ESQUEMA DETECTADO: {list(raw_data[0].keys())}")
            print(f"[DEBUG] Ejemplo Raw: {raw_data[0]}\n")
        
        if FASE_OBJETIVO == "EXTRACT": exit()

        # --- 2. TRANSFORM ---
        clean_data = transform_data(raw_data)
        if clean_data:
            print(f"[DEBUG] Ejemplo Clean: {clean_data[0]}\n")

        if FASE_OBJETIVO == "TRANSFORM": exit()

        # --- 3. LOAD ---
        if not clean_data:
            logger.warning("Sin datos para cargar.")
        else:
            load_to_db(clean_data, TARGET_DB_URI)
        
        duration = datetime.now() - start_time
        logger.info(f"=== PIPELINE FINALIZADO CON ÉXITO en {duration} ===")
        
    except Exception as e:
        logger.critical(f"=== FALLO CRÍTICO EN FASE {FASE_OBJETIVO}: {e} ===")