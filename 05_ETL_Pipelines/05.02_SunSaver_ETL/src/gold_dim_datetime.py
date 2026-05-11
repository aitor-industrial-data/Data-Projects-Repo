import sqlalchemy
from sqlalchemy import create_engine, text
from sqlalchemy.exc import SQLAlchemyError
from datetime import datetime, timezone
from zoneinfo import ZoneInfo

import config_paths
from logger_config import setup_logging


logger  = setup_logging()
DB_PATH = config_paths.get_db_path()

SPAIN_TZ = ZoneInfo("Europe/Madrid")

FESTIVOS_NACIONALES = {
    (1,  1), (1,  6), (5,  1), (8, 15),
    (10, 12), (11, 1), (12, 6), (12, 8), (12, 25),
}

TARIFF_LABELS = {"P1": "punta", "P2": "llano", "P3": "valle", "P6": "super-valle"}


# ─────────────────────────────────────────────────────────────────────────────
# BUSINESS LOGIC
# ─────────────────────────────────────────────────────────────────────────────

def get_tariff_period(dt_local: datetime) -> str:
    """Returns the Spanish electricity tariff period (P1/P2/P3/P6) for a local datetime."""
    if dt_local.weekday() >= 5 or (dt_local.month, dt_local.day) in FESTIVOS_NACIONALES:
        return "P6"
    h = dt_local.hour
    if 10 <= h < 14 or 18 <= h < 22:
        return "P1"
    if 8 <= h < 10 or 14 <= h < 18 or 22 <= h < 24:
        return "P2"
    return "P3"


# ─────────────────────────────────────────────────────────────────────────────
# BUILD
# ─────────────────────────────────────────────────────────────────────────────

def build_dim_datetime(engine: sqlalchemy.engine.Engine) -> int:
    """
    Generates gold_dim_datetime from the distinct unix_time values in
    clean_weather, enriching each slot with calendar and tariff attributes.
    Returns the number of rows inserted.
    """
    logger.info("[INIT] ── build_dim_datetime starting ──────────────────────")

    try:
        with engine.begin() as conn:
            rows = conn.execute(text("""
                SELECT unix_time, MAX(is_daylight) AS is_daylight
                FROM clean_weather
                GROUP BY unix_time
                ORDER BY unix_time
            """)).fetchall()

        if not rows:
            logger.warning("[EXTRACT] clean_weather is empty — gold_dim_datetime not generated")
            return 0

        logger.info("[EXTRACT] %d distinct unix_time slot(s) read from clean_weather", len(rows))

        registros = []
        for row in rows:
            dt_utc   = datetime.fromtimestamp(row.unix_time, tz=timezone.utc)
            dt_local = dt_utc.astimezone(SPAIN_TZ)
            period   = get_tariff_period(dt_local)

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
                "tariff_period":  period,
                "tariff_label":   TARIFF_LABELS[period],
            })

        logger.info("[TRANSFORM] Calendar and tariff attributes derived for %d slot(s)", len(registros))

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

        total = len(registros)
        logger.info("[DONE] gold_dim_datetime rebuilt — rows inserted: %d", total)
        return total

    except SQLAlchemyError as exc:
        logger.error("[ERROR] SQLAlchemy error in build_dim_datetime: %s", exc)
        raise
    except Exception as exc:
        logger.error("[ERROR] Unexpected error processing datetime dimension: %s", exc)
        raise


# ─────────────────────────────────────────────────────────────────────────────
# ORCHESTRATOR ENTRY POINT
# ─────────────────────────────────────────────────────────────────────────────

def load_dim_datetime() -> int:
    """Module entry point. Returns the number of rows written (0 on failure)."""
    try:
        engine = create_engine(f"sqlite:///{DB_PATH}")
        return build_dim_datetime(engine)
    except Exception as exc:
        logger.critical("[ERROR] Critical failure in load_dim_datetime: %s", exc)
        return 0


# ─────────────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    load_dim_datetime()
