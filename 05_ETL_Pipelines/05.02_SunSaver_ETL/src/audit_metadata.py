import sqlite3
from datetime import datetime, timezone
from sqlalchemy import create_engine, Table, Column, Integer, String, DateTime, Float, MetaData
from sqlalchemy.exc import SQLAlchemyError

import config_paths
from logger_config import setup_logging

"""
ETL AUDIT & METADATA MANAGER
----------------------------
Author: Aitor Asin
Description: Provides observability into pipeline executions. 
             Stores execution telemetry (duration, row counts, status) 
             to facilitate SLA monitoring and debugging.
"""

logger = setup_logging()

# Database Schema Definition
metadata = MetaData()
audit_table = Table(
    "etl_metadata", metadata,
    Column("id",               Integer,  primary_key=True, autoincrement=True),
    Column("pipeline_name",    String,   nullable=False),
    Column("status",           String,   nullable=False),
    Column("duration_seconds", Float),
    Column("rows_affected",    Integer),
    Column("error_message",    String),
    Column("env",              String),
    Column("executed_at",      DateTime, default=lambda: datetime.now(timezone.utc)),
)

def save_etl_metadata(status: str, duration: float, rows: int = 0, error: str = None) -> None:
    """
    Persists pipeline telemetry to the centralized audit table.
    Ensures the table exists before insertion (Lazy Initialization).
    """
    logger.info(
        "[METADATA] Recording audit log — Status: %s | Duration: %.2fs | Rows: %d",
        status, duration, rows,
    )

    try:
        # Resolve database URI
        db_path = config_paths.get_db_path()
        engine = create_engine(f"sqlite:///{db_path}")

        # Ensure schema exists (DDL)
        metadata.create_all(engine)

        # Execute Insertion (DML)
        with engine.connect() as conn:
            stmt = audit_table.insert().values(
                pipeline_name="SunSaver_ETL",
                status=status,
                duration_seconds=round(duration, 2),
                rows_affected=rows,
                error_message=error,
                env="DEV",
            )
            conn.execute(stmt)
            conn.commit()

        logger.info("[METADATA] Audit record committed successfully")

    except SQLAlchemyError as exc:
        logger.error("[METADATA] Database error during audit persistence: %s", exc)
    except Exception as exc:
        logger.error("[METADATA] Unexpected error in metadata module: %s", exc)


if __name__ == "__main__":
    # Test execution for validation
    save_etl_metadata(
        status="SUCCESS", 
        duration=4.25, 
        rows=250, 
        error=None
    )