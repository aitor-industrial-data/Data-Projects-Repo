################################################################################
# 13_config_dict_manager.py
# AUTOR: Aitor | Ingeniero Técnico Industrial | Data Engineer
# PROYECTO: Gestión Dinámica de Configuraciones ETL (Python Core)
#
# ENUNCIADO:
# 1. Simular la carga y gestión de parámetros de un pipeline de datos.
# 2. Implementar estructuras anidadas (Nesting) para organizar metadatos y conexiones.
# 3. Aplicar acceso seguro a claves mediante métodos nativos para evitar crashes.
# 4. Actualizar parámetros en bloque (Bulk Update) y validar integridad de datos.
# 5. Foco Técnico: Diccionarios Avanzados, Métodos .get() / .update() e Iteración.
################################################################################

# 1. Diccionario Anidado (Estructura tipo JSON/NoSQL)
etl_config = {
    'database': {
        'name': "chinook_v2",
        'schema': 'public',
        'port': 5432
    },
    'performance': {
        'batch_size': 500,
        'retry_attempts': 3,
        'is_active': True
    },
    'metadata': {
        'last_updated': "2026-03-01",
        'env': 'production'
    }
}

print("--- Data Pipeline Configuration Manager ---")

# 2. Acceso Seguro con .get() y Valores por Defecto
current_db = etl_config.get('database').get('name', 'default_db')
print(f'Base de datos actual: {current_db}')

# 3. Entrada de Usuario y Validación
new_val = input('Enter new batch_size (integer): ')

try:
    new_batch_size = int(new_val)
    
    if new_batch_size <= 0:
        print('\n---> Error: Batch size must be positive.')
    else:
        # 4. Actualización en Bloque (Bulk Update)
        if new_batch_size > 1000:
            print('\n---> Warning: High memory usage mode activated.')
        
        etl_config['performance'].update({
            'batch_size': new_batch_size,
            'is_active': True
        })
        
        # 5. Modificación Dinámica de Metadatos
        etl_config['metadata']['last_updated'] = '2026-03-16'

except ValueError:
    print(f'---> Error: "{new_val}" is not a valid number.')

# 6. Visualización Profesional mediante Desempaquetado (Items)
print('\n[REPORTE FINAL DE CONFIGURACIÓN]')
for section, details in etl_config.items():
    print(f'\n📁 Categoría: {section.upper()}')
    if isinstance(details, dict):
        for key, value in details.items():
            print(f'   ↳ {key}: {value}')