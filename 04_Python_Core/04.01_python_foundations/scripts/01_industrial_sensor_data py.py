################################################################################
# 01_industrial_sensor_data.py
# AUTOR: Aitor | Ingeniero Técnico Industrial | Data Engineer
# PROYECTO: Automatización de Telemetría (Python Core)
#
# ENUNCIADO:
# 1. Definir variables para telemetría industrial (Temperatura, Presión, Estado).
# 2. Realizar el "parsing" de un string crudo (raw_data) mediante split.
# 3. Realizar conversión de tipos (Casting):
#    - ID a Integer.
#    - Temperatura a Float.
#    - Presión a Integer.
#    - Estado a Booleano mediante comparación lógica.
# 4. Calcular una variable derivada (Conversión de mbar a bar).
# 5. Mostrar por consola los datos y validar sus tipos con la función type().
################################################################################

# 1. Dato crudo del sensor (Simulación de entrada industrial)
raw_data = "SENSOR_ID:042|TEMP:78.6|PRES:3050|ACTIVE:True"

# 2. Extracción de datos (Parsing)
parts = raw_data.split('|')

# Extraemos los valores de cada parte tras los ':'
val_id = parts[0].split(':')[1]
val_temp = parts[1].split(':')[1]
val_pres = parts[2].split(':')[1]
val_active = parts[3].split(':')[1]

# 3. Conversión de Tipos (Casting)
sensor_id = int(val_id)          
temperatura = float(val_temp)    
presion = int(val_pres)          
# Conversión segura a booleano
esta_activa = val_active == "True"

# 4. Operación con variables (Cálculo de ingeniería)
presion_bar = presion / 1000.0

# 5. Salida de datos y validación de tipos
print("=== REPORTE TÉCNICO DE SENSORES ===")
print(f"ID del Sensor: {sensor_id} | Tipo: {type(sensor_id)}")
print(f"Temperatura: {temperatura}°C | Tipo: {type(temperatura)}")
print(f"Presión: {presion_bar} bar | Tipo: {type(presion_bar)}")
print(f"Estado Activo: {esta_activa} | Tipo: {type(esta_activa)}")

print("-" * 35)
print(f"RESUMEN: El sensor {sensor_id} registra {temperatura}°C y {presion_bar} bar.")
