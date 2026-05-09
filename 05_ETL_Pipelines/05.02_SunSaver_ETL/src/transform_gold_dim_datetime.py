import sqlite3
from datetime import datetime, timezone
from zoneinfo import ZoneInfo
import workspace_manager
from logger_config import setup_logging


logger = setup_logging()

DB_PATH = workspace_manager.get_db_path()
SPAIN_TZ = ZoneInfo("Europe/Madrid")

FESTIVOS_NACIONALES = {
    (1,  1),  # Año Nuevo
    (1,  6),  # Reyes
    (5,  1),  # Día del Trabajo
    (8,  15), # Asunción
    (10, 12), # Fiesta Nacional
    (11, 1),  # Todos los Santos
    (12, 6),  # Día de la Constitución
    (12, 8),  # Inmaculada
    (12, 25), # Navidad
}

TARIFF_LABELS = {
    "P1": "punta",
    "P2": "llano",
    "P3": "valle",
    "P6": "super-valle",
}


def get_tariff_period(dt_local: datetime) -> str:
    """
    Devuelve el periodo tarifario (P1/P2/P3/P6) para un datetime en hora local española.
    """
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


def build_dim_datetime(conn: sqlite3.Connection) -> None:
    """
    Genera gold_dim_datetime a partir de los unix_time de clean_weather.
    """
    try:
        logger.info("Generando gold_dim_datetime a partir de clean_weather...")
        
        # 1. Extracción de datos únicos
        rows = conn.execute("""
            SELECT unix_time, MAX(is_daylight) as is_daylight 
            FROM clean_weather 
            GROUP BY unix_time 
            ORDER BY unix_time
            """
        ).fetchall()

        if not rows:
            logger.warning("clean_weather está vacía — no se generó gold_dim_datetime")
            return

        # 2. Transformación
        registros = []
        for (unix_time, is_daylight) in rows:
            dt_utc   = datetime.fromtimestamp(unix_time, tz=timezone.utc)
            dt_local = dt_utc.astimezone(SPAIN_TZ)
            tariff_period = get_tariff_period(dt_local)

            registros.append((
                unix_time,
                dt_utc.strftime("%Y-%m-%d %H:%M:%S"),
                dt_local.strftime("%Y-%m-%d %H:%M:%S"),
                dt_utc.strftime("%Y-%m-%d"),
                dt_utc.hour,
                dt_local.hour,
                dt_local.strftime("%A").lower(),
                is_daylight,
                1 if dt_local.weekday() >= 5 else 0,
                1 if (dt_local.month, dt_local.day) in FESTIVOS_NACIONALES else 0,
                dt_local.month,
                dt_local.year,
                tariff_period,
                TARIFF_LABELS[tariff_period],
            ))

        # 3. Carga (Atomic Transaction)
        conn.execute("DROP TABLE IF EXISTS gold_dim_datetime")
        conn.execute("""
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
        """)

        conn.executemany(
            "INSERT INTO gold_dim_datetime VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
            registros,
        )
        conn.commit()
        logger.info(f"✅ gold_dim_datetime generada: {len(registros)} filas insertadas")

    except sqlite3.Error as e:
        logger.error(f"❌ Error de base de datos en build_dim_datetime: {e}")
        conn.rollback()
        raise
    except Exception as e:
        logger.error(f"❌ Error inesperado procesando fechas: {e}")
        raise


def load_dim_datetime() -> None:
    """Maneja el ciclo de vida de la conexión."""
    try:
        with sqlite3.connect(DB_PATH) as conn:
            build_dim_datetime(conn)
    except Exception as e:
        logger.critical(f"Fallo crítico en el cargador de dimensiones temporales: {e}")


if __name__ == "__main__":
    load_dim_datetime()