

import logging
import a_extract_pvgis
import a_db_manager


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

client = {
            "name":          "Nave Industrial Pamplona",
            "latitude":      42.8124,
            "longitude":     -1.6922,
            "peak_power_kw": 16.0,       # 40 paneles × 400W
            "panel_area_m2": 80.0,       # 40 paneles × 2m²
            "efficiency":    0.20,       # 20% — panel crystSi estándar
            "panel_type":    "crystSi",  # Silicio cristalino — coef. térmico -0.40%/°C
            "loss_pct":      14.0,       # Estándar del sector (cables, inversor, suciedad)
            "angle":         30,         # Inclinación óptima para Navarra
            "aspect":        0,          # Orientación sur
            "mounting":      "free",     # Ventilado (estructura elevada)
            "timezone":      "Europe/Madrid"
        }

clients = [
        {
            "name":          "Nave Industrial Pamplona",
            "latitude":      42.8124,
            "longitude":     -1.6922,
            "peak_power_kw": 16.0,       # 40 paneles × 400W
            "panel_area_m2": 80.0,       # 40 paneles × 2m²
            "efficiency":    0.20,       # 20% — panel crystSi estándar
            "panel_type":    "crystSi",  # Silicio cristalino — coef. térmico -0.40%/°C
            "loss_pct":      14.0,       # Estándar del sector (cables, inversor, suciedad)
            "angle":         30,         # Inclinación óptima para Navarra
            "aspect":        0,          # Orientación sur
            "mounting":      "free",     # Ventilado (estructura elevada)
            "timezone":      "Europe/Madrid"
        },
        {
            "name":          "Polígono Industrial Zaragoza",
            "latitude":      41.6488,
            "longitude":     -0.8891,
            "peak_power_kw": 50.0,
            "panel_area_m2": 250.0,
            "efficiency":    0.21,
            "panel_type":    "crystSi",
            "loss_pct":      14.0,
            "angle":         28,
            "aspect":        0,
            "mounting":      "free",
            "timezone":      "Europe/Madrid"
        },
        {
            "name":          "Edificio Oficinas Madrid",
            "latitude":      40.4168,
            "longitude":     -3.7038,
            "peak_power_kw": 8.0,
            "panel_area_m2": 40.0,
            "efficiency":    0.19,
            "panel_type":    "CdTe",     # Telururo de cadmio — menos sensible al calor
            "loss_pct":      16.0,       # Más pérdidas por integración en edificio sin ventilación
            "angle":         15,
            "aspect":        10,         # Ligeramente desviado del sur
            "mounting":      "building",
            "timezone":      "Europe/Madrid"
        },
        {
            "name":          "Finca Recreativa Ciriza",
            "latitude":      42.794390,
            "longitude":     -1.822150,
            "peak_power_kw": 2.5,        # 5 paneles × 500W
            "panel_area_m2": 10.0,       # 5 paneles × 2m²
            "efficiency":    0.20,       # 20% — panel crystSi estándar
            "panel_type":    "crystSi",  # Silicio cristalino — coef. térmico -0.40%/°C
            "loss_pct":      14.0,       # Estándar del sector (cables, inversor, suciedad)
            "angle":         30,         # Inclinación óptima para Navarra
            "aspect":        0,          # Orientación sur
            "mounting":      "free",     # Ventilado (estructura elevada)
            "timezone":      "Europe/Madrid"
        },
    ]


raw_pvgis=a_extract_pvgis.extract_pvgis(client)
print(raw_pvgis['outputs']['tmy_hourly'][9])

a_db_manager.create_tables()
for client in clients:
    a_db_manager.load_bronze(raw_pvgis, 'raw_solar',client['name'])

