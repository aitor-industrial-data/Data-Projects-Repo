################################################################################
# 07_selenium_dynamic_extractor.py
# AUTOR: Aitor | Ingeniero Técnico Industrial | Data Engineer
# PROYECTO: Extracción de Contenido Dinámico con Selenium (Python para Ingeniería)
#
# ENUNCIADO:
# 1. El script debe automatizar un navegador real para acceder a sitios web que
#    renderizan su contenido mediante JavaScript (SPAs).
# 2. El objetivo es capturar datos que no están presentes en el HTML inicial y
#    requieren tiempo de carga o interacción.
# 3. El programa debe realizar los siguientes pasos técnicos:
#    - Configurar 'Selenium' en modo 'headless' (sin ventana) para entornos Linux/WSL.
#    - Implementar 'WebDriverWait' y 'Expected Conditions' para manejar la 
#      asincronía de la red de forma profesional.
#    - Localizar elementos del DOM mediante selectores CSS o XPath.
#    - Extraer el texto de los elementos y cerrar el proceso del navegador.
# 4. Mostrar por consola los elementos recuperados y confirmar el cierre del driver.
# 5. FOCO TÉCNICO: Automatización de navegadores, manejo de esperas explícitas,
#    renderizado de JavaScript y gestión de recursos del sistema.
################################################################################

from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time

# 1. Configuración del Navegador (Chrome/Chromium)
chrome_options = Options()
chrome_options.add_argument("--headless")  # Necesario para WSL2 (sin interfaz gráfica)
chrome_options.add_argument("--no-sandbox")
chrome_options.add_argument("--disable-dev-shm-usage")

# 2. Definición de origen (Extract)
url = 'http://py4e-data.dr-chuck.net/comments_42.html' # Ejemplo de prueba o cualquier SPA

# Inicializamos el Driver
service = Service('/snap/bin/chromium.chromedriver')
driver = webdriver.Chrome(service=service, options=chrome_options)

print(f"Iniciando navegador para extraer de: {url}")

try:
    # 3. Navegación y Espera (Transform / Wait)
    driver.get(url)
    
    # Espera explícita: Esperamos hasta 10 segundos a que aparezcan los spans de comentarios
    # Esto es mucho más profesional que usar time.sleep()
    wait = WebDriverWait(driver, 10)
    elementos = wait.until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, "span.comments")))

    # 4. Procesamiento de datos
    conteo_total = 0
    print(f"Se han encontrado {len(elementos)} elementos dinámicos.")

    for el in elementos:
        # Extraemos el texto del elemento renderizado por JS
        valor = int(el.text)
        conteo_total += valor

    # 5. Salida de resultados (Reporte)
    print(f"Suma total de datos dinámicos: {conteo_total}")

except Exception as e:
    print(f"Error durante la automatización: {e}")

finally:
    # Cerramos el navegador y el proceso para liberar RAM (Crítico en ingeniería)
    driver.quit()
    print("Navegador cerrado y recursos liberados.")