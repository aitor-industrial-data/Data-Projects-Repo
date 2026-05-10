"""
orchestrator.py
---------------
Orquestador del pipeline ETL de SunSaver con recuento de registros.
"""

import sys
import time
import argparse
from datetime import datetime, timezone
from typing import Callable, Tuple, Union

# ── Módulos del proyecto ─────────────────────────────────────────────────────
from logger_config import setup_logging
from audit_metadata import save_etl_metadata
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

# ── Logging ───────────────────────────────────────────────────────────────────

logger = setup_logging()

# ─────────────────────────────────────────────────────────────────────────────
# Definición del pipeline
# ─────────────────────────────────────────────────────────────────────────────
PIPELINE: list[tuple[int, str, Callable]] = [
    (1, "extract_clients",           bronze_ingest_clients.extract_clients),
    (1, "extract_energy_prices",     bronze_ingest_prices_ree.extract_energy_prices),
    (2, "transform_clients",         silver_transform_clients.transform_clients),
    (2, "transform_energy_prices",   silver_transform_prices.transform_energy_prices),
    (3, "extract_openweather",       bronze_ingest_weather_owm.extract_openweather),
    (4, "transform_openweather",     silver_transform_weather.transform_openweather),
    (5, "extract_generation_data",   silver_calc_pv_generation.extract_generation_data),
    (6, "gold_dim_clients",          gold_dim_clients.load_dim_client),
    (6, "gold_dim_datetime",         gold_dim_datetime.load_dim_datetime),
    (6, "gold_dim_weather",          gold_dim_weather.load_dim_weather),
    (6, "gold_fact_energy",          gold_fact_energy_forecast.load_fact_energy_forecast),
]

# ─────────────────────────────────────────────────────────────────────────────
# Runner
# ─────────────────────────────────────────────────────────────────────────────

def run_step(name: str, fn: Callable, dry_run: bool = False) -> Tuple[bool, int]:
    """
    Ejecuta un paso del pipeline. 
    Devuelve: (éxito: bool, filas_procesadas: int)
    """
    if dry_run:
        logger.info(f" [DRY-RUN] {name}")
        return True, 0

    logger.info(f"  ▶  {name} ...")
    t0 = time.monotonic()

    try:
        # Ejecutamos la función. Se espera que devuelva un entero (filas) o True/False.
        result = fn()
        elapsed = time.monotonic() - t0

        if result is False:
            logger.error(f"  ✗  {name} devolvió False ({elapsed:.1f}s)")
            return False, 0

        # Si el resultado es un entero, lo usamos como recuento; si es True, usamos 0.
        rows = result if isinstance(result, int) else 0
        
        logger.info(f"  ✔  {name} completado ({elapsed:.1f}s) | Filas: {rows}")
        return True, rows

    except Exception as e:
        elapsed = time.monotonic() - t0
        logger.error(f"  ✗  {name} lanzó excepción ({elapsed:.1f}s): {e}", exc_info=True)
        return False, 0


def run_pipeline(from_stage: int = 1, dry_run: bool = False) -> bool:
    """
    Ejecuta el pipeline completo y consolida métricas.
    """
    t_global_start = time.monotonic() 
    started_at = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")
    pipeline_status = "SUCCESS"
    errors_list = []
    total_rows_processed = 0  # <--- Acumulador de registros reales

    logger.info("\n"+ "*" * 120)
    logger.info("=" * 60)
    logger.info(f"  PIPELINE SUNSAVER — inicio (UTC): {started_at}")
    
    if from_stage > 1:
        logger.info(f"  Arrancando desde stage {from_stage}")
    if dry_run:
        logger.info("  MODO DRY-RUN: no se ejecuta nada")
    logger.info("=" * 60)

    steps_ok = 0
    steps_ko = 0
    current_stage = None
    stage_results: dict[int, list[bool]] = {}

    try:
        for stage_num, name, fn in PIPELINE:
            if stage_num < from_stage:
                continue

            if stage_num != current_stage:
                current_stage = stage_num
                logger.info(f"\n── STAGE {stage_num} {'─'*40}")

            # Ejecutamos el paso y capturamos éxito y filas
            ok, rows = run_step(name, fn, dry_run=dry_run)
            total_rows_processed += rows

            stage_results.setdefault(stage_num, []).append(ok)
            
            if ok:
                steps_ok += 1
            else:
                steps_ko += 1
                errors_list.append(name)

            if not any(stage_results[stage_num]):
                pipeline_status = f"FAILED AT STAGE {stage_num}"
                logger.critical(f"\n💥 Stage {stage_num} ha abortado completamente.")
                return False

    except Exception as e:
        pipeline_status = "CRITICAL ERROR"
        errors_list.append(f"EXCEPTION: {str(e)[:50]}...")
        logger.error(f"Error inesperado en el orquestador: {e}")
        raise e

    finally:
        elapsed_total = time.monotonic() - t_global_start
        error_detail = f"Fallos en: {', '.join(errors_list)}" if errors_list else None

        if steps_ko > 0 and "FAILED" not in pipeline_status:
            pipeline_status = "PARTIAL SUCCESS"

        if not dry_run:
            try:
                # Ahora 'rows' guarda el recuento total acumulado de registros procesados
                save_etl_metadata(
                    status=pipeline_status, 
                    duration=round(elapsed_total, 2),
                    rows=total_rows_processed, 
                    error=error_detail
                )
                logger.info(f"[METADATA] Registro guardado. Status: {pipeline_status} | Total Filas: {total_rows_processed}")
            except Exception as meta_err:
                logger.error(f"[METADATA] Error al guardar auditoría: {meta_err}")

        logger.info("\n" + "=" * 104)
        logger.info(f"  PIPELINE FINALIZADO en {elapsed_total:.2f}s")
        logger.info(f"  Total Filas: {total_rows_processed}  |  Steps OK: {steps_ok}  |  Steps KO: {steps_ko}")

    return steps_ko == 0

# ── CLI ──────────────────────────────────────────────────────────────────────

def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Orquestador del pipeline ETL SunSaver.",
        formatter_class=argparse.RawTextHelpFormatter,
    )
    parser.add_argument(
        "--stage", type=int, default=1, metavar="N",
        help="Stage desde el que arrancar (1-6)."
    )
    parser.add_argument(
        "--dry-run", action="store_true",
        help="Muestra el plan de ejecución sin llamar a ninguna función.",
    )
    return parser.parse_args()


if __name__ == "__main__":
    args = parse_args()
    success = run_pipeline(from_stage=args.stage, dry_run=args.dry_run)
    sys.exit(0 if success else 1)