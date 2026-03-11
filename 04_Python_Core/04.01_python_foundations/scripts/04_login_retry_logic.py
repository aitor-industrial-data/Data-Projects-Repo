################################################################################
# 04_login_retry_logic.py
# AUTOR: Aitor | Ingeniero Técnico Industrial | Data Engineer
# PROYECTO: Sistema de Seguridad de Acceso (Python Core)
#
# ENUNCIADO:
# 1. Simular un sistema de acceso que permite validar credenciales.
# 2. El sistema debe evaluar si el usuario y la contraseña son correctos.
# 3. Foco Técnico: Lógica de Decisión (if/elif/else) y String Manipulation.
################################################################################

# 1. Credenciales maestras
true_user = 'aitor_admin'
true_password = 'password2026'

# 2. Captura de datos con normalización inmediata
# .strip() elimina espacios y .lower() asegura que el usuario no sea sensible a mayúsculas
user_input = input("Escribe tu nombre: ").strip().lower()
password_input = input("Escribe tu password: ").strip()

# 3. Lógica de Decisión (Foco Técnico: if/elif/else) 
if user_input == true_user and password_input == true_password:
    print('¡ÉXITO! Conexión establecida con la base de datos')
elif user_input == true_user and password_input != true_password:
    print('Error: Contraseña incorrecta.')
elif user_input != true_user and password_input == true_password:
    print('Error: Usuario no reconocido.')
else:
    print('Error: Credenciales completamente inválidas.')

# 4. Validación de tipos para seguimiento del Mes 4 
print(f"\n[DEBUG] Tipo de variable user_input: {type(user_input)}")
