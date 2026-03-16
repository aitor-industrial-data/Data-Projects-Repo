################################################################################
# 11_config_parser_immutable.py
# AUTOR: Aitor | Ingeniero Técnico Industrial | Data Engineer
# PROYECTO: Parser de Configuración de Base de Datos (Python Core)
#
# ENUNCIADO:
# 1. Simular la recepción de credenciales de conexión mediante una TUPLA.
# 2. El sistema debe recibir una tupla con el formato: 
#    (host, port, database_name, user, password, environment)
# 3. Extraer los valores individualmente utilizando "Unpacking" (Desempaquetado).
# 4. Implementar una función que verifique si el entorno (environment) es 
#    "Production" o "Development" para aplicar reglas de seguridad.
# 5. Foco Técnico: Uso de Tuplas para integridad de datos y Desempaquetado eficiente.
################################################################################

DB_CONFIG = ("192.168.1.44", 5432, "chinook_db", "admin_aitor", "P@ssw0rd2026", "Production")

def parse_configuration(config_data: tuple):
    # --- TÉCNICA UNPACKING ---
    # Esto asigna cada elemento de la tupla a una variable por posición
    host, port, db_name, user, password, env = config_data
    
    if env == "Production":
        print('[WARNING] High Security Mode Active')
        masked_pw = '*' * len(password)
        # Retornamos una nueva tupla (inmutabilidad)
        return (host, port, db_name, user, masked_pw, env)
    
    elif env == "Development":
        print('[INFO] Debug Mode Active. Full access granted')
        return config_data # Retornamos la original tal cual

    else:
        print('[ERROR] Unknown Environment. Connection Refused')
        return None

# Ejecución y test
secure_config = parse_configuration(DB_CONFIG)
print(f"Final Data: {secure_config}")