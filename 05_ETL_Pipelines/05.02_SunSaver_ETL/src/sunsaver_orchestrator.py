import logging
import extract_openweather
import transform_openweather
import extract_pvgis
import transform_pvgis
import persistence_manager

# 1. CONFIGURACIÓN GLOBAL DEL LOGGING
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)

logger = logging.getLogger(__name__)



def run_sunsaver_pipeline():
    """Orquestador principal del Robot ETL SunSaver."""
    
    logger.info("🚀 Iniciando Pipeline ETL de SunSaver...")
    
    # 1. ASEGURAR INFRAESTRUCTURA (Tablas)
    persistence_manager.create_tables()

    # --- FLUJO 1: CLIMA (OpenWeather) ---
    logger.info("📡 [CLIMA] Iniciando extracción...")
    raw_weather = extract_openweather.get_weather_forecast()
    
    # Guardar datos crudos de api en db
    persistence_manager.save_bronze_to_db(raw_weather, 'raw_data_weather')
    bronce_table=persistence_manager.read_bronze_from_db('raw_data_weather',True)
    # Ahora enviamos la lista completa al transformador unificado
    clean_weather = transform_openweather.transform_weather_data(bronce_table) 
    
    if clean_weather:
        persistence_manager.save_to_db(clean_weather, "weather_forecast")
    else:
        logger.warning("⚠️  No se procesaron datos de Clima.")


    # --- FLUJO 2: SOLAR (PVGIS) ---
    logger.info("🛰️  [SOLAR] Iniciando extracción...")
    raw_solar = extract_pvgis.get_pvgis_data()

    # Guardar datos crudos de api en db
    persistence_manager.save_bronze_to_db(raw_solar, 'raw_data_solar')
    
    # El transformador de PVGIS ya procesa la lista internamente
    clean_solar = transform_pvgis.transform_pvgis_data(raw_solar)
    
    if clean_solar:
        persistence_manager.save_to_db(clean_solar, "solar_generation")
    else:
        logger.warning("⚠️ No se procesaron datos de Solar.")


    logger.info("🏁 PROCESO ETL GLOBAL FINALIZADO CON ÉXITO.")

if __name__ == "__main__":
    run_sunsaver_pipeline()