import pandas as pd
from datetime import datetime, timezone
from sqlalchemy import create_engine, text

import config_paths
import engine_pv_physics as pvgen
from logger_config import setup_logging

"""
SILVER LAYER: ENERGY SIMULATION ORCHESTRATOR
--------------------------------------------
Author: Aitor Asin
Description: Merges cleaned client and weather data to execute a high-fidelity 
             PV physics engine. Produces solar generation and industrial 
             consumption forecasts at scale.
"""

logger = setup_logging()

# ─────────────────────────────────────────────────────────────────────────────
# STEP 1: EXTRACT (Silver-to-Silver Join)
# ─────────────────────────────────────────────────────────────────────────────


def get_merged_silver_data(table_1: str = "clean_clients", table_2: str = "clean_weather") -> pd.DataFrame:
    """
    Performs a relational join between metadata and weather forecasts using SQLAlchemy.
    Filters for active windows only (unix_time >= now).
    """
    db_path  = config_paths.get_db_path()
    now_unix = int(datetime.now(timezone.utc).timestamp())
    

    engine = create_engine(f"sqlite:///{db_path}")

    logger.info("[EXTRACT] Merging Silver layers for active window (t >= %d)", now_unix)

    try:
        with engine.connect() as conn:
            query = f"""
            SELECT c.*, w.unix_time, w.forecast_time_utc, w.temp_celsius, w.humidity_pct,
                   w.clouds_pct, w.rain_prob_norm, w.wind_speed_mps, w.weather_id,
                   w.weather_main, w.weather_description, w.is_daylight
            FROM {table_1} AS c
            INNER JOIN {table_2} AS w ON c.client_id = w.client_id
            WHERE w.unix_time >= {now_unix}
            """
            # En SQLAlchemy es buena práctica envolver el string de la consulta en text()
            df = pd.read_sql_query(text(query), conn)

        logger.info("[EXTRACT] %d row(s) ready for simulation", len(df))
        return df
    except Exception as exc:
        logger.error("[EXTRACT] Failed to merge Silver tables: %s", exc)
        return pd.DataFrame()
    
# ─────────────────────────────────────────────────────────────────────────────
# STEP 2: TRANSFORM (PV Physics Engine)
# ─────────────────────────────────────────────────────────────────────────────

def transform_pv_generation(df_raw: pd.DataFrame) -> pd.DataFrame:
    """
    Executes the row-level physics simulation. 
    Optimised to bypass heavy calculations during low-sun/night hours.
    """
    if df_raw.empty:
        return pd.DataFrame()

    logger.info("[TRANSFORM] Running PV physics engine on %d records", len(df_raw))
    results = []

    try:
        for _, row in df_raw.iterrows():
            # 1. Solar Trigonometry
            alfa, azimuth = pvgen.calculate_solar_position(
                row["latitude"], row["longitude"], row["forecast_time_utc"]
            )

            # 2. Simulation Logic (Threshold gate: 2 degrees)
            if alfa < 2:
                poa = p_gen = pr = 0.0
                t_cell = row["temp_celsius"]
            else:
                ghi = pvgen.calculate_ghi(alfa, row["clouds_pct"], row["weather_id"])
                dni, dhi = pvgen.decompose_erbs(ghi, alfa, row["forecast_time_utc"])
                poa = pvgen.calculate_total_poa(dni, dhi, ghi, alfa, azimuth, row["angle"], row["aspect"])
                t_cell = pvgen.calculate_t_cell(row["temp_celsius"], row["wind_speed_mps"], poa)
                p_gen, pr = pvgen.calculate_power_output(poa, t_cell, row["pv_peak_power_kw"], row["loss_pct"])

            # 3. Consumption Model (Industrial Profile)
            p_con = pvgen.calculate_industrial_consumption(
                row["forecast_time_utc"], row["nominal_load_kw"], row["temp_celsius"]
            )

            results.append({
                "client_id":            row["client_id"],
                "unix_time":            row["unix_time"],
                "forecast_time_utc":    row["forecast_time_utc"],
                "t_cell_celsius":       round(t_cell, 3),
                "poa_wm2":              round(poa,    3),
                "pv_power_gen_kw":      round(p_gen,  3),
                "pv_performance_ratio": round(pr,     3),
                "power_con_kw":         round(p_con,  3),
                "calculated_at_utc":    datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S"),
            })

        return pd.DataFrame(results)
    except Exception as exc:
        logger.error("[TRANSFORM] PV engine error: %s", exc)
        return pd.DataFrame()

# ─────────────────────────────────────────────────────────────────────────────
# STEP 3: LOAD (Atomic Upsert)
# ─────────────────────────────────────────────────────────────────────────────

def load_generation_to_silver(df: pd.DataFrame, table_name: str = "clean_calculations") -> bool:
    """
    Persists simulation results to Silver. 
    Uses (client_id, unix_time) as PK to ensure idempotent updates.
    """
    if df.empty: return False
    
    db_path = config_paths.get_db_path()
    engine = create_engine(f"sqlite:///{db_path}")

    try:
        with engine.begin() as conn:
            conn.execute(text(f"""
                CREATE TABLE IF NOT EXISTS {table_name} (
                    client_id TEXT NOT NULL, unix_time INTEGER NOT NULL,
                    forecast_time_utc TEXT NOT NULL, pv_power_gen_kw REAL,
                    pv_performance_ratio REAL, poa_wm2 REAL, t_cell_celsius REAL,
                    power_con_kw REAL, calculated_at_utc TEXT NOT NULL,
                    PRIMARY KEY (client_id, unix_time)
                )
            """))

            cols = list(df.columns)
            query = text(f"INSERT OR REPLACE INTO {table_name} ({', '.join(cols)}) VALUES ({', '.join(':'+c for c in cols)})")
            conn.execute(query, df.to_dict(orient="records"))
        return True
    except Exception as exc:
        logger.error("[LOAD] Failed to persist calculations: %s", exc)
        return False

# ─────────────────────────────────────────────────────────────────────────────
# ORCHESTRATOR
# ─────────────────────────────────────────────────────────────────────────────

def extract_generation_data() -> int:
    """
    Main orchestration flow for the PV simulation pipeline.
    """
    logger.info("[INIT] ── PV Generation Pipeline Started ──")

    df_merged = get_merged_silver_data()
    if df_merged.empty: return 0

    df_calculated = transform_pv_generation(df_merged)
    if df_calculated.empty: return 0

    if load_generation_to_silver(df_calculated):
        logger.info("[DONE] Simulation pipeline finished successfully")
        return len(df_calculated)
    
    return 0

if __name__ == "__main__":
    extract_generation_data()