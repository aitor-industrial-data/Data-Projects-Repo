import os
import json
import stat
import pandas as pd
from typing import Optional
from pathlib import Path
from datetime import datetime, timezone

import config_paths
from logger_config import setup_logging

"""
BRONZE LAYER: CLIENT INGESTION (Source-to-Bronze)
------------------------------------------------
Author: Aitor Asin
Description: Extracts raw client data from Excel spreadsheets and persists 
             it as immutable JSON files in the Bronze layer. 
             Tracks lineage via a persistent process manifest.
"""

logger = setup_logging()

# ─────────────────────────────────────────────────────────────────────────────
# STEP 1: EXTRACT (Source System)
# ─────────────────────────────────────────────────────────────────────────────

def extract_clients_from_excel() -> list[dict]:
    """
    Reads the master client Excel file.
    Includes dependency checks and null-value normalisation for JSON safety.
    """
    BASE_DIR   = Path(__file__).resolve().parent.parent
    excel_path = BASE_DIR / "data" / "clients_source.xlsx"

    logger.info("[EXTRACT] Reading source master: %s", excel_path.name)

    if not excel_path.exists():
        logger.error("[EXTRACT] Source file missing at %s", excel_path)
        return []

    try:
        # Load data using pandas
        df = pd.read_excel(excel_path)
        
        if df.empty:
            logger.warning("[EXTRACT] Source file is empty.")
            return []

        # Normalise NaN to None (JSON null) to ensure serialisation consistency
        df = df.astype(object).where(pd.notnull(df), None)
        
        logger.info("[EXTRACT] %d raw records loaded from Excel", len(df))
        return df.to_dict(orient="records")

    except ImportError:
        logger.error("[EXTRACT] Dependency 'openpyxl' not found. Please install it.")
        return []
    except Exception as exc:
        logger.error("[EXTRACT] Extraction failed: %s", exc)
        return []

# ─────────────────────────────────────────────────────────────────────────────
# STEP 2: INGEST (Bronze Persistence)
# ─────────────────────────────────────────────────────────────────────────────

def ingest_clients_to_bronze(records: list[dict]) -> Optional[str]:
    """
    Saves records into the Bronze directory. 
    Applies chmod 444 to treat the data as a 'Single Source of Truth' (immutable).
    """
    bronze_dir = config_paths.get_bronze_path()
    os.makedirs(bronze_dir, exist_ok=True)

    # Unique identifier for the batch (IDP: Ingestion Date/Time)
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    filename  = f"clients_{timestamp}.json"
    full_path = os.path.join(bronze_dir, filename)

    try:
        logger.info("[BRONZE] Persisting immutable batch: %s", filename)
        
        with open(full_path, "w", encoding="utf-8") as fh:
            json.dump(records, fh, ensure_ascii=False, indent=4)

        # Apply Read-Only permissions (immutable logic)
        os.chmod(full_path, stat.S_IRUSR | stat.S_IRGRP | stat.S_IROTH) 
        
        return full_path
    except Exception as exc:
        logger.error("[BRONZE] Persistence failed: %s", exc)
        return None

# ─────────────────────────────────────────────────────────────────────────────
# STEP 3: LINEAGE (Manifest Tracking)
# ─────────────────────────────────────────────────────────────────────────────

def _update_manifest(bronze_dir: str, path_file: str) -> None:
    """
    Updates the shared manifest file to alert the Silver layer of new pending data.
    """
    manifest_path = os.path.join(bronze_dir, "_process_manifest_clients.json")

    new_task = {
        "source":     "clients_source.xlsx",
        "path":       path_file,
        "status":     "pending",
        "created_at": datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S"),
        "updated_at": datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S"),
    }

    all_tasks = []
    if os.path.exists(manifest_path):
        try:
            with open(manifest_path, "r", encoding="utf-8") as fh:
                all_tasks = json.load(fh)
        except Exception:
            logger.warning("[MANIFEST] Recovering manifest state...")

    all_tasks.append(new_task)

    with open(manifest_path, "w", encoding="utf-8") as fh:
        json.dump(all_tasks, fh, indent=4, ensure_ascii=False)
    
    logger.info("[MANIFEST] Entry added for file lineage tracking")

# ─────────────────────────────────────────────────────────────────────────────
# ENTRY POINT
# ─────────────────────────────────────────────────────────────────────────────

def extract_clients() -> int:
    """
    Orchestrates the Bronze ingestion flow.
    Returns: Ingested row count (int)
    """
    logger.info("[INIT] ── Bronze Client Ingestion Started ──")

    raw_clients = extract_clients_from_excel()
    if not raw_clients: return 0

    path_file = ingest_clients_to_bronze(raw_clients)
    if not path_file: return 0

    _update_manifest(str(config_paths.get_bronze_path()), path_file)

    return len(raw_clients)

if __name__ == "__main__":
    extract_clients()