import os
import json
import stat
import requests
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Optional, Union
from dotenv import load_dotenv

import config_paths
from logger_config import setup_logging

"""
ENERGY PRICE INGESTION: REE API TO BRONZE LAYER
----------------------------------------------
Author: Aitor Asin
Description: Automated extraction of PVPC (Spanish electricity market) prices.
             Implements robust error handling for API availability and 
             ensures data lineage through a manifest-driven architecture.
"""

logger = setup_logging()
load_dotenv()

# ─────────────────────────────────────────────────────────────────────────────
# EXTRACT LAYER: API INTERFACE
# ─────────────────────────────────────────────────────────────────────────────

def extract_raw_json_from_ree() -> Union[dict, bool]:
    """
    Fetches the PVPC energy prices for the next day from Red Eléctrica de España (REE).
    Returns the raw API payload or False if data is unpublished or unavailable.
    """
    #today =datetime.now().strftime("%Y-%m-%d")
    tomorrow = (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d")

    # API configuration for PVPC (id=1001)
    url = (
        "https://apidatos.ree.es/es/datos/mercados/precios-mercados-tiempo-real"
        f"?start_date={tomorrow}T00:00&end_date={tomorrow}T23:59"
        "&time_trunc=hour&geo_trunc=electric_system"
        "&geo_limit=peninsular&geo_ids=8741"
    )
    headers = {
        "Accept": "application/json",
        "Origin": "https://www.ree.es",
        "Referer": "https://www.ree.es/",
    }

    logger.info("[EXTRACT] Requesting PVPC prices for %s from REE API", tomorrow)

    try:
        response = requests.get(url, headers=headers, timeout=15)
        response.raise_for_status()
        all_data = response.json()

        # Identify the specific PVPC series (ID 1001)
        pvpc_item = next(
            (item for item in all_data.get("included", []) if item.get("id") == "1001"),
            None
        )

        if pvpc_item and pvpc_item.get("attributes", {}).get("values"):
            n_values = len(pvpc_item["attributes"]["values"])
            logger.info("[EXTRACT] PVPC data retrieved — %d hourly values for %s", n_values, tomorrow)
            
            # Return only the relevant node to minimize storage footprint
            all_data["included"] = [pvpc_item]
            return all_data

        logger.warning("[EXTRACT] No PVPC values for %s (Expected publication > 20:30 CET)", tomorrow)
        return False

    except requests.exceptions.HTTPError as exc:
        status_code = exc.response.status_code
        logger.error("[EXTRACT] API HTTP Error %d: %s", status_code, exc)
    except Exception as exc:
        logger.error("[EXTRACT] Unexpected API connection error: %s", exc)
    
    return False


# ─────────────────────────────────────────────────────────────────────────────
# LOAD LAYER: BRONZE PERSISTENCE
# ─────────────────────────────────────────────────────────────────────────────

def ingest_ree_to_bronze(api_response: dict) -> Optional[str]:
    """
    Saves the API response as an immutable JSON file in the Bronze zone.
    Implements file-level protection to ensure data integrity.
    """
    bronze_dir = Path(config_paths.get_bronze_path())
    bronze_dir.mkdir(parents=True, exist_ok=True)

    timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    full_path = bronze_dir / f"prices_{timestamp}.json"

    logger.info("[BRONZE] Persisting REE payload → %s", full_path.name)

    try:
        with full_path.open("w", encoding="utf-8") as fh:
            json.dump(api_response, fh, ensure_ascii=False, indent=4)

        # Set immutable: Read-only for User, Group, and Others (444)
        os.chmod(full_path, stat.S_IRUSR | stat.S_IRGRP | stat.S_IROTH)
        logger.info("[BRONZE] File sealed (chmod 444): %s", full_path.name)
        return str(full_path.absolute())

    except Exception as exc:
        logger.error("[BRONZE] Failed to write file %s: %s", full_path.name, exc)
        return None


# ─────────────────────────────────────────────────────────────────────────────
# CONTROL LAYER: MANIFEST & ORCHESTRATION
# ─────────────────────────────────────────────────────────────────────────────

def _update_manifest(bronze_dir: str, path_file: str) -> None:
    """
    Appends the ingestion task to the REE control manifest.
    Used by the Silver layer to track unprocessed files.
    """
    manifest_path = Path(bronze_dir) / "_process_manifest_ree.json"
    now_ts = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")

    new_task = {
        "source": "REE",
        "path": path_file,
        "status": "pending",
        "created_at": now_ts,
        "updated_at": now_ts,
    }

    all_tasks = []
    if manifest_path.exists():
        try:
            with manifest_path.open("r", encoding="utf-8") as fh:
                all_tasks = json.load(fh)
        except Exception:
            logger.warning("[MANIFEST] Corrupt manifest — creating new history")

    all_tasks.append(new_task)

    with manifest_path.open("w", encoding="utf-8") as fh:
        json.dump(all_tasks, fh, indent=4, ensure_ascii=False)

    pending = sum(1 for t in all_tasks if t["status"] == "pending")
    logger.info("[MANIFEST] REE manifest updated — pending tasks: %d", pending)


def extract_energy_prices() -> Union[int, bool]:
    """
    Core execution flow: API Fetch -> Bronze Storage -> Manifest Update.
    Returns record count or False for orchestration flow control.
    """
    logger.info("[INIT] ── extract_energy_prices starting ────────────────────")

    # 1. API Extraction
    raw_prices = extract_raw_json_from_ree()
    if raw_prices is False:
        logger.warning("[INIT] Data unavailable — signalling PARTIAL SUCCESS")
        return False

    # 2. Record Validation
    try:
        total_hours = len(raw_prices["included"][0]["attributes"]["values"])
    except (KeyError, IndexError):
        logger.error("[EXTRACT] Invalid API payload structure")
        return False

    # 3. Bronze Ingestion
    path_file = ingest_ree_to_bronze(raw_prices)
    if not path_file:
        return False

    # 4. Manifest Registration
    bronze_dir = config_paths.get_bronze_path()
    _update_manifest(str(bronze_dir), path_file)

    logger.info("[DONE] Ingestion complete — hourly records: %d", total_hours)
    return total_hours


if __name__ == "__main__":
    extract_energy_prices()