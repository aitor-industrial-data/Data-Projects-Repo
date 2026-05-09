import sqlalchemy
from sqlalchemy import create_engine, text
from sqlalchemy.exc import SQLAlchemyError
from datetime import datetime, timezone
from zoneinfo import ZoneInfo
import workspace_manager
from logger_config import setup_logging

# Configuración de logs y base de datos
logger = setup_logging()
DB_PATH = workspace_manager.get_db_path()
SPAIN_TZ = ZoneInfo("Europe/Madrid")

# Constantes de negocio
FESTIVOS_NACIONALES = {
    (1,  1), (1,  6), (5,  1), (8,  15), 
    (10, 12), (11, 1), (12, 6), (12, 8), (12, 25)
}

TARIFF_LABELS = {
    "P1": "punta",
    "P2": "llano",
    "P3": "valle",
    "P6": "super-valle",
}

def get_tariff_period(dt_local: datetime) -> str:
    """Devuelve el periodo tarifario (P1/P2/P3/P6) según normativa española."""
    is_weekend = dt_local.weekday() >= 5
    is_festivo = (dt_local.month, dt_local.day) in FESTIVOS_NACIONALES

    if is_weekend or is_festivo:
        return "P6"

    h = dt_local.hour
    if 10 <= h < 14 or 18 <= h < 22:
        return "P1"
    elif 8 <= h < 10 or 14 <= h < 18 or 22 <= h < 24:
        return "P2"
    else:
        return "P3"

def build_dim_datetime(engine: sqlalchemy.engine.Engine) -> int:
    """
    Genera gold_dim_datetime a partir de los datos de clean_weather usando SQLAlchemy.
    Retorna el número de filas insertadas.
    """
    try:
        logger.info("Generando gold_dim_datetime a partir de clean_weather (SQLAlchemy)...")
        
        with engine.begin() as conn:
            # 1. Extracción de datos únicos
            query_select = text("""
                SELECT unix_time, MAX(is_daylight) as is_daylight 
                FROM clean_weather 
                GROUP BY unix_time 
                ORDER BY unix_time
            """)
            
            result = conn.execute(query_select)
            rows = result.fetchall()

            if not rows:
                logger.warning("clean_weather está vacía — no se generó gold_dim_datetime")
                return 0

            # 2. Transformación a lista de diccionarios (Formato óptimo para SQLAlchemy)
            registros = []
            for row in rows:
                dt_utc   = datetime.fromtimestamp(row.unix_time, tz=timezone.utc)
                dt_local = dt_utc.astimezone(SPAIN_TZ)
                tariff_period = get_tariff_period(dt_local)

                registros.append({
                    "unix_time":      row.unix_time,
                    "datetime_utc":   dt_utc.strftime("%Y-%m-%d %H:%M:%S"),
                    "datetime_local": dt_local.strftime("%Y-%m-%d %H:%M:%S"),
                    "date":           dt_utc.strftime("%Y-%m-%d"),
                    "hour_utc":       dt_utc.hour,
                    "hour_local":     dt_local.hour,
                    "day_of_week":    dt_local.strftime("%A").lower(),
                    "is_daylight":    row.is_daylight,
                    "is_weekend":     1 if dt_local.weekday() >= 5 else 0,
                    "is_festivo":     1 if (dt_local.month, dt_local.day) in FESTIVOS_NACIONALES else 0,
                    "month":          dt_local.month,
                    "year":           dt_local.year,
                    "tariff_period":  tariff_period,
                    "tariff_label":   TARIFF_LABELS[tariff_period]
                })

            # 3. Preparación de la tabla Gold
            conn.execute(text("DROP TABLE IF EXISTS gold_dim_datetime"))
            conn.execute(text("""
                CREATE TABLE gold_dim_datetime (
                    unix_time        INTEGER PRIMARY KEY,
                    datetime_utc     TEXT    NOT NULL,
                    datetime_local   TEXT    NOT NULL,
                    date             TEXT    NOT NULL,
                    hour_utc         INTEGER NOT NULL,
                    hour_local       INTEGER NOT NULL,
                    day_of_week      TEXT    NOT NULL,
                    is_daylight      INTEGER NOT NULL,
                    is_weekend       INTEGER NOT NULL,
                    is_festivo       INTEGER NOT NULL,
                    month            INTEGER NOT NULL,
                    year             INTEGER NOT NULL,
                    tariff_period    TEXT    NOT NULL,
                    tariff_label     TEXT    NOT NULL
                )
            """))

            # 4. Inserción masiva
            insert_query = text("""
                INSERT INTO gold_dim_datetime VALUES (
                    :unix_time, :datetime_utc, :datetime_local, :date, :hour_utc, 
                    :hour_local, :day_of_week, :is_daylight, :is_weekend, 
                    :is_festivo, :month, :year, :tariff_period, :tariff_label
                )
            """)
            
            conn.execute(insert_query, registros)
            
            total_filas = len(registros)
            logger.info(f"✅ gold_dim_datetime generada: {total_filas} filas insertadas")
            logger.info(f"Datos totales procesados: {total_filas}")
            return total_filas

    except SQLAlchemyError as e:
        logger.error(f"❌ Error de base de datos en build_dim_datetime: {e}")
        raise
    except Exception as e:
        logger.error(f"❌ Error inesperado procesando fechas: {e}")
        raise

def load_dim_datetime() -> int:
    """Maneja el ciclo de vida del motor de base de datos."""
    try:
        engine = create_engine(f"sqlite:///{DB_PATH}")
        return build_dim_datetime(engine)
    except Exception as e:
        logger.critical(f"Fallo crítico en el cargador de dimensiones temporales: {e}")
        return 0

if __name__ == "__main__":
    load_dim_datetime()