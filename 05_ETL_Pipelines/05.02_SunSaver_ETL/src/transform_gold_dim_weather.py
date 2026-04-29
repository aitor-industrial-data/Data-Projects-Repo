import sqlite3
import logging
import db_manager

logger = logging.getLogger(__name__)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)

DB_PATH = db_manager.get_db_path()


def build_dim_weather(conn: sqlite3.Connection) -> None:
    """
    Genera gold_dim_weather como tabla de dimensión de condiciones meteorológicas.

    PK: weather_id (entero nativo de OpenWeather, p.ej. 800 = Clear sky).
    Contiene la descripción canónica asociada a cada weather_id.

    Fuente: clean_weather — se extrae el par (weather_id, weather_main,
    weather_description) distinto. En caso de que un mismo weather_id tenga
    varias descripciones en los datos (p.ej. variaciones de texto), se toma
    la más frecuente para garantizar unicidad en la PK.
    """
    logger.info("Generando gold_dim_weather...")

    conn.execute("DROP TABLE IF EXISTS gold_dim_weather")
    conn.execute("""
        CREATE TABLE gold_dim_weather (
            weather_id          INTEGER NOT NULL PRIMARY KEY,
            weather_main        TEXT    NOT NULL,   -- 'Clear', 'Clouds', 'Rain'…
            weather_description TEXT    NOT NULL,   -- descripción detallada OpenWeather

            _loaded_at_utc      TEXT    NOT NULL
        )
    """)

    # Por cada weather_id tomamos la (weather_main, weather_description)
    # más frecuente en los datos históricos para resolver posibles duplicados.
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

    n = conn.execute("SELECT COUNT(*) FROM gold_dim_weather").fetchone()[0]
    logger.info(f"✅ gold_dim_weather generada: {n} filas insertadas")


def load_dim_weather() -> None:
    with sqlite3.connect(DB_PATH) as conn:
        build_dim_weather(conn)


if __name__ == "__main__":
    load_dim_weather()
