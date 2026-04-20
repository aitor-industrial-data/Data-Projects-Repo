# ==============================================================================
# sunsaver_orchestrator.py
# ------------------------------------------------------------------------------
# RESPONSABILIDAD : Orquestar la ejecución completa del pipeline ETL SunSaver.
# ------------------------------------------------------------------------------
# QUÉ HACE ESTE SCRIPT:
#   Es el punto de entrada del pipeline recurrente. Lee todos los clientes
#   registrados en la DB y ejecuta el pipeline completo para cada uno:
#
#     1. EXTRACT    → OpenWeather: datos meteorológicos de los próximos 5 días
#     2. LOAD       → Guarda datos crudos en bronce (raw_weather)
#     3. READ       → Lee desde bronce (desacopla extract de transform)
#     4. TRANSFORM  → Limpia y normaliza datos meteorológicos (silver_weather)
#     5. CALCULATE  → Predice generación solar con fórmula matemática
#     6. LOAD       → Guarda predicciones en silver_solar_forecast
#
# DISEÑO MULTI-CLIENTE:
#   - Los clientes se registran UNA VEZ con setup_clients.py
#   - El pipeline itera sobre todos los clientes en cada ejecución
#   - Si un cliente falla, los demás continúan ejecutándose
#
# SEPARACIÓN SETUP vs PIPELINE:
#   setup_clients.py    → registro de clientes + calibración PVGIS (una vez)
#   sunsaver_orchestrator.py → pipeline recurrente (cada hora/día)
#
# FLUJOS ACTUALES:
#   - Clima    : OpenWeatherMap → raw_weather → silver_weather
#   - Solar    : cálculo matemático → silver_solar_forecast
#
# FLUJOS FUTUROS:
#   - Precios  : ESIOS (REE) → raw_prices → silver_prices
#   - Decisiones: silver_weather + silver_solar_forecast + silver_prices → oro
# ------------------------------------------------------------------------------
# EJECUCIÓN:
#   cd src
#   python setup_clients.py          # primera vez
#   python sunsaver_orchestrator.py  # cada ejecución
# ==============================================================================

import logging

import extract_openweather
import transform_openweather
import calculate_solar_forecast
import db_manager

# ------------------------------------------------------------------------------
# CONFIGURACIÓN GLOBAL DEL LOGGING
# Se configura aquí — en el punto de entrada — para que todos los módulos
# hereden esta configuración a través de logging.getLogger(__name__).
# ------------------------------------------------------------------------------

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)

logger = logging.getLogger(__name__)


def run_pipeline_for_client(client: dict):
    """
    Ejecuta el pipeline ETL completo para un cliente específico.

    Si un flujo falla (ej: API de clima no responde), los demás continúan.

    Parámetros:
        client : dict — configuración del cliente leída desde la tabla 'clients'.
    """
    client_id   = client['id']
    client_name = client['name']

    logger.info(f"👤 Procesando cliente: '{client_name}' (id={client_id})")

    # --------------------------------------------------------------------------
    # FLUJO 1: CLIMA (OpenWeatherMap)
    # Pronóstico de 5 días con intervalos de 3h para la ubicación del cliente.
    # silver_weather usa INSERT OR REPLACE — siempre contiene la predicción
    # más actualizada. El historial completo queda en raw_weather (bronce).
    # --------------------------------------------------------------------------

    logger.info(f"  📡 [CLIMA] Extrayendo para '{client_name}'...")
    silver_weather = []
    try:
        # EXTRACT: datos crudos de la API para las coordenadas del cliente
        raw_weather = extract_openweather.extract_weather(
            lat=client['latitude'],
            lon=client['longitude']
        )

        # LOAD BRONCE: historial inmutable de todas las ingestas
        db_manager.load_bronze(raw_weather, 'raw_weather', client_id=client_id)

        # READ BRONCE: leemos desde DB para desacoplar extract de transform
        bronze_weather = db_manager.read_bronze('raw_weather', client_id=client_id, latest_only=True)

        # TRANSFORM: limpieza, casting y normalización
        silver_weather = transform_openweather.transform_weather(bronze_weather, client_id=client_id)

        # LOAD PLATA: INSERT OR REPLACE — sobreescribe predicciones anteriores
        if silver_weather:
            db_manager.load_to_db(silver_weather, "silver_weather")
        else:
            logger.warning(f"  ⚠️  No se generaron datos de clima para '{client_name}'.")

    except Exception as e:
        logger.error(f"  ❌ Flujo de clima fallido para '{client_name}': {e}")

    # --------------------------------------------------------------------------
    # FLUJO 2: PREDICCIÓN SOLAR (cálculo matemático)
    # Usa los datos de silver_weather + parámetros del cliente para predecir
    # la potencia generada hora a hora durante los próximos 5 días.
    # No necesita llamada a API — todo se calcula localmente.
    # --------------------------------------------------------------------------

    logger.info(f"  ☀️  [SOLAR] Calculando predicción para '{client_name}'...")
    try:
        if not silver_weather:
            logger.warning(f"  ⚠️  Sin datos de clima — omitiendo predicción solar para '{client_name}'.")
        else:
            # CALCULATE: fórmula P = A × r × H × PR con ajuste térmico
            solar_forecast = calculate_solar_forecast.calculate_solar_forecast(
                silver_weather=silver_weather,
                client=client
            )

            # LOAD PLATA: INSERT OR REPLACE — sobreescribe predicciones anteriores
            if solar_forecast:
                db_manager.load_to_db(solar_forecast, "silver_solar_forecast")
            else:
                logger.warning(f"  ⚠️  No se generó predicción solar para '{client_name}'.")

    except Exception as e:
        logger.error(f"  ❌ Predicción solar fallida para '{client_name}': {e}")

    # --------------------------------------------------------------------------
    # FLUJO 3: PRECIOS DE LA LUZ (ESIOS — Red Eléctrica España)
    # Pendiente de implementar — precios horarios del mercado eléctrico.
    # --------------------------------------------------------------------------

    # logger.info(f"  💶 [PRECIOS] Extrayendo para '{client_name}'...")
    # raw_prices    = extract_esios.extract_prices()
    # db_manager.load_bronze(raw_prices, 'raw_prices', client_id=client_id)
    # bronze_prices = db_manager.read_bronze('raw_prices', client_id=client_id, latest_only=True)
    # silver_prices = transform_esios.transform_prices(bronze_prices, client_id=client_id)
    # db_manager.load_to_db(silver_prices, "silver_prices")

    logger.info(f"✅ Pipeline finalizado para '{client_name}'.")


def run_pipeline():
    """
    Ejecuta el pipeline ETL completo para todos los clientes registrados.
    """
    logger.info("🚀 Iniciando Pipeline ETL SunSaver (multi-cliente)...")

    # Garantizamos que todas las tablas existen antes de operar
    db_manager.create_tables()

    # Cargamos todos los clientes registrados
    clients = db_manager.get_all_clients()

    if not clients:
        logger.warning("⚠️  No hay clientes registrados en la DB.")
        logger.warning("    Ejecuta primero: python setup_clients.py")
        logger.info("🏁 Pipeline ETL SunSaver finalizado (sin clientes).")
        return

    logger.info(f"👥 {len(clients)} cliente(s) encontrado(s). Iniciando procesamiento...")

    # Procesamos cada cliente de forma independiente
    for client in clients:
        run_pipeline_for_client(client)

    logger.info("🏁 Pipeline ETL SunSaver finalizado para todos los clientes.")


if __name__ == "__main__":
    run_pipeline()
