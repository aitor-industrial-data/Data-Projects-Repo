import sqlalchemy
from sqlalchemy import create_engine, text
from sqlalchemy.exc import SQLAlchemyError

import workspace_manager
from logger_config import setup_logging


logger  = setup_logging()
DB_PATH = workspace_manager.get_db_path()


# ─────────────────────────────────────────────────────────────────────────────
# BUILD
# ─────────────────────────────────────────────────────────────────────────────

def build_dim_weather(engine: sqlalchemy.engine.Engine) -> int:
    """
    Generates gold_dim_weather as a type-2 weather condition dimension,
    using a ROW_NUMBER window function to resolve duplicate weather_id entries
    by selecting the most frequently observed (main, description) pair.
    Returns the number of rows inserted.
    """
    logger.info("[INIT] ── build_dim_weather starting ───────────────────────")

    try:
        with engine.begin() as conn:
            conn.execute(text("DROP TABLE IF EXISTS gold_dim_weather"))
            conn.execute(text("""
                CREATE TABLE gold_dim_weather (
                    weather_id          INTEGER NOT NULL PRIMARY KEY,
                    weather_main        TEXT    NOT NULL,
                    weather_description TEXT    NOT NULL,
                    _loaded_at_utc      TEXT    NOT NULL
                )
            """))

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

        logger.info("[DONE] gold_dim_weather rebuilt — rows inserted: %d", total)
        return total

    except SQLAlchemyError as exc:
        logger.error("[ERROR] SQLAlchemy error in build_dim_weather: %s", exc)
        raise
    except Exception as exc:
        logger.error("[ERROR] Unexpected error in build_dim_weather: %s", exc)
        raise


# ─────────────────────────────────────────────────────────────────────────────
# ORCHESTRATOR ENTRY POINT
# ─────────────────────────────────────────────────────────────────────────────

def load_dim_weather() -> int:
    """Module entry point. Returns the number of rows written (0 on failure)."""
    try:
        engine = create_engine(f"sqlite:///{DB_PATH}")
        return build_dim_weather(engine)
    except Exception as exc:
        logger.critical("[ERROR] Critical failure in load_dim_weather: %s", exc)
        return 0


# ─────────────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    load_dim_weather()
