import sqlite3
from datetime import datetime, timezone
import workspace_manager
from logger_config import setup_logging


logger = setup_logging()

DB_PATH = workspace_manager.get_db_path()


def build_fact_energy_forecast(conn: sqlite3.Connection) -> None:
    """
    Actualiza la tabla gold_fact_energy_forecast de forma incremental.
    JOIN directo en unix_time con PVPC horario de clean_prices.
    """
    try:
        logger.info("Iniciando actualización de ventana activa en Gold Layer...")

        # 1. Asegurar esquema
        conn.execute("""
            CREATE TABLE IF NOT EXISTS gold_fact_energy_forecast (
                client_id               TEXT    NOT NULL,
                unix_time               INTEGER NOT NULL,
                forecast_time_utc       TEXT    NOT NULL,
                pv_power_gen_kw         REAL,
                pv_performance_ratio    REAL,
                poa_wm2                 REAL,
                t_cell_celsius          REAL,
                power_consumption_kw    REAL,
                temp_celsius            REAL,
                humidity_pct            REAL,
                clouds_pct              REAL,
                rain_prob_norm          REAL,
                wind_speed_mps          REAL,
                weather_id              INTEGER,
                price_pvpc_eur_mwh      REAL,
                _loaded_at_utc          TEXT    NOT NULL,
                PRIMARY KEY (client_id, unix_time)
            )
        """)

        # 2. Ventana de tiempo con margen
        buffer_seconds = 7200  # 2 horas de margen
        start_unix = int(datetime.now(timezone.utc).timestamp()) - buffer_seconds

        # 3. UPSERT Incremental
        query = f"""
            INSERT OR REPLACE INTO gold_fact_energy_forecast
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
                pvpc.price_euro_mwh     AS price_pvpc_eur_mwh,
                STRFTIME('%Y-%m-%d %H:%M:%S', 'now') AS _loaded_at_utc
            FROM clean_calculations c
            LEFT JOIN clean_weather w
                ON  w.client_id = c.client_id
                AND w.unix_time = c.unix_time
            LEFT JOIN clean_prices pvpc
                ON  pvpc.unix_time  = c.unix_time
                AND pvpc.price_type = 'PVPC'
            WHERE c.unix_time >= {start_unix}
        """
        
        cursor = conn.execute(query)
        rows_affected = cursor.rowcount

        # 4. Índices
        conn.execute("CREATE INDEX IF NOT EXISTS idx_gold_fact_unix_time  ON gold_fact_energy_forecast (unix_time)")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_gold_fact_weather_id ON gold_fact_energy_forecast (weather_id)")

        conn.commit()
        
        logger.info(
            f"✅ Gold Layer actualizada: {rows_affected} registros "
            f"(Unixtime >= {start_unix})"
        )

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