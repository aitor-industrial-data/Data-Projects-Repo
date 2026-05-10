import pandas as pd
import os
import json
import numpy as np
from datetime import datetime, timezone
from sqlalchemy import create_engine, text

import config_paths
from logger_config import setup_logging

"""
SILVER LAYER: ENERGY PRICE TRANSFORMATION (REE)
-----------------------------------------------
Author: Aitor Asin
Description: Normalizes and cleans Red Eléctrica de España (REE) raw data.
             Handles JSON parsing, outlier detection, linear interpolation 
             for missing values, and idempotent loading into Silver.
"""

logger = setup_logging()

# ─────────────────────────────────────────────────────────────────────────────
# STEP 1: EXTRACT (Bronze → memory)
# ─────────────────────────────────────────────────────────────────────────────

def extract_raw_ree_from_json(file_path: str) -> pd.DataFrame:
    """
    Ingests raw JSON from Bronze REE and wraps it in a DataFrame 
    with lineage metadata.
    """
    try:
        with open(file_path, "r", encoding="utf-8") as fh:
            raw = json.load(fh)

        df = pd.DataFrame([{
            "_ingested_at_utc": datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S"),
            "_source_file":     os.path.basename(file_path),
            "raw_data":         json.dumps(raw),
        }])

        logger.debug("[EXTRACT] Bronze file loaded: %s", os.path.basename(file_path))
        return df
    except Exception as exc:
        logger.error("[EXTRACT] Failed to read Bronze file %s: %s", os.path.basename(file_path), exc)
        return pd.DataFrame()

# ─────────────────────────────────────────────────────────────────────────────
# STEP 2: TRANSFORM (Data Refinement & Time Series Cleaning)
# ─────────────────────────────────────────────────────────────────────────────

def transform_prices_bronze_to_silver(df_raw: pd.DataFrame) -> pd.DataFrame:
    """
    Normalizes datetime, filters outliers, and applies linear interpolation
    to ensure a continuous price series.
    """
    if df_raw.empty:
        logger.warning("[TRANSFORM] Input DataFrame is empty — skipping")
        return pd.DataFrame()

    try:
        records = []
        # JSON Parsing logic
        for _, row in df_raw.iterrows():
            raw_json   = json.loads(row["raw_data"])
            source     = row["_source_file"]
            ingested   = row["_ingested_at_utc"]

            for series in raw_json.get("included", []):
                price_type = series.get("type")
                for v in series.get("attributes", {}).get("values", []):
                    records.append({
                        "price_type":       price_type,
                        "datetime_utc":     v.get("datetime"),
                        "price_euro_mwh":   float(v.get("value")),
                        "_source_file":     source,
                        "_ingested_at_utc": ingested,
                    })

        df = pd.DataFrame(records)
        if df.empty: return pd.DataFrame()

        # 1. Date Normalization & Quality Gate
        df["datetime_utc"] = pd.to_datetime(df["datetime_utc"], errors="coerce", utc=True)
        df = df.dropna(subset=["datetime_utc"])

        # 2. Outlier Filtering (Physical constraints for EUR/MWh)
        lower, upper  = -100, 2000
        outlier_mask  = (df["price_euro_mwh"] < lower) | (df["price_euro_mwh"] > upper)
        if outlier_mask.any():
            logger.warning("[TRANSFORM] Filtering %d outlier(s) outside [%d, %d]", outlier_mask.sum(), lower, upper)
            df = df[~outlier_mask]

        # 3. Time Series Integrity: Deduplication & Interpolation
        df = df.sort_values("_ingested_at_utc", ascending=False)
        df = df.drop_duplicates(subset=["price_type", "datetime_utc"], keep="first")
        df = df.sort_values(["price_type", "datetime_utc"]).reset_index(drop=True)

        # Handle gaps using linear interpolation per price series
        df["price_euro_mwh"] = df.groupby("price_type")["price_euro_mwh"].transform(
            lambda x: x.interpolate(method="linear").ffill().bfill().round(4)
        )

        # 4. Unix Alignment (Unified key for cross-table joins)
        df["unix_time"] = df["datetime_utc"].dt.tz_localize(None).astype("datetime64[s]").astype("int64")

        logger.info("[TRANSFORM] %d Silver-quality price records produced", len(df))
        return df
    except Exception as exc:
        logger.error("[TRANSFORM] Price transformation failed: %s", exc)
        return pd.DataFrame()

# ─────────────────────────────────────────────────────────────────────────────
# STEP 3: LOAD (Idempotent Upsert)
# ─────────────────────────────────────────────────────────────────────────────

def load_ree_to_silver(df: pd.DataFrame, table_name: str = "clean_prices") -> bool:
    """
    Persists data into Silver using INSERT OR REPLACE to ensure idempotency.
    """
    if df.empty: return False
    
    db_path = config_paths.get_db_path()
    try:
        df_sql = df.copy()
        df_sql["datetime_utc"]     = pd.to_datetime(df_sql["datetime_utc"]).dt.strftime("%Y-%m-%d %H:%M:%S")
        df_sql["_ingested_at_utc"] = pd.to_datetime(df_sql["_ingested_at_utc"]).dt.strftime("%Y-%m-%d %H:%M:%S")

        engine = create_engine(f"sqlite:///{db_path}")
        with engine.begin() as conn:
            conn.execute(text(f"""
                CREATE TABLE IF NOT EXISTS {table_name} (
                    unix_time           INTEGER NOT NULL,
                    datetime_utc        TEXT    NOT NULL,
                    price_type          TEXT    NOT NULL,
                    price_euro_mwh      REAL,
                    _source_file        TEXT,
                    _ingested_at_utc    TEXT    NOT NULL,
                    PRIMARY KEY (datetime_utc, price_type)
                )
            """))

            columns = df_sql.columns.tolist()
            query = text(f"""
                INSERT OR REPLACE INTO {table_name} ({', '.join(columns)})
                VALUES ({', '.join(':' + c for c in columns)})
            """)
            conn.execute(query, df_sql.to_dict(orient="records"))
        
        return True
    except Exception as exc:
        logger.error("[LOAD] Failed to write to '%s': %s", table_name, exc)
        return False

# ─────────────────────────────────────────────────────────────────────────────
# STEP 4: ORCHESTRATOR
# ─────────────────────────────────────────────────────────────────────────────

def transform_energy_prices() -> int:
    """
    Master task for REE data. Processes Bronze manifest and returns total records.
    """
    logger.info("[INIT] ── Starting transform_energy_prices ──")
    
    manifest_path = os.path.join(config_paths.get_bronze_path(), "_process_manifest_ree.json")
    if not os.path.exists(manifest_path):
        return 0

    with open(manifest_path, "r", encoding="utf-8") as fh:
        tasks = json.load(fh)

    actionable = [t for t in tasks if t["status"] in ("pending", "error")]
    if not actionable: return 0

    session_rows = 0
    for task in actionable:
        try:
            df_raw = extract_raw_ree_from_json(task["path"])
            df_silver = transform_prices_bronze_to_silver(df_raw)
            
            if not df_silver.empty and load_ree_to_silver(df_silver):
                task.update({"status": "success", "updated_at": datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")})
                task.pop("error", None)
                session_rows += len(df_silver)
            else:
                raise ValueError("Transformation or Load failed")
        except Exception as exc:
            task.update({"status": "error", "error": str(exc), "updated_at": datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")})
            logger.error("[ERROR] Task failed: %s", exc)

    with open(manifest_path, "w", encoding="utf-8") as fh:
        json.dump(tasks, fh, indent=4, ensure_ascii=False)

    return session_rows

if __name__ == "__main__":
    transform_energy_prices()