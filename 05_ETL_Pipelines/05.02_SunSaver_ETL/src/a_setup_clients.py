import os
import logging
import sqlite3
import db_manager
import os
import sqlite3
import logging
import json
from pathlib import Path
from dotenv import load_dotenv

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)

logger = logging.getLogger(__name__)


def setup():
    """Crea las tablas y registra los clientes iniciales."""

    db_manager.create_tables()



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
            "battery_capacity_kwh": 0.0,
            "soc_min_pct": 20.0,
            "installation_cost_eur": 0.0,
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
            "battery_capacity_kwh": 0.0,
            "soc_min_pct": 20.0,
            "installation_cost_eur": 0.0,
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
            "battery_capacity_kwh": 0.0,
            "soc_min_pct": 20.0,
            "installation_cost_eur": 0.0,
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
            "battery_capacity_kwh": 0.0,
            "soc_min_pct": 20.0,
            "installation_cost_eur": 0.0,
            "timezone":      "Europe/Madrid"
        },
    ]

    # 1. Preparar la consulta SQL con placeholders
    # Usamos nombres de columnas explícitos para evitar errores
    query = '''
        INSERT INTO clients (
            name, latitude, longitude, peak_power_kw, panel_area_m2, 
            efficiency, panel_type, loss_pct, angle, aspect, 
            mounting, battery_capacity_kwh, soc_min_pct, 
            installation_cost_eur, timezone
        ) VALUES (
            :name, :latitude, :longitude, :peak_power_kw, :panel_area_m2, 
            :efficiency, :panel_type, :loss_pct, :angle, :aspect, 
            :mounting, :battery_capacity_kwh, :soc_min_pct, 
            :installation_cost_eur, :timezone
        )
    '''

    # 3. Insertar todos los datos de golpe
    try:
        cursor.executemany(query, clients)
        connection.commit()
        print(f"Éxito: {len(clients)} clientes insertados correctamente.")
    except Exception as e:
        connection.rollback()
        print(f"Error al insertar: {e}")


if __name__ == "__main__":
    setup()
