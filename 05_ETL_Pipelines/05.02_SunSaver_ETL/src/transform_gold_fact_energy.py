import sqlite3
import logging
import db_manager

# Configuración de logging profesional
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)

DB_PATH = db_manager.get_db_path()


def build_fact_energy_forecast(conn: sqlite3.Connection) -> None:
    """
    Genera gold_fact_energy_forecast unificando cálculos, clima y precios.
    Implementa lógica de agregación para el precio Spot (media horaria).
    """
    try:
        logger.info("Generando gold_fact_energy_forecast...")

        # 1. Preparación del esquema
        conn.execute("DROP TABLE IF EXISTS gold_fact_energy_forecast")
        conn.execute("""
            CREATE TABLE gold_fact_energy_forecast (
                client_id               TEXT    NOT NULL,
                unix_time               INTEGER NOT NULL,   -- FK → gold_dim_datetime
                forecast_time_utc       TEXT    NOT NULL,

                -- Solar y Consumo
                pv_power_gen_kw         REAL,
                pv_performance_ratio    REAL,
                poa_wm2                 REAL,
                t_cell_celsius          REAL,
                power_consumption_kw    REAL,

                -- Meteorología
                temp_celsius            REAL,
                humidity_pct            REAL,
                clouds_pct              REAL,
                rain_prob_norm          REAL,
                wind_speed_mps          REAL,
                weather_id              INTEGER,

                -- Precios (€/MWh)
                price_pvpc_eur_mwh      REAL,
                price_spot_eur_mwh      REAL,

                -- Metadatos
                _loaded_at_utc          TEXT    NOT NULL,

                PRIMARY KEY (client_id, unix_time),
                FOREIGN KEY (weather_id) REFERENCES gold_dim_weather (weather_id)
            )
        """)

        # 2. Inserción masiva con JOINs y Agregaciones
        conn.execute("""
            INSERT INTO gold_fact_energy_forecast
            SELECT
                c.client_id,
                c.unix_time,
                c.forecast_time_utc,
                c.pv_power_gen_kw,
                c.pv_performance_ratio,
                c.poa_wm2,
                c.t_cell_celsius,
                c.power_con_kw,
                w.temp_celsius,
                w.humidity_pct,
                w.clouds_pct,
                w.rain_prob_norm,
                w.wind_speed_mps,
                w.weather_id,
                pvpc.price_euro_mwh AS price_pvpc_eur_mwh,
                spot_avg.price_spot_avg AS price_spot_eur_mwh,
                STRFTIME('%Y-%m-%d %H:%M:%S', 'now') AS _loaded_at_utc
            FROM clean_calculations c
            LEFT JOIN clean_weather w
                ON w.client_id = c.client_id
                AND w.unix_time = c.unix_time
            LEFT JOIN clean_prices pvpc
                ON pvpc.unix_time = c.unix_time
                AND pvpc.price_type = 'PVPC'
            LEFT JOIN (
                SELECT
                    unix_time - (unix_time % 3600)  AS hour_unix,
                    ROUND(AVG(price_euro_mwh), 6)   AS price_spot_avg
                FROM clean_prices
                WHERE price_type = 'Precio mercado spot'
                GROUP BY hour_unix
            ) spot_avg
                ON spot_avg.hour_unix = c.unix_time
        """)

        # 3. Creación de Índices para Performance
        conn.execute("CREATE INDEX IF NOT EXISTS idx_gold_fact_unix_time ON gold_fact_energy_forecast (unix_time)")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_gold_fact_weather_id ON gold_fact_energy_forecast (weather_id)")

        conn.commit()
        
        n = conn.execute("SELECT COUNT(*) FROM gold_fact_energy_forecast").fetchone()[0]
        logger.info(f"✅ gold_fact_energy_forecast generada: {n} filas insertadas")

    except sqlite3.Error as e:
        logger.error(f"❌ Error de base de datos en build_fact_energy_forecast: {e}")
        conn.rollback()
        raise
    except Exception as e:
        logger.error(f"❌ Error inesperado en la tabla de hechos: {e}")
        raise


def load_fact_energy_forecast() -> bool:
    try:
        with sqlite3.connect(DB_PATH) as conn:
            conn.execute("PRAGMA foreign_keys = ON")
            build_fact_energy_forecast(conn)
        return True           
    except Exception as e:
        logger.critical(f"Fallo crítico al cargar la Fact Table: {e}")
        return False         


if __name__ == "__main__":
    load_fact_energy_forecast()