

import os
import sqlite3
import logging
import json
from pathlib import Path
from dotenv import load_dotenv

logger = logging.getLogger(__name__)

load_dotenv()

# ------------------------------------------------------------------------------
# RUTA A LA BASE DE DATOS (PORTABILIDAD TOTAL)
# ------------------------------------------------------------------------------

# __file__ es '.../src/db_manager.py'
# .parent       es '.../src/'
# .parent.parent es '.../' (raíz del proyecto)
BASE_DIR    = Path(__file__).resolve().parent.parent
_DEFAULT_DB = BASE_DIR / "data" / "sunsaver.db"

_db_path_env = os.getenv("DB_PATH")

# Convertimos a string absoluto para que SQLite no tenga ambigüedades
if _db_path_env:
    DB_PATH = str(Path(_db_path_env).absolute())
else:
    DB_PATH = str(_DEFAULT_DB.absolute())


# ==============================================================================
# INFRAESTRUCTURA — CREACIÓN DE TABLAS
# ==============================================================================

def create_tables():
    """
    Crea todas las tablas de la base de datos si no existen.
    También crea el directorio data/ si no existe (portabilidad en nuevos PCs).

    Es seguro ejecutarla múltiples veces — no borra datos existentes.
    """
    # Aseguramos que el directorio de la DB existe antes de conectar
    db_folder = Path(DB_PATH).parent
    if not db_folder.exists():
        logger.info(f"📁 Creando carpeta de base de datos: {db_folder}")
        db_folder.mkdir(parents=True, exist_ok=True)

    # Logueamos la ruta activa solo si se está usando el fallback
    if not _db_path_env:
        logger.warning(f"⚠️  DB_PATH no definido en .env — usando ruta calculada: {DB_PATH}")

    try:
        with sqlite3.connect(DB_PATH) as conn:
            cursor = conn.cursor()

            # ------------------------------------------------------------------
            # TABLA DE CLIENTES
            # Centraliza la configuración de cada instalación solar.
            # loss_pct se calcula con PVGIS al registrar el cliente y no cambia.
            # El pipeline ETL recurrente lee esta tabla para saber qué procesar.
            # ------------------------------------------------------------------

            cursor.execute('''
                CREATE TABLE IF NOT EXISTS clients (
                      id                      INTEGER PRIMARY KEY AUTOINCREMENT,
                    name                    TEXT NOT NULL,
                    latitude                REAL NOT NULL,
                    longitude               REAL NOT NULL,
                    peak_power_kw           REAL NOT NULL,   
                    panel_area_m2           REAL NOT NULL,
                    efficiency              REAL NOT NULL,
                    panel_type              TEXT NOT NULL,
                    loss_pct                REAL NOT NULL,
                    angle                   INTEGER NOT NULL,
                    aspect                  INTEGER NOT NULL,
                    mounting                TEXT NOT NULL,
                    battery_capacity_kwh    REAL NOT NULL,
                    soc_min_pct             REAL NOT NULL,
                    installation_cost_eur   REAL NOT NULL,
                    timezone                TEXT NOT NULL
                )
            ''')

            # ------------------------------------------------------------------
            # CAPA BRONCE — datos crudos de APIs recurrentes
            # Solo OpenWeather y ESIOS son recurrentes.
            # PVGIS se usa solo en el setup de cada cliente, no en el pipeline.
            # ------------------------------------------------------------------

            cursor.execute('''
                CREATE TABLE IF NOT EXISTS raw_solar (
                    id          INTEGER PRIMARY KEY AUTOINCREMENT,
                    client_id   INTEGER NOT NULL,
                    ingested_at TEXT DEFAULT (datetime('now')),
                    raw_data    TEXT,
                    FOREIGN KEY (client_id) REFERENCES clients(id)
                )
            ''')

            cursor.execute('''
                CREATE TABLE IF NOT EXISTS raw_weather (
                    id          INTEGER PRIMARY KEY AUTOINCREMENT,
                    client_id   INTEGER NOT NULL,
                    ingested_at TEXT DEFAULT (datetime('now')),
                    raw_data    TEXT,
                    FOREIGN KEY (client_id) REFERENCES clients(id)
                )
            ''')

            cursor.execute('''
                CREATE TABLE IF NOT EXISTS raw_prices (
                    id          INTEGER PRIMARY KEY AUTOINCREMENT,
                    client_id   INTEGER NOT NULL,
                    ingested_at TEXT DEFAULT (datetime('now')),
                    raw_data    TEXT,
                    FOREIGN KEY (client_id) REFERENCES clients(id)
                )
            ''')

            # ------------------------------------------------------------------
            # CAPA PLATA — datos meteorológicos limpios
            # INSERT OR REPLACE con PRIMARY KEY (unix_timestamp, client_id)
            # garantiza que siempre contiene la predicción más reciente.
            # El historial completo de ingestas está en raw_weather (bronce).
            # ------------------------------------------------------------------

            cursor.execute('''
                CREATE TABLE IF NOT EXISTS silver_weather (
                    unix_timestamp INTEGER NOT NULL,
                    client_id      INTEGER NOT NULL,
                    forecast_time  TEXT,
                    temperature    REAL,
                    cloud_coverage INTEGER,
                    condition_desc TEXT,
                    wind_speed     REAL,
                    wind_gust      REAL,
                    source         TEXT,
                    PRIMARY KEY (unix_timestamp, client_id),
                    FOREIGN KEY (client_id) REFERENCES clients(id)
                )
            ''')

            cursor.execute('''
                CREATE TABLE IF NOT EXISTS silver_prices (
                    unix_timestamp INTEGER NOT NULL,
                    client_id      INTEGER NOT NULL,
                    price          REAL,
                    currency       TEXT,
                    source         TEXT,
                    PRIMARY KEY (unix_timestamp, client_id),
                    FOREIGN KEY (client_id) REFERENCES clients(id)
                )
            ''')

            # ------------------------------------------------------------------
            # CAPA PLATA — predicción de generación solar
            # Calculada matemáticamente a partir de silver_weather y los
            # parámetros de la instalación del cliente (tabla clients).
            # INSERT OR REPLACE garantiza que siempre tiene la predicción
            # más actualizada para cada timestamp y cliente.
            # ------------------------------------------------------------------

            cursor.execute('''
                CREATE TABLE IF NOT EXISTS silver_solar_forecast (
                    unix_timestamp   INTEGER NOT NULL,
                    client_id        INTEGER NOT NULL,
                    forecast_time    TEXT,
                    irradiance_wm2   REAL,    -- Irradiancia estimada en plano inclinado (W/m²)
                    temperature_c    REAL,    -- Temperatura ambiente usada en el cálculo (°C)
                    cloud_factor     REAL,    -- Factor de reducción por nubosidad (0.0 - 1.0)
                    performance_ratio REAL,   -- PR ajustado por temperatura
                    predicted_power_kw REAL,  -- Potencia generada estimada (kW)
                    PRIMARY KEY (unix_timestamp, client_id),
                    FOREIGN KEY (client_id) REFERENCES clients(id)
                )
            ''')

            # ------------------------------------------------------------------
            # CAPA ORO — (placeholder para desarrollo futuro)
            # Aquí irán las decisiones energéticas y datos para visualizaciones:
            #   energy_decisions (unix_timestamp, client_id, action, reason, savings_eur)
            # ------------------------------------------------------------------

            logger.info("🗄️  Infraestructura de base de datos verificada correctamente.")

    except sqlite3.Error as e:
        logger.error(f"❌ Error al crear las tablas: {e}")



# ==============================================================================
# CAPA BRONCE — ESCRITURA Y LECTURA
# ==============================================================================

def load_client(data, table_name: str) -> None:
    """
    Guarda datos crudos de la API en la capa bronce.

    Acepta tanto un dict único (PVGIS — JSON completo) como una lista de dicts
    (OpenWeather, ESIOS — un registro por elemento).

    Parámetros:
        data       : dict o list[dict] — datos crudos a guardar.
        table_name : str — nombre de la tabla bronce (ej: 'raw_weather').
        
    """
    if not data:
        logger.warning(f"⚠️  No hay datos para guardar en {table_name}.")
        return

    try:
        with sqlite3.connect(DB_PATH) as conn:
            cursor = conn.cursor()

            if isinstance(data, dict):
                values = [ json.dumps(data)]
            elif isinstance(data, list):
                values = [json.dumps(record) for record in data]
            else:
                logger.error(f"Tipo de dato no soportado para bronce: {type(data)}")
                return

            cursor.executemany(
                f"INSERT INTO {table_name} (raw_data) VALUES ( ?)", values
            )

        logger.info(f"✅ Bronce: {len(values)} registros guardados).")

    except sqlite3.Error as e:
        logger.error(f"❌ Error al guardar en bronce ({table_name}): {e}")

        

def load_bronze(data, table_name: str, client_id: int) -> None:
    """
    Guarda datos crudos de la API en la capa bronce.

    Acepta tanto un dict único (PVGIS — JSON completo) como una lista de dicts
    (OpenWeather, ESIOS — un registro por elemento).

    Parámetros:
        data       : dict o list[dict] — datos crudos a guardar.
        table_name : str — nombre de la tabla bronce (ej: 'raw_weather').
        client_id  : int — id del cliente al que pertenecen los datos.
    """
    if not data:
        logger.warning(f"⚠️  No hay datos para guardar en {table_name}.")
        return

    try:
        with sqlite3.connect(DB_PATH) as conn:
            cursor = conn.cursor()

            if isinstance(data, dict):
                values = [(client_id, json.dumps(data))]
            elif isinstance(data, list):
                values = [(client_id, json.dumps(record)) for record in data]
            else:
                logger.error(f"Tipo de dato no soportado para bronce: {type(data)}")
                return

            cursor.executemany(
                f"INSERT INTO {table_name} (client_id, raw_data) VALUES (?, ?)", values
            )

        logger.info(f"✅ Bronce: {len(values)} registros guardados en '{table_name}' (client_id={client_id}).")

    except sqlite3.Error as e:
        logger.error(f"❌ Error al guardar en bronce ({table_name}): {e}")


def read_bronze(table_name: str, client_id: int, latest_only: bool = True):
    """
    Lee datos crudos de la capa bronce y los deserializa a objetos Python.

    Filtra por client_id y detecta automáticamente el tipo de dato:
      - 1 fila con dict  → devuelve dict       (PVGIS)
      - N filas con dict → devuelve list[dict]  (OpenWeather, ESIOS)

    Parámetros:
        table_name  : str  — nombre de la tabla bronce.
        client_id   : int  — id del cliente cuyos datos se quieren leer.
        latest_only : bool — si True, devuelve solo la última ingesta del cliente.

    Retorna:
        dict, list[dict] o None si no hay datos.
    """
    try:
        with sqlite3.connect(DB_PATH) as conn:
            cursor = conn.cursor()

            if latest_only:
                cursor.execute(f"""
                    SELECT raw_data FROM {table_name}
                    WHERE client_id = ?
                    AND ingested_at = (
                        SELECT MAX(ingested_at) FROM {table_name}
                        WHERE client_id = ?
                    )
                """, (client_id, client_id))
            else:
                cursor.execute(
                    f"SELECT raw_data FROM {table_name} WHERE client_id = ?",
                    (client_id,)
                )

            rows = cursor.fetchall()

        if not rows:
            logger.warning(f"⚠️  No hay datos en '{table_name}' para client_id={client_id}.")
            return None

        records = [json.loads(row[0]) for row in rows]

        if len(records) == 1 and isinstance(records[0], dict):
            logger.info(f"✅ Bronce: 1 registro leído de '{table_name}' (dict, client_id={client_id}).")
            return records[0]

        logger.info(f"✅ Bronce: {len(records)} registros leídos de '{table_name}' (list[dict], client_id={client_id}).")
        return records

    except sqlite3.Error as e:
        logger.error(f"❌ Error al leer de bronce ({table_name}): {e}")
        return None


# ==============================================================================
# CAPA PLATA Y ORO — ESCRITURA
# ==============================================================================

def load_to_db(data_list: list[dict], table_name: str) -> None:
    """
    Inserta una lista de registros limpios en la tabla especificada.

    Válido para cualquier capa de destino (plata, oro).
    Usa INSERT OR REPLACE — si ya existe un registro con el mismo
    PRIMARY KEY (unix_timestamp, client_id), lo sobreescribe con los
    datos más recientes. Esto garantiza que silver_weather y
    silver_solar_forecast siempre tienen la predicción más actualizada.

    Parámetros:
        data_list  : list[dict] — registros limpios a insertar (deben incluir client_id).
        table_name : str — nombre de la tabla destino.
    """
    if not data_list:
        logger.warning(f"⚠️  No hay datos para guardar en '{table_name}'.")
        return

    try:
        with sqlite3.connect(DB_PATH) as conn:
            cursor = conn.cursor()

            keys         = data_list[0].keys()
            columns      = ', '.join(keys)
            placeholders = ', '.join(['?' for _ in keys])

            sql    = f"INSERT OR REPLACE INTO {table_name} ({columns}) VALUES ({placeholders})"
            values = [tuple(d.values()) for d in data_list]

            cursor.executemany(sql, values)

        logger.info(f"✅ {len(data_list)} registros guardados en '{table_name}'.")

    except sqlite3.Error as e:
        logger.error(f"❌ Error al guardar en '{table_name}': {e}")
