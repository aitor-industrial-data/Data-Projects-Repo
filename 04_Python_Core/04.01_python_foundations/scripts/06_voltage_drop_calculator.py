################################################################################
# 06_voltage_drop_calculator.py
# AUTOR: Aitor | Ingeniero Técnico Industrial | Data Engineer
# PROYECTO: Calculadora de Caída de Tensión Normativa (Python Core)
#
# ENUNCIADO:
# 1. Desarrollar una herramienta para el cálculo de caída de tensión monofásica.
# 2. Implementar extracción de datos mediante manipulación de strings (ETL local).
# 3. Validar materiales (Cobre/Aluminio) y secciones mediante funciones.
# 4. Diagnosticar la seguridad de la instalación basándose en el límite del 3%.
# 5. Foco Técnico: Variables, String Manipulation, Control de Flujo y Funciones.
################################################################################

import time

# --- PRESENTACIÓN VISUAL ---
print("="*60)
print("⚡ SISTEMA DE CÁLCULO ELÉCTRICO NORMATIVO (REBT)")
print("="*60)

# --- 1. FUNCIÓN DE CÁLCULO (Lógica de Ingeniería) ---
def calcular_caida(L, I, S, mat):
    """
    Calcula la caída de tensión según material y sección.
    Retorna el valor en Voltios o None si el material no es válido.
    """
    # Definición de conductividad (sigma) según REBT
    if mat in ['CU', 'COBRE']:
        sigma = 56
    elif mat in ['AL', 'ALUMINIO']:
        sigma = 35
    else:
        return None  # Salida de seguridad para materiales no contemplados
    
    # Fórmula: (2 * L * I) / (sigma * S)
    v_drop = (2 * L * I) / (sigma * S)
    return round(v_drop, 2)

# --- 2. ENTRADA DE DATOS (Interfaz de Usuario) ---
# Solicitamos datos variables por terminal
print("\n[INPUT] Parámetros de línea:")
longitud_input = input(' > Introduzca longitud de línea (m): ')
intensidad_input = input(' > Introduzca intensidad de carga (A): ')

# Simulación de string proveniente de un log o base de datos "sucia"
input_usuario = "  Material: COBRE | Seccion: 6  "

# --- 3. TRANSFORMACIÓN Y LIMPIEZA (Data Wrangling) ---
# Separamos el string por el delimitador de tubería '|'
material_raw, seccion_raw = input_usuario.strip().split('|')

# Extraemos el valor después de los dos puntos ':' y normalizamos
material = material_raw.split(':')[-1].strip().upper()
seccion_val = seccion_raw.split(':')[-1].strip()

# --- 4. VALIDACIÓN DE TIPOS (Data Quality) ---
try:
    L = float(longitud_input)
    I = float(intensidad_input)
    S = float(seccion_val)
except ValueError:
    print(f'\n[FATAL ERROR] Los valores numéricos introducidos no son válidos.')
    print("="*60)
    quit() # Finaliza el script si hay error de tipo

# --- 5. EJECUCIÓN Y LÓGICA DE DECISIÓN ---
# Tensión de referencia para el cálculo de porcentaje (Monofásica 230V)
V_REF = 230
LIMITE_3_PORCIENTO = 6.9

print("\n[PROCESANDO] Calculando caída de tensión...")
time.sleep(0.5) # Simulación de procesamiento para efecto visual

resultado = calcular_caida(L, I, S, material)

# Verificamos si el cálculo fue posible
if resultado is None:
    print(f"\n[ERROR] Material '{material}' no reconocido. Use COBRE o ALUMINIO.")
else:
    # --- REPORTE TÉCNICO FINAL ---
    print(f"\n{' INFORME DE CUMPLIMIENTO TÉCNICO ':#^60}")
    print(f" ESPECIFICACIONES: {material} {S}mm²")
    print(f" PARÁMETROS: {L}m de longitud | {I}A de intensidad")
    print("-" * 60)
    print(f" CAÍDA DE TENSIÓN CALCULADA: {resultado} V")
    print(f" LÍMITE NORMATIVO ADMISIBLE (3%): {LIMITE_3_PORCIENTO} V")
    print("-" * 60)
    
    # Diagnóstico final basado en normativa
    if resultado > LIMITE_3_PORCIENTO:
        print(f' STATUS: [ ❌ PELIGRO ]')
        print(f' DIAGNÓSTICO: SECCIÓN INSUFICIENTE. Riesgo de sobrecalentamiento.')
    else:
        print(f' STATUS: [ ✅ OK ]')
        print(f' DIAGNÓSTICO: INSTALACIÓN SEGURA. Cumple con el REBT.')
    
    print("#"*60 + "\n")