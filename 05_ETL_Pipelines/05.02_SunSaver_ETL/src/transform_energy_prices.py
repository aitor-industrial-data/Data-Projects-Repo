import pandas as pd
import os
from datetime import datetime, timezone
import json
from sqlalchemy import create_engine, text

import workspace_manager
from logger_config import setup_logging


logger = setup_logging()


# ─────────────────────────────────────────────────────────────────────────────
# EXTRACT (Bronze → memory)
# ─────────────────────────────────────────────────────────────────────────────

def extract_raw_ree_from_json(file_path: str) -> pd.DataFrame:
    """Reads a Bronze REE JSON file and wraps it in an audit-enriched DataFrame."""
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
# TRANSFORM
# ─────────────────────────────────────────────────────────────────────────────

def transform_prices_bronze_to_silver(df_raw: pd.DataFrame) -> pd.DataFrame:
    """
    Parses raw REE JSON, normalises datetime, handles outliers, deduplicates
    and interpolates missing values to produce Silver-quality price records.
    """
    if df_raw.empty:
        logger.warning("[TRANSFORM] Input DataFrame is empty — nothing to transform")
        return pd.DataFrame()

    logger.info("[TRANSFORM] Parsing and cleaning REE price data")

    try:
        records = []

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
        if df.empty:
            logger.warning("[TRANSFORM] No price records found in payload")
            return pd.DataFrame()

        # Date normalisation
        df["datetime_utc"] = pd.to_datetime(df["datetime_utc"], errors="coerce", utc=True)
        df = df.dropna(subset=["datetime_utc"])

        # Outlier filtering
        lower, upper  = -100, 2000
        outlier_mask  = (df["price_euro_mwh"] < lower) | (df["price_euro_mwh"] > upper)
        outlier_count = outlier_mask.sum()
        if outlier_count:
            logger.warning(
                "[TRANSFORM] %d price value(s) outside [%d, %d] EUR/MWh — filtered",
                outlier_count, lower, upper,
            )
            df = df[~outlier_mask]

        # Deduplication and interpolation
        df = df.sort_values("_ingested_at_utc", ascending=False)
        df = df.drop_duplicates(subset=["price_type", "datetime_utc"], keep="first")
        df = df.sort_values(["price_type", "datetime_utc"]).reset_index(drop=True)
        df["price_euro_mwh"] = df.groupby("price_type")["price_euro_mwh"].transform(
            lambda x: x.interpolate(method="linear").ffill().bfill().round(4)
        )

        # Unix timestamp aligned with weather and fact tables
        df["unix_time"] = (
            df["datetime_utc"]
            .dt.tz_localize(None)
            .astype("datetime64[s]")
            .astype("int64")
        )

        logger.info("[TRANSFORM] %d Silver-quality price record(s) produced", len(df))
        return df

    except Exception as exc:
        logger.error("[TRANSFORM] Price transformation failed: %s", exc)
        return pd.DataFrame()


# ─────────────────────────────────────────────────────────────────────────────
# LOAD → SILVER
# ─────────────────────────────────────────────────────────────────────────────

def load_ree_to_silver(df: pd.DataFrame, table_name: str = "clean_prices") -> bool:
    """Upserts validated price records into Silver using (datetime_utc, price_type) PK."""
    db_path = workspace_manager.get_db_path()

    if df.empty:
        logger.warning("[LOAD] DataFrame is empty — nothing written to '%s'", table_name)
        return False

    logger.info("[LOAD] Upserting %d price record(s) into '%s'", len(df), table_name)

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
            conn.execute(
                text(f"""
                    INSERT OR REPLACE INTO {table_name} ({', '.join(columns)})
                    VALUES ({', '.join(':' + c for c in columns)})
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

def transform_energy_prices() -> int:
    """
    Module entry point: reads pending/error tasks from the REE Bronze manifest,
    transforms each file and loads it to Silver, then persists updated statuses.
    Returns the total number of hourly price records committed to Silver.
    """
    logger.info("[INIT] ── transform_energy_prices starting ──────────────────")

    bronze_dir    = workspace_manager.get_bronze_path()
    manifest_path = os.path.join(bronze_dir, "_process_manifest_ree.json")

    if not os.path.exists(manifest_path):
        logger.info("[INIT] No REE manifest found — nothing to process")
        return 0

    with open(manifest_path, "r", encoding="utf-8") as fh:
        all_tasks = json.load(fh)

    actionable = [t for t in all_tasks if t["status"] in ("pending", "error")]
    if not actionable:
        logger.info("[INIT] All REE manifest tasks already processed — nothing to do")
        return 0

    pending_n = sum(1 for t in actionable if t["status"] == "pending")
    retry_n   = sum(1 for t in actionable if t["status"] == "error")
    logger.info("[INIT] Tasks to process — new: %d | retries: %d", pending_n, retry_n)

    session_rows = session_ok = session_err = 0

    for task in actionable:
        path_file = task["path"]
        fname     = os.path.basename(path_file)

        logger.info("[EXTRACT] Processing Bronze file: %s", fname)

        try:
            df_raw = extract_raw_ree_from_json(path_file)
            if df_raw.empty:
                raise ValueError("Bronze file is empty or unreadable")

            df_silver = transform_prices_bronze_to_silver(df_raw)
            if df_silver.empty:
                raise ValueError("Transformation produced an empty DataFrame")

            rows = len(df_silver)
            if load_ree_to_silver(df_silver):
                task.update({"status": "success", "updated_at": datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")})
                task.pop("error", None)
                session_rows += rows
                session_ok   += 1
                logger.info("[LOAD] %s → %d hourly record(s) committed to Silver", fname, rows)
            else:
                raise ValueError("Silver load returned False")

        except Exception as exc:
            task.update({
                "status":     "error",
                "error":      str(exc),
                "updated_at": datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S"),
            })
            session_err += 1
            logger.error("[ERROR] %s failed: %s", fname, exc)

    with open(manifest_path, "w", encoding="utf-8") as fh:
        json.dump(all_tasks, fh, indent=4, ensure_ascii=False)

    logger.info(
        "[DONE] transform_energy_prices finished — tasks ok: %d | errors: %d | rows written: %d",
        session_ok, session_err, session_rows,
    )
    return session_rows


# ─────────────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    transform_energy_prices()
