import pandas as pd
from datetime import datetime, timezone
import sqlite3
from sqlalchemy import create_engine, text

import workspace_manager
import pv_generation_engine as pvgen
from logger_config import setup_logging


logger = setup_logging()


# ─────────────────────────────────────────────────────────────────────────────
# EXTRACT
# ─────────────────────────────────────────────────────────────────────────────

def get_merged_silver_data(
    table_name_1: str = "clean_clients",
    table_name_2: str = "clean_weather",
) -> pd.DataFrame:
    """
    Joins clients and weather data for the active forecast window
    (unix_time >= now) and returns the merged DataFrame.
    """
    db_path  = workspace_manager.get_db_path()
    now_unix = int(datetime.now(timezone.utc).timestamp())

    logger.info(
        "[EXTRACT] Querying active window from '%s' ⨝ '%s' (unix_time >= %d)",
        table_name_1, table_name_2, now_unix,
    )

    try:
        with sqlite3.connect(str(db_path)) as conn:
            query = f"""
            SELECT c.*,
                   w.unix_time,
                   w.forecast_time_utc,
                   w.temp_celsius,
                   w.humidity_pct,
                   w.clouds_pct,
                   w.rain_prob_norm,
                   w.wind_speed_mps,
                   w.weather_id,
                   w.weather_main,
                   w.weather_description,
                   w.is_daylight
            FROM {table_name_1} AS c
            INNER JOIN {table_name_2} AS w ON c.client_id = w.client_id
            WHERE w.unix_time >= {now_unix}
            """
            df = pd.read_sql_query(query, conn)

        logger.info("[EXTRACT] %d row(s) fetched from active forecast window", len(df))
        return df

    except Exception as exc:
        logger.error("[EXTRACT] Failed to query Silver tables: %s", exc)
        return pd.DataFrame()


# ─────────────────────────────────────────────────────────────────────────────
# TRANSFORM
# ─────────────────────────────────────────────────────────────────────────────

def transform_pv_generation(df_raw: pd.DataFrame) -> pd.DataFrame:
    """
    Runs the physical PV simulation engine row-by-row over the merged dataset
    and returns a DataFrame of calculated energy metrics.
    """
    if df_raw.empty:
        logger.warning("[TRANSFORM] Input DataFrame is empty — skipping PV calculation")
        return pd.DataFrame()

    logger.info("[TRANSFORM] Running PV engine on %d record(s)", len(df_raw))

    results = []

    try:
        for _, row in df_raw.iterrows():
            alfa, azimuth = pvgen.calculate_solar_position(
                row["latitude"], row["longitude"], row["forecast_time_utc"]
            )

            if alfa < 2:                        # Sun below engineering threshold → no generation
                ghi = dni = dhi = poa = p_gen = pr = 0.0
                t_cell = row["temp_celsius"]
                p_con  = pvgen.calculate_industrial_consumption(
                    row["forecast_time_utc"], row["nominal_load_kw"], row["temp_celsius"]
                )
            else:
                ghi        = pvgen.calculate_ghi(alfa, row["clouds_pct"], row["weather_id"])
                dni, dhi   = pvgen.decompose_erbs(ghi, alfa, row["forecast_time_utc"])
                poa        = pvgen.calculate_total_poa(
                    dni, dhi, ghi, alfa, azimuth, row["angle"], row["aspect"]
                )
                t_cell     = pvgen.calculate_t_cell(row["temp_celsius"], row["wind_speed_mps"], poa)
                p_gen, pr  = pvgen.calculate_power_output(
                    poa, t_cell, row["pv_peak_power_kw"], row["loss_pct"]
                )
                p_con      = pvgen.calculate_industrial_consumption(
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

        df_out = pd.DataFrame(results)
        logger.info("[TRANSFORM] PV engine completed — %d calculations produced", len(df_out))
        return df_out

    except Exception as exc:
        logger.error("[TRANSFORM] PV engine error: %s", exc)
        return pd.DataFrame()


# ─────────────────────────────────────────────────────────────────────────────
# LOAD → SILVER
# ─────────────────────────────────────────────────────────────────────────────

def load_generation_to_silver(df: pd.DataFrame, table_name: str = "clean_calculations") -> bool:
    """
    Upserts PV calculation results into Silver using a composite PK
    (client_id, unix_time) to guarantee idempotency.
    """
    db_path = workspace_manager.get_db_path()

    if df.empty:
        logger.warning("[LOAD] DataFrame is empty — nothing written to '%s'", table_name)
        return False

    logger.info("[LOAD] Upserting %d record(s) into '%s'", len(df), table_name)

    try:
        df_sql = df.copy()
        if pd.api.types.is_datetime64_any_dtype(df_sql["forecast_time_utc"]):
            df_sql["forecast_time_utc"] = df_sql["forecast_time_utc"].dt.strftime("%Y-%m-%d %H:%M:%S")

        engine = create_engine(f"sqlite:///{db_path}")

        with engine.begin() as connection:
            connection.execute(text(f"""
                CREATE TABLE IF NOT EXISTS {table_name} (
                    client_id               TEXT    NOT NULL,
                    unix_time               INTEGER NOT NULL,
                    forecast_time_utc       TEXT    NOT NULL,
                    pv_power_gen_kw         REAL,
                    pv_performance_ratio    REAL,
                    poa_wm2                 REAL,
                    t_cell_celsius          REAL,
                    power_con_kw            REAL,
                    calculated_at_utc       TEXT    NOT NULL,
                    PRIMARY KEY (client_id, unix_time)
                )
            """))

            columns      = list(df_sql.columns)
            placeholders = [f":{col}" for col in columns]
            connection.execute(
                text(f"""
                    INSERT OR REPLACE INTO {table_name}
                    ({', '.join(columns)})
                    VALUES ({', '.join(placeholders)})
                """),
                df_sql.to_dict(orient="records"),
            )

        logger.info("[LOAD] %d record(s) written to '%s'", len(df), table_name)
        return True

    except Exception as exc:
        logger.error("[LOAD] Failed to write to '%s': %s", table_name, exc)
        return False


# ─────────────────────────────────────────────────────────────────────────────
# ORCHESTRATOR ENTRY POINT
# ─────────────────────────────────────────────────────────────────────────────

def extract_generation_data() -> int:
    """
    Module entry point: extract merged Silver data → run PV engine → load results.
    Returns the number of calculation records written (0 on failure).
    """
    logger.info("[INIT] ── extract_generation_data starting ──────────────────")

    df_merged = get_merged_silver_data()
    if df_merged.empty:
        logger.warning("[INIT] No active forecast data found — nothing to calculate")
        return 0

    df_calculated = transform_pv_generation(df_merged)
    if df_calculated.empty:
        logger.error("[TRANSFORM] PV engine returned no results — aborting load")
        return 0

    total = len(df_calculated)

    if load_generation_to_silver(df_calculated):
        logger.info("[DONE] extract_generation_data finished — calculations written: %d", total)
        return total

    logger.error("[DONE] Load step failed — 0 records committed")
    return 0


# ─────────────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    extract_generation_data()
