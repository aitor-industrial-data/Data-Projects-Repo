################################################################################
# 04_login_retry_logic.py
# AUTOR: Aitor | Ingeniero Técnico Industrial | Data Engineer
# PROYECTO: Sistema de Seguridad de Acceso con Reintentos (Python Core)
#
# ENUNCIADO:
# 1. Simular un sistema de acceso que permite máximo 3 intentos fallidos.
# 2. Foco Técnico: Bucles (Loops) y Lógica de Decisión (if/elif/else).
################################################################################

# 1. Credenciales maestras
true_user = 'aitor_admin'
true_password = 'password2026'

# 2. Configuración de reintentos
attempts = 0
max_attempts = 3
access_granted = False

print(f"--- SISTEMA DE SEGURIDAD (Máximo {max_attempts} intentos) ---\n")

# 3. Bucle de control (Foco Técnico: Loops)
while attempts < max_attempts:
    # Captura de datos con normalización
    user_input = input(f"[{attempts + 1}/{max_attempts}] Usuario: ").strip().lower()
    password_input = input(f"[{attempts + 1}/{max_attempts}] Password: ").strip()

    # Lógica de Decisión
    if user_input == true_user and password_input == true_password:
        print('\n¡ÉXITO! Conexión establecida con la base de datos.')
        access_granted = True
        break  # Salimos del bucle inmediatamente al acertar
    else:
        attempts += 1
        remaining = max_attempts - attempts
        if remaining > 0:
            print(f"Credenciales incorrectas. Te quedan {remaining} intentos.\n")
        else:
            print("\nError: Has agotado todos los intentos.")

# 4. Bloqueo final si no se logró el acceso
if not access_granted:
    print("SISTEMA BLOQUEADO. Contacte con el administrador de sistemas.")
