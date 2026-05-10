import pandas as pd
import os
import json
from datetime import datetime, timezone
from sqlalchemy import create_engine, text

import config_paths
from logger_config import setup_logging

"""
SILVER LAYER: WEATHER DATA TRANSFORMATION (OpenWeather)
-------------------------------------------------------
Author: Aitor Asin
Description: Processes raw multi-client weather forecasts. Implements temporal 
             upsampling (3h to 1h) via linear interpolation, calculates 
             daylight flags, and ensures idempotency through composite PKs.
"""

logger = setup_logging()

# ─────────────────────────────────────────────────────────────────────────────
# STEP 1: EXTRACT (Bronze → memory)
# ─────────────────────────────────────────────────────────────────────────────

def extract_raw_weather_from_json(file_path: str, client_id: str) -> pd.DataFrame:
    """
    Ingests Bronze weather JSON and attaches client context and audit metadata.
    """
    try:
        with open(file_path, "r", encoding="utf-8") as fh:
            raw = json.load(fh)

        df = pd.DataFrame([{
            "client_id":        client_id,
            "_ingested_at_utc": datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S"),
            "_source_file":     os.path.basename(file_path),
            "raw_data":         json.dumps(raw),
        }])

        logger.debug("[EXTRACT] Bronze file loaded for client: %s", client_id)
        return df
    except Exception as exc:
        logger.error("[EXTRACT] Failed to read Bronze file %s: %s", os.path.basename(file_path), exc)
        return pd.DataFrame()

# ─────────────────────────────────────────────────────────────────────────────
# STEP 2: TRANSFORM (Resampling & Feature Engineering)
# ─────────────────────────────────────────────────────────────────────────────

def transform_weather_bronze_to_silver(df_raw: pd.DataFrame) -> pd.DataFrame:
    """
    Parses OpenWeather payload, performs hourly linear interpolation, 
    and derives solar-relevant features like 'is_daylight'.
    """
    if df_raw.empty:
        logger.warning("[TRANSFORM] Input DataFrame is empty — skipping")
        return pd.DataFrame()

    all_clients_data = []

    try:
        for _, row in df_raw.iterrows():
            # 1. Parsing JSON structure
            raw_json = json.loads(row["raw_data"])
            forecasts = raw_json.get("list", [])
            
            records = [{
                "forecast_time_utc":   f.get("dt_txt"),
                "temp_celsius":        f.get("main", {}).get("temp"),
                "humidity_pct":        f.get("main", {}).get("humidity"),
                "clouds_pct":          f.get("clouds", {}).get("all"),
                "rain_prob_norm":      f.get("pop"),
                "wind_speed_mps":      f.get("wind", {}).get("speed"),
                "weather_id":          f.get("weather", [{}])[0].get("id"),
                "weather_main":        f.get("weather", [{}])[0].get("main"),
                "weather_description": f.get("weather", [{}])[0].get("description"),
                "pod":                 f.get("sys", {}).get("pod"),
            } for f in forecasts]

            df_c = pd.DataFrame(records)
            df_c["forecast_time_utc"] = pd.to_datetime(df_c["forecast_time_utc"])
            df_c = df_c.drop_duplicates(subset=["forecast_time_utc"], keep="last")

            # 2. Temporal Resampling (3h -> 1h resolution)
            df_c = df_c.set_index("forecast_time_utc").resample("1h").asfreq()

            # Linear interpolation for continuous physical variables
            num_cols = ["temp_celsius", "humidity_pct", "clouds_pct", "rain_prob_norm", "wind_speed_mps"]
            df_c[num_cols] = df_c[num_cols].interpolate(method="linear").round(3)

            # Forward fill for categorical/descriptive weather data
            cat_cols = ["weather_id", "weather_main", "weather_description", "pod"]
            df_c[cat_cols] = df_c[cat_cols].ffill()

            # 3. Feature Engineering
            df_c = df_c.reset_index()
            df_c["client_id"] = row["client_id"]
            df_c["_ingested_at_utc"] = row["_ingested_at_utc"]
            df_c["_source_file"] = row["_source_file"]
            
            # Universal key for joins
            df_c["unix_time"] = (df_c["forecast_time_utc"] - pd.Timestamp("1970-01-01")) // pd.Timedelta("1s")
            df_c["is_daylight"] = df_c["pod"].apply(lambda x: 1 if x == "d" else 0)

            all_clients_data.append(df_c)

        df_final = pd.concat(all_clients_data, ignore_index=True)
        
        # Cleanup
        df_final["rain_prob_norm"] = df_final["rain_prob_norm"].fillna(0)
        df_final = df_final.dropna(subset=["client_id", "forecast_time_utc"])
        if "pod" in df_final.columns: df_final = df_final.drop(columns=["pod"])

        logger.info("[TRANSFORM] %d Silver-quality hourly weather records produced", len(df_final))
        return df_final

    except Exception as exc:
        logger.error("[TRANSFORM] Weather transformation failed: %s", exc)
        return pd.DataFrame()

# ─────────────────────────────────────────────────────────────────────────────
# STEP 3: LOAD (Atomic Silver Upsert)
# ─────────────────────────────────────────────────────────────────────────────

def load_weather_to_silver(df: pd.DataFrame, table_name: str = "clean_weather") -> bool:
    """
    Upserts records to Silver layer. Uses (client_id, unix_time) as PK 
    to handle overlapping forecast updates idempotently.
    """
    if df.empty: return False
    
    db_path = config_paths.get_db_path()
    try:
        df_sql = df.copy()
        df_sql["forecast_time_utc"] = df_sql["forecast_time_utc"].dt.strftime("%Y-%m-%d %H:%M:%S")
        df_sql["_ingested_at_utc"]  = pd.to_datetime(df_sql["_ingested_at_utc"]).dt.strftime("%Y-%m-%d %H:%M:%S")

        engine = create_engine(f"sqlite:///{db_path}")
        with engine.begin() as conn:
            conn.execute(text(f"""
                CREATE TABLE IF NOT EXISTS {table_name} (
                    client_id TEXT NOT NULL, unix_time INTEGER NOT NULL,
                    forecast_time_utc TEXT NOT NULL, temp_celsius REAL,
                    humidity_pct REAL, clouds_pct REAL, rain_prob_norm REAL,
                    wind_speed_mps REAL, weather_id INTEGER, weather_main TEXT,
                    weather_description TEXT, is_daylight INTEGER,
                    _source_file TEXT, _ingested_at_utc TEXT NOT NULL,
                    PRIMARY KEY (client_id, unix_time)
                )
            """))

            cols = list(df_sql.columns)
            query = text(f"INSERT OR REPLACE INTO {table_name} ({', '.join(cols)}) VALUES ({', '.join(':'+c for c in cols)})")
            conn.execute(query, df_sql.to_dict(orient="records"))
        return True
    except Exception as exc:
        logger.error("[LOAD] Failed to write to '%s': %s", table_name, exc)
        return False

# ─────────────────────────────────────────────────────────────────────────────
# STEP 4: ORCHESTRATOR
# ─────────────────────────────────────────────────────────────────────────────

def transform_openweather() -> int:
    """
    Master entry point for weather processing. 
    Processes the Bronze manifest and updates state.
    """
    logger.info("[INIT] ── Starting transform_openweather ──")
    
    manifest_path = os.path.join(config_paths.get_bronze_path(), "_process_manifest_openweather.json")
    if not os.path.exists(manifest_path): return 0

    with open(manifest_path, "r", encoding="utf-8") as fh:
        tasks = json.load(fh)

    actionable = [t for t in tasks if t["status"] in ("pending", "error")]
    if not actionable: return 0

    session_rows = 0
    for task in actionable:
        try:
            df_raw = extract_raw_weather_from_json(task["path"], task["client_id"])
            df_silver = transform_weather_bronze_to_silver(df_raw)
            
            if not df_silver.empty and load_weather_to_silver(df_silver):
                task.update({"status": "success", "updated_at": datetime.now(timezone.utc).isoformat()})
                task.pop("error", None)
                session_rows += len(df_silver)
            else:
                raise ValueError("Transformation or Load failed")
        except Exception as exc:
            task.update({"status": "error", "error": str(exc), "updated_at": datetime.now(timezone.utc).isoformat()})
            logger.error("[ERROR] Task failed for client %s: %s", task.get("client_id"), exc)

    with open(manifest_path, "w", encoding="utf-8") as fh:
        json.dump(tasks, fh, indent=4)

    return session_rows

if __name__ == "__main__":
    transform_openweather()