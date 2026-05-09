import sqlalchemy
from sqlalchemy import create_engine, text
from sqlalchemy.exc import SQLAlchemyError
import workspace_manager
from logger_config import setup_logging

# Configuración de logs y base de datos
logger = setup_logging()
DB_PATH = workspace_manager.get_db_path()

def build_dim_weather(engine: sqlalchemy.engine.Engine) -> int:
    """
    Genera gold_dim_weather como tabla de dimensión de condiciones meteorológicas.
    Retorna el número de filas insertadas.
    """
    try:
        logger.info("Generando gold_dim_weather (SQLAlchemy)...")

        # engine.begin() abre la transacción y hace commit/rollback automáticamente
        with engine.begin() as conn:
            # 1. Limpieza de tabla previa
            conn.execute(text("DROP TABLE IF EXISTS gold_dim_weather"))
            
            # 2. Creación de la estructura Gold
            conn.execute(text("""
                CREATE TABLE gold_dim_weather (
                    weather_id           INTEGER NOT NULL PRIMARY KEY,
                    weather_main         TEXT    NOT NULL,
                    weather_description  TEXT    NOT NULL,
                    _loaded_at_utc       TEXT    NOT NULL
                )
            """))

            # 3. Inserción directa mediante SQL puro (más eficiente para transformaciones internas)
            # La lógica de desempate por frecuencia se mantiene igual
            insert_query = text("""
                INSERT INTO gold_dim_weather
                SELECT 
                    weather_id, 
                    weather_main, 
                    weather_description,
                    STRFTIME('%Y-%m-%d %H:%M:%S', 'now') AS _loaded_at_utc
                FROM (
                    SELECT 
                        weather_id, 
                        weather_main, 
                        weather_description,
                        COUNT(*) AS freq,
                        ROW_NUMBER() OVER (
                            PARTITION BY weather_id 
                            ORDER BY COUNT(*) DESC
                        ) AS rn
                    FROM clean_weather
                    WHERE weather_id IS NOT NULL
                    GROUP BY weather_id, weather_main, weather_description
                )
                WHERE rn = 1
            """)
            
            conn.execute(insert_query)

            # 4. Verificación y conteo para el orquestador
            n = conn.execute(text("SELECT COUNT(*) FROM gold_dim_weather")).scalar()
            logger.info(f"✅ gold_dim_weather generada: {n} filas insertadas")
            logger.info(f"Datos totales procesados: {n}")
            return n

    except SQLAlchemyError as e:
        logger.error(f"❌ Error de SQLAlchemy al construir gold_dim_weather: {e}")
        raise
    except Exception as e:
        logger.error(f"❌ Error inesperado en el script de clima: {e}")
        raise

def load_dim_weather() -> int:
    """Maneja el ciclo de vida del motor de base de datos."""
    try:
        engine = create_engine(f"sqlite:///{DB_PATH}")
        return build_dim_weather(engine)
    except Exception as e:
        logger.critical(f"No se pudo completar la carga de gold_dim_weather: {e}")
        return 0

if __name__ == "__main__":
    load_dim_weather()