"""
orchestrator.py
---------------
Orquestador del pipeline ETL de SunSaver.

Orden de ejecución:
    STAGE 1 — Extracción Bronze
        1a. extract_clients          (Excel → raw_clients)
        1b. extract_energy_prices    (REE API → raw_prices)

    STAGE 2 — Transformación Silver independiente
        2a. transform_clients        (raw_clients → clean_clients)
        2b. transform_energy_prices  (raw_prices  → clean_prices)

    STAGE 3 — Extracción dependiente de Silver
        3a. extract_openweather      (OpenWeather API → raw_weather)  [necesita clean_clients]

    STAGE 4 — Transformación Silver dependiente
        4a. transform_openweather    (raw_weather → clean_weather)

    STAGE 5 — Cálculo PV  [necesita clean_clients + clean_weather]
        5a. extract_generation_data  (→ clean_calculations)

    STAGE 6 — Capa Gold
        6a. transform_gold_dim_clients
        6b. transform_gold_dim_datetime
        6c. transform_gold_dim_weather
        6d. transform_gold_fact_energy  [necesita las 3 dims anteriores]

Uso:
    python orchestrator.py           # Ejecuta el pipeline completo
    python orchestrator.py --stage 3 # Ejecuta solo desde el stage indicado
    python orchestrator.py --dry-run # Muestra el plan sin ejecutar nada
"""

import sys
import time
import logging
import argparse
from datetime import datetime, timezone
from typing import Callable

# ── Módulos del proyecto ─────────────────────────────────────────────────────
import extract_clients
import extract_energy_prices
import transform_clients
import transform_energy_prices
import extract_openweather
import transform_openweather
import extract_power_data
import transform_gold_dim_clients
import transform_gold_dim_datetime
import transform_gold_dim_weather
import transform_gold_fact_energy

# ── Logging ───────────────────────────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger("orchestrator")


# ─────────────────────────────────────────────────────────────────────────────
# Definición del pipeline
# Cada step es: (stage_num, nombre, función a ejecutar)
# ─────────────────────────────────────────────────────────────────────────────
PIPELINE: list[tuple[int, str, Callable]] = [
    # STAGE 1 — Bronze: fuentes externas, sin dependencias entre sí
    (1, "extract_clients",           extract_clients.extract_clients),
    (1, "extract_energy_prices",     extract_energy_prices.extract_energy_prices),

    # STAGE 2 — Silver: transformaciones independientes
    (2, "transform_clients",         transform_clients.transform_clients),
    (2, "transform_energy_prices",   transform_energy_prices.transform_energy_prices),

    # STAGE 3 — Bronze dependiente: necesita clean_clients para saber coordenadas
    (3, "extract_openweather",       extract_openweather.extract_openweather),

    # STAGE 4 — Silver dependiente: normaliza el JSON crudo del clima
    (4, "transform_openweather",     transform_openweather.transform_openweather),

    # STAGE 5 — Cálculo PV: necesita clean_clients + clean_weather
    (5, "extract_generation_data",   extract_power_data.extract_generation_data),

    # STAGE 6 — Gold: dimensiones primero, fact table al final
    (6, "gold_dim_clients",          transform_gold_dim_clients.load_dim_client),
    (6, "gold_dim_datetime",         transform_gold_dim_datetime.load_dim_datetime),
    (6, "gold_dim_weather",          transform_gold_dim_weather.load_dim_weather),
    (6, "gold_fact_energy",          transform_gold_fact_energy.load_fact_energy_forecast),
]


# ─────────────────────────────────────────────────────────────────────────────
# Runner
# ─────────────────────────────────────────────────────────────────────────────

def run_step(name: str, fn: Callable, dry_run: bool = False) -> bool:
    """
    Ejecuta un paso del pipeline con cronómetro y captura de excepciones.
    Devuelve True si tuvo éxito, False si falló.
    """
    if dry_run:
        logger.info(f"  [DRY-RUN] {name}")
        return True

    logger.info(f"  ▶  {name} ...")
    t0 = time.monotonic()

    try:
        result = fn()
        elapsed = time.monotonic() - t0

        
        if result is False:
            logger.error(f"  ✗  {name} devolvió False ({elapsed:.1f}s)")
            return False

        logger.info(f"  ✔  {name} completado ({elapsed:.1f}s)")
        return True

    except Exception as e:
        elapsed = time.monotonic() - t0
        logger.error(f"  ✗  {name} lanzó excepción ({elapsed:.1f}s): {e}", exc_info=True)
        return False


def run_pipeline(from_stage: int = 1, dry_run: bool = False) -> bool:
    """
    Ejecuta el pipeline completo desde `from_stage`.
    Si algún stage falla completamente (todos sus steps fallan), aborta.
    """
    started_at = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")
    logger.info("=" * 60)
    logger.info(f"  PIPELINE SUNSAVER — inicio: {started_at}")
    if from_stage > 1:
        logger.info(f"  Arrancando desde stage {from_stage}")
    if dry_run:
        logger.info("  MODO DRY-RUN: no se ejecuta nada")
    logger.info("=" * 60)

    t_global = time.monotonic()
    steps_ok = 0
    steps_ko = 0
    current_stage = None

    # Agrupamos por stage para poder detectar si un stage entero falla
    stage_results: dict[int, list[bool]] = {}

    for stage_num, name, fn in PIPELINE:
        # Saltar stages anteriores al punto de entrada
        if stage_num < from_stage:
            continue

        # Cabecera de stage nuevo
        if stage_num != current_stage:
            current_stage = stage_num
            logger.info(f"\n── STAGE {stage_num} {'─'*40}")

        ok = run_step(name, fn, dry_run=dry_run)

        stage_results.setdefault(stage_num, []).append(ok)
        if ok:
            steps_ok += 1
        else:
            steps_ko += 1

        # Si algún stage crítico falla por completo, abortamos
        # (todos los steps del stage han devuelto False)
        if not any(stage_results[stage_num]):
            logger.critical(
                f"\n💥 Stage {stage_num} ha fallado completamente. "
                f"Abortando pipeline para evitar datos corruptos en stages posteriores."
            )
            return False

    # ── Resumen final ─────────────────────────────────────────────────────────
    elapsed_total = time.monotonic() - t_global
    logger.info("\n" + "=" * 104)
    logger.info(f"  PIPELINE FINALIZADO en {elapsed_total:.1f}s")
    logger.info(f"  Steps OK: {steps_ok}  |  Steps KO: {steps_ko}")

    if steps_ko > 0:
        logger.warning(
            f"  ⚠️  {steps_ko} step(s) fallaron pero el pipeline continuó. "
            f"Revisa los logs anteriores."
        )
    else:
        logger.info("  ✅ Todos los steps completados correctamente.")

    logger.info("=" * 60)
    return steps_ko == 0


# ─────────────────────────────────────────────────────────────────────────────
# CLI
# ─────────────────────────────────────────────────────────────────────────────

def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Orquestador del pipeline ETL SunSaver.",
        formatter_class=argparse.RawTextHelpFormatter,
    )
    parser.add_argument(
        "--stage",
        type=int,
        default=1,
        metavar="N",
        help=(
            "Stage desde el que arrancar (1-6). Útil para reejecutar\n"
            "solo la parte que falló sin repetir todo el pipeline.\n"
            "  1 = Bronze completo (por defecto)\n"
            "  2 = Silver independiente\n"
            "  3 = OpenWeather extract\n"
            "  4 = OpenWeather transform\n"
            "  5 = Cálculo PV\n"
            "  6 = Capa Gold"
        ),
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Muestra el plan de ejecución sin llamar a ninguna función.",
    )
    return parser.parse_args()


if __name__ == "__main__":
    args = parse_args()

    success = run_pipeline(from_stage=args.stage, dry_run=args.dry_run)
    sys.exit(0 if success else 1)