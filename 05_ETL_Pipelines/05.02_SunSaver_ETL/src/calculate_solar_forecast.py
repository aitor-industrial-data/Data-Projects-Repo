# ==============================================================================
# calculate_solar_forecast.py
# ------------------------------------------------------------------------------
# RESPONSABILIDAD : Calcular la predicción de generación solar para cada cliente.
# CAPA ETL        : TRANSFORM (cálculo sobre datos de plata)
# ==============================================================================

import math
import logging
from datetime import datetime, timezone

logger = logging.getLogger(__name__)

# ==============================================================================
# ESTIMACIÓN DE POSICIÓN E IRRADIANCIA
# ==============================================================================

def calculate_solar_position(unix_timestamp: int, lat: float, lon: float) -> dict:
    """Calcula posición solar usando algoritmo simplificado de la NOAA."""
    dt = datetime.fromtimestamp(unix_timestamp, tz=timezone.utc)
    day_of_year = dt.timetuple().tm_yday

    # Hora solar corregida por longitud
    hour_utc = dt.hour + dt.minute / 60.0 + dt.second / 3600.0
    solar_time = hour_utc + lon / 15.0

    # Declinación y Ángulo Horario
    declination = 23.45 * math.sin(math.radians(360 / 365 * (day_of_year - 81)))
    hour_angle = (solar_time - 12) * 15

    lat_rad = math.radians(lat)
    dec_rad = math.radians(declination)
    ha_rad = math.radians(hour_angle)

    # Elevación
    sin_elevation = (math.sin(lat_rad) * math.sin(dec_rad) +
                     math.cos(lat_rad) * math.cos(dec_rad) * math.cos(ha_rad))
    elevation = math.degrees(math.asin(max(-1, min(1, sin_elevation))))

    # Azimut
    cos_azimuth = ((math.sin(dec_rad) - math.sin(lat_rad) * math.sin(math.radians(elevation))) /
                   (math.cos(lat_rad) * math.cos(math.radians(elevation))))
    azimuth = math.degrees(math.acos(max(-1, min(1, cos_azimuth))))
    
    if hour_angle > 0:
        azimuth = 360 - azimuth

    return {"elevation_deg": round(elevation, 2), "azimuth_deg": round(azimuth, 2)}

def estimate_irradiance(unix_timestamp: int, lat: float, lon: float,
                        cloud_coverage_pct: int, angle: int, aspect: int) -> float:
    """Calcula irradiancia en plano inclinado usando AOI (Ángulo de Incidencia)."""
    SOLAR_CONSTANT = 1361.0
    solar_pos = calculate_solar_position(unix_timestamp, lat, lon)
    sun_elev = solar_pos["elevation_deg"]
    sun_azim = solar_pos["azimuth_deg"]

    if sun_elev <= 0:
        return 0.0

    # Conversión a radianes
    sun_elev_rad = math.radians(sun_elev)
    sun_azim_rad = math.radians(sun_azim)
    panel_tilt_rad = math.radians(angle)
    
    # En tu DB Sur=0. La fórmula requiere Sur=180.
    panel_az_rad = math.radians(aspect + 180) 

    # Cálculo de AOI (Angle of Incidence)
    cos_aoi = (math.sin(sun_elev_rad) * math.cos(panel_tilt_rad) +
               math.cos(sun_elev_rad) * math.sin(panel_tilt_rad) * math.cos(sun_azim_rad - panel_az_rad))

    aoi_factor = max(0.0, cos_aoi)

    # Transmitancia atmosférica estimada (0.75) y factor nubes (reducción máx 85%)
    clearsky_tilted = SOLAR_CONSTANT * 0.75 * aoi_factor
    cloud_factor = 1.0 - (cloud_coverage_pct / 100.0) * 0.85
    
    return round(max(0.0, clearsky_tilted * cloud_factor), 2)

# ==============================================================================
# CÁLCULO DE POTENCIA GENERADA
# ==============================================================================

def calculate_power_kw(irradiance_wm2: float, temperature_c: float,
                       panel_area_m2: float, efficiency: float,
                       loss_pct: float, panel_type: str) -> tuple[float, float]:
    """Aplica el Performance Ratio ajustado por temperatura según el tipo de panel."""
    pr_base = 1.0 - (loss_pct / 100.0)

    # Coeficientes térmicos (Pérdida por cada °C sobre 25°C)
    THERMAL_COEFF = {"crystSi": 0.004, "CIS": 0.0036, "CdTe": 0.0025}
    t_coeff = THERMAL_COEFF.get(panel_type, 0.004)

    # El panel solo sufre degradación si T > 25°C
    thermal_correction = 1.0 - t_coeff * max(0.0, temperature_c - 25.0)
    performance_ratio = round(pr_base * thermal_correction, 4)

    # Potencia (W) = A * Eff * Irr * PR
    power_w = panel_area_m2 * efficiency * irradiance_wm2 * performance_ratio
    return max(0.0, round(power_w / 1000.0, 3)), performance_ratio

# ==============================================================================
# PROCESAMIENTO POR CLIENTE
# ==============================================================================

def calculate_solar_forecast(silver_weather: list[dict], client: dict) -> list[dict]:
    """Itera sobre el clima y genera la tabla de predicción para un cliente."""
    if not silver_weather:
        return []

    forecast_data = []
    
    for record in silver_weather:
        try:
            irradiance = estimate_irradiance(
                unix_timestamp=record['unix_timestamp'],
                lat=client['latitude'],
                lon=client['longitude'],
                cloud_coverage_pct=record['cloud_coverage'],
                angle=client['angle'],
                aspect=client['aspect']
            )

            predicted_kw, pr = calculate_power_kw(
                irradiance_wm2=irradiance,
                temperature_c=record['temperature'],
                panel_area_m2=client['panel_area_m2'],
                efficiency=client['efficiency'],
                loss_pct=client['loss_pct'],
                panel_type=client.get('panel_type', 'crystSi')
            )

            forecast_data.append({
                "unix_timestamp": record['unix_timestamp'],
                "client_id": client['id'],
                "forecast_time": record['forecast_time'],
                "irradiance_wm2": irradiance,
                "temperature_c": record['temperature'],
                "cloud_factor": round(1.0 - (record['cloud_coverage'] / 100.0) * 0.85, 4),
                "performance_ratio": pr,
                "predicted_power_kw": predicted_kw
            })

        except Exception as e:
            logger.error(f"Error procesando registro {record.get('unix_timestamp')}: {e}")
            continue

    return forecast_data