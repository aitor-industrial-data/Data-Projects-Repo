import os
import json
import stat
import sqlite3
import requests
import pandas as pd
from dotenv import load_dotenv
from datetime import datetime, timezone
from typing import Dict, Any, Optional

import workspace_manager
from logger_config import setup_logging


logger = setup_logging()
load_dotenv()


# ─────────────────────────────────────────────────────────────────────────────
# EXTRACT
# ─────────────────────────────────────────────────────────────────────────────

def extract_weather(lat: float, lon: float) -> Dict[str, Any]:
    """Calls the OpenWeatherMap 5-day/3-hour forecast endpoint for one location."""
    API_KEY = os.getenv("WEATHER_API_KEY")

    if not API_KEY:
        logger.error("[EXTRACT] WEATHER_API_KEY is not set in the environment — check .env")
        return {}

    params = {
        "lat":   lat,
        "lon":   lon,
        "appid": API_KEY,
        "units": "metric",
        "lang":  "en",
    }

    try:
        response = requests.get(
            "https://api.openweathermap.org/data/2.5/forecast",
            params=params,
            timeout=15,
        )
        response.raise_for_status()
        data = response.json()

        if not data:
            raise ValueError("OpenWeatherMap returned an empty payload")

        logger.debug("[EXTRACT] Weather payload received for (lat=%.4f, lon=%.4f)", lat, lon)
        return data

    except Exception as exc:
        logger.error("[EXTRACT] Failed to fetch weather for (lat=%.4f, lon=%.4f): %s", lat, lon, exc)
        raise


# ─────────────────────────────────────────────────────────────────────────────
# INGEST → BRONZE
# ─────────────────────────────────────────────────────────────────────────────

def ingest_openweather_to_bronze(api_response: dict, client_id: str) -> Optional[str]:
    """
    Persists the raw OpenWeatherMap payload to the Bronze layer as an immutable
    JSON file (chmod 444) and returns the absolute path for lineage tracking.
    """
    bronze_dir = workspace_manager.get_bronze_path()
    os.makedirs(bronze_dir, exist_ok=True)

    timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    filename  = f"weather_{client_id}_{timestamp}.json"
    full_path = os.path.join(bronze_dir, filename)

    try:
        with open(full_path, "w", encoding="utf-8") as fh:
            json.dump(api_response, fh, ensure_ascii=False, indent=4)

        os.chmod(full_path, stat.S_IRUSR | stat.S_IRGRP | stat.S_IROTH)   # 444 — immutable
        logger.info("[BRONZE] File sealed (chmod 444): %s", filename)
        return full_path

    except Exception as exc:
        logger.error("[BRONZE] Persistence failed for client %s: %s", client_id, exc)
        return None


# ─────────────────────────────────────────────────────────────────────────────
# MANIFEST
# ─────────────────────────────────────────────────────────────────────────────

def _update_manifest(bronze_dir: str, new_extractions: list) -> None:
    """Appends new 'pending' entries to the OpenWeather process manifest."""
    manifest_path = os.path.join(bronze_dir, "_process_manifest_openweather.json")

    all_tasks: list = []
    if os.path.exists(manifest_path):
        try:
            with open(manifest_path, "r", encoding="utf-8") as fh:
                all_tasks = json.load(fh)
        except Exception:
            logger.warning("[MANIFEST] Could not parse existing OpenWeather manifest — starting fresh")

    all_tasks.extend(new_extractions)

    with open(manifest_path, "w", encoding="utf-8") as fh:
        json.dump(all_tasks, fh, indent=4, ensure_ascii=False)

    pending = sum(1 for t in all_tasks if t["status"] == "pending")
    logger.info(
        "[MANIFEST] OpenWeather manifest updated — new tasks: %d | total pending: %d",
        len(new_extractions),
        pending,
    )


# ─────────────────────────────────────────────────────────────────────────────
# ORCHESTRATOR ENTRY POINT
# ─────────────────────────────────────────────────────────────────────────────

def extract_openweather(client_table: str = "clean_clients") -> int:
    """
    Module entry point: reads active clients from Silver, fetches weather for
    each location, ingests payloads to Bronze, and updates the process manifest.

    Returns the number of Bronze files successfully created (0 on failure).
    """
    logger.info("[INIT] ── extract_openweather starting ──────────────────────")

    db_path = workspace_manager.get_db_path()

    try:
        with sqlite3.connect(str(db_path)) as conn:
            df_clients = pd.read_sql(
                f"SELECT client_id, latitude, longitude FROM {client_table}", conn
            )
    except Exception as exc:
        logger.error("[EXTRACT] Failed to read clients from '%s': %s", client_table, exc)
        return 0

    logger.info("[EXTRACT] %d client(s) loaded from '%s'", len(df_clients), client_table)

    new_extractions: list = []
    success_count   = 0
    error_count     = 0

    for _, row in df_clients.iterrows():
        client_id = row["client_id"]
        lat, lon  = row["latitude"], row["longitude"]

        try:
            raw_weather = extract_weather(lat, lon)

            if not raw_weather:
                logger.warning("[EXTRACT] Empty payload for client %s — skipping", client_id)
                error_count += 1
                continue

            path_file = ingest_openweather_to_bronze(raw_weather, client_id)
            if not path_file:
                error_count += 1
                continue

            new_extractions.append({
                "source":     "openweather",
                "client_id":  client_id,
                "path":       path_file,
                "status":     "pending",
                "created_at": datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S"),
                "updated_at": datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S"),
            })
            success_count += 1
            logger.info("[EXTRACT] client_id=%s → Bronze file written", client_id)

        except Exception as exc:
            logger.error("[EXTRACT] Error processing client %s: %s", client_id, exc)
            error_count += 1
            continue

    if new_extractions:
        bronze_dir = workspace_manager.get_bronze_path()
        _update_manifest(str(bronze_dir), new_extractions)

    logger.info(
        "[DONE] extract_openweather finished — files created: %d | errors: %d",
        success_count,
        error_count,
    )
    return success_count


# ─────────────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    extract_openweather()
