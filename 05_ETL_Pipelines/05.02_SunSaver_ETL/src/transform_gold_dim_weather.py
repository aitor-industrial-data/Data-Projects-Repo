import sqlite3
import logging
import workspace_manager

# Configuración de logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)

DB_PATH = workspace_manager.get_db_path()


def build_dim_weather(conn: sqlite3.Connection) -> None:
    """
    Genera gold_dim_weather como tabla de dimensión de condiciones meteorológicas.
    Usa una Window Function para desempatar descripciones por cada weather_id.
    """
    try:
        logger.info("Generando gold_dim_weather...")

        # Iniciamos la transacción para asegurar que el DROP y el INSERT sean atómicos
        conn.execute("DROP TABLE IF EXISTS gold_dim_weather")
        
        conn.execute("""
            CREATE TABLE gold_dim_weather (
                weather_id           INTEGER NOT NULL PRIMARY KEY,
                weather_main         TEXT    NOT NULL,   -- 'Clear', 'Clouds', 'Rain'…
                weather_description  TEXT    NOT NULL,   -- descripción detallada
                _loaded_at_utc       TEXT    NOT NULL
            )
        """)

        # Inserción con lógica de resolución de duplicados (frecuencia)
        conn.execute("""
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

        conn.commit()

        # Verificación rápida
        n = conn.execute("SELECT COUNT(*) FROM gold_dim_weather").fetchone()[0]
        logger.info(f"✅ gold_dim_weather generada: {n} filas insertadas")

    except sqlite3.Error as e:
        logger.error(f"❌ Error de SQLite al construir gold_dim_weather: {e}")
        conn.rollback()
        raise
    except Exception as e:
        logger.error(f"❌ Error inesperado en el script de clima: {e}")
        raise


def load_dim_weather() -> None:
    """Maneja la conexión a la base de datos para la dimensión de clima."""
    try:
        with sqlite3.connect(DB_PATH) as conn:
            build_dim_weather(conn)
    except Exception as e:
        logger.critical(f"No se pudo completar la carga de gold_dim_weather: {e}")


if __name__ == "__main__":
    load_dim_weather()