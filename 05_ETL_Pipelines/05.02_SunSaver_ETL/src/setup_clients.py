# ==============================================================================
# setup_clients.py
# ------------------------------------------------------------------------------
# RESPONSABILIDAD : Registrar los clientes iniciales en la base de datos.
# ------------------------------------------------------------------------------
# QUÉ HACE ESTE SCRIPT:
#   Inserta los clientes en la tabla 'clients' de la DB con todos sus
#   parámetros de instalación. Los clientes quedan guardados permanentemente
#   y el pipeline ETL recurrente los leerá en cada ejecución.
#
# CUÁNDO EJECUTARLO:
#   - La primera vez que se configura el proyecto
#   - Cuando se quiere añadir un nuevo cliente
#   - NUNCA en el pipeline automático — es un script de setup, no de ETL
#
# PARÁMETROS DE INSTALACIÓN:
#   loss_pct   → Pérdidas del sistema en %. Valor estándar del sector: 14%.
#               
#   panel_type → Tipo de panel fotovoltaico. Afecta al coeficiente térmico
#                usado en el cálculo de potencia generada:
#                  'crystSi' → -0.40%/°C (silicio cristalino — más común)
#                  'CIS'     → -0.36%/°C (cobre-indio-selenio)
#                  'CdTe'    → -0.25%/°C (telururo de cadmio — menos sensible al calor)
#
# EJECUCIÓN:
#   cd src
#   python setup_clients.py
# ==============================================================================

import logging
import db_manager

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)

logger = logging.getLogger(__name__)


def setup():
    """Crea las tablas y registra los clientes iniciales."""

    db_manager.create_tables()

    # Comprobamos si ya hay clientes registrados para no duplicar
    existing = db_manager.get_all_clients()
    if existing:
        logger.warning(f"⚠️  Ya hay {len(existing)} cliente(s) registrado(s) en la DB.")
        logger.warning("    Para añadir más, llama a db_manager.add_client() directamente.")
        return

    # --------------------------------------------------------------------------
    # CLIENTES DE PRUEBA
    # Instalaciones ficticias pero realistas para demostración del sistema.
    # loss_pct = 14% — valor estándar del sector para instalaciones nuevas.
    # --------------------------------------------------------------------------

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

    registered = 0
    for client in clients:
        client_id = db_manager.add_client(**client)
        if client_id:
            registered += 1

    logger.info(f"🏁 Setup completado: {registered} cliente(s) registrado(s).")


if __name__ == "__main__":
    setup()
