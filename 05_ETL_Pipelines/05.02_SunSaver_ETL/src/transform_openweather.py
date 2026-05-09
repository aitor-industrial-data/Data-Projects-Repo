import pandas as pd
import os
import json
from datetime import datetime, timezone
from sqlalchemy import create_engine, text

import workspace_manager
from logger_config import setup_logging


logger = setup_logging()


# ─────────────────────────────────────────────────────────────────────────────
# EXTRACT (Bronze → memory)
# ─────────────────────────────────────────────────────────────────────────────

def extract_raw_weather_from_json(file_path: str, client_id: str) -> pd.DataFrame:
    """Reads a Bronze OpenWeather JSON file and wraps it in an audit-enriched DataFrame."""
    try:
        with open(file_path, "r", encoding="utf-8") as fh:
            raw = json.load(fh)

        df = pd.DataFrame([{
            "client_id":        client_id,
            "_ingested_at_utc": datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S"),
            "_source_file":     os.path.basename(file_path),
            "raw_data":         json.dumps(raw),
        }])

        logger.debug("[EXTRACT] Bronze file loaded for client_id=%s: %s", client_id, os.path.basename(file_path))
        return df

    except Exception as exc:
        logger.error("[EXTRACT] Failed to read Bronze file %s: %s", os.path.basename(file_path), exc)
        return pd.DataFrame()


# ─────────────────────────────────────────────────────────────────────────────
# TRANSFORM
# ─────────────────────────────────────────────────────────────────────────────

def transform_weather_bronze_to_silver(df_raw: pd.DataFrame) -> pd.DataFrame:
    """
    Parses the raw OpenWeatherMap forecast payload, resamples to hourly
    resolution via linear interpolation and forward-fill, and computes
    derived features (unix_time, is_daylight) for each client.
    """
    if df_raw.empty:
        logger.warning("[TRANSFORM] Input DataFrame is empty — nothing to transform")
        return pd.DataFrame()

    logger.info("[TRANSFORM] Processing weather data for %d client batch(es)", len(df_raw))

    all_clients: list = []

    try:
        for _, row in df_raw.iterrows():
            client_id  = row["client_id"]
            ingested   = row["_ingested_at_utc"]
            source     = row["_source_file"]
            raw_json   = json.loads(row["raw_data"])
            forecasts  = raw_json.get("list", [])

            records = [
                {
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
                }
                for f in forecasts
            ]

            df_c = pd.DataFrame(records)
            df_c["forecast_time_utc"] = pd.to_datetime(df_c["forecast_time_utc"])
            df_c = df_c.drop_duplicates(subset=["forecast_time_utc"], keep="last")

            # Resample to 1-hour resolution
            df_c = df_c.set_index("forecast_time_utc").resample("1h").asfreq()

            num_cols = ["temp_celsius", "humidity_pct", "clouds_pct", "rain_prob_norm", "wind_speed_mps"]
            df_c[num_cols] = df_c[num_cols].interpolate(method="linear").round(3)

            cat_cols = ["weather_id", "weather_main", "weather_description", "pod"]
            df_c[cat_cols] = df_c[cat_cols].ffill()

            df_c = df_c.reset_index()
            df_c["client_id"]        = client_id
            df_c["_ingested_at_utc"] = ingested
            df_c["_source_file"]     = source
            df_c["unix_time"]        = (
                (df_c["forecast_time_utc"] - pd.Timestamp("1970-01-01")) // pd.Timedelta("1s")
            )
            df_c["is_daylight"] = df_c["pod"].apply(lambda x: 1 if x == "d" else 0)

            all_clients.append(df_c)
            logger.debug(
                "[TRANSFORM] client_id=%s — %d hourly slot(s) after resampling",
                client_id, len(df_c),
            )

        df_final = pd.concat(all_clients, ignore_index=True)

        # Final null cleanup
        df_final["rain_prob_norm"]  = df_final["rain_prob_norm"].fillna(0)
        df_final["_ingested_at_utc"] = pd.to_datetime(df_final["_ingested_at_utc"], errors="coerce")
        df_final = df_final.dropna(subset=["client_id", "forecast_time_utc"])

        if "pod" in df_final.columns:
            df_final = df_final.drop(columns=["pod"])

        logger.info("[TRANSFORM] %d Silver-quality row(s) produced across all clients", len(df_final))
        return df_final

    except Exception as exc:
        logger.error("[TRANSFORM] Weather transformation failed: %s", exc)
        return pd.DataFrame()


# ─────────────────────────────────────────────────────────────────────────────
# LOAD → SILVER
# ─────────────────────────────────────────────────────────────────────────────

def load_weather_to_silver(df: pd.DataFrame, table_name: str = "clean_weather") -> bool:
    """
    Upserts validated weather records into Silver using a composite PK
    (client_id, unix_time) to guarantee idempotency across forecast refreshes.
    """
    db_path = workspace_manager.get_db_path()

    if df.empty:
        logger.warning("[LOAD] DataFrame is empty — nothing written to '%s'", table_name)
        return False

    logger.info("[LOAD] Upserting %d record(s) into '%s'", len(df), table_name)

    try:
        df_sql = df.copy()
        df_sql["forecast_time_utc"] = df_sql["forecast_time_utc"].dt.strftime("%Y-%m-%d %H:%M:%S")
        df_sql["_ingested_at_utc"]  = df_sql["_ingested_at_utc"].dt.strftime("%Y-%m-%d %H:%M:%S")

        engine = create_engine(f"sqlite:///{db_path}")

        with engine.begin() as conn:
            conn.execute(text(f"""
                CREATE TABLE IF NOT EXISTS {table_name} (
                    client_id               TEXT    NOT NULL,
                    unix_time               INTEGER NOT NULL,
                    forecast_time_utc       TEXT    NOT NULL,
                    temp_celsius            REAL,
                    humidity_pct            REAL,
                    clouds_pct              REAL,
                    rain_prob_norm          REAL,
                    wind_speed_mps          REAL,
                    weather_id              INTEGER,
                    weather_main            TEXT,
                    weather_description     TEXT,
                    is_daylight             INTEGER,
                    _source_file            TEXT,
                    _ingested_at_utc        TEXT    NOT NULL,
                    PRIMARY KEY (client_id, unix_time)
                )
            """))

            cols = list(df_sql.columns)
            conn.execute(
                text(f"""
                    INSERT OR REPLACE INTO {table_name} ({', '.join(cols)})
                    VALUES ({', '.join(':' + c for c in cols)})
                """),
                df_sql.to_dict(orient="records"),
            )

        logger.info("[LOAD] '%s' updated — %d record(s) upserted", table_name, len(df))
        return True

    except Exception as exc:
        logger.error("[LOAD] Failed to write to '%s': %s", table_name, exc)
        return False


# ─────────────────────────────────────────────────────────────────────────────
# ORCHESTRATOR ENTRY POINT
# ─────────────────────────────────────────────────────────────────────────────

def transform_openweather() -> int:
    """
    Module entry point: reads pending/error tasks from the OpenWeather Bronze
    manifest, transforms each file and loads it to Silver, then persists
    updated task statuses.  Returns total hourly records committed to Silver.
    """
    logger.info("[INIT] ── transform_openweather starting ────────────────────")

    bronze_dir    = workspace_manager.get_bronze_path()
    manifest_path = os.path.join(bronze_dir, "_process_manifest_openweather.json")

    if not os.path.exists(manifest_path):
        logger.info("[INIT] No OpenWeather manifest found — nothing to process")
        return 0

    with open(manifest_path, "r", encoding="utf-8") as fh:
        all_tasks = json.load(fh)

    actionable = [t for t in all_tasks if t["status"] in ("pending", "error")]
    if not actionable:
        logger.info("[INIT] All OpenWeather manifest tasks already processed — nothing to do")
        return 0

    pending_n = sum(1 for t in actionable if t["status"] == "pending")
    retry_n   = sum(1 for t in actionable if t["status"] == "error")
    logger.info("[INIT] Tasks to process — new: %d | retries: %d", pending_n, retry_n)

    session_rows = session_ok = session_err = 0

    for task in actionable:
        client_id = task["client_id"]
        path_file = task["path"]
        fname     = os.path.basename(path_file)

        logger.info("[EXTRACT] Processing client_id=%s — file: %s", client_id, fname)

        try:
            df_raw = extract_raw_weather_from_json(path_file, client_id)
            if df_raw.empty:
                raise ValueError("Bronze file is empty or unreadable")

            df_silver = transform_weather_bronze_to_silver(df_raw)
            if df_silver.empty:
                raise ValueError("Transformation produced an empty DataFrame")

            rows = len(df_silver)
            if load_weather_to_silver(df_silver):
                task.update({"status": "success", "updated_at": datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")})
                task.pop("error", None)
                session_rows += rows
                session_ok   += 1
                logger.info("[LOAD] client_id=%s → %d hourly record(s) committed to Silver", client_id, rows)
            else:
                raise ValueError("Silver load returned False")

        except Exception as exc:
            task.update({
                "status":     "error",
                "error":      str(exc),
                "updated_at": datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S"),
            })
            session_err += 1
            logger.error("[ERROR] client_id=%s — %s: %s", client_id, fname, exc)

    with open(manifest_path, "w", encoding="utf-8") as fh:
        json.dump(all_tasks, fh, indent=4, ensure_ascii=False)

    logger.info(
        "[DONE] transform_openweather finished — tasks ok: %d | errors: %d | rows written: %d",
        session_ok, session_err, session_rows,
    )
    return session_rows


# ─────────────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    transform_openweather()
