import sqlalchemy
from sqlalchemy import create_engine, text
from sqlalchemy.exc import SQLAlchemyError
import workspace_manager
from logger_config import setup_logging

# Configuración de logs y base de datos
logger = setup_logging()
DB_PATH = workspace_manager.get_db_path()

def build_dim_client(engine: sqlalchemy.engine.Engine) -> int:
    """
    Genera gold_dim_client a partir de clean_clients aplicando lógica de negocio.
    Retorna el número de filas insertadas utilizando SQLAlchemy.
    """
    try:
        logger.info("Generando gold_dim_client a partir de clean_clients (SQLAlchemy)...")

        # Usamos un bloque 'with engine.begin()' para manejar la transacción automáticamente
        with engine.begin() as conn:
            # 1. Extraer datos de la capa Silver
            query_select = text("""
                SELECT
                    client_id, name, description, latitude, longitude, timezone,
                    nominal_load_kw, pv_peak_power_kw, panel_area_m2,
                    efficiency, panel_type, loss_pct, angle, aspect, mounting,
                    battery_capacity_kwh, soc_min_pct, installation_cost_eur
                FROM clean_clients
                ORDER BY client_id
            """)
            
            result = conn.execute(query_select)
            rows = result.fetchall()

            if not rows:
                logger.warning("clean_clients está vacía — no se generó gold_dim_client")
                return 0

            # 2. Procesar lógica de negocio y campos derivados
            registros = []
            for row in rows:
                # Acceso por nombre de columna (más seguro que índices en SQLAlchemy)
                has_solar = 1 if (row.pv_peak_power_kw or 0) > 0 else 0
                has_battery = 1 if (row.battery_capacity_kwh or 0) > 0 else 0

                registros.append({
                    "client_id": row.client_id,
                    "name": row.name,
                    "description": row.description,
                    "latitude": row.latitude,
                    "longitude": row.longitude,
                    "timezone": row.timezone,
                    "nominal_load_kw": row.nominal_load_kw,
                    "pv_peak_power_kw": row.pv_peak_power_kw,
                    "panel_area_m2": row.panel_area_m2,
                    "efficiency": row.efficiency,
                    "panel_type": row.panel_type,
                    "loss_pct": row.loss_pct,
                    "angle": row.angle,
                    "aspect": row.aspect,
                    "mounting": row.mounting,
                    "battery_capacity_kwh": row.battery_capacity_kwh,
                    "soc_min_pct": row.soc_min_pct,
                    "installation_cost_eur": row.installation_cost_eur,
                    "has_solar": has_solar,
                    "has_battery": has_battery
                })

            # 3. Recrear la tabla en la capa Gold
            conn.execute(text("DROP TABLE IF EXISTS gold_dim_client"))
            
            create_table_query = text("""
                CREATE TABLE gold_dim_client (
                    client_id               TEXT    PRIMARY KEY,
                    name                    TEXT    NOT NULL,
                    description             TEXT,
                    latitude                REAL    NOT NULL,
                    longitude               REAL    NOT NULL,
                    timezone                TEXT    NOT NULL,
                    nominal_load_kw         REAL    NOT NULL,
                    pv_peak_power_kw        REAL    NOT NULL,
                    panel_area_m2           REAL    NOT NULL,
                    efficiency              REAL    NOT NULL,
                    panel_type              TEXT    NOT NULL,
                    loss_pct                REAL    NOT NULL,
                    angle                   REAL    NOT NULL,
                    aspect                  REAL    NOT NULL,
                    mounting                TEXT    NOT NULL,
                    battery_capacity_kwh    REAL    NOT NULL,
                    soc_min_pct             REAL    NOT NULL,
                    installation_cost_eur   REAL    NOT NULL,
                    has_solar               INTEGER NOT NULL,
                    has_battery             INTEGER NOT NULL
                )
            """)
            conn.execute(create_table_query)

            # 4. Inserción masiva usando diccionarios (estilo SQLAlchemy core)
            insert_query = text("""
                INSERT INTO gold_dim_client (
                    client_id, name, description, latitude, longitude, timezone,
                    nominal_load_kw, pv_peak_power_kw, panel_area_m2,
                    efficiency, panel_type, loss_pct, angle, aspect, mounting,
                    battery_capacity_kwh, soc_min_pct, installation_cost_eur,
                    has_solar, has_battery
                ) VALUES (
                    :client_id, :name, :description, :latitude, :longitude, :timezone,
                    :nominal_load_kw, :pv_peak_power_kw, :panel_area_m2,
                    :efficiency, :panel_type, :loss_pct, :angle, :aspect, :mounting,
                    :battery_capacity_kwh, :soc_min_pct, :installation_cost_eur,
                    :has_solar, :has_battery
                )
            """)
            
            conn.execute(insert_query, registros)
            
            total_filas = len(registros)
            logger.info(f"✅ gold_dim_client generada: {total_filas} filas insertadas")
            logger.info(f"Datos totales procesados: {total_filas}")
            return total_filas

    except SQLAlchemyError as e:
        logger.error(f"❌ Error de SQLAlchemy en build_dim_client: {e}")
        # engine.begin() hace rollback automático si hay una excepción
        raise 
    except Exception as e:
        logger.error(f"❌ Error inesperado: {e}")
        raise


def load_dim_client() -> int:
    """Maneja la creación del motor y el flujo principal."""
    try:
        # Creamos el engine (usamos el path nativo de Ubuntu que tienes configurado)
        engine = create_engine(f"sqlite:///{DB_PATH}")
        return build_dim_client(engine)
    except Exception as e:
        logger.critical(f"Hubo un fallo crítico en el proceso de carga: {e}")
        return 0

if __name__ == "__main__":
    load_dim_client()