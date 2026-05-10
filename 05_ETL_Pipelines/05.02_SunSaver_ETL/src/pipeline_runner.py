import sys
import time
import argparse
from datetime import datetime, timezone
from typing import Callable, Tuple

# ── Project Modules ──────────────────────────────────────────────────────────
from logger_config import setup_logging
from audit_metadata import save_etl_metadata

# Import functional modules (Bronze/Silver/Gold layers)
import bronze_ingest_clients
import bronze_ingest_prices_ree
import silver_transform_clients
import silver_transform_prices
import bronze_ingest_weather_owm
import silver_transform_weather
import silver_calc_pv_generation
import gold_dim_clients
import gold_dim_datetime
import gold_dim_weather
import gold_fact_energy_forecast

"""
SUNSAVER ETL ORCHESTRATOR
-------------------------
Author: Aitor Asin
Description: Master controller for the SunSaver pipeline. Manages cross-layer 
             dependencies from Bronze ingestion to Gold-standard analytical tables.
             Implements stage-gate logic, performance profiling, and audit logging.
"""

logger = setup_logging()

# ─────────────────────────────────────────────────────────────────────────────
# PIPELINE TOPOLOGY
# ─────────────────────────────────────────────────────────────────────────────
# Define stages, task names, and function pointers for easy maintenance.
PIPELINE: list[tuple[int, str, Callable]] = [
    (1, "Extract Clients",           bronze_ingest_clients.extract_clients),
    (1, "Extract Energy Prices",     bronze_ingest_prices_ree.extract_energy_prices),
    (2, "Transform Clients",         silver_transform_clients.transform_clients),
    (2, "Transform Energy Prices",   silver_transform_prices.transform_energy_prices),
    (3, "Extract OpenWeather",       bronze_ingest_weather_owm.extract_openweather),
    (4, "Transform OpenWeather",     silver_transform_weather.transform_openweather),
    (5, "Calculate PV Generation",   silver_calc_pv_generation.extract_generation_data),
    (6, "Gold: Dim Clients",          gold_dim_clients.load_dim_client),
    (6, "Gold: Dim Datetime",         gold_dim_datetime.load_dim_datetime),
    (6, "Gold: Dim Weather",          gold_dim_weather.load_dim_weather),
    (6, "Gold: Fact Energy Forecast", gold_fact_energy_forecast.load_fact_energy_forecast),
]

# ─────────────────────────────────────────────────────────────────────────────
# RUNNER CORE
# ─────────────────────────────────────────────────────────────────────────────

def run_step(name: str, fn: Callable, dry_run: bool = False) -> Tuple[bool, int]:
    """
    Executes a single pipeline task and tracks its metrics.
    Returns: (success_bool, rows_processed_int)
    """
    if dry_run:
        logger.info(f" [DRY-RUN] Step: {name}")
        return True, 0

    logger.info(f"  ▶  Executing: {name} ...")
    t0 = time.monotonic()

    try:
        # Pipeline functions return Row Count (int) or Success Status (bool)
        result = fn()
        elapsed = time.monotonic() - t0

        if result is False:
            logger.error(f"  ✗  {name} returned False ({elapsed:.1f}s)")
            return False, 0

        # Cast boolean True to 0, otherwise use the returned row count
        rows = result if isinstance(result, int) else 0
        
        logger.info(f"  ✔  {name} finished ({elapsed:.1f}s) | Records: {rows}")
        return True, rows

    except Exception as e:
        elapsed = time.monotonic() - t0
        logger.error(f"  ✗  {name} CRITICAL ERROR ({elapsed:.1f}s): {e}", exc_info=True)
        return False, 0


def run_pipeline(from_stage: int = 1, dry_run: bool = False) -> bool:
    """
    Executes the full ETL flow and persists audit metadata.
    """
    t_global_start = time.monotonic() 
    started_at = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")
    pipeline_status = "SUCCESS"
    errors_list = []
    total_rows_processed = 0

    logger.info("\n" + "*" * 100)
    logger.info(f"  SUNSAVER PIPELINE START — {started_at} (UTC)")
    if from_stage > 1: logger.info(f"  Resuming from Stage {from_stage}")
    if dry_run:        logger.info("  [!] DRY-RUN MODE: No side effects")
    logger.info("*" * 100)

    steps_ok = steps_ko = 0
    current_stage = None
    stage_results: dict[int, list[bool]] = {}

    try:
        for stage_num, name, fn in PIPELINE:
            if stage_num < from_stage: continue

            # Visual stage break
            if stage_num != current_stage:
                current_stage = stage_num
                logger.info(f"\n── STAGE {stage_num} {'─'*50}")

            # Execute task
            ok, rows = run_step(name, fn, dry_run=dry_run)
            total_rows_processed += rows
            
            stage_results.setdefault(stage_num, []).append(ok)
            
            if ok: steps_ok += 1
            else:
                steps_ko += 1
                errors_list.append(name)

            # Fault Tolerance: If a whole stage fails, stop the entire pipeline
            if not any(stage_results[stage_num]):
                pipeline_status = f"FAILED AT STAGE {stage_num}"
                logger.critical(f"\n💥 Stage {stage_num} failed completely. Aborting.")
                return False

    except Exception as e:
        pipeline_status = "CRITICAL ERROR"
        errors_list.append(str(e)[:50])
        logger.error(f"Unexpected orchestrator error: {e}")
        raise e

    finally:
        # Performance calculation
        elapsed_total = time.monotonic() - t_global_start
        error_detail = f"Failures in: {', '.join(errors_list)}" if errors_list else None

        if steps_ko > 0 and "FAILED" not in pipeline_status:
            pipeline_status = "PARTIAL SUCCESS"

        # Persistence of Pipeline Run Audit
        if not dry_run:
            try:
                save_etl_metadata(
                    status=pipeline_status, 
                    duration=round(elapsed_total, 2),
                    rows=total_rows_processed, 
                    error=error_detail
                )
                logger.info(f"[AUDIT] Run metadata saved. Rows: {total_rows_processed}")
            except Exception as meta_err:
                logger.error(f"[AUDIT] Meta-persistence failed: {meta_err}")

        logger.info("\n" + "=" * 100)
        logger.info(f"  PIPELINE FINISHED in {elapsed_total:.2f}s")
        logger.info(f"  Rows: {total_rows_processed}  |  OK: {steps_ok}  |  KO: {steps_ko}")

    return steps_ko == 0

# ── CLI ENTRYPOINT ───────────────────────────────────────────────────────────

def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="SunSaver ETL Pipeline Orchestrator.",
        formatter_class=argparse.RawTextHelpFormatter,
    )
    parser.add_argument("--stage", type=int, default=1, help="Start from stage N (1-6).")
    parser.add_argument("--dry-run", action="store_true", help="Log execution plan only.")
    return parser.parse_args()


if __name__ == "__main__":
    args = parse_args()
    success = run_pipeline(from_stage=args.stage, dry_run=args.dry_run)
    sys.exit(0 if success else 1)