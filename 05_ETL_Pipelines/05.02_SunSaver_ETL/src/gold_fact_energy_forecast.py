import sqlalchemy
from sqlalchemy import create_engine, text
from sqlalchemy.exc import SQLAlchemyError
from datetime import datetime, timezone
from typing import Union

import config_paths
from logger_config import setup_logging

"""
GOLD LAYER: FACT TABLE (ENERGY FORECAST)
----------------------------------------
Author: Aitor Asin
Description: The "Heart" of the analytical model. Joins calculations, 
             weather, and prices into a single, high-performance table.
             Implements an incremental 'Upsert' strategy with a 2-hour window.
"""

logger = setup_logging()

# ─────────────────────────────────────────────────────────────────────────────
# DATA ORCHESTRATION: FACT TABLE UPSERT
# ─────────────────────────────────────────────────────────────────────────────

def build_fact_energy_forecast(engine: sqlalchemy.engine.Engine) -> int:
    """
    Consolidates energy metrics, weather conditions, and market prices.
    Uses 'INSERT OR REPLACE' to maintain an idempotent pipeline.
    """
    logger.info("[INIT] ── Rebuilding gold_fact_energy_forecast ──────────────")

    # Incremental window: We process from 2 hours ago to the future
    buffer_seconds = 7200
    start_unix = int(datetime.now(timezone.utc).timestamp()) - buffer_seconds

    logger.info("[EXTRACT] Processing window: unix_time >= %d", start_unix)

    try:
        with engine.begin() as conn:
            # 1. DDL: SCHEMA DEFINITION
            # Client_id and unix_time form the composite primary key
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

            # 2. DML: CONSOLIDATED JOIN (Calculations + Weather + Prices)
            # We use LEFT JOINs to ensure we don't lose records if weather/price 
            # is missing for a specific slot.
            query = text("""
                INSERT OR REPLACE INTO gold_fact_energy_forecast
                SELECT
                    calc.client_id,
                    calc.unix_time,
                    calc.forecast_time_utc,
                    calc.pv_power_gen_kw,
                    calc.pv_performance_ratio,
                    calc.poa_wm2,
                    calc.t_cell_celsius,
                    calc.power_con_kw,
                    w.temp_celsius,
                    w.humidity_pct,
                    w.clouds_pct,
                    w.rain_prob_norm,
                    w.wind_speed_mps,
                    w.weather_id,
                    pvpc.price_euro_mwh             AS price_pvpc_eur_mwh,
                    STRFTIME('%Y-%m-%d %H:%M:%S', 'now') AS _loaded_at_utc
                FROM clean_calculations calc
                LEFT JOIN clean_weather w
                    ON  w.client_id = calc.client_id
                    AND w.unix_time = calc.unix_time
                LEFT JOIN clean_prices pvpc
                    ON  pvpc.unix_time  = calc.unix_time
                    AND pvpc.price_type = 'PVPC'
                WHERE calc.unix_time >= :start_unix
            """)
            
            result = conn.execute(query, {"start_unix": start_unix})
            rows_affected = result.rowcount

            # 3. PERFORMANCE: IDEMPOTENT INDEXING
            # Crucial for fast filtering in Dashboards/PowerBI
            conn.execute(text(
                "CREATE INDEX IF NOT EXISTS idx_gold_fact_unix_time  "
                "ON gold_fact_energy_forecast (unix_time)"
            ))
            conn.execute(text(
                "CREATE INDEX IF NOT EXISTS idx_gold_fact_weather_id "
                "ON gold_fact_energy_forecast (weather_id)"
            ))

        logger.info("[DONE] Upsert complete — Rows affected: %d", rows_affected)
        return rows_affected

    except SQLAlchemyError as exc:
        logger.error("[ERROR] SQL Execution failure: %s", exc)
        raise
    except Exception as exc:
        logger.error("[ERROR] Unexpected error in fact table build: %s", exc)
        raise


# ─────────────────────────────────────────────────────────────────────────────
# ENTRY POINT
# ─────────────────────────────────────────────────────────────────────────────

def load_fact_energy_forecast() -> Union[int, bool]:
    """
    Main entry point for the fact table loader.
    Ensures the DB engine is configured for modern SQLite features.
    """
    try:
        db_path = config_paths.get_db_path()
        engine = create_engine(f"sqlite:///{db_path}")
        return build_fact_energy_forecast(engine)
    except Exception as exc:
        logger.critical("[ERROR] Fact table orchestrator failure: %s", exc)
        return False


if __name__ == "__main__":
    load_fact_energy_forecast()