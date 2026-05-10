import logging
import os
from pathlib import Path
from datetime import datetime

"""
OBSERVABILITY MODULE: CENTRALISED LOGGING
-----------------------------------------
Author: Aitor Asin
Description: Implements a thread-safe singleton logger for the SunSaver pipeline.
             Outputs structured logs to daily rotating files and console.
Format: TIMESTAMP | LEVEL | MODULE | MESSAGE
"""

def setup_logging() -> logging.Logger:
    """
    Configures and returns the SunSaver logger.
    Ensures idempotency to prevent duplicate handlers across the pipeline.
    """

    # 1. Path Management (Absolute paths for reliability)
    BASE_DIR = Path(__file__).resolve().parent.parent
    log_dir  = BASE_DIR / "logs"
    log_dir.mkdir(parents=True, exist_ok=True)

    # Daily log rotation naming convention
    log_path = log_dir / f"sunsaver_{datetime.now().strftime('%Y-%m-%d')}.log"

    # 2. Logger Initialisation
    logger = logging.getLogger("SunSaver")
    logger.setLevel(logging.DEBUG)  # Capture all, handlers will filter

    # Singleton Guard: Avoid adding multiple handlers to the same logger instance
    if logger.handlers:
        return logger

    # 3. Standardised Formatting
    fmt = logging.Formatter(
        fmt     = "%(asctime)s | %(levelname)-8s | %(module)-30s | %(message)s",
        datefmt = "%Y-%m-%d %H:%M:%S",
    )

    # 4. Handlers Configuration
    
    # File Handler: Persistent storage for auditing and debugging (INFO+)
    fh = logging.FileHandler(log_path, mode="a", encoding="utf-8")
    fh.setLevel(logging.INFO)
    fh.setFormatter(fmt)

    # Console Handler: Real-time monitoring during execution (INFO+)
    ch = logging.StreamHandler()
    ch.setLevel(logging.INFO)
    ch.setFormatter(fmt)

    # 5. Attachment
    logger.addHandler(fh)
    logger.addHandler(ch)

    return logger