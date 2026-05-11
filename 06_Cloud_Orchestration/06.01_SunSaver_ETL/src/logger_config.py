import logging
import os
from pathlib import Path
from datetime import datetime


def setup_logging() -> logging.Logger:
    """
    Configures and returns the centralised SunSaver logger.

    Output format  : TIMESTAMP | LEVEL    | MODULE  | MESSAGE
    Destinations   : rotating daily file  +  stderr console
    Logger name    : 'SunSaver'  (singleton — safe to call from multiple modules)
    """

    BASE_DIR = Path(__file__).resolve().parent.parent
    log_dir  = BASE_DIR / "logs"
    log_dir.mkdir(parents=True, exist_ok=True)

    log_path = log_dir / f"sunsaver_{datetime.now().strftime('%Y-%m-%d')}.log"

    logger = logging.getLogger("SunSaver")
    logger.setLevel(logging.DEBUG)          # Root level: DEBUG — handlers filter further

    if logger.handlers:                     # Idempotent: skip if already configured
        return logger

    fmt = logging.Formatter(
        fmt     = "%(asctime)s | %(levelname)-8s | %(module)-30s | %(message)s",
        datefmt = "%Y-%m-%d %H:%M:%S",
    )

    # ── File handler (INFO+) ──────────────────────────────────────────────────
    fh = logging.FileHandler(log_path, mode="a", encoding="utf-8")
    fh.setLevel(logging.INFO)
    fh.setFormatter(fmt)

    # ── Console handler (INFO+) ───────────────────────────────────────────────
    ch = logging.StreamHandler()
    ch.setLevel(logging.INFO)
    ch.setFormatter(fmt)

    logger.addHandler(fh)
    logger.addHandler(ch)

    return logger
