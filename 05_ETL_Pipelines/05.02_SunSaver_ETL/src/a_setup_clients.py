import sqlite3
import hashlib

# Lista de clientes (Tu fuente de verdad)
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

def generate_client_id(name):
    """Genera un ID consistente basado en el nombre."""
    return hashlib.md5(name.encode('utf-8')).hexdigest()[:12]

def ingest_clients_to_bronze(client_list):
    # Conexión a la base de datos
    db_path = "data_projects_repo.db"
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # Crear tabla si no existe
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS clients_bronze (
            client_id TEXT PRIMARY KEY,
            name TEXT UNIQUE,
            latitude REAL,
            longitude REAL,
            peak_power_kw REAL,
            panel_area_m2 REAL,
            efficiency REAL,
            panel_type TEXT,
            loss_pct REAL,
            angle REAL,
            aspect REAL,
            mounting TEXT,
            battery_capacity_kwh REAL,
            soc_min_pct REAL,
            installation_cost_eur REAL,
            timezone TEXT
        )
    ''')

    for client in client_list:
        client['client_id'] = generate_client_id(client['name'])
        
        # SQL para inserción o actualización (Upsert)
        sql = '''
            INSERT OR REPLACE INTO clients_bronze VALUES (
                :client_id, :name, :latitude, :longitude, :peak_power_kw, 
                :panel_area_m2, :efficiency, :panel_type, :loss_pct, :angle, 
                :aspect, :mounting, :battery_capacity_kwh, :soc_min_pct, 
                :installation_cost_eur, :timezone
            )
        '''
        cursor.execute(sql, client)

    conn.commit()
    conn.close()
    print(f"Proceso completado: {len(client_list)} clientes procesados en la capa Bronze.")

if __name__ == "__main__":
    ingest_clients_to_bronze(clients)