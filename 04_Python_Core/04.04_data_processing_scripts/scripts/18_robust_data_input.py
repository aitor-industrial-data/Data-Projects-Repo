################################################################################
# 18_robust_data_input.py
# AUTOR: Aitor | Ingeniero Técnico Industrial | Data Engineer
# PROYECTO: Interfaz de Entrada de Datos para Activos Industriales (Python Core)
#
# ENUNCIADO:
# 1. Crear un sistema de entrada de datos por consola para activos de planta.
# 2. Implementar una función de validación universal con manejo de excepciones.
# 3. Asegurar la integridad de datos técnicos (Potencia, Eficiencia y Horas).
# 4. Evitar el colapso del script ante entradas no numéricas (ValueError).
# 5. Foco Técnico: Try/Except, Bucles de Control, Robustez y Data Quality.
################################################################################

def get_validated_float(prompt, min_val=0.0, max_val=float('inf')):
    """
    Pide un dato por consola, lo valida y lo devuelve convertido a float.
    Mantiene al usuario en un bucle hasta que el dato sea correcto.
    """
    while True:
        user_input = input(prompt)
        try:
            value = float(user_input)
            if value < min_val or value > max_val:
                print(f"[ERROR] Value {value} out of range ({min_val} to {max_val}).")
                continue
            return value  # Si todo está bien, sale de la función con el número
        except ValueError:
            print(f"[ERROR] Invalid input '{user_input}'. Please enter a numeric value.")

# --- Programa Principal ---

# Para el ID, solo validamos que no esté vacío
motor_id = ""
while not motor_id:
    motor_id = input("ENTER MOTOR ID: ").strip()
    if not motor_id:
        print("[ERROR] Motor ID cannot be empty.")

# Usamos la función para el resto de datos técnicos
power_kw = get_validated_float("ENTER POWER (kW): ", min_val=0.1)
efficiency = get_validated_float("ENTER EFFICIENCY (0.01 to 1.0): ", min_val=0.01, max_val=1.0)
runtime_h = get_validated_float("ENTER RUNTIME (h): ", min_val=0.0)

# Construcción del diccionario final
motor = {
    "asset_id": motor_id,
    "power_kw": power_kw,
    "efficiency": efficiency,
    "runtime_h": runtime_h
}

print("\n" + "="*30)
print("REGISTERED MOTOR DATA:")
print("="*30)
for key, val in motor.items():
    print(f"{key.upper():<15}: {val}")
print("="*30)
