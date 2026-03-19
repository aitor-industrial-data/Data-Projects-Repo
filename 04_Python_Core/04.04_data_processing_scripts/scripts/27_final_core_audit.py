################################################################################
# 27_final_core_audit.py
# AUTOR: Aitor | Ingeniero Técnico Industrial | Data Engineer
# PROYECTO: Sistema de Auditoría de Activos Industriales (Python Core)
#
# ENUNCIADO:
# 1. Desarrollar un pipeline robusto para la auditoría técnica de motores eléctricos.
# 2. Implementar Programación Orientada a Objetos (OOP) para modelar activos industriales, 
#    gestionando potencias, tiempos de ejecución (runtime) y estados operativos.
# 3. Integración de Datos (ETL): Extraer nombres de identificación desde la base de 
#    datos SQL 'Chinook', aplicando limpieza de caracteres especiales y normalización 
#    mediante métodos de string avanzados.
# 4. Lógica de Ingeniería: Diagnosticar márgenes de seguridad basados en horas de uso, 
#    automatizando la clasificación de estados en 'WARNING' (>5000h) y 'CRITICAL' (>10000h).
# 5. Persistencia y Robustez: Implementar manejo de errores (Try-Except) para accesos 
#    a DB y ficheros, generando un informe técnico profesional (.txt) con métricas 
#    de rendimiento y resumen de alertas.
# 6. Foco Técnico: OOP, Integración SQL (sqlite3), Logging Profesional, File I/O 
#    y List Comprehensions para optimización de datos.
################################################################################

import sqlite3
import time
import logging
import os
from datetime import datetime

# --- CONFIGURACIÓN DE LOGGING (Nivel Profesional) ---
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

class ElectricMotor:
    """Represents industrial assets for maintenance auditing."""
    def __init__(self, id_motor: str, model: str, power_kw: float, runtime_h: float, state: str):
        self.id_motor = id_motor
        self.model = model
        self.power_kw = power_kw
        self.runtime_h = runtime_h
        self.state = state  

    def audit_status(self):
        """Core engineering logic: safety margin evaluation."""
        if self.runtime_h > 10000:
            self.state = "CRITICAL"
        elif self.runtime_h > 5000:
            self.state = "WARNING"

# --- DATA PIPELINE FUNCTIONS ---

def get_db_path():
    """Returns the absolute path for the Chinook database."""
    # Ajuste dinámico para entorno WSL2 / Documents
    base_dir = os.path.expanduser("~/Documents/Data-Projects-Repo")
    db_path = os.path.join(base_dir, 'Chinook_Sqlite.sqlite')
    return db_path if os.path.exists(db_path) else 'Chinook_Sqlite.sqlite'

def run_final_audit():
    start_time = time.time()
    logging.info("Starting industrial audit system...")

    # 1. INITIAL DATA (Hito 27: Consolidación)
    config_data = [
        {"id": "M-01", "mod": "VFD-Alpha", "kw": 45.0, "h": 850.0, "st": "active"},
        {"id": "M-02", "mod": "Direct-Beta", "kw": 75.0, "h": 6200.0, "st": "mantenimiento"},
        {"id": "M-03", "mod": "VFD-Gamma", "kw": 110.0, "h": 12500.0, "st": "active"}
    ]

    fleet = [ElectricMotor(m["id"], m["mod"], m["kw"], m["h"], m["st"]) for m in config_data]

    # 2. CHINOOK INTEGRATION & CLEANING (Hito 21 & 23)
    clean_names = []
    try:
        with sqlite3.connect(get_db_path()) as conn:
            cursor = conn.cursor()
            # Optimizamos la query para obtener nombres de tracks para los motores
            cursor.execute("SELECT Name FROM Track ORDER BY RANDOM() LIMIT 3;")
            rows = cursor.fetchall()

            chars_to_remove = '*#$%@$€'
            table = str.maketrans('', '', chars_to_remove)

            clean_names = [
                row[0].translate(table).strip().upper() if row[0] else "GENERIC_CORE"
                for row in rows
            ]
    except sqlite3.Error as e:
        logging.error(f"Database access failed: {e}")
        clean_names = [f"EM-RESERVE-{i}" for i in range(len(fleet))]

    # 3. CONSOLIDATION (Hito 27)
    for motor, name in zip(fleet, clean_names):
        motor.model = f"{motor.model}::{name}"
        motor.audit_status()

    # 4. PERSISTENCE: PROFESSIONAL REPORT (Hito 17 & 102)
    report_file = f"audit_report_{datetime.now().strftime('%Y%m%d')}.txt"
    try:
        with open(report_file, "w", encoding="utf-8") as f:
            header = f"INDUSTRIAL ASSET AUDIT | {datetime.now().isoformat()}"
            f.write(f"{header}\n{'='*len(header)}\n\n")
            
            # Formateado de tabla profesional
            f.write(f"{'ID':<8} | {'MODEL/TRACK':<35} | {'RUNTIME':<10} | {'STATUS':<10}\n")
            f.write("-" * 75 + "\n")
            
            for m in fleet:
                f.write(f"{m.id_motor:<8} | {m.model[:35]:<35} | {m.runtime_h:>7} h | {m.state:<10}\n")
            
            # Summary with List Comprehension (Hito 107)
            warnings = [m for m in fleet if m.state in ["WARNING", "CRITICAL"]]
            f.write(f"\n{'='*len(header)}\n")
            f.write(f"TOTAL ASSETS: {len(fleet)} | ALERTS: {len(warnings)}\n")

        logging.info(f"Report successfully saved to: {report_file}")

    except IOError as e:
        logging.error(f"Failed to write report: {e}")

    # 5. PERFORMANCE METRIC (Hito 114)
    duration = time.time() - start_time
    logging.info(f"Process finished in {duration:.4f} seconds.")

if __name__ == "__main__":
    run_final_audit()