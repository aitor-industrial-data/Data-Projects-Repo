################################################################################
# 26_csv_to_sqlite_bulk.py
# AUTOR: Aitor | Ingeniero Técnico Industrial | Data Engineer
# PROYECTO: Pipeline de Ingesta Masiva (Python Core)
#
# ENUNCIADO:
# 1. Desarrollar un script para la carga automatizada de datos desde un 
#    archivo CSV externo hacia una base de datos SQLite.
# 2. Implementar una lógica de "Carga Masiva" (Bulk Load) utilizando el 
#    método executemany() para optimizar el rendimiento de inserción.
# 3. Crear automáticamente la tabla de destino definiendo el esquema técnico 
#    adecuado (Data Types) para cada columna.
# 4. Asegurar la integridad de la operación mediante el manejo de transacciones 
#    (Commit/Rollback) y cierre seguro de conexiones.
# 5. Foco Técnico: Ingestión de Datos, Librería sqlite3, Manejo de CSV y 
#    Optimización de Transacciones.
################################################################################

import sqlite3
import csv
import os

# --- 1. GENERACIÓN DEL DATASET (Simulación de Origen) ---
file_name = 'sensor_data.csv'
header = ['sensor_id', 'timestamp', 'temperature', 'status']
data = [
    ('SN-001', '2026-03-19 08:00:00', 22.5, 'OK'),
    ('SN-002', '2026-03-19 08:05:00', 45.8, 'WARNING'),
    ('SN-001', '2026-03-19 08:10:00', 23.1, 'OK'),
    ('SN-003', '2026-03-19 08:15:00', 120.2, 'CRITICAL')
]

with open(file_name, mode='w', newline='', encoding='utf-8') as file:
    writer = csv.writer(file)
    writer.writerow(header)
    writer.writerows(data)

# --- 2. PROCESO ETL (Extract, Transform, Load) ---
print("\n"+"="*60)
print("🚀 INICIANDO PIPELINE DE INGESTA: CSV -> SQLITE")
print("="*60)

try:
    # Conexión y creación de tabla
    with sqlite3.connect("industrial_metrics.db") as conn:
        cursor = conn.cursor()
        
        # Definición de Esquema Técnico
        cursor.execute("DROP TABLE IF EXISTS sensor_readings")
        cursor.execute("""
            CREATE TABLE sensor_readings (
                sensor_id TEXT,
                timestamp TEXT,
                temperature REAL,
                status TEXT
            )
        """)
        
        # Extracción y Transformación
        with open(file_name, 'r', encoding='utf-8') as f:
            reader = csv.reader(f)
            next(reader)  # Omitimos la cabecera para no meter "sensor_id" como dato
            
            # Cargamos todo en una lista de tuplas para el Bulk Insert
            clean_data = [tuple(row) for row in reader]
        
        # Carga Masiva (Bulk Load)
        cursor.executemany("INSERT INTO sensor_readings VALUES (?, ?, ?, ?)", clean_data)
        
        conn.commit()
        
        # Validación de Carga
        cursor.execute("SELECT COUNT(*) FROM sensor_readings")
        total_rows = cursor.fetchone()[0]

    # --- REPORTE DE SALIDA ---
    print(f"\n[📊 STATUS REPORT]")
    print(f" ├─ {'Archivo origen:':<20} {file_name}")
    print(f" ├─ {'Registros leídos:':<20} {len(clean_data)}")
    print(f" ├─ {'Carga en DB:':<20} {total_rows} filas insertadas")
    print(f" └─ {'Transacción:':<20} SUCCESS ✅")
    print("\n" + "="*60)

except Exception as e:
    print(f"\n[❌ FATAL ERROR]: {e}")