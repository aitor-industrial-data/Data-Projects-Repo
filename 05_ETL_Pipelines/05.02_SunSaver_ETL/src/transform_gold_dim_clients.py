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


def build_dim_client(conn: sqlite3.Connection) -> None:
    """
    Genera gold_dim_client a partir de clean_clients.

    Cambios respecto a Silver:
      - Se añaden campos derivados: has_solar, has_battery
      - Se elimina _ingested_at_utc (metadata de pipeline, no de negocio)
      - Si un cliente cambia sus datos en Silver (nuevo panel, nueva batería…),
        basta volver a ejecutar este script: DROP + INSERT reconstruye la tabla.
    """
    logger.info("Generando gold_dim_client a partir de clean_clients...")

    rows = conn.execute("""
        SELECT
            client_id,
            name,
            description,
            latitude,
            longitude,
            timezone,
            nominal_load_kw,
            pv_peak_power_kw,
            panel_area_m2,
            efficiency,
            panel_type,
            loss_pct,
            angle,
            aspect,
            mounting,
            battery_capacity_kwh,
            soc_min_pct,
            installation_cost_eur
        FROM clean_clients
        ORDER BY client_id
    """).fetchall()

    if not rows:
        logger.warning("clean_clients está vacía — no se generó gold_dim_client")
        return

    registros = []

    for row in rows:
        (
            client_id, name, description,
            latitude, longitude, timezone,
            nominal_load_kw, pv_peak_power_kw, panel_area_m2,
            efficiency, panel_type, loss_pct,
            angle, aspect, mounting,
            battery_capacity_kwh, soc_min_pct, installation_cost_eur,
        ) = row

        has_solar   = 1 if (pv_peak_power_kw or 0) > 0 else 0
        has_battery = 1 if (battery_capacity_kwh or 0) > 0 else 0

        registros.append((
            client_id,
            name,
            description,
            latitude,
            longitude,
            timezone,
            nominal_load_kw,       # consumo nominal (kW)
            pv_peak_power_kw,      # potencia pico instalación solar (kWp)
            panel_area_m2,
            efficiency,            # eficiencia del panel (0-1)
            panel_type,            # crystalline, thin-film…
            loss_pct,              # pérdidas sistema (%)
            angle,                 # inclinación panel (grados)
            aspect,                # orientación panel (grados desde sur)
            mounting,              # tipo de montaje
            battery_capacity_kwh,
            soc_min_pct,           # estado de carga mínimo permitido (%)
            installation_cost_eur,
            has_solar,             # derivado: tiene generación solar
            has_battery,           # derivado: tiene batería
        ))

    conn.execute("DROP TABLE IF EXISTS gold_dim_client")
    conn.execute("""
        CREATE TABLE gold_dim_client (
            client_id             TEXT    PRIMARY KEY,
            name                  TEXT    NOT NULL,
            description           TEXT,
            latitude              REAL    NOT NULL,
            longitude             REAL    NOT NULL,
            timezone              TEXT    NOT NULL,
            nominal_load_kw       REAL    NOT NULL,   -- consumo nominal
            pv_peak_power_kw      REAL    NOT NULL,   -- potencia pico solar (kWp)
            panel_area_m2         REAL    NOT NULL,
            efficiency            REAL    NOT NULL,   -- 0.0 a 1.0
            panel_type            TEXT    NOT NULL,
            loss_pct              REAL    NOT NULL,   -- % pérdidas sistema
            angle                 REAL    NOT NULL,   -- inclinación (grados)
            aspect                REAL    NOT NULL,   -- orientación (grados)
            mounting              TEXT    NOT NULL,
            battery_capacity_kwh  REAL    NOT NULL,
            soc_min_pct           REAL    NOT NULL,
            installation_cost_eur REAL    NOT NULL,
            has_solar             INTEGER NOT NULL,   -- 0/1 derivado de pv_peak_power_kw
            has_battery           INTEGER NOT NULL    -- 0/1 derivado de battery_capacity_kwh
        )
    """)

    conn.executemany(
        "INSERT INTO gold_dim_client VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
        registros,
    )
    conn.commit()

    logger.info(f"✅ gold_dim_client generada: {len(registros)} filas insertadas")


def load_dim_client() -> None:
    with sqlite3.connect(DB_PATH) as conn:
        build_dim_client(conn)


if __name__ == "__main__":
    
    load_dim_client()