import sqlalchemy
from sqlalchemy import create_engine, text
from sqlalchemy.exc import SQLAlchemyError
from datetime import datetime, timezone

import workspace_manager
from logger_config import setup_logging


logger  = setup_logging()
DB_PATH = workspace_manager.get_db_path()


# ─────────────────────────────────────────────────────────────────────────────
# BUILD
# ─────────────────────────────────────────────────────────────────────────────

def build_fact_energy_forecast(engine: sqlalchemy.engine.Engine) -> int:
    """
    Incrementally upserts the Gold fact table by joining the active forecast
    window (unix_time >= now - 2h) from clean_calculations with clean_weather
    and clean_prices.  Returns the number of rows affected.
    """
    logger.info("[INIT] ── build_fact_energy_forecast starting ──────────────")

    buffer_seconds = 7200
    start_unix     = int(datetime.now(timezone.utc).timestamp()) - buffer_seconds

    logger.info("[EXTRACT] Active window lower bound: unix_time >= %d (now - %ds)", start_unix, buffer_seconds)

    try:
        with engine.begin() as conn:
            # Ensure table exists with full schema
            conn.execute(text("""
                CREATE TABLE IF NOT EXISTS gold_fact_energy_forecast (
                    client_id               TEXT    NOT NULL,
                    unix_time               INTEGER NOT NULL,
                    forecast_time_utc       TEXT    NOT NULL,
                    pv_power_gen_kw         REAL,
                    pv_performance_ratio    REAL,
                    poa_wm2                 REAL,
                    t_cell_celsius          REAL,
                    power_consumption_kw    REAL,
                    temp_celsius            REAL,
                    humidity_pct            REAL,
                    clouds_pct              REAL,
                    rain_prob_norm          REAL,
                    wind_speed_mps          REAL,
                    weather_id              INTEGER,
                    price_pvpc_eur_mwh      REAL,
                    _loaded_at_utc          TEXT    NOT NULL,
                    PRIMARY KEY (client_id, unix_time)
                )
            """))

            result = conn.execute(text("""
                INSERT OR REPLACE INTO gold_fact_energy_forecast
                SELECT
                    c.client_id,
                    c.unix_time,
                    c.forecast_time_utc,
                    c.pv_power_gen_kw,
                    c.pv_performance_ratio,
                    c.poa_wm2,
                    c.t_cell_celsius,
                    c.power_con_kw,
                    w.temp_celsius,
                    w.humidity_pct,
                    w.clouds_pct,
                    w.rain_prob_norm,
                    w.wind_speed_mps,
                    w.weather_id,
                    pvpc.price_euro_mwh             AS price_pvpc_eur_mwh,
                    STRFTIME('%Y-%m-%d %H:%M:%S', 'now') AS _loaded_at_utc
                FROM clean_calculations c
                LEFT JOIN clean_weather w
                    ON  w.client_id = c.client_id
                    AND w.unix_time = c.unix_time
                LEFT JOIN clean_prices pvpc
                    ON  pvpc.unix_time  = c.unix_time
                    AND pvpc.price_type = 'PVPC'
                WHERE c.unix_time >= :start_unix
            """), {"start_unix": start_unix})

            rows_affected = result.rowcount

            # Optimisation indexes — idempotent
            conn.execute(text(
                "CREATE INDEX IF NOT EXISTS idx_gold_fact_unix_time  "
                "ON gold_fact_energy_forecast (unix_time)"
            ))
            conn.execute(text(
                "CREATE INDEX IF NOT EXISTS idx_gold_fact_weather_id "
                "ON gold_fact_energy_forecast (weather_id)"
            ))

        logger.info(
            "[DONE] gold_fact_energy_forecast updated — rows upserted: %d (window start: %d)",
            rows_affected, start_unix,
        )
        return rows_affected

    except SQLAlchemyError as exc:
        logger.error("[ERROR] SQLAlchemy error in build_fact_energy_forecast: %s", exc)
        raise
    except Exception as exc:
        logger.error("[ERROR] Unexpected error in build_fact_energy_forecast: %s", exc)
        raise


# ─────────────────────────────────────────────────────────────────────────────
# ORCHESTRATOR ENTRY POINT
# ─────────────────────────────────────────────────────────────────────────────

def load_fact_energy_forecast() -> int:
    """Module entry point. Returns the number of rows upserted (0 on failure)."""
    try:
        engine = create_engine(f"sqlite:///{DB_PATH}")
        with engine.connect() as conn:
            conn.execute(text("PRAGMA foreign_keys = ON"))
        return build_fact_energy_forecast(engine)
    except Exception as exc:
        logger.critical("[ERROR] Critical failure in load_fact_energy_forecast: %s", exc)
        return 0


# ─────────────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    load_fact_energy_forecast()
