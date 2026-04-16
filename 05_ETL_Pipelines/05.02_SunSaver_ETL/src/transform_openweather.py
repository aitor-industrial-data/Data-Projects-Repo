
def transform_weather_forecast(item: dict) -> dict:
    """
    TRANSFORM: Converts raw data to explicit types and handles errors.
    """
    try:
        # 1. Extraemos y aseguramos Tipos de Datos (Casting)
        # La fecha la dejamos en str (formato ISO para SQLite)
        raw_forecast_time = item.get('dt_txt', "")
        clean_forecast_time = str(raw_forecast_time)
        
        # El timestamp debe ser entero para cálculos rápidos
        raw_unix_ts = item.get('dt', 0)
        clean_unix_ts = int(raw_unix_ts)
        
        # La temperatura en decimales
        raw_temp = item.get('main', {}).get('temp', 0.0)
        clean_temp = round(float(raw_temp),2)

        # El porcentaje de nubosidad es un entero
        raw_clouds = item.get('clouds', {}).get('all', 0)
        clean_clouds = int(raw_clouds)

        # La descripcion en minusculas
        raw_desc = item.get('weather', [{}])[0].get('description', 'unknown')
        clean_desc = str(raw_desc).strip().lower()
        
        # El viento en float
        raw_w_speed = item.get('wind', {}).get('speed', 0.0)
        clean_w_speed = round(float(raw_w_speed),2)

        # Usamos un .get() extra para gust porque a veces no viene en la API
        raw_w_gust = item.get('wind', {}).get('gust', clean_w_speed)
        clean_w_gust = round(float(raw_w_gust),2)

        # 2. Retornamos el diccionario limpio
        return {
            "forecast_time":   clean_forecast_time,
            "unix_timestamp":  clean_unix_ts,
            "temperature":     clean_temp,
            "cloud_coverage":  clean_clouds,
            "condition_desc":  clean_desc,
            "wind_speed":      clean_w_speed,
            "wind_gust":       clean_w_gust
        }

    except (ValueError, TypeError, KeyError) as e:
        # Si un dato viene mal (ej: una letra donde debería haber un número)
        print(f"⚠️ Error transforming record {item.get('dt')}: {e}")
        return None