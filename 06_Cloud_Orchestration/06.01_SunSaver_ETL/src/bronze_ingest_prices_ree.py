import requests
import stat
import os
from datetime import datetime, timedelta, timezone
from dotenv import load_dotenv
import json
from typing import Optional, Union

import config_paths
from logger_config import setup_logging


logger = setup_logging()
load_dotenv()


# ─────────────────────────────────────────────────────────────────────────────
# EXTRACT
# ─────────────────────────────────────────────────────────────────────────────

def extract_raw_json_from_ree() -> Union[dict, bool]:
    """
    Fetches tomorrow's PVPC prices (id=1001) from Red Eléctrica de España.
    Returns the raw API payload or False when data is not yet published.
    """
    tomorrow = (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d")

    url = (
        "https://apidatos.ree.es/es/datos/mercados/precios-mercados-tiempo-real"
        f"?start_date={tomorrow}T00:00&end_date={tomorrow}T23:59"
        "&time_trunc=hour&geo_trunc=electric_system"
        "&geo_limit=peninsular&geo_ids=8741"
    )
    headers = {
        "Accept":   "application/json",
        "Origin":   "https://www.ree.es",
        "Referer":  "https://www.ree.es/",
    }

    logger.info("[EXTRACT] Requesting PVPC prices for %s from REE API", tomorrow)

    try:
        response = requests.get(url, headers=headers, timeout=15)
        response.raise_for_status()
        all_data = response.json()

        pvpc_item = next(
            (item for item in all_data.get("included", []) if item.get("id") == "1001"),
            None,
        )

        if pvpc_item and pvpc_item["attributes"].get("values"):
            n_values = len(pvpc_item["attributes"]["values"])
            logger.info("[EXTRACT] PVPC data retrieved — %d hourly values for %s", n_values, tomorrow)
            all_data["included"] = [pvpc_item]
            return all_data

        logger.warning(
            "[EXTRACT] REE returned no PVPC values for %s "
            "(prices are typically published after 20:30 CET)",
            tomorrow,
        )
        return False

    except requests.exceptions.HTTPError as exc:
        code = response.status_code
        if code in (500, 502, 503, 504):
            logger.error("[EXTRACT] REE server unavailable (HTTP %d) — prices not yet published", code)
        else:
            logger.error("[EXTRACT] Unexpected HTTP error from REE (HTTP %d): %s", code, exc)
        return False

    except Exception as exc:
        logger.error("[EXTRACT] Unexpected error contacting REE API: %s", exc)
        return False


# ─────────────────────────────────────────────────────────────────────────────
# INGEST → BRONZE
# ─────────────────────────────────────────────────────────────────────────────

def ingest_ree_to_bronze(api_response: dict) -> Optional[str]:
    """
    Persists the raw REE payload to the Bronze layer as an immutable JSON file
    (chmod 444) and returns the absolute path for lineage tracking.
    """
    bronze_dir = config_paths.get_bronze_path()
    os.makedirs(bronze_dir, exist_ok=True)

    timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    filename  = f"prices_{timestamp}.json"
    full_path = os.path.join(bronze_dir, filename)

    logger.info("[BRONZE] Writing REE payload → %s", filename)

    try:
        with open(full_path, "w", encoding="utf-8") as fh:
            json.dump(api_response, fh, ensure_ascii=False, indent=4)

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
    """Appends a new 'pending' entry to the REE process manifest."""
    manifest_path = os.path.join(bronze_dir, "_process_manifest_ree.json")

    new_task = {
        "source":     "REE",
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
            logger.warning("[MANIFEST] Could not parse existing REE manifest — starting fresh")

    all_tasks.append(new_task)

    with open(manifest_path, "w", encoding="utf-8") as fh:
        json.dump(all_tasks, fh, indent=4, ensure_ascii=False)

    pending = sum(1 for t in all_tasks if t["status"] == "pending")
    logger.info("[MANIFEST] REE manifest updated — pending tasks: %d", pending)


# ─────────────────────────────────────────────────────────────────────────────
# ORCHESTRATOR ENTRY POINT
# ─────────────────────────────────────────────────────────────────────────────

def extract_energy_prices() -> Union[int, bool]:
    """
    Module entry point: fetch PVPC → ingest to Bronze → update manifest.

    Returns:
        int  — number of hourly price records ingested on success.
        False — when REE data is unavailable or a critical error occurs,
                signalling the orchestrator to mark the run as PARTIAL SUCCESS.
    """
    logger.info("[INIT] ── extract_energy_prices starting ────────────────────")

    raw_prices = extract_raw_json_from_ree()
    if raw_prices is False:
        logger.warning("[INIT] No REE data available — signalling PARTIAL SUCCESS to orchestrator")
        return False

    try:
        total_hours = len(raw_prices["included"][0]["attributes"]["values"])
    except (KeyError, IndexError):
        logger.error("[EXTRACT] Unrecognised REE payload structure — cannot count records")
        return False

    path_file = ingest_ree_to_bronze(raw_prices)
    if not path_file:
        logger.error("[BRONZE] Ingestion failed — aborting")
        return False

    bronze_dir = config_paths.get_bronze_path()
    _update_manifest(str(bronze_dir), path_file)

    logger.info("[DONE] extract_energy_prices finished — hourly records ingested: %d", total_hours)
    return total_hours


# ─────────────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    extract_energy_prices()
