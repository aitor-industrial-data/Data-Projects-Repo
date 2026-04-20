# ==============================================================================
# transform_openweather.py
# ------------------------------------------------------------------------------
# RESPONSABILIDAD : Transformar los datos CRUDOS de OpenWeather a formato limpio.
# CAPA ETL        : TRANSFORM
# ENTRADA         : list[dict] — datos crudos leídos desde la capa bronce
# SALIDA          : list[dict] — registros limpios y tipados para capa plata
# ------------------------------------------------------------------------------
# QUÉ HACE ESTE SCRIPT:
#   - Extrae solo los campos relevantes de cada registro crudo
#   - Garantiza los tipos de dato correctos (casting explícito)
#   - Normaliza valores de texto (strip, lowercase)
#   - Maneja valores ausentes con defaults seguros
#   - Añade client_id a cada registro para soporte multi-cliente
#   - Si un registro individual falla, lo salta y continúa con el resto
# ==============================================================================

import logging

logger = logging.getLogger(__name__)


def transform_weather(raw_data: list[dict], client_id: int) -> list[dict]:
    """
    Transforma los registros crudos de OpenWeather a formato limpio para la DB.

    Parámetros:
        raw_data  : list[dict] — lista de registros crudos de la capa bronce.
        client_id : int — id del cliente al que pertenecen los datos.

    Retorna:
        list[dict] — lista de registros limpios con las claves:
            unix_timestamp : int   — timestamp Unix
            client_id      : int   — id del cliente (para multi-cliente)
            forecast_time  : str   — timestamp legible (UTC)
            temperature    : float — temperatura en °C
            cloud_coverage : int   — cobertura nubosa en %
            condition_desc : str   — descripción normalizada del tiempo
            wind_speed     : float — velocidad del viento en m/s
            wind_gust      : float — ráfaga de viento en m/s
            source         : str   — identificador de origen del dato
    """
    if not raw_data:
        logger.warning("⚠️  No hay datos de clima para transformar.")
        return []

    transformed_data = []

    for item in raw_data:
        try:
            # ------------------------------------------------------------------
            # 1. EXTRACCIÓN Y CASTING DE TIPOS
            # Usamos .get() con valores por defecto para evitar KeyError.
            # El casting explícito garantiza que los tipos son correctos
            # independientemente de cómo lleguen los datos desde la API.
            # ------------------------------------------------------------------

            clean_unix_ts       = int(item.get('dt', 0))
            clean_forecast_time = str(item.get('dt_txt', ""))
            clean_temp          = round(float(item.get('main', {}).get('temp', 0.0)), 2)
            clean_clouds        = int(item.get('clouds', {}).get('all', 0))
            clean_wind_speed    = round(float(item.get('wind', {}).get('speed', 0.0)), 2)

            # La ráfaga no siempre está presente — usamos la velocidad como fallback
            clean_wind_gust = round(float(item.get('wind', {}).get('gust', clean_wind_speed)), 2)

            # La descripción viene en una lista — cogemos el primer elemento
            raw_desc   = item.get('weather', [{}])[0].get('description', 'unknown')
            clean_desc = str(raw_desc).strip().lower()

            # ------------------------------------------------------------------
            # 2. CONSTRUCCIÓN DEL REGISTRO LIMPIO
            # unix_timestamp y client_id van primero porque forman la
            # PRIMARY KEY compuesta en la tabla silver_weather.
            # El campo 'source' permite rastrear el origen en consultas cruzadas.
            # ------------------------------------------------------------------

            row = {
                "unix_timestamp": clean_unix_ts,
                "client_id":      client_id,
                "forecast_time":  clean_forecast_time,
                "temperature":    clean_temp,
                "cloud_coverage": clean_clouds,
                "condition_desc": clean_desc,
                "wind_speed":     clean_wind_speed,
                "wind_gust":      clean_wind_gust,
                "source":         "OpenWeather_API"
            }

            transformed_data.append(row)

        except (ValueError, TypeError, KeyError) as e:
            # Registro corrupto o con formato inesperado — lo saltamos y seguimos.
            # Logueamos el timestamp del registro problemático para facilitar auditoría.
            logger.warning(f"⚠️  Registro omitido (dt={item.get('dt', 'unknown')}): {e}")
            continue

    logger.info(f"✅ Transformación de clima finalizada: {len(transformed_data)} registros (client_id={client_id}).")
    return transformed_data
