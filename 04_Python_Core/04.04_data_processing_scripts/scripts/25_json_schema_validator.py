################################################################################
# 25_json_schema_validator.py
# AUTOR: Aitor | Ingeniero Técnico Industrial | Data Engineer
# PROYECTO: Validador de Esquemas de Configuración Técnica (Python Core)
#
# ENUNCIADO:
# 1. Desarrollar un motor de validación para archivos de configuración JSON.
# 2. Definir un "Esquema Maestro" que contenga las claves obligatorias.
# 3. Implementar una lógica de detección de "Missing Keys".
# 4. Validar la integridad de los valores y tipos de datos (int, str, float).
# 5. Foco Técnico: Diccionarios, Manejo de JSON y Validación de Estructuras.
################################################################################

import os

# --- INTERFAZ DE SISTEMA ---
print("\n"+"="*60)
print("🚀 DATA PIPELINE: INICIALIZANDO DIAGNÓSTICO DE CONFIGURACIÓN")
print("="*60)

# Datos de entrada (Simulación de JSON)
received_config = {
    "project_name": "Data-Pipeline-Alpha",
    "version": 1.0,
    "database": {
        "host": "localhost",
        "user": "admin",
        # Falta la clave 'password'
        "port": "5432"  # Es un string, pero debería ser un entero
    },
    "retry_attempts": "3" # Es un string, debería ser un entero
}

# Esquema de referencia
required_keys = ["project_name", "version", "database", "retry_attempts"]
db_required_keys = ["host", "user", "password", "port"]

errors = []

# 1. Validar Claves Principales
for req_key in required_keys:
    if req_key not in received_config:
        errors.append(f"❌ E01 | Nodo Principal ausente: '{req_key}'")

# 2. Validar Claves de Database (Solo si el nodo existe)
if "database" in received_config:
    for db_key in db_required_keys:
        if db_key not in received_config["database"]:
            errors.append(f"❌ E02 | Clave '{db_key}' faltante en nodo 'database'")

# 3. Validar Tipos de Datos (Requisito 4 del enunciado)
# Validamos el puerto
port = received_config.get("database", {}).get("port")
if port and not isinstance(port, int):
    errors.append(f"⚠️  T01 | Error de Tipo: 'port' (Esperado: INT | Recibido: {type(port).__name__.upper()})")

# Validamos los reintentos
retries = received_config.get("retry_attempts")
if retries and not isinstance(retries, int):
    errors.append(f"⚠️  T02 | Error de Tipo: 'retry_attempts' (Esperado: INT | Recibido: {type(retries).__name__.upper()})")

# --- GENERACIÓN DE REPORTE FINAL ---
if errors:
    print(f"\n{' STATUS: CRITICAL FAILURE ':#^60}")
    print(f"Se han detectado {len(errors)} anomalía(s) en el archivo de configuración:\n")
    for error in errors:
        print(f" > {error}")
    print("\n" + "="*60)
    print("ACCIÓN REQUERIDA: Corregir el archivo JSON antes de reintentar.")
    print("="*60)
else:
    print(f"\n{' STATUS: OPERATIONAL ':#^60}")
    print("✅ Configuración validada con éxito.")
    print("✅ Esquema de base de datos íntegro.")
    print("✅ Tipos de datos verificados.")
    print("\nPROCESO: Iniciando inyección de datos en 3, 2, 1...")
    print("="*60)