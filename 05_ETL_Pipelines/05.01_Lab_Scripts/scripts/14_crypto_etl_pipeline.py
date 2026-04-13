################################################################################
# 14_crypto_etl_pipeline.py
# AUTOR: Aitor | Ingeniero Técnico Industrial | Data Engineer
# PROYECTO: ETL Pipeline - Seguimiento de Activos Cripto y Persistencia SQL
#
# ENUNCIADO:
# Desarrollar un pipeline robusto de ingeniería de datos que automatice el ciclo:
# 1. EXTRACT: Extracción paginada desde la API de CoinGecko con gestión activa 
#    de Rate Limiting (Error 429) y control de cortesía (Backoff).
# 2. TRANSFORM: Normalización de tipos de datos, limpieza de strings y redondeo
#    financiero de precios para garantizar la integridad del esquema (Wrangling).
# 3. LOAD: Persistencia en base de datos SQLite mediante SQLAlchemy, empleando 
#    técnicas de Batching para optimizar el rendimiento de las transacciones I/O.
# 4. ORCHESTRATION: Implementación de un modo de ejecución por fases (Targeted 
#    Execution) para facilitar el debug y la validación incremental.
#
# FOCO TÉCNICO: REST API Consumption, SQLAlchemy ORM, Rate Limit Handling.
################################################################################

import os
import time
import requests
import logging
from typing import List, Dict, Any
from datetime import datetime

from dotenv import load_dotenv
from sqlalchemy import create_engine, Column, Integer, String, Float
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

# Parámetros de entorno con defaults de seguridad
API_URL = os.getenv("ETL_API_URL", "https://api.coingecko.com/api/v3/coins/markets") 
TARGET_DB_URI = os.getenv("ETL_DB_URI", "sqlite:///crypto_data.db")
BATCH_SIZE = int(os.getenv("ETL_BATCH_SIZE", 500))
API_KEY = os.getenv("ETL_API_KEY")

HEADERS = {
    "Authorization": f"Bearer {API_KEY}",
    "Content-Type": "application/json",
    "User-Agent": "DataEngineer-ETL-Aitor/1.0"
}

# ==============================================================================
# 1. MODELADO DE DATOS (ORM)
# ==============================================================================
Base = declarative_base()

class CryptoPrice(Base):
    """Esquema de la tabla para el almacenamiento de precios actuales."""
    __tablename__ = 'cryptoprices'
    id = Column(Integer, primary_key=True, autoincrement=True)
    coin_id = Column(String, index=True, unique=True)
    symbol = Column(String)
    name = Column(String)
    current_price = Column(Float)
    last_updated = Column(String)

# ==============================================================================
# 2. FASE: EXTRACT
# ==============================================================================
def extract_from_api(url: str, max_pages: int = None) -> List[Dict[str, Any]]:
    """Extrae datos de la API gestionando paginación y límites de tráfico."""
    logger.info(f"Iniciando extracción desde: {url}")
    all_data = []
    page = 1

    try:
        while True:
            if max_pages and page > max_pages:
                logger.info(f"Límite de páginas alcanzado: {max_pages}")
                break

            # Ajuste dinámico de parámetros según documentación de la API
            params = {
                "vs_currency": "usd",
                "order": "market_cap_desc",
                "per_page": 100,
                "page": page,
                "sparkline": "false"
            }
            
            response = requests.get(url, params=params, headers=HEADERS, timeout=15)
            
            # Gestión avanzada de Rate Limit
            if response.status_code == 429:
                wait_time = int(response.headers.get("Retry-After", 60))
                logger.warning(f"Rate limit (429). Reintentando en {wait_time}s...")
                time.sleep(wait_time)
                continue

            response.raise_for_status()
            page_data = response.json()

            if not page_data: 
                break
                
            all_data.extend(page_data)
            logger.info(f"Página {page} completada. Registros totales: {len(all_data)}")
            
            page += 1
            time.sleep(1.2) # Delay de cortesía para evitar bloqueos preventivos

        return all_data

    except requests.exceptions.RequestException as e:
        logger.error(f"Error crítico en fase EXTRACT: {e}")
        raise

# ==============================================================================
# 3. FASE: TRANSFORM
# ==============================================================================
def transform_data(raw_data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Aplica lógica de limpieza y normalización de tipos (Data Wrangling)."""
    logger.info("Iniciando transformación de datos...")
    clean_data = []

    for item in raw_data:
        try:
            # Mapeo y casting preventivo
            clean_item = {
                'coin_id': str(item.get('id', '')).strip(),
                'symbol': str(item.get('symbol', '')).strip().upper(),
                'name': str(item.get('name', '')).strip(),
                'current_price': round(float(item.get('current_price', 0) or 0), 2),
                'last_updated': str(item.get('last_updated', ''))
            }
            clean_data.append(clean_item)
        except (TypeError, ValueError) as e:
            logger.warning(f"Registro omitido por error de formato: {e}")
            continue

    logger.info(f"Transformación finalizada. Registros aptos: {len(clean_data)}")
    return clean_data

# ==============================================================================
# 4. FASE: LOAD
# ==============================================================================
def load_to_db(clean_data: List[Dict[str, Any]], db_uri: str) -> None:
    """Persistencia en DB con lógica Upsert (Update or Insert) y Batch commits."""
    logger.info("Iniciando carga con lógica Upsert en base de datos...")
    
    engine = create_engine(db_uri, echo=False)
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    session = Session()

    try:
        total_records = len(clean_data)
        
        # Usamos enumerate para mantener el control del batching
        for index, data_dict in enumerate(clean_data, 1):
            
            # --- LÓGICA UPSERT ---
            # 1. Buscamos si el activo ya existe por su coin_id
            existing_coin = session.query(CryptoPrice).filter_by(coin_id=data_dict['coin_id']).first()
            
            if existing_coin:
                # 2. Si existe, actualizamos sus valores volátiles
                existing_coin.current_price = data_dict['current_price']
                existing_coin.last_updated = data_dict['last_updated']
            else:
                # 3. Si no existe, creamos el registro nuevo
                new_record = CryptoPrice(**data_dict)
                session.add(new_record)
            
            # --- GESTIÓN DE COMMITS (BATCHING) ---
            # Seguimos agrupando los commits para no saturar el disco
            if index % BATCH_SIZE == 0 or index == total_records:
                session.commit()
                progress = (index / total_records) * 100
                logger.info(f"Progreso carga: {progress:.1f}% ({index}/{total_records})")

    except SQLAlchemyError as e:
        session.rollback()
        logger.critical(f"Error de base de datos en fase LOAD: {e}")
        raise
    finally:
        session.close()

# ==============================================================================
# ORQUESTADOR (MODO DESARROLLO)
# ==============================================================================
if __name__ == "__main__":
    logger.info("=== INICIANDO PIPELINE ETL INTERACTIVO ===")
    start_time = datetime.now()
    
    # CONTROL DE FLUJO: Definir fase límite ("EXTRACT", "TRANSFORM", "LOAD")
    TARGET_PHASE = "LOAD" 

    try:
        # --- EJECUCIÓN: EXTRACT ---
        raw_data = extract_from_api(API_URL, max_pages=3)
        
        if raw_data:
            print(f"\n[DEBUG] Esquema detectado: {list(raw_data[0].keys())}")
            print(f"[DEBUG] Snapshot Raw: {raw_data[0]}\n")
        
        if TARGET_PHASE == "EXTRACT":
            logger.info("Pipeline interrumpido tras EXTRACT (según configuración).")
            exit()

        # --- EJECUCIÓN: TRANSFORM ---
        clean_data = transform_data(raw_data)
        
        if clean_data:
            print(f"[DEBUG] Snapshot Clean: {clean_data[0]}\n")

        if TARGET_PHASE == "TRANSFORM":
            logger.info("Pipeline interrumpido tras TRANSFORM (según configuración).")
            exit()

        # --- EJECUCIÓN: LOAD ---
        if not clean_data:
            logger.warning("No se detectaron datos válidos. Carga abortada.")
        else:
            load_to_db(clean_data, TARGET_DB_URI)
        
        total_duration = datetime.now() - start_time
        logger.info(f"=== PIPELINE FINALIZADO CON ÉXITO | DURACIÓN: {total_duration} ===")
        
    except Exception as e:
        logger.critical(f"=== FALLO CRÍTICO EN PIPELINE: {e} ===")