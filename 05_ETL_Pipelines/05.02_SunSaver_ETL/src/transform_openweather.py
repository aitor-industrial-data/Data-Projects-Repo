import logging

logger = logging.getLogger(__name__)

def transform_weather_data(raw_data: list[dict]) -> list[dict]:
    """
    TRANSFORM unificado: Recibe el JSON completo y devuelve una LISTA de diccionarios.
    Mantiene la lógica interna original de limpieza y tipos.
    """
    if not raw_data:
        logger.warning("⚠️  No hay datos de clima para transformar.")
        return []

    # Extraemos la lista de pronósticos del JSON de OpenWeather
    forecast_list = raw_data
    transformed_data = []

    for item in forecast_list:
        try:
                    
            # 1. Extraemos y aseguramos Tipos de Datos (Casting)
            raw_forecast_time = item.get('dt_txt', "")
            clean_forecast_time = str(raw_forecast_time)
            
            raw_unix_ts = item.get('dt', 0)
            clean_unix_ts = int(raw_unix_ts)
            
            raw_temp = item.get('main', {}).get('temp', 0.0)
            clean_temp = round(float(raw_temp), 2)

            raw_clouds = item.get('clouds', {}).get('all', 0)
            clean_clouds = int(raw_clouds)

            raw_desc = item.get('weather', [{}])[0].get('description', 'unknown')
            clean_desc = str(raw_desc).strip().lower()
            
            raw_w_speed = item.get('wind', {}).get('speed', 0.0)
            clean_w_speed = round(float(raw_w_speed), 2)

            raw_w_gust = item.get('wind', {}).get('gust', clean_w_speed)
            clean_w_gust = round(float(raw_w_gust), 2)

            # 2. Construimos el diccionario de la fila
            row_dict = {
                "forecast_time":   clean_forecast_time,
                "unix_timestamp":  clean_unix_ts,
                "temperature":     clean_temp,
                "cloud_coverage":  clean_clouds,
                "condition_desc":  clean_desc,
                "wind_speed":      clean_w_speed,
                "wind_gust":       clean_w_gust,
                "source":          "OpenWeather_API" # Identificador de origen
            }
            
            # Guardamos en nuestra lista unificada
            transformed_data.append(row_dict)

        except (ValueError, TypeError, KeyError) as e:
            logger.warning(f"⚠️ Error transformando registro {item.get('dt')}: {e}")
            continue # Saltamos la fila corrupta y seguimos con la lista

    logger.info(f"✅ Transformación de clima finalizada: {len(transformed_data)} registros.")
    return transformed_data