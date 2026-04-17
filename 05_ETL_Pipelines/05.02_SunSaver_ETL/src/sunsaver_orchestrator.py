import logging
import extract_openweather
import transform_openweather
import persistence_manager

# 1. CONFIGURACIÓN GLOBAL DEL LOGGING
# Esto afecta a todos los archivos importados
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)

logger = logging.getLogger(__name__)

def run_weather_pipeline():
    # 1. Asegurar que las tablas existen
    logger.info("🚀 Iniciando Pipeline ETL de SunSaver...")
    persistence_manager.create_tables()

    # 2. Proceso para OpenWeather
    logger.info("📡 Iniciando extracción de datos de Clima...")
    raw_data_list = extract_openweather.get_weather_forecast()
    
    if raw_data_list:
        clean_data_list = []
        
        # Transformación Registro a Registro
        for item in raw_data_list:
            clean_item = transform_openweather.transform_weather_forecast(item)
            if clean_item:
                clean_data_list.append(clean_item)
        
        # 3. Guardado Masivo
        if clean_data_list:
            persistence_manager.save_to_db(clean_data_list, "weather_forecast")
            logger.info(f"🏁 ETL finalizado con éxito: {len(clean_data_list)} registros.")
        else:
            logger.warning("⚠️ No se generaron datos limpios para guardar.")
    else:
        logger.error("❌ No se pudieron obtener datos brutos de la API.")

if __name__ == "__main__":
    run_weather_pipeline()