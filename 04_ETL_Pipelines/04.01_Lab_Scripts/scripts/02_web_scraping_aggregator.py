################################################################################
# 02_web_scraping_aggregator.py
# AUTOR: Aitor | Ingeniero Técnico Industrial | Data Engineer
# PROYECTO: Extracción y Agregación de Datos Web (Python para Ingeniería)
#
# ENUNCIADO:
# 1. El script debe realizar una solicitud HTTP a una URL específica utilizando 
#    la librería 'urllib' para recuperar contenido HTML.
# 2. El objetivo es analizar el documento HTML para extraer datos numéricos 
#    embebidos en etiquetas específicas.
# 3. El programa debe realizar los siguientes pasos técnicos:
#    - Configurar un contexto SSL para omitir la validación de certificados, 
#      permitiendo el acceso a sitios con configuraciones de seguridad diversas.
#    - Utilizar 'BeautifulSoup' con el parser 'html.parser' para transformar 
#      el HTML crudo en un objeto navegable.
#    - Identificar y recuperar todas las etiquetas de tipo 'span'.
#    - Iterar sobre la colección de etiquetas, extraer su contenido textual, 
#      convertirlo a tipo entero (casting) y realizar una suma acumulativa.
# 4. Al finalizar, el script debe mostrar por consola el resultado total de 
#    la agregación de los comentarios encontrados.
# 5. FOCO TÉCNICO: Web Scraping, análisis de DOM (Document Object Model), 
#    manejo de librerías de terceros (BS4) y procesamiento de tipos de datos.
################################################################################

from urllib.request import urlopen
from bs4 import BeautifulSoup
import ssl

# 1. Configuración de seguridad: Ignorar errores de certificado SSL
# Útil para entornos de desarrollo y extracción de datos rápida
ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE

# 2. Definición de origen y adquisición de datos (Extract)
url = 'http://py4e-data.dr-chuck.net/comments_2383798.html'
html = urlopen(url, context=ctx).read()

# 3. Análisis del HTML (Parse)
# Convertimos el HTML en un objeto 'Soup' para buscar elementos fácilmente
soup = BeautifulSoup(html, "html.parser")

# 4. Extracción y procesamiento (Transform)
# Recuperamos todas las etiquetas <span> de la página
tags = soup('span')
suma_comentarios = 0

for tag in tags:
    # Extraemos el contenido, lo convertimos a entero y acumulamos
    # tag.contents[0] accede al texto dentro de la etiqueta <span>
    comentarios = int(tag.contents[0])
    suma_comentarios += comentarios

# 5. Salida de resultados (Load / Report)
print(f'La suma total de comentarios es: {suma_comentarios}')