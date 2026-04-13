################################################################################
# etl_master_template.py
# AUTOR: Aitor | Ingeniero Técnico Industrial | Data Engineer
# PROYECTO: Plantilla Maestra ETL (Extracción API -> Transformación -> Carga BD)
#
# DESCRIPCIÓN:
# Boilerplate profesional para pipelines de datos. Contiene la estructura base
# para extraer datos de una API (JSON), aplicar limpieza en memoria y cargar
# los resultados en una base de datos relacional usando Batching.
################################################################################

import os
import time
import requests
import logging
from typing import List, Dict, Any
from datetime import datetime

# Librerías externas (Instalar con pip install python-dotenv requests sqlalchemy)
from dotenv import load_dotenv
from sqlalchemy import create_engine, Column, Integer, String, Float, Boolean, text
from sqlalchemy.orm import declarative_base, sessionmaker
from sqlalchemy.exc import SQLAlchemyError


# ==============================================================================
# 0. CONFIGURACIÓN INICIAL Y LOGGING 
# ==============================================================================
# CARGA DE SECRETOS: Esta función busca un archivo llamado .env en tu carpeta
# y sube todas sus variables a la memoria del sistema operativo.
load_dotenv() 

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)

# Parámetros desde .env (con fallbacks de seguridad)
API_URL = os.getenv("ETL_API_URL", "https://api.example.com/placeholder") 
TARGET_DB_URI = os.getenv("ETL_DB_URI", "sqlite:///default_local.db")

try:
    BATCH_SIZE = int(os.getenv("ETL_BATCH_SIZE", 500))
except ValueError:
    logger.warning("BATCH_SIZE no válido en .env. Usando defecto: 500")
    BATCH_SIZE = 500

API_KEY = os.getenv("ETL_API_KEY") # No ponemos fallback aquí, si no hay llave, suele fallar

# Definimos los headers estándar de la industria
# Nota: Si la API no requiere Token, este diccionario no afectará negativamente
HEADERS = {
    "Authorization": f"Bearer {API_KEY}", # O "X-API-KEY": API_KEY, depende de la API
    "Content-Type": "application/json",
    "User-Agent": "DataEngineer-ETL-Aitor/1.0" # Identifica tu script ante el servidor
}

# ==============================================================================
# 1. DEFINICIÓN DEL MODELO DE DATOS 
# ==============================================================================

# Ver como son los dato antes de definir el modelo necesitamos ver como son los datos:
"""response = requests.get(API_URL, headers=HEADERS, timeout=15)
response.raise_for_status() 
all_data = response.json()

print(response.headers) # Esto imprime los headers donde se puede ver si el json es paginado o no
print(all_data[0]) # Esto imprime en consola el primer registro completo"""


# Ahora que hemos visto los datos, definimos la tabla
Base = declarative_base()

class TargetModel(Base):
    __tablename__ = 'target_table_name'
    id = Column(Integer, primary_key=True, autoincrement=True)
    # field_name = Column(String)

# ==============================================================================
# 2. FASE EXTRACT 
# ==============================================================================
def extract_from_api(url: str, max_pages: int = None) -> List[Dict[str, Any]]:
    """Extrae datos de un endpoint REST (API)."""
    logger.info(f"Iniciando extracción desde: {url}")
    all_data = []

    try:
        # --- [DESACTIVADO] Lógica de Paginación ---
        # Si la API es paginada, desactiva la "Petición simple" y activa este bloque
        # OJO: Si el JSON viene envuelto en una llave, ej: data["results"]
        # Deberías retornar: return all_data.get("results", [])
        """
        page = 1
        while True:
            if max_pages and page > max_pages:
                logger.info(f"Límite de páginas alcanzado por configuración: {max_pages}")
                break
                
            # --- [CONFIGURACIÓN DE PARÁMETROS] ---
            # OJO: Cada API es un mundo. Revisa la documentación o el primer response.json()
            # 1.  {"page": page, "per_page": 100}
            # 2.  {"offset": page*100, "limit": 100}
            # 3.  {"p": page, "size": 50}
            params = {"page": page, "per_page": 100} # Ajustas segun parametros API
            response = requests.get(url, params=params, headers=HEADERS, timeout=15)
            
            # Gestión de Rate Limit (Error 429: Demasiadas peticiones)
            if response.status_code == 429:
                wait = int(response.headers.get("Retry-After", 30))
                logger.warning(f"Rate limit detectado. Esperando {wait}s...")
                time.sleep(wait)
                continue

            response.raise_for_status()
            page_data = response.json()

            if not page_data: # Condición de salida: no hay más datos
                break
                
            all_data.extend(page_data)
            logger.info(f"Página {page} extraída. Total: {len(all_data)} registros.")
            
            page += 1
            time.sleep(1) # CORTESÍA: 1 seg entre llamadas para evitar bloqueos
        
        return all_data
        """

        # --- [ACTIVADO] Petición simple ---
        # Se usa cuando la API devuelve todos los datos en una sola llamada
        # OJO: Si el JSON viene envuelto en una llave, ej: data["results"]
        # Deberías retornar: return all_data.get("results", [])
        response = requests.get(url, headers=HEADERS, timeout=15)
        response.raise_for_status() 
        all_data = response.json()
        
        logger.info(f"Extracción exitosa. Registros obtenidos: {len(all_data)}")
        return all_data

    except requests.exceptions.RequestException as e:
        logger.error(f"Error de conexión en la fase EXTRACT: {e}")
        raise # Detenemos el pipeline si falla la extracción básica

# ==============================================================================
# 3. FASE TRANSFORM 
# ==============================================================================
def transform_data(raw_data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Aplica reglas de calidad y limpieza a los datos brutos."""
    logger.info("Iniciando fase de transformación...")
    clean_data = []

    for item in raw_data:
        try:
            # [RELLENAR] Mapeo y transformación
            clean_item = {
                # 'name': str(item.get('item_name', '')).strip(),
                # 'category': str(item.get('category', 'UNCATEGORIZED')).strip().upper(),
                # 'price': float(str(item.get('current_price', 0)).strip()),
                # etc...
            }
            clean_data.append(clean_item)
            
        except Exception as e:
            logger.warning(f"Error transformando registro {item}: {e}")
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
        # --- LÓGICA DE LIMPIEZA (OPCIONAL) ---
        # Borra todos los datos existentes para evitar duplicados en cada ejecución
        """
        session.query(TargetModel).delete() 
        logger.info("Tabla previa limpiada (Truncate).")"""
        
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
        logger.info("Conexión a la base de datos cerrada.")

    
# ==============================================================================
# ORQUESTADOR PRINCIPAL
# ==============================================================================
if __name__ == "__main__":
    logger.info("=== INICIANDO PIPELINE ETL (MODO DESARROLLO) ===")
    start_time = datetime.now()
    
    # CONTROL DE FASES: Cambia esto según lo que quieras probar ("EXTRACT", "TRANSFORM" o "LOAD")
    FASE_OBJETIVO = "LOAD" 

    try:
        # --- FASE 1: EXTRACT ---
        # Usamos un límite pequeño para pruebas rápidas, para extraccion completa borrar max_pages
        raw_data = extract_from_api(API_URL, max_pages=2)
        
        # Inspección visual inmediata
        print(f"\n[DEBUG] Registros extraídos: {len(raw_data)}")
        if raw_data:
            print(f"[DEBUG] Ejemplo Raw:\n{raw_data[0]}\n")
        
        if FASE_OBJETIVO == "EXTRACT":
            logger.info("Interrupción programada tras EXTRACT.")
            exit()

        # --- FASE 2: TRANSFORM ---
        clean_data = transform_data(raw_data)
        
        # Inspección visual tras limpieza
        if clean_data:
            print(f"[DEBUG] Ejemplo Clean:\n{clean_data[0]}\n")

        if FASE_OBJETIVO == "TRANSFORM":
            logger.info("Interrupción programada tras TRANSFORM.")
            exit()

        # --- FASE 3: LOAD (Guard Clause) ---
        if not clean_data:
            logger.warning("No hay datos válidos para cargar. Abortando pipeline.")
        else:
            load_to_db(clean_data, TARGET_DB_URI)
        
        # Medición final (Solo si llegamos al final)
        duration = datetime.now() - start_time
        logger.info(f"=== PIPELINE FINALIZADO CON ÉXITO en {duration} ===")
        
    except Exception as e:
        logger.critical(f"=== FALLO CRÍTICO EN FASE {FASE_OBJETIVO}: {e} ===")