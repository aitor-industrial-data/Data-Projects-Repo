################################################################################
# 03_safety_margin_check.py
# AUTOR: Aitor | Ingeniero Técnico Industrial | Data Engineer
# PROYECTO: Sistema de Monitoreo de Presión (Python Core)
#
# ENUNCIADO:
# 1. Recibir una lectura cruda de presión en formato string.
# 2. Limpiar el string y convertirlo a tipo numérico (int).
# 3. Evaluar el rango de seguridad usando estructuras if/elif/else.
# 4. Generar un mensaje de estado profesional y calcular el margen de seguridad.
################################################################################

# 1. Simulación de entrada de datos (Datos del sensor con ruido/espacios)
raw_pressure_data = "  PRESSURE_READING: 2750 MBAR  "

# 2. Limpieza y Procesamiento (Visto en ejercicios anteriores)
# Pasamos a mayúsculas para asegurar el split y quitamos espacios laterales
clean_data = raw_pressure_data.strip().upper()

# Extraemos el valor numérico (entre los dos puntos y el espacio de MBAR)
# "PRESSURE_READING: 2750 MBAR" -> split(':') -> ["PRESSURE_READING", " 2750 MBAR"]
value_str = clean_data.split(':')[1].replace("MBAR", "").strip()

# Conversión de tipo (Casting)
pressure_mbar = int(value_str)

# 3. Lógica de Control de Flujo (if / elif / else)
status = ""
alert_level = 0  # 0: Low, 1: Medium, 2: High

if pressure_mbar <= 2000:
    status = "SAFE"
    alert_level = 0
elif 2000 < pressure_mbar <= 3000:
    status = "WARNING"
    alert_level = 1
else:
    status = "CRITICAL"
    alert_level = 2

# 4. Cálculo adicional (Operadores matemáticos)
# Calculamos cuánto falta o cuánto sobra respecto al límite crítico (3000)
safety_margin = 3000 - pressure_mbar

# 5. Salida de datos formateada
print("=" * 50)
print("SISTEMA DE CONTROL DE PRESIÓN - PLANTA INDUSTRIAL")
print("=" * 50)
print(f"[*] Lectura procesada: {pressure_mbar} mbar")
print(f"[*] Estado del sistema: {status}")

if alert_level == 1:
    print(f"[!] AVISO: Quedan {safety_margin} mbar para el nivel CRÍTICO.")
elif alert_level == 2:
    print(f"[!!!] PELIGRO: Presión excedida en {abs(safety_margin)} mbar!")
else:
    print("[+] Sistema operando dentro de los parámetros normales.")

print("-" * 50)
print(f"INFO TÉCNICA: Variable 'pressure_mbar' es {type(pressure_mbar)}")