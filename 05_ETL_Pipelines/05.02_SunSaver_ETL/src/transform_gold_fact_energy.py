import sqlalchemy
from sqlalchemy import create_engine, text
from sqlalchemy.exc import SQLAlchemyError
from datetime import datetime, timezone
import workspace_manager
from logger_config import setup_logging

# Configuración de logs y base de datos
logger = setup_logging()
DB_PATH = workspace_manager.get_db_path()

def build_fact_energy_forecast(engine: sqlalchemy.engine.Engine) -> int:
    """
    Actualiza la tabla gold_fact_energy_forecast de forma incremental usando SQLAlchemy.
    JOIN directo en unix_time con PVPC horario de clean_prices.
    """
    try:
        logger.info("Iniciando actualización de ventana activa en Gold Layer (SQLAlchemy)...")

        with engine.begin() as conn:
            # 1. Asegurar esquema de la Fact Table
            conn.execute(text("""
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
            """))

            # 2. Ventana de tiempo con margen (2 horas)
            buffer_seconds = 7200
            start_unix = int(datetime.now(timezone.utc).timestamp()) - buffer_seconds

            # 3. UPSERT Incremental (INSERT OR REPLACE)
            # Usamos parámetros nombrados (:start_unix) para mayor seguridad
            query_upsert = text(f"""
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
                WHERE c.unix_time >= :start_unix
            """)
            
            result = conn.execute(query_upsert, {"start_unix": start_unix})
            rows_affected = result.rowcount

            # 4. Optimización mediante Índices
            conn.execute(text("CREATE INDEX IF NOT EXISTS idx_gold_fact_unix_time  ON gold_fact_energy_forecast (unix_time)"))
            conn.execute(text("CREATE INDEX IF NOT EXISTS idx_gold_fact_weather_id ON gold_fact_energy_forecast (weather_id)"))

            logger.info(
                f"✅ Gold Layer actualizada: {rows_affected} registros "
                f"(Unixtime >= {start_unix})"
            )
            logger.info(f"Datos totales procesados: {rows_affected}")
            return rows_affected

    except SQLAlchemyError as e:
        logger.error(f"❌ Error de SQLAlchemy en build_fact_energy_forecast: {e}")
        raise
    except Exception as e:
        logger.error(f"❌ Error inesperado en la tabla de hechos: {e}")
        raise


def load_fact_energy_forecast() -> int:
    """Maneja la conexión y el retorno del conteo de filas para el orquestador."""
    try:
        # Siguiendo tus specs de Ubuntu nativo y WSL2
        engine = create_engine(f"sqlite:///{DB_PATH}")
        # Habilitar claves foráneas en la sesión si fuera necesario
        with engine.connect() as conn:
            conn.execute(text("PRAGMA foreign_keys = ON"))
        
        return build_fact_energy_forecast(engine)
    except Exception as e:
        logger.critical(f"Fallo crítico al cargar la Fact Table: {e}")
        return 0

if __name__ == "__main__":
    load_fact_energy_forecast()