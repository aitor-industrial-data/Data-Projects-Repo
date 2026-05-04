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


def build_dim_client(conn: sqlite3.Connection) -> None:
    """
    Genera gold_dim_client a partir de clean_clients aplicando lógica de negocio.
    """
    try:
        logger.info("Generando gold_dim_client a partir de clean_clients...")

        rows = conn.execute("""
            SELECT
                client_id, name, description, latitude, longitude, timezone,
                nominal_load_kw, pv_peak_power_kw, panel_area_m2,
                efficiency, panel_type, loss_pct, angle, aspect, mounting,
                battery_capacity_kwh, soc_min_pct, installation_cost_eur
            FROM clean_clients
            ORDER BY client_id
        """).fetchall()

        if not rows:
            logger.warning("clean_clients está vacía — no se generó gold_dim_client")
            return

        registros = []
        for row in rows:
            # Desempaquetado y lógica de campos derivados
            (
                client_id, name, description, lat, lon, tz,
                load, pv_kw, area, eff, p_type, loss,
                ang, asp, mount, batt_kwh, soc, cost
            ) = row

            has_solar = 1 if (pv_kw or 0) > 0 else 0
            has_battery = 1 if (batt_kwh or 0) > 0 else 0

            registros.append((
                client_id, name, description, lat, lon, tz,
                load, pv_kw, area, eff, p_type, loss,
                ang, asp, mount, batt_kwh, soc, cost,
                has_solar, has_battery
            ))

        # Transacción atómica: Borrar, Crear e Insertar
        conn.execute("DROP TABLE IF EXISTS gold_dim_client")
        conn.execute("""
            CREATE TABLE gold_dim_client (
                client_id             TEXT    PRIMARY KEY,
                name                  TEXT    NOT NULL,
                description           TEXT,
                latitude              REAL    NOT NULL,
                longitude             REAL    NOT NULL,
                timezone              TEXT    NOT NULL,
                nominal_load_kw       REAL    NOT NULL,
                pv_peak_power_kw      REAL    NOT NULL,
                panel_area_m2         REAL    NOT NULL,
                efficiency            REAL    NOT NULL,
                panel_type            TEXT    NOT NULL,
                loss_pct              REAL    NOT NULL,
                angle                 REAL    NOT NULL,
                aspect                REAL    NOT NULL,
                mounting              TEXT    NOT NULL,
                battery_capacity_kwh  REAL    NOT NULL,
                soc_min_pct           REAL    NOT NULL,
                installation_cost_eur REAL    NOT NULL,
                has_solar             INTEGER NOT NULL,
                has_battery           INTEGER NOT NULL
            )
        """)

        conn.executemany(
            "INSERT INTO gold_dim_client VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
            registros,
        )
        conn.commit()
        logger.info(f"✅ gold_dim_client generada: {len(registros)} filas insertadas")

    except sqlite3.Error as e:
        logger.error(f"❌ Error de base de datos en build_dim_client: {e}")
        conn.rollback()  # Deshacer cambios si algo falló
        raise  # Re-lanzar para que el proceso padre sepa que falló
    except Exception as e:
        logger.error(f"❌ Error inesperado: {e}")
        raise


def load_dim_client() -> None:
    """Maneja la conexión y el flujo principal."""
    try:
        with sqlite3.connect(DB_PATH) as conn:
            build_dim_client(conn)
    except Exception as e:
        logger.critical(f"Hubo un fallo crítico en el proceso de carga: {e}")


if __name__ == "__main__":
    load_dim_client()