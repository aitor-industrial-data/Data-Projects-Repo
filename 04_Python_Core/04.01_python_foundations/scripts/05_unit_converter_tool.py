################################################################################
# 05_unit_converter_tool.py
# AUTOR: Aitor | Ingeniero Técnico Industrial | Data Engineer
# PROYECTO: Terminal de Diagnóstico y Conversión (Mes 4 - Funciones I)
#
# ENUNCIADO:
# 1. Crear funciones reutilizables para validación, conversión y diagnóstico.
# 2. Implementar un sistema de login de 3 intentos usando lógica anidada.
# 3. Realizar conversiones de potencia (kW a HP) y evaluar rangos de presión.
# 4. Foco Técnico: Encapsulamiento en funciones.
################################################################################

# Credenciales de acceso (Administración de Planta)
true_user = 'aitor'
true_password = 'data2026'

# --- 1. DEFINICIÓN DE FUNCIONES TÉCNICAS ---

def logging(user, password):
    """Valida el acceso al sistema de control."""
    return user == true_user and password == true_password

def pot_calculator(kw):
    """Conversión de potencia de entrada a unidad imperial (HP)."""
    # Eliminado try/except: convertimos directamente
    kw_val = float(kw)
    hp = round(kw_val / 0.7457, 2)
    return hp

def press_oil(bar):
    """
    Diagnóstico de presión de aceite (Rangos reales Motor Industrial):
    - < 1.5 bar: Presión insuficiente (Peligro de gripado).
    - 1.5 a 5.0 bar: Rango Nominal de operación.
    - > 5.0 bar: Sobrepresión (Posible obstrucción o válvula defectuosa).
    """
    # Eliminado try/except: convertimos directamente
    bar_val = float(bar)
    if bar_val > 5.0:
        return 'ALERTA: SOBREPRESIÓN DETECTADA'
    elif bar_val >= 1.5:
        return 'OPERACIÓN NOMINAL (ESTABLE)'
    else:
        return 'CRÍTICO: PRESIÓN INSUFICIENTE (STOP)'

# --- 2. PROTOCOLO DE ACCESO (Security Layer) ---

print(">>> INICIALIZANDO SISTEMA DE CONTROL INDUSTRIAL v4.0 <<<")
user = input('ID Usuario: ').lower().strip()
password = input('Token Acceso: ')

if not logging(user, password):
    print('\n[AUTH ERROR] Credenciales no válidas. Intentos restantes: 2')
    user = input('ID Usuario: ').lower().strip()
    password = input('Token Acceso: ')
    
    if not logging(user, password):
        print('\n[AUTH ERROR] Credenciales no válidas. Intentos restantes: 1')
        user = input('ID Usuario: ').lower().strip()
        password = input('Token Acceso: ')
        
        if not logging(user, password):
            print('\n[SECURITY ALERT] Acceso denegado. Terminal bloqueada.')
            quit()

# --- 3. EJECUCIÓN DE DIAGNÓSTICO ---

print(f'\n--- SESIÓN INICIADA: {true_user.upper()} ---')

# Cálculo de Potencia
raw_kw = input('Entrada Potencia Motor (kW): ').strip()

# IMPORTANTE: Al quitar el try/except, si no introducen un número, 
# el programa fallará en la línea del float() dentro de la función.
hp_result = pot_calculator(raw_kw)

if hp_result is not None:
    print(f'[CONVERSIÓN] Potencia calculada: {hp_result} HP')
else:
    print('[ERROR] El formato de kW introducido es incorrecto.')

# Diagnóstico de Presión
raw_bar = input('Entrada Presión Aceite (Bar): ').strip()
status_msg = press_oil(raw_bar)

print(f'[DIAGNÓSTICO] Estado del lubricante: {status_msg}')

print("\n>>> PROCESO FINALIZADO SIN ERRORES CRÍTICOS <<<")