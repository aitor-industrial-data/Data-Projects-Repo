import pandas as pd
import os
import json
from sqlalchemy import create_engine, text
import numpy as np
from datetime import datetime, timezone

import workspace_manager
from logger_config import setup_logging


logger = setup_logging()


# ─────────────────────────────────────────────────────────────────────────────
# EXTRACT (Bronze → memory)
# ─────────────────────────────────────────────────────────────────────────────

def extract_clients_from_json(file_path: str) -> pd.DataFrame:
    """Reads a Bronze JSON file and returns a raw DataFrame with audit columns."""
    try:
        with open(file_path, "r", encoding="utf-8") as fh:
            raw = json.load(fh)

        df = pd.DataFrame(raw)
        df["_ingested_at_utc"] = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")
        df["_source_file"]     = os.path.basename(file_path)

        logger.debug("[EXTRACT] %d raw row(s) loaded from %s", len(df), os.path.basename(file_path))
        return df

    except Exception as exc:
        logger.error("[EXTRACT] Failed to read Bronze file %s: %s", os.path.basename(file_path), exc)
        return pd.DataFrame()


# ─────────────────────────────────────────────────────────────────────────────
# TRANSFORM (Bronze quality → Silver quality)
# ─────────────────────────────────────────────────────────────────────────────

def transform_clients_bronze_to_silver(df_raw: pd.DataFrame) -> pd.DataFrame:
    """
    Applies type coercion, business-rule validation, deduplication and null
    imputation to promote client records from Bronze to Silver quality.
    """
    if df_raw.empty:
        logger.warning("[TRANSFORM] Input DataFrame is empty — nothing to transform")
        return pd.DataFrame()

    logger.info("[TRANSFORM] Transforming %d raw client record(s)", len(df_raw))

    try:
        df = df_raw.copy()

        numeric_cols = [
            "latitude", "longitude", "nominal_load_kw", "pv_peak_power_kw",
            "panel_area_m2", "efficiency", "loss_pct", "angle", "aspect",
            "battery_capacity_kwh", "soc_min_pct", "installation_cost_eur",
        ]
        text_cols = [
            "client_id", "name", "description", "panel_type",
            "mounting", "timezone", "_ingested_at_utc",
        ]

        for col in numeric_cols:
            df[col] = pd.to_numeric(df[col], errors="coerce")
        for col in text_cols:
            df[col] = df[col].astype(str).replace(["None", "nan", "NaN", "null"], np.nan)

        df["_ingested_at_utc"] = pd.to_datetime(df["_ingested_at_utc"], errors="coerce")

        # Drop records missing critical fields
        critical = ["client_id", "name", "latitude", "longitude", "pv_peak_power_kw", "_ingested_at_utc"]
        before   = len(df)
        df       = df.dropna(subset=critical)
        dropped  = before - len(df)
        if dropped:
            logger.warning("[TRANSFORM] %d record(s) dropped — missing critical field(s): %s", dropped, critical)

        # ── Business rules ────────────────────────────────────────────────────
        df["latitude"]  = df["latitude"].round(6)
        df["longitude"] = df["longitude"].round(6)
        df["name"]      = df["name"].str.upper().str.strip()

        df = df[df["latitude"].between(-90, 90) & df["longitude"].between(-180, 180)]
        df.loc[~df["angle"].between(0, 90),   "angle"]   = 30.0
        df.loc[~df["aspect"].between(1, 360), "aspect"]  = 180.0
        df.loc[~df["loss_pct"].between(0, 90),  "loss_pct"]  = 14.0
        df.loc[~df["soc_min_pct"].between(0, 90), "soc_min_pct"] = 20.0
        df.loc[df["efficiency"].notna() & ~df["efficiency"].between(0, 1), "efficiency"] = 0.15

        df = df[df["pv_peak_power_kw"] > 0]
        for col in ["panel_area_m2", "battery_capacity_kwh", "installation_cost_eur"]:
            df.loc[df[col] < 0, col] = 0

        # ── Deduplication (keep most recent ingestion per client) ─────────────
        df = df.sort_values("_ingested_at_utc", ascending=False)
        df = df.drop_duplicates(subset=["client_id"], keep="first")
        df["_ingested_at_utc"] = df["_ingested_at_utc"].dt.strftime("%Y-%m-%d %H:%M:%S")

        # ── Null imputation ───────────────────────────────────────────────────
        df = df.fillna({
            "description":           "unknown",
            "nominal_load_kw":       df["pv_peak_power_kw"] * 1.3,
            "panel_area_m2":         0.0,
            "efficiency":            0.15,
            "panel_type":            "unknown",
            "loss_pct":              14.0,
            "angle":                 30.0,
            "aspect":                180.0,
            "mounting":              "unknown",
            "battery_capacity_kwh":  0.0,
            "soc_min_pct":           20.0,
            "installation_cost_eur": 0.0,
            "timezone":              "UTC",
        })

        df = df.reset_index(drop=True)
        logger.info("[TRANSFORM] Silver-quality records produced: %d", len(df))
        return df

    except Exception as exc:
        logger.error("[TRANSFORM] Transformation failed: %s", exc)
        return pd.DataFrame()


# ─────────────────────────────────────────────────────────────────────────────
# LOAD → SILVER
# ─────────────────────────────────────────────────────────────────────────────

def load_clients_to_silver(df: pd.DataFrame, table_name: str = "clean_clients") -> bool:
    """
    Rebuilds the Silver client table from scratch and bulk-inserts the
    validated DataFrame.  client_id is enforced as PRIMARY KEY.
    """
    db_path = workspace_manager.get_db_path()

    if df.empty:
        logger.warning("[LOAD] DataFrame is empty — nothing written to '%s'", table_name)
        return False

    logger.info("[LOAD] Writing %d record(s) to '%s'", len(df), table_name)

    try:
        engine = create_engine(f"sqlite:///{db_path}")

        with engine.begin() as conn:
            conn.execute(text(f"DROP TABLE IF EXISTS {table_name}"))
            conn.execute(text(f"""
                CREATE TABLE {table_name} (
                    client_id               TEXT NOT NULL PRIMARY KEY,
                    name                    TEXT NOT NULL,
                    description             TEXT NOT NULL,
                    latitude                REAL NOT NULL,
                    longitude               REAL NOT NULL,
                    nominal_load_kw         REAL NOT NULL,
                    pv_peak_power_kw        REAL NOT NULL,
                    panel_area_m2           REAL NOT NULL,
                    efficiency              REAL NOT NULL,
                    panel_type              TEXT NOT NULL,
                    loss_pct                REAL NOT NULL,
                    angle                   REAL NOT NULL,
                    aspect                  REAL NOT NULL,
                    mounting                TEXT NOT NULL,
                    battery_capacity_kwh    REAL NOT NULL,
                    soc_min_pct             REAL NOT NULL,
                    installation_cost_eur   REAL NOT NULL,
                    timezone                TEXT NOT NULL,
                    _source_file            TEXT NOT NULL,
                    _ingested_at_utc        TEXT NOT NULL
                )
            """))
            df.to_sql(table_name, con=conn, if_exists="append", index=False)

        logger.info("[LOAD] '%s' rebuilt — %d record(s) inserted", table_name, len(df))
        return True

    except Exception as exc:
        logger.error("[LOAD] Failed to write to '%s': %s", table_name, exc)
        return False


# ─────────────────────────────────────────────────────────────────────────────
# ORCHESTRATOR ENTRY POINT
# ─────────────────────────────────────────────────────────────────────────────

def transform_clients() -> int:
    """
    Module entry point: reads pending/error tasks from the Bronze manifest,
    transforms each file and loads it to Silver, then persists updated task
    statuses.  Returns the total number of rows committed to Silver.
    """
    logger.info("[INIT] ── transform_clients starting ──────────────────────────")

    bronze_dir    = workspace_manager.get_bronze_path()
    manifest_path = os.path.join(bronze_dir, "_process_manifest_clients.json")

    if not os.path.exists(manifest_path):
        logger.info("[INIT] No manifest found at %s — nothing to process", manifest_path)
        return 0

    with open(manifest_path, "r", encoding="utf-8") as fh:
        all_tasks = json.load(fh)

    actionable = [t for t in all_tasks if t["status"] in ("pending", "error")]
    if not actionable:
        logger.info("[INIT] All manifest tasks already processed — nothing to do")
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
            df_raw = extract_clients_from_json(path_file)
            if df_raw.empty:
                raise ValueError("Bronze file is empty or unreadable")

            df_silver = transform_clients_bronze_to_silver(df_raw)
            if df_silver.empty:
                raise ValueError("Transformation produced an empty DataFrame")

            rows = len(df_silver)
            if load_clients_to_silver(df_silver):
                task.update({"status": "success", "updated_at": datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")})
                task.pop("error", None)
                session_rows += rows
                session_ok   += 1
                logger.info("[LOAD] %s → %d row(s) committed to Silver", fname, rows)
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
        "[DONE] transform_clients finished — tasks ok: %d | errors: %d | rows written: %d",
        session_ok, session_err, session_rows,
    )
    return session_rows


# ─────────────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    transform_clients()
