import sqlite3
import logging
from datetime import datetime, timezone
from zoneinfo import ZoneInfo
import db_manager

logger = logging.getLogger(__name__)

DB_PATH = db_manager.get_db_path()
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
    Aplica la estructura de la tarifa 2.0TD de REE vigente desde junio 2021.
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
    Genera gold_dim_datetime a partir de los unix_time únicos que existen en
    clean_openweather. Así la dimensión cubre exactamente los slots temporales
    que tienen datos reales (granularidad 3h), sin generar filas vacías.

    La PK es el propio unix_time, lo que facilita el JOIN directo desde
    clean_openweather y desde la futura fact_energy_forecast.
    """
    logger.info("Generando gold_dim_datetime a partir de clean_openweather...")

    rows = conn.execute(
        "SELECT DISTINCT unix_time FROM clean_weather ORDER BY unix_time"
    ).fetchall()

    if not rows:
        logger.warning("clean_weather está vacía — no se generó gold_dim_datetime")
        return

    registros = []

    for (unix_time,) in rows:
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
            1 if dt_local.weekday() >= 5 else 0,
            1 if (dt_local.month, dt_local.day) in FESTIVOS_NACIONALES else 0,
            dt_local.month,
            dt_local.year,
            tariff_period,
            TARIFF_LABELS[tariff_period],
        ))

    conn.execute("DROP TABLE IF EXISTS gold_dim_datetime")
    conn.execute("""
        CREATE TABLE gold_dim_datetime (
            datetime_id      INTEGER PRIMARY KEY,
            datetime_utc     TEXT    NOT NULL,
            datetime_local   TEXT    NOT NULL,
            date             TEXT    NOT NULL,
            hour_utc         INTEGER NOT NULL,
            hour_local       INTEGER NOT NULL,
            day_of_week      TEXT    NOT NULL,
            is_weekend       INTEGER NOT NULL,
            is_festivo       INTEGER NOT NULL,
            month            INTEGER NOT NULL,
            year             INTEGER NOT NULL,
            tariff_period    TEXT    NOT NULL,
            tariff_label     TEXT    NOT NULL
        )
    """)

    conn.executemany(
        "INSERT INTO gold_dim_datetime VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)",
        registros,
    )
    conn.commit()

    logger.info(f"✅ gold_dim_datetime generada: {len(registros)} filas insertadas")


def load_dim_datetime() -> None:
    with sqlite3.connect(DB_PATH) as conn:
        build_dim_datetime(conn)


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
    load_dim_datetime()