import os
import json
import stat
import pandas as pd
from typing import Optional
from pathlib import Path
from datetime import datetime, timezone

import workspace_manager
from logger_config import setup_logging


logger = setup_logging()


# ─────────────────────────────────────────────────────────────────────────────
# EXTRACT
# ─────────────────────────────────────────────────────────────────────────────

def extract_clients_from_excel() -> list[dict]:
    """Reads the client master spreadsheet and returns raw records."""

    BASE_DIR   = Path(__file__).resolve().parent.parent
    excel_path = BASE_DIR / "data" / "clients_source.xlsx"

    logger.info("[EXTRACT] Source: %s", excel_path)

    if not excel_path.exists():
        logger.error("[EXTRACT] File not found: %s", excel_path)
        return []

    try:
        df = pd.read_excel(excel_path)
    except ImportError:
        logger.error("[EXTRACT] Missing dependency 'openpyxl' — run: pip install openpyxl")
        return []
    except Exception as exc:
        logger.error("[EXTRACT] Failed to read Excel: %s", exc)
        return []

    if df.empty:
        logger.warning("[EXTRACT] Spreadsheet is empty: %s", excel_path.name)
        return []

    # Normalise NaN → None so the JSON serialiser produces valid null values
    df = df.astype(object).where(pd.notnull(df), None)

    logger.info("[EXTRACT] %d client record(s) read from %s", len(df), excel_path.name)
    return df.to_dict(orient="records")


# ─────────────────────────────────────────────────────────────────────────────
# INGEST → BRONZE
# ─────────────────────────────────────────────────────────────────────────────

def ingest_clients_to_bronze(records: list[dict]) -> Optional[str]:
    """
    Persists raw client records to the Bronze layer as an immutable JSON file
    (chmod 444) and returns the absolute path for lineage tracking.
    """
    bronze_dir = workspace_manager.get_bronze_path()
    os.makedirs(bronze_dir, exist_ok=True)

    timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    filename  = f"clients_{timestamp}.json"
    full_path = os.path.join(bronze_dir, filename)

    logger.info("[BRONZE] Writing %d record(s) → %s", len(records), filename)

    try:
        with open(full_path, "w", encoding="utf-8") as fh:
            json.dump(records, fh, ensure_ascii=False, indent=4)

        os.chmod(full_path, stat.S_IRUSR | stat.S_IRGRP | stat.S_IROTH)   # 444 — immutable
        logger.info("[BRONZE] File sealed (chmod 444): %s", filename)
        return full_path

    except Exception as exc:
        logger.error("[BRONZE] Persistence failed for %s: %s", filename, exc)
        return None


# ─────────────────────────────────────────────────────────────────────────────
# MANIFEST
# ─────────────────────────────────────────────────────────────────────────────

def _update_manifest(bronze_dir: str, path_file: str) -> None:
    """Appends a new 'pending' entry to the clients process manifest."""
    manifest_path = os.path.join(bronze_dir, "_process_manifest_clients.json")

    new_task = {
        "source":     "clients_source.xlsx",
        "path":       path_file,
        "status":     "pending",
        "created_at": datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S"),
        "updated_at": datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S"),
    }

    all_tasks: list = []
    if os.path.exists(manifest_path):
        try:
            with open(manifest_path, "r", encoding="utf-8") as fh:
                all_tasks = json.load(fh)
        except Exception:
            logger.warning("[MANIFEST] Could not parse existing manifest — starting fresh")

    all_tasks.append(new_task)

    with open(manifest_path, "w", encoding="utf-8") as fh:
        json.dump(all_tasks, fh, indent=4, ensure_ascii=False)

    pending = sum(1 for t in all_tasks if t["status"] == "pending")
    logger.info("[MANIFEST] clients manifest updated — pending tasks: %d", pending)


# ─────────────────────────────────────────────────────────────────────────────
# ORCHESTRATOR ENTRY POINT
# ─────────────────────────────────────────────────────────────────────────────

def extract_clients() -> int:
    """
    Module entry point: extract → ingest to Bronze → update manifest.
    Returns the number of raw client records ingested (0 on failure).
    """
    logger.info("[INIT] ── extract_clients starting ──────────────────────────")

    raw_clients = extract_clients_from_excel()
    if not raw_clients:
        logger.warning("[INIT] No records extracted — aborting")
        return 0

    path_file = ingest_clients_to_bronze(raw_clients)
    if not path_file:
        logger.error("[INIT] Bronze ingestion failed — aborting")
        return 0

    bronze_dir = workspace_manager.get_bronze_path()
    _update_manifest(str(bronze_dir), path_file)

    total = len(raw_clients)
    logger.info("[DONE] extract_clients finished — records ingested: %d", total)
    return total


# ─────────────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    extract_clients()
