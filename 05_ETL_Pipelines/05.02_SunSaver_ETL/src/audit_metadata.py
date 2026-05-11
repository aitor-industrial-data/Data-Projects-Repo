from sqlalchemy import create_engine, Table, Column, Integer, String, DateTime, Float, MetaData
from datetime import datetime, timezone

import config_paths
from logger_config import setup_logging


logger = setup_logging()

metadata      = MetaData()
metadata_table = Table(
    "etl_metadata", metadata,
    Column("id",              Integer,  primary_key=True),
    Column("pipeline_name",   String),
    Column("status",          String),
    Column("duration_seconds",Float),
    Column("rows_affected",   Integer),
    Column("error_message",   String),
    Column("env",             String),
    Column("executed_at",     DateTime, default=datetime.now(timezone.utc)),
)


def save_etl_metadata(status: str, duration: float, rows: int = 0, error: str = None) -> None:
    """
    Persists a pipeline execution record to the etl_metadata audit table.

    Args:
        status   : Final pipeline status string (e.g. SUCCESS, PARTIAL SUCCESS, FAILED).
        duration : Wall-clock duration in seconds.
        rows     : Total rows processed across all pipeline steps.
        error    : Human-readable error summary, or None on clean runs.
    """
    logger.info(
        "[METADATA] Saving audit record — status: %s | duration: %.2fs | rows: %d",
        status, duration, rows,
    )

    try:
        db_path = config_paths.get_db_path()
        engine  = create_engine(f"sqlite:///{db_path}")
        metadata.create_all(engine)

        with engine.connect() as conn:
            conn.execute(metadata_table.insert().values(
                pipeline_name   = "SunSaver_ETL",
                status          = status,
                duration_seconds= round(duration, 2),
                rows_affected   = rows,
                error_message   = error,
                env             = "DEV",
            ))
            conn.commit()

        logger.info("[METADATA] Audit record committed successfully")

    except Exception as exc:
        logger.error("[METADATA] Failed to persist audit record: %s", exc)


# ─────────────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    save_etl_metadata(status="TEST_RUN", duration=1.5, rows=100, error=None)
