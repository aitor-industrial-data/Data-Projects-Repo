import sqlalchemy
from sqlalchemy import create_engine, text
from sqlalchemy.exc import SQLAlchemyError
from typing import Union

import config_paths
from logger_config import setup_logging

"""
GOLD LAYER: WEATHER DIMENSION
-----------------------------
Author: Aitor Asin
Description: Normalizes weather conditions into a canonical dimension table.
             Uses Window Functions (ROW_NUMBER) to resolve many-to-one 
             mappings between IDs and descriptions in raw weather data.
"""

logger = setup_logging()

# ─────────────────────────────────────────────────────────────────────────────
# BUILD PROCESS: DATA DENORMALIZATION & CLEANUP
# ─────────────────────────────────────────────────────────────────────────────

def build_dim_weather(engine: sqlalchemy.engine.Engine) -> int:
    """
    Generates gold_dim_weather. 
    Implements a 'Most Frequent Wins' logic to ensure each weather_id 
    has exactly one canonical description.
    """
    logger.info("[INIT] ── Rebuilding gold_dim_weather ───────────────────────")

    try:
        # We use a single transaction block for the entire DDL/DML sequence
        with engine.begin() as conn:
            # 1. SCHEMA DEFINITION
            conn.execute(text("DROP TABLE IF EXISTS gold_dim_weather"))
            conn.execute(text("""
                CREATE TABLE gold_dim_weather (
                    weather_id          INTEGER NOT NULL PRIMARY KEY,
                    weather_main        TEXT    NOT NULL,
                    weather_description TEXT    NOT NULL,
                    _loaded_at_utc      TEXT    NOT NULL
                )
            """))

            # 2. TRANSFORMATION & LOAD
            # The CTE/Subquery resolves cases where an ID has multiple descriptions
            # selecting the most frequent one (Mode) per ID.
            conn.execute(text("""
                INSERT INTO gold_dim_weather
                SELECT
                    weather_id,
                    weather_main,
                    weather_description,
                    STRFTIME('%Y-%m-%d %H:%M:%S', 'now') AS _loaded_at_utc
                FROM (
                    SELECT
                        weather_id,
                        weather_main,
                        weather_description,
                        COUNT(*) AS freq,
                        ROW_NUMBER() OVER (
                            PARTITION BY weather_id
                            ORDER BY COUNT(*) DESC
                        ) AS rn
                    FROM clean_weather
                    WHERE weather_id IS NOT NULL
                    GROUP BY weather_id, weather_main, weather_description
                )
                WHERE rn = 1
            """))

            total = conn.execute(text("SELECT COUNT(*) FROM gold_dim_weather")).scalar()

        logger.info("[DONE] gold_dim_weather refreshed — Unique conditions: %d", total)
        return total

    except SQLAlchemyError as exc:
        logger.error("[ERROR] SQL Execution failure: %s", exc)
        raise
    except Exception as exc:
        logger.error("[ERROR] Unexpected error in weather dimension build: %s", exc)
        raise


# ─────────────────────────────────────────────────────────────────────────────
# ORCHESTRATOR ENTRY POINT
# ─────────────────────────────────────────────────────────────────────────────

def load_dim_weather() -> Union[int, bool]:
    """
    Entry point for the ETL pipeline. 
    Ensures the weather dimension is ready for fact-table joins.
    """
    try:
        db_path = config_paths.get_db_path()
        engine = create_engine(f"sqlite:///{db_path}")
        return build_dim_weather(engine)
    except Exception as exc:
        logger.critical("[ERROR] Critical failure in load_dim_weather: %s", exc)
        return False


if __name__ == "__main__":
    load_dim_weather()