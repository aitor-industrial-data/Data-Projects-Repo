################################################################################
# 04_xml_data_aggregator.py
# AUTOR: Aitor | Ingeniero Técnico Industrial | Data Engineer
# PROYECTO: Extracción y Procesamiento de Estructuras XML (Python para Ingeniería)
#
# ENUNCIADO:
# 1. El script debe solicitar una URL al usuario para recuperar un archivo XML.
# 2. El objetivo es analizar el XML, localizar todos los nodos de conteo y 
#    calcular la suma total de los comentarios.
# 3. El programa debe realizar los siguientes pasos técnicos:
#    - Utilizar 'urllib' para la transferencia de datos sobre HTTP.
#    - Emplear 'xml.etree.ElementTree' para parsear la cadena de bytes (UTF-8).
#    - Aplicar un selector XPath ('.//count') para encontrar todos los nodos 
#      relevantes sin importar su profundidad en el árbol.
#    - Iterar, convertir a entero y acumular los valores encontrados.
# 4. Mostrar métricas de control: caracteres recuperados, cantidad de elementos 
#    procesados y la suma final.
# 5. FOCO TÉCNICO: Procesamiento de datos semi-estructurados (XML), XPath, 
#    y manejo de objetos ElementTree.
################################################################################

import urllib.request
import xml.etree.ElementTree as ET
import ssl

# Configuración para ignorar errores de certificado SSL (buena práctica en labs)
ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE

# 1. Entrada de datos
url = input('Enter location: ')
if len(url) < 1: 
    # URL por defecto para pruebas rápidas
    url = 'http://py4e-data.dr-chuck.net/comments_2383800.xml'

print(f'Retrieving {url}')

# 2. Extracción (Extract)
try:
    uh = urllib.request.urlopen(url, context=ctx)
    data = uh.read()
    info=json.load(data)
    print(f'Retrieved {len(data)} characters')

    # 3. Análisis y Transformación (Transform)
    # Convertimos la cadena XML en un árbol de elementos (ElementTree)
    tree = ET.fromstring(data)

    # Buscamos todas las etiquetas <count> usando XPath
    counts = tree.findall('.//count')
    
    lista_numeros = []

    for item in counts:
        # Extraemos el texto dentro de la etiqueta, convertimos a entero
        # y lo añadimos a nuestra lista de procesamiento
        numero = int(item.text)
        lista_numeros.append(numero)

    # 4. Salida de resultados (Load / Report)
    print(f'Count: {len(lista_numeros)}')
    print(f'Sum: {sum(lista_numeros)}')

except Exception as e:
    print(f"Error al procesar los datos: {e}")