################################################################################
# 06_voltage_drop_calculator.py
# AUTOR: Aitor | Ingeniero Técnico Industrial | Data Engineer
# PROYECTO: Calculadora de Caída de Tensión Normativa
#
# ENUNCIADO:
# 1. Desarrollar una herramienta para el cálculo de caída de tensión monofásica.
# 2. Implementar extracción de datos mediante manipulación de strings (ETL local).
# 3. Validar materiales (Cobre/Aluminio) y secciones mediante funciones.
# 4. Diagnosticar la seguridad de la instalación basándose en el límite del 3%.
# 5. Foco Técnico: Variables, String Manipulation, Control de Flujo y Funciones.
################################################################################

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
longitud_input = input('Introduzca longitud de línea (m): ')
intensidad_input = input('Introduzca intensidad de carga (A): ')

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
    print(f'[ERROR] Los valores numéricos introducidos no son válidos.')
    quit() # Finaliza el script si hay error de tipo

# --- 5. EJECUCIÓN Y LÓGICA DE DECISIÓN ---
# Tensión de referencia para el cálculo de porcentaje (Monofásica 230V)
V_REF = 230
LIMITE_3_PORCIENTO = 6.9

resultado = calcular_caida(L, I, S, material)

# Verificamos si el cálculo fue posible
if resultado is None:
    print(f"[ERROR] Material '{material}' no reconocido. Use COBRE o ALUMINIO.")
else:
    print(f"\n" + "="*40)
    print(f"ANÁLISIS TÉCNICO PARA: {material} {S}mm²")
    print(f"Caída de tensión calculada: {resultado} V")
    print("-" * 40)
    
    # Diagnóstico final basado en normativa
    if resultado > LIMITE_3_PORCIENTO:
        print(f'[PELIGRO] SECCIÓN INSUFICIENTE. Caída > {LIMITE_3_PORCIENTO}V (3%)')
    else:
        print('[OK] INSTALACIÓN SEGURA. Cumple con la caída admisible.')
    print("="*40)