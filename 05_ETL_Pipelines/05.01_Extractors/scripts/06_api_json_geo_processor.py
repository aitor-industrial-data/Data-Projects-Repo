################################################################################
# 06_api_json_geo_processor.py
# AUTOR: Aitor | Ingeniero Técnico Industrial | Data Engineer
# PROYECTO: Interacción con APIs REST y Procesamiento de Plus Codes (Python)
#
# ENUNCIADO:
# 1. El script solicita una ubicación (address) al usuario.
# 2. Realiza una petición GET a una API de Open Street Map (subset estático).
# 3. Codifica los parámetros de la URL de forma segura usando 'urllib.parse'.
# 4. Extrae el primer 'plus_code' encontrado en la estructura GeoJSON devuelta.
# 5. Pasos técnicos:
#    - Gestión de parámetros de consulta (query parameters).
#    - Manejo de respuestas JSON complejas (anidamiento de 'features' y 'properties').
#    - Extracción de identificadores de ubicación textual (Plus Codes).
# 6. FOCO TÉCNICO: Integración de sistemas, limpieza de strings y navegación de
#    estructuras JSON anidadas de nivel profesional.
################################################################################

import urllib.request, urllib.parse, urllib.error
import json
import ssl

# Configuración de SSL para entornos de desarrollo
ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE

# Endpoint de la API proporcionado por el curso
url_servicio = 'http://py4e-data.dr-chuck.net/opengeo?'

# 1. Entrada de datos
direccion = input('Introduzca la ubicación: ')
if len(direccion) < 1:
    # Ubicación objetivo del ejercicio
    direccion = 'Georgia State University'

# 2. Preparación de la URL (URL Encoding)
parametros = dict()
parametros['q'] = direccion
url = url_servicio + urllib.parse.urlencode(parametros)

print(f'Recuperando {url}')

try:
    # 3. Extracción (Extract)
    uh = urllib.request.urlopen(url, context=ctx)
    datos = uh.read().decode()
    print(f'Se recuperaron {len(datos)} caracteres')

    # 4. Análisis (Transform)
    js = json.loads(datos)
    
    # Validación de la estructura de datos recibida
    if not js or 'features' not in js or len(js['features']) == 0:
        print('==== Error: No se encontraron resultados o fallo en la descarga ====')
    else:
        # Navegamos por la estructura: features[0] -> properties -> plus_code
        # El Plus Code es una forma moderna de dirección basada en coordenadas
        # Si no encuentra 'plus_code', devuelve None en lugar de romper el programa
        plus_code = js['features'][0]['properties'].get('plus_code', 'No disponible')
        
        # 5. Salida de resultados (Reporte)
        print(f'Plus code: {plus_code}')

except Exception as e:
    print(f"Error en la conexión o en el procesado: {e}")