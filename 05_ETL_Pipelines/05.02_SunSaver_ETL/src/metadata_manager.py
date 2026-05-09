from sqlalchemy import create_engine, Table, Column, Integer, String, DateTime, Float, MetaData
from datetime import datetime, timezone
import workspace_manager
from logger_config import setup_logging

logger = setup_logging()

# Definimos el esquema global con las nuevas columnas profesionales
metadata = MetaData()
metadata_table = Table(
    'etl_metadata', metadata,
    Column('id', Integer, primary_key=True),
    Column('pipeline_name', String),
    Column('status', String),
    Column('duration_seconds', Float),
    Column('rows_affected', Integer),
    Column('error_message', String),  
    Column('env', String),            
    Column('executed_at', DateTime, default=datetime.now(timezone.utc))
)

def save_etl_metadata(status: str, duration: float, rows: int = 0, error: str = None):
    """
    Guarda los metadatos de ejecución. 
    'rows' y 'error' son opcionales para mayor flexibilidad.
    """
    try:
        db_path = workspace_manager.get_db_path()
        engine = create_engine(f"sqlite:///{db_path}")
        
        # Esto aplicará los cambios si la tabla no existe
        metadata.create_all(engine)
        
        with engine.connect() as conn:
            stmt = metadata_table.insert().values(
                pipeline_name="SunSaver_ETL",
                status=status,
                duration_seconds=round(duration, 2),
                rows_affected=rows,
                error_message=error,
                env="DEV" # Podrías leer esto de un .env en el futuro
            )
            conn.execute(stmt)
            conn.commit()
        
        logger.info(f"Metadata guardada (Status: {status}, Rows: {rows}, Duration: {duration:.2f}s)")

    except Exception as e:
        logger.error(f"CRÍTICO: No se pudo guardar la metadata. Error: {e}")

if __name__ == "__main__":
    print("Probando registro de metadatos profesional...")
    save_etl_metadata(status="TEST_RUN", duration=1.5, rows=100, error="Sin errores")
    print("Registro completado.")