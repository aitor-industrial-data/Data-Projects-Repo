################################################################################
# 05_extractor_datos_json.py
# AUTOR: Aitor | Ingeniero Técnico Industrial | Data Engineer
# PROYECTO: Extracción y Procesamiento de Estructuras JSON (Python para Ingeniería)
#
# ENUNCIADO:
# 1. El script debe solicitar una URL al usuario para recuperar un archivo JSON.
# 2. El objetivo es analizar el JSON, localizar los campos "count" dentro de la 
#    lista "comments" y calcular la suma total.
# 3. El programa debe realizar los siguientes pasos técnicos:
#    - Utilizar 'urllib' para la transferencia de datos sobre HTTP.
#    - Emplear la librería 'json' para parsear la cadena de texto a un diccionario.
#    - Iterar sobre la lista de elementos para extraer y acumular los valores.
# 4. Mostrar métricas de control: caracteres recuperados, cantidad de elementos 
#    procesados y la suma final.
# 5. FOCO TÉCNICO: Procesamiento de datos semi-estructurados (JSON), manejo de 
#    diccionarios y listas, y peticiones HTTP.
################################################################################

import urllib.request, urllib.parse, urllib.error
import json
import ssl

# Configuración de SSL para ignorar errores de certificado en entornos de laboratorio
ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE

# 1. Entrada de datos
url = input('Introduzca la ubicación: ')
if len(url) < 1:
    # URL por defecto (Datos reales del ejercicio)
    url = 'http://py4e-data.dr-chuck.net/comments_2383801.json'

print(f'Recuperando {url}')

try:
    # 2. Extracción (Extract)
    enlace = urllib.request.urlopen(url, context=ctx)
    datos_brutos = enlace.read().decode()
    print(f'Se recuperaron {len(datos_brutos)} caracteres')

    # 3. Análisis y Transformación (Transform)
    # Convertimos la cadena JSON en un objeto de Python (diccionario)
    info = json.loads(datos_brutos)
    
    # La estructura JSON contiene una clave principal "comments" que es una lista
    lista_comentarios = info.get('comments', [])
    
    valores_conteo = []
    for item in lista_comentarios:
        # Extraemos el valor de la clave 'count' y lo convertimos a entero
        numero = int(item['count'])
        valores_conteo.append(numero)

    # 4. Salida de resultados (Reporte)
    print(f'Cantidad: {len(valores_conteo)}')
    print(f'Suma: {sum(valores_conteo)}')

except Exception as e:
    print(f"Error al procesar los datos: {e}")

    