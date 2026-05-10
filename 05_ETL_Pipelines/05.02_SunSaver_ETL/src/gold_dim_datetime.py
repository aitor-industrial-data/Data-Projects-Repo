import sqlalchemy
from sqlalchemy import create_engine, text
from sqlalchemy.exc import SQLAlchemyError
from datetime import datetime, timezone
from zoneinfo import ZoneInfo
from typing import Union

import config_paths
from logger_config import setup_logging

"""
GOLD LAYER: TIME DIMENSION (DATETIME)
-------------------------------------
Author: Aitor Asin
Description: Generates the Time Dimension for the analytical model. 
             Handles timezone conversions (UTC to Madrid) and 
             injects business logic for Spanish electricity tariffs.
"""

logger = setup_logging()

# Business Rules Constants
SPAIN_TZ = ZoneInfo("Europe/Madrid")
FESTIVOS_NACIONALES = {
    (1, 1), (1, 6), (5, 1), (8, 15),
    (10, 12), (11, 1), (12, 6), (12, 8), (12, 25),
}
TARIFF_LABELS = {"P1": "punta", "P2": "llano", "P3": "valle", "P6": "super-valle"}

# ─────────────────────────────────────────────────────────────────────────────
# ANALYTICAL LOGIC: ELECTRICITY TARIFFS
# ─────────────────────────────────────────────────────────────────────────────

def get_tariff_period(dt_local: datetime) -> str:
    """
    Classifies a timestamp into the 2.0TD Spanish tariff periods.
    Strategic for energy cost optimization analytics.
    """
    # Weekends and Bank Holidays are always P6 (Off-peak)
    if dt_local.weekday() >= 5 or (dt_local.month, dt_local.day) in FESTIVOS_NACIONALES:
        return "P6"
    
    h = dt_local.hour
    if 10 <= h < 14 or 18 <= h < 22:
        return "P1" # Peak
    if 8 <= h < 10 or 14 <= h < 18 or 22 <= h < 24:
        return "P2" # Mid-peak
    
    return "P3" # Flat/Valley


# ─────────────────────────────────────────────────────────────────────────────
# BUILD PROCESS
# ─────────────────────────────────────────────────────────────────────────────

def build_dim_datetime(engine: sqlalchemy.engine.Engine) -> int:
    """
    Extracts unique timestamps from Silver layer and enriches them 
    with calendar attributes and energy market segments.
    """
    logger.info("[INIT] ── Rebuilding gold_dim_datetime ──────────────────────")

    try:
        # 1. SOURCE EXTRACTION: Distinct slots from weather data
        with engine.connect() as conn:
            result = conn.execute(text("""
                SELECT unix_time, MAX(is_daylight) AS is_daylight
                FROM clean_weather
                GROUP BY unix_time
                ORDER BY unix_time
            """))
            rows = result.fetchall()

        if not rows:
            logger.warning("[EXTRACT] No data found in clean_weather")
            return 0

        # 2. TRANSFORMATION: Dimensional Enrichment
        registros = []
        for row in rows:
            # Timezone management: UTC to Local (Europe/Madrid)
            dt_utc = datetime.fromtimestamp(row.unix_time, tz=timezone.utc)
            dt_local = dt_utc.astimezone(SPAIN_TZ)
            period = get_tariff_period(dt_local)

            registros.append({
                "unix_time":      row.unix_time,
                "datetime_utc":   dt_utc.strftime("%Y-%m-%d %H:%M:%S"),
                "datetime_local": dt_local.strftime("%Y-%m-%d %H:%M:%S"),
                "date":           dt_local.strftime("%Y-%m-%d"),
                "hour_utc":       dt_utc.hour,
                "hour_local":     dt_local.hour,
                "day_of_week":    dt_local.strftime("%A").lower(),
                "is_daylight":    row.is_daylight,
                "is_weekend":     1 if dt_local.weekday() >= 5 else 0,
                "is_festivo":     1 if (dt_local.month, dt_local.day) in FESTIVOS_NACIONALES else 0,
                "month":          dt_local.month,
                "year":           dt_local.year,
                "tariff_period":  period,
                "tariff_label":   TARIFF_LABELS[period],
            })

        # 3. ATOMIC LOAD
        with engine.begin() as conn:
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
            
            conn.execute(text("""
                INSERT INTO gold_dim_datetime VALUES (
                    :unix_time, :datetime_utc, :datetime_local, :date, :hour_utc,
                    :hour_local, :day_of_week, :is_daylight, :is_weekend,
                    :is_festivo, :month, :year, :tariff_period, :tariff_label
                )
            """), registros)

        logger.info("[DONE] gold_dim_datetime refreshed — Records: %d", len(registros))
        return len(registros)

    except SQLAlchemyError as exc:
        logger.error("[ERROR] SQL Integrity failure: %s", exc)
        raise
    except Exception as exc:
        logger.error("[ERROR] Transformation logic failure: %s", exc)
        raise


def load_dim_datetime() -> Union[int, bool]:
    """Orchestrator entry point for the datetime dimension."""
    try:
        db_path = config_paths.get_db_path()
        engine = create_engine(f"sqlite:///{db_path}")
        return build_dim_datetime(engine)
    except Exception as exc:
        logger.critical("[ERROR] Critical failure in load_dim_datetime: %s", exc)
        return False


if __name__ == "__main__":
    load_dim_datetime()