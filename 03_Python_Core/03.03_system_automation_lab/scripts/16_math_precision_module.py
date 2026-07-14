################################################################################
# 16_math_precision_module.py
# AUTOR: Aitor | Ingeniero Técnico Industrial | Data Engineer
# PROYECTO: Auditoría de Precisión y Rendimiento Industrial (Python Core)
#
# ENUNCIADO:
# 1. Registrar el inicio del proceso de cálculo.
# 2. Aplicar funciones matemáticas avanzadas para validación técnica.
# 3. Simular latencia de proceso y calcular el tiempo total de ejecución.
# 4. Foco Técnico: Librerías math y datetime, formateo de tiempos y precisión.
################################################################################

from datetime import datetime
import math
import time

# 1. Captura de Timestamp inicial (Start Audit)
start_time = datetime.now()

# 2. Cálculos de Ingeniería (Simulación de carga)
target_value = 1450.75
square_root = math.sqrt(target_value)

time.sleep(0.5) # Simulación de latencia de red/proceso
tech_ceil = math.ceil(target_value)

time.sleep(0.5)
tech_floor = math.floor(target_value)

# Cálculo de área de influencia (PI * r^2)
sensor_area = math.pi * math.pow(target_value, 2)

# 3. Finalización y cálculo de Delta (Duración)
end_time = datetime.now()
execution_duration = end_time - start_time

# 4. Reporte Técnico Formateado
print("=" * 50)
print(f"📋 AUDITORÍA TÉCNICA DE SISTEMA")
# Formateamos el timestamp para que sea profesional: DD/MM/YYYY HH:MM:SS
print(f"Fecha/Hora: {start_time.strftime('%d/%m/%Y %H:%M:%S')}")
print("=" * 50)

print(f"Valor Base Analizado: {target_value}")
print(f"  ↳ Raíz Cuadrada:    {square_root:.4f}")
print(f"  ↳ Margen Superior:  {tech_ceil}")
print(f"  ↳ Límite Inferior:  {tech_floor}")
print(f"  ↳ Área Influencia:  {sensor_area:.2f} m²")

print("-" * 50)
# Mostramos solo los segundos totales para mayor claridad
print(f"⏱️  Tiempo total de proceso: {execution_duration.total_seconds():.4f} segundos")
print("=" * 50)
