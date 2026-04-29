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

# Cada slot de clima/cálculos es de 3 horas = 10800 segundos.
# Para hacer JOIN con precios (que van por hora), necesitamos alinear
# el unix_time del slot de 3h al unix_time de la hora que lo contiene.
# Ejemplo: slot 15:00 UTC → precio de la hora 15:00 UTC (PVPC)
#          slot 15:00 UTC → media spot de 15:00, 15:15, 15:30, 15:45 UTC
#
# En clean_prices los unix_time ya están en UTC, igual que en clean_calculations.
# El alineamiento es directo: unix_time del slot == unix_time del precio PVPC
# porque OpenWeather también reporta slots a horas en punto (12:00, 15:00…).


def build_fact_energy_forecast(conn: sqlite3.Connection) -> None:
    """
    Genera gold_fact_energy_forecast haciendo JOIN de:
      - clean_calculations         (base: client_id + unix_time, granularidad 3h)
      - clean_weather        (clima: mismo client_id + unix_time)
      - clean_prices PVPC    (precio regulado: unix_time == slot unix_time)
      - clean_prices Spot    (precio mercado: media de los 4 slots de 15min
                              dentro de la misma hora del slot)

    La PK es (client_id, unix_time) — no se usa surrogate key porque
    este par ya es único y facilita depuración y recargas incrementales.

    weather_id actúa como FK → gold_dim_weather (weather_main y
    weather_description se consultan desde esa dimensión, no se
    almacenan aquí para evitar redundancia).
    """
    logger.info("Generando gold_fact_energy_forecast...")

    conn.execute("DROP TABLE IF EXISTS gold_fact_energy_forecast")
    conn.execute("""
        CREATE TABLE gold_fact_energy_forecast (
            -- Claves
            client_id               TEXT    NOT NULL,
            unix_time               INTEGER NOT NULL,   -- FK → gold_dim_datetime
            forecast_time_utc       TEXT    NOT NULL,

            -- Solar (calculado por pv_generation_engine)
            pv_power_gen_kw         REAL,   -- generación fotovoltaica prevista (kW)
            pv_performance_ratio    REAL,   -- ratio rendimiento real vs STC (0-1)
            poa_wm2                 REAL,   -- irradiancia en plano del panel (W/m²)
            t_cell_celsius          REAL,   -- temperatura célula solar (ºC)

            -- Energía (kW en el slot de 3h)
            power_consumption_kw    REAL,   -- consumo previsto
            self_consumption_kw     REAL,   -- autoconsumo solar
            grid_export_kw          REAL,   -- excedente exportado a red
            grid_import_kw          REAL,   -- energía importada de red

            -- Meteorología (weather_main y weather_description via FK → gold_dim_weather)
            temp_celsius            REAL,
            humidity_pct            REAL,
            clouds_pct              REAL,
            rain_prob_norm          REAL,   -- probabilidad lluvia normalizada 0-1
            wind_speed_mps          REAL,   -- velocidad viento (m/s)
            weather_id              INTEGER,  -- FK → gold_dim_weather.weather_id

            -- Precios (€/MWh)
            price_pvpc_eur_mwh      REAL,   -- precio PVPC hora del slot
            price_spot_eur_mwh      REAL,   -- precio spot medio 4 cuartos de hora

            -- Coste económico derivado (€)
            -- grid_import_kw  → energía que se paga
            -- /1000 para pasar kW→MWh, *3 porque el slot es de 3 horas
            cost_pvpc_eur           REAL,   -- grid_import_kw * 3/1000 * price_pvpc
            cost_spot_eur           REAL,   -- grid_import_kw * 3/1000 * price_spot

            -- Metadatos
            _loaded_at_utc          TEXT    NOT NULL,

            PRIMARY KEY (client_id, unix_time),
            FOREIGN KEY (weather_id) REFERENCES gold_dim_weather (weather_id)
        )
    """)

    conn.execute("""
        INSERT INTO gold_fact_energy_forecast

        SELECT
            c.client_id,
            c.unix_time,
            c.forecast_time_utc,

            -- Solar
            c.pv_power_gen_kw,
            c.pv_performance_ratio,
            c.poa_wm2,
            c.t_cell_celsius,

            -- Energía
            c.power_con_kw,
            c.self_consumption_kw,
            c.grid_export_kw,
            c.grid_import_kw,

            -- Meteorología (sin weather_main ni weather_description: están en gold_dim_weather)
            w.temp_celsius,
            w.humidity_pct,
            w.clouds_pct,
            w.rain_prob_norm,
            w.wind_speed_mps,
            w.weather_id,

            -- Precio PVPC: el unix_time del slot coincide exactamente con
            -- la hora en punto del PVPC (ambos en UTC, OpenWeather usa horas en punto)
            pvpc.price_euro_mwh                             AS price_pvpc_eur_mwh,

            -- Precio Spot: media de los 4 intervalos de 15min dentro de la misma hora
            -- unix_time del slot >= unix_time del cuarto de hora
            -- unix_time del cuarto de hora < unix_time del slot + 3600 (1 hora)
            spot_avg.price_spot_avg                         AS price_spot_eur_mwh,

            -- Coste: energía importada de red * duración slot (3h) * precio
            ROUND(c.grid_import_kw * 3.0 / 1000.0 * pvpc.price_euro_mwh, 6)     AS cost_pvpc_eur,
            ROUND(c.grid_import_kw * 3.0 / 1000.0 * spot_avg.price_spot_avg, 6) AS cost_spot_eur,

            STRFTIME('%Y-%m-%d %H:%M:%S', 'now')            AS _loaded_at_utc

        FROM clean_calculations c

        -- JOIN clima: mismo client + mismo unix_time (granularidad 3h)
        LEFT JOIN clean_weather w
            ON w.client_id = c.client_id
            AND w.unix_time = c.unix_time

        -- JOIN PVPC: precio de la hora en punto que coincide con el slot
        LEFT JOIN clean_prices pvpc
            ON pvpc.unix_time = c.unix_time
            AND pvpc.price_type = 'PVPC'

        -- JOIN Spot: media de los 4 cuartos de hora dentro de esa misma hora
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

    # Índices de optimización.
    # Útil para reportes temporales globales (de todos los clientes)
    conn.execute("CREATE INDEX IF NOT EXISTS idx_gold_fact_unix_time ON gold_fact_energy_forecast (unix_time)")
    # Útil si sueles filtrar por condición meteorológica en dashboards
    conn.execute("CREATE INDEX IF NOT EXISTS idx_gold_fact_weather_id ON gold_fact_energy_forecast (weather_id)")

    conn.commit()

    n = conn.execute("SELECT COUNT(*) FROM gold_fact_energy_forecast").fetchone()[0]
    logger.info(f"✅ gold_fact_energy_forecast generada: {n} filas insertadas")


def load_fact_energy_forecast() -> None:
    with sqlite3.connect(DB_PATH) as conn:
        build_fact_energy_forecast(conn)


if __name__ == "__main__":
    load_fact_energy_forecast()
