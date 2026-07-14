################################################################################
# 08_monitoring_stream_sim.py
# AUTOR: Aitor | Ingeniero Técnico Industrial | Data Engineer
# PROYECTO: Sistema de Vigilancia de Presión Crítica (Python Core)
#
# ENUNCIADO:
# 1. Simular la lectura continua de un sensor de presión industrial.
# 2. El bucle debe detenerse inmediatamente cuando se supere el umbral.
# 3. Foco Técnico: Bucle While y simulación de flujos de datos (Streaming).
################################################################################

import random
import time

# Configuración de umbrales técnicos
pressure_limit = 7.5
current_pressure = 0.0

# Simulación de monitoreo en tiempo real
while True:
    time.sleep(0.7)  # Delay para simular la frecuencia de muestreo del sensor
    current_pressure = round(random.uniform(5, 9), 2)
    if current_pressure > pressure_limit:
        break
    print(f'[OK] Pressure: {current_pressure} bar')

# Protocolo de parada de emergencia (Fuera del bucle)
print('-' * 45)
print(f'[EMERGENCY STOP] Pressure: {current_pressure} bar - {time.strftime("%H:%M:%S")}')