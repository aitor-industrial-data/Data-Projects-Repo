################################################################################
# 03_recursive_web_crawler.py
# AUTOR: Aitor | Ingeniero Técnico Industrial | Data Engineer
# PROYECTO: Navegación Recursiva y Extracción de Enlaces (Python para Ingeniería)
#
# ENUNCIADO:
# 1. El script debe realizar una navegación automatizada a través de múltiples 
#    páginas web siguiendo una secuencia específica de hipervínculos.
# 2. El objetivo es identificar el enlace en la posición 18 (índice 17) de la 
#    página actual y utilizarlo como origen para la siguiente iteración.
# 3. El programa debe realizar los siguientes pasos técnicos:
#    - Implementar un bucle de control que ejecute el proceso 7 veces.
#    - En cada iteración, solicitar el HTML de la URL actual omitiendo la 
#      verificación de certificados SSL/TLS para evitar bloqueos de red.
#    - Analizar el DOM con 'BeautifulSoup' para localizar todas las etiquetas '<a>'.
#    - Extraer el atributo 'href' del elemento en la posición 18 y actualizar 
#      la variable de control de flujo.
# 4. Al finalizar las 7 iteraciones, el script debe imprimir la URL final 
#    alcanzada, que contiene el nombre objetivo del ejercicio.
# 5. FOCO TÉCNICO: Crawling recursivo, manejo de listas de objetos (DOM), 
#    control de flujo con 'while' y gestión de estados de navegación.
################################################################################

import urllib.request, urllib.parse, urllib.error
from bs4 import BeautifulSoup
import ssl

# 1. Configuración de seguridad: Ignorar errores de certificado SSL/TLS
# Necesario para acceder a servidores de prácticas con protocolos antiguos
ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE

# 2. Parámetros de configuración del Crawler
url = 'http://py4e-data.dr-chuck.net/known_by_Ogheneruno.html'
iteraciones_objetivo = 7
posicion_enlace = 17 # Índice 17 corresponde al enlace número 18
contador = 1

print(f"Iniciando navegación desde: {url}")

# 3. Bucle de navegación recursiva (Recursive Scraping)
while contador <= iteraciones_objetivo:
    # Extracción (Extract)
    html = urllib.request.urlopen(url, context=ctx).read()
    soup = BeautifulSoup(html, 'html.parser')
    
    # Análisis (Transform)
    tags = soup('a')
    
    # Validación: Asegurarse de que el enlace existe para evitar IndexError
    if len(tags) > posicion_enlace:
        url = tags[posicion_enlace].get('href', None)
        print(f"Paso {contador}: Navegando a {url}")
    else:
        print("Error: No se encontró el enlace en la posición especificada.")
        break
        
    contador += 1

# 4. Resultado final (Load / Report)
print("-" * 50)
print(f"PROCESO COMPLETADO.")
print(f"La URL final después de {iteraciones_objetivo} saltos es: {url}")