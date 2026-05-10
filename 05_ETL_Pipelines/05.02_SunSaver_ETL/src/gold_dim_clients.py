import sqlalchemy
from sqlalchemy import create_engine, text
from sqlalchemy.exc import SQLAlchemyError
from typing import Union

import config_paths
from logger_config import setup_logging

"""
GOLD LAYER: DIMENSION MODELING (CLIENTS)
----------------------------------------
Author: Aitor Asin
Description: Rebuilds the Gold-level client dimension. Implements business 
             logic for derived features (flags) and ensures schema 
             integrity for analytical downstream consumers.
"""

logger = setup_logging()

# ─────────────────────────────────────────────────────────────────────────────
# BUSINESS LOGIC: DIMENSION REBUILD
# ─────────────────────────────────────────────────────────────────────────────

def build_dim_client(engine: sqlalchemy.engine.Engine) -> int:
    """
    Transforms Silver data (clean_clients) into Gold (gold_dim_client).
    Derives analytical flags: 'has_solar' and 'has_battery'.
    """
    logger.info("[INIT] ── Rebuilding gold_dim_client ────────────────────────")

    try:
        # 1. EXTRACTION FROM SILVER LAYER
        with engine.connect() as conn:
            result = conn.execute(text("SELECT * FROM clean_clients ORDER BY client_id"))
            rows = result.fetchall()

        if not rows:
            logger.warning("[EXTRACT] clean_clients is empty — Nothing to process")
            return 0

        logger.info("[EXTRACT] %d client(s) loaded for transformation", len(rows))

        # 2. TRANSFORMATION: Logic & Feature Derivation
        # We use dictionary comprehension for cleaner mapping
        registros = []
        for r in rows:
            data = dict(r._mapping)
            # Add business logic flags
            data["has_solar"] = 1 if (data.get("pv_peak_power_kw") or 0) > 0 else 0
            data["has_battery"] = 1 if (data.get("battery_capacity_kwh") or 0) > 0 else 0
            registros.append(data)

        logger.info("[TRANSFORM] Business logic applied (Solar/Battery flags)")

        # 3. ATOMIC LOAD (Gold Layer)
        # We wrap in a transaction (engine.begin) to ensure consistency
        with engine.begin() as conn:
            # Recreate table with explicit schema
            conn.execute(text("DROP TABLE IF EXISTS gold_dim_client"))
            conn.execute(text("""
                CREATE TABLE gold_dim_client (
                    client_id               TEXT    PRIMARY KEY,
                    name                    TEXT    NOT NULL,
                    description             TEXT,
                    latitude                REAL    NOT NULL,
                    longitude               REAL    NOT NULL,
                    timezone                TEXT    NOT NULL,
                    nominal_load_kw         REAL    NOT NULL,
                    pv_peak_power_kw        REAL    NOT NULL,
                    panel_area_m2           REAL    NOT NULL,
                    efficiency              REAL    NOT NULL,
                    panel_type              TEXT    NOT NULL,
                    loss_pct                REAL    NOT NULL,
                    angle                   REAL    NOT NULL,
                    aspect                  REAL    NOT NULL,
                    mounting                TEXT    NOT NULL,
                    battery_capacity_kwh    REAL    NOT NULL,
                    soc_min_pct             REAL    NOT NULL,
                    installation_cost_eur   REAL    NOT NULL,
                    has_solar               INTEGER NOT NULL,
                    has_battery             INTEGER NOT NULL
                )
            """))

            # Bulk Insert using bound parameters (Safe from SQL Injection)
            conn.execute(text("""
                INSERT INTO gold_dim_client (
                    client_id, name, description, latitude, longitude, timezone,
                    nominal_load_kw, pv_peak_power_kw, panel_area_m2,
                    efficiency, panel_type, loss_pct, angle, aspect, mounting,
                    battery_capacity_kwh, soc_min_pct, installation_cost_eur,
                    has_solar, has_battery
                ) VALUES (
                    :client_id, :name, :description, :latitude, :longitude, :timezone,
                    :nominal_load_kw, :pv_peak_power_kw, :panel_area_m2,
                    :efficiency, :panel_type, :loss_pct, :angle, :aspect, :mounting,
                    :battery_capacity_kwh, :soc_min_pct, :installation_cost_eur,
                    :has_solar, :has_battery
                )
            """), registros)

        total = len(registros)
        logger.info("[DONE] gold_dim_client refreshed — Total records: %d", total)
        return total

    except SQLAlchemyError as exc:
        logger.error("[ERROR] SQLAlchemy integrity failure: %s", exc)
        raise
    except Exception as exc:
        logger.error("[ERROR] Unexpected transformation error: %s", exc)
        raise


# ─────────────────────────────────────────────────────────────────────────────
# ORCHESTRATOR ENTRY POINT
# ─────────────────────────────────────────────────────────────────────────────

def load_dim_client() -> Union[int, bool]:
    """
    Module entry point for the orchestrator.
    """
    try:
        db_path = config_paths.get_db_path()
        engine = create_engine(f"sqlite:///{db_path}")
        return build_dim_client(engine)
    except Exception as exc:
        logger.critical("[ERROR] Dimension build failed: %s", exc)
        return False


if __name__ == "__main__":
    load_dim_client()