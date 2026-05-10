import os
import json
import stat
from sqlalchemy import create_engine
import requests
import pandas as pd
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Any, Optional
from dotenv import load_dotenv

import config_paths
from logger_config import setup_logging

"""
EXTERNAL DATA ENRICHMENT: OPENWEATHER API PIPELINE
--------------------------------------------------
Author: Aitor Asin
Description: Orchestrates weather data extraction based on existing client 
             coordinates. Implements a loop-and-ingest pattern with 
             fault tolerance and automated manifest tracking.
"""

logger = setup_logging()
load_dotenv()

# ─────────────────────────────────────────────────────────────────────────────
# EXTRACT LAYER: EXTERNAL API CONSUMPTION
# ─────────────────────────────────────────────────────────────────────────────

def extract_weather(lat: float, lon: float) -> Dict[str, Any]:
    """
    Calls OpenWeatherMap API for specific geographic coordinates.
    Returns the raw forecast payload.
    """
    api_key = os.getenv("WEATHER_API_KEY")

    if not api_key:
        logger.error("[EXTRACT] WEATHER_API_KEY missing in environment")
        return {}

    params = {
        "lat": lat,
        "lon": lon,
        "appid": api_key,
        "units": "metric",
        "lang": "en",
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

        logger.debug("[EXTRACT] Payload received for (lat=%.4f, lon=%.4f)", lat, lon)
        return data

    except Exception as exc:
        logger.error("[EXTRACT] API Failure for (lat=%.4f, lon=%.4f): %s", lat, lon, exc)
        raise


# ─────────────────────────────────────────────────────────────────────────────
# LOAD LAYER: BRONZE PERSISTENCE
# ─────────────────────────────────────────────────────────────────────────────

def ingest_openweather_to_bronze(api_response: dict, client_id: str) -> Optional[str]:
    """
    Persists the raw weather payload as an immutable JSON file.
    Naming convention includes client_id for easy partitioning/debugging.
    """
    bronze_dir = Path(config_paths.get_bronze_path())
    bronze_dir.mkdir(parents=True, exist_ok=True)

    timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    full_path = bronze_dir / f"weather_{client_id}_{timestamp}.json"

    try:
        with full_path.open("w", encoding="utf-8") as fh:
            json.dump(api_response, fh, ensure_ascii=False, indent=4)

        # Enforce immutability (Read-only 444)
        os.chmod(full_path, stat.S_IRUSR | stat.S_IRGRP | stat.S_IROTH)
        logger.info("[BRONZE] File sealed (chmod 444): %s", full_path.name)
        return str(full_path.absolute())

    except Exception as exc:
        logger.error("[BRONZE] Persistence failed for client %s: %s", client_id, exc)
        return None


# ─────────────────────────────────────────────────────────────────────────────
# CONTROL LAYER: BATCH MANIFEST UPDATE
# ─────────────────────────────────────────────────────────────────────────────

def _update_manifest(bronze_dir: str, new_extractions: list) -> None:
    """
    Updates the OpenWeather manifest with a batch of new extraction tasks.
    Ensures scalability by appending all successful extractions at once.
    """
    manifest_path = Path(bronze_dir) / "_process_manifest_openweather.json"
    all_tasks = []

    if manifest_path.exists():
        try:
            with manifest_path.open("r", encoding="utf-8") as fh:
                all_tasks = json.load(fh)
        except Exception:
            logger.warning("[MANIFEST] Manifest parse error — starting fresh")

    all_tasks.extend(new_extractions)

    with manifest_path.open("w", encoding="utf-8") as fh:
        json.dump(all_tasks, fh, indent=4, ensure_ascii=False)

    pending = sum(1 for t in all_tasks if t["status"] == "pending")
    logger.info("[MANIFEST] Updated — New: %d | Total Pending: %d", len(new_extractions), pending)


# ─────────────────────────────────────────────────────────────────────────────
# ORCHESTRATOR ENTRY POINT
# ─────────────────────────────────────────────────────────────────────────────



def extract_openweather(client_table: str = "clean_clients") -> int:
    """
    Main flow:
    1. Reads location metadata from the Silver Layer (Database) using SQLAlchemy.
    2. Iterates and fetches weather for each client.
    3. Ingests to Bronze and updates process control metadata.
    """
    logger.info("[INIT] ── extract_openweather starting ──────────────────────")
    db_path = config_paths.get_db_path()
    
    
    engine = create_engine(f"sqlite:///{db_path}")

    try:
        # Usamos el engine directamente con pandas
        with engine.connect() as conn:
            df_clients = pd.read_sql(
                f"SELECT client_id, latitude, longitude FROM {client_table}", 
                conn
            )
    except Exception as exc:
        logger.error("[EXTRACT] Failed to load clients from Silver layer: %s", exc)
        return 0

    logger.info("[EXTRACT] Processing %d client(s)", len(df_clients))

    new_extractions = []
    success_count = 0

    for _, row in df_clients.iterrows():
        c_id = row["client_id"]
        lat, lon = row["latitude"], row["longitude"]

        try:
            raw_weather = extract_weather(lat, lon)
            if not raw_weather:
                continue

            path_file = ingest_openweather_to_bronze(raw_weather, str(c_id))
            if path_file:
                new_extractions.append({
                    "source": "openweather",
                    "client_id": c_id,
                    "path": path_file,
                    "status": "pending",
                    "created_at": datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S"),
                    "updated_at": datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S"),
                })
                success_count += 1
                logger.info("[EXTRACT] client_id=%s → Ingested", c_id)

        except Exception as exc:
            logger.error("[EXTRACT] Critical error for client %s: %s", c_id, exc)
            continue

    
    if new_extractions:
        _update_manifest(config_paths.get_bronze_path(), new_extractions)

    logger.info("[DONE] Extraction finished — Files created: %d", success_count)
    return success_count


if __name__ == "__main__":
    extract_openweather()