from datetime import datetime
import logging

logger = logging.getLogger(__name__)

def transform_pvgis_data(raw_data: dict) -> list:
    """
    Transforma el JSON bruto de PVGIS con manejo de errores por cada registro.
    """
    if not raw_data:
        logger.warning("⚠️ No hay datos para transformar.")
        return []

    hourly_list = raw_data.get("outputs", {}).get("hourly", [])
    transformed_data = []

    for row in hourly_list:
        try:
            # 1. Procesamiento de Fecha
            raw_time = row.get("time")
            if not raw_time:
                continue # Saltamos si no hay tiempo

            dt_obj = datetime.strptime(raw_time, "%Y%m%d:%H%M")
            clean_timestamp = dt_obj.strftime("%Y-%m-%d %H:00:00")

            raw_power = row.get("P", 0)
            clean_power = round(float(raw_power / 1000), 3) # De W a kW

            raw_irradiance = row.get("G(i)", 0.0)
            clean_irradiance = round(float(raw_irradiance),3)

            raw_temp = row.get("T2m", 0.0)
            clean_temp = round(float(raw_temp),3)

            raw_sun_height = row.get("H_sun", 0.0)
            clean_sun_height = round(float(raw_sun_height),3)
            

            # 3. Construcción del Item
            item = {
                "timestamp": clean_timestamp,  
                "power_kw": clean_power, 
                "irradiance_wm2": clean_irradiance,
                "temp_c": clean_temp,
                "sun_height_deg": clean_sun_height,
                "source": "PVGIS_JRC_EU"
            }
            transformed_data.append(item)

        except (ValueError, TypeError) as e:
            # Si una fila falla, logueamos el error pero el bucle SIGUE
            logger.error(f"❌ Error transformando fila {row.get('time', 'unknown')}: {e}")
            continue 

    logger.info(f"✅ Transformación completada: {len(transformed_data)}/8760 registros procesados con éxito.")
    return transformed_data
    
