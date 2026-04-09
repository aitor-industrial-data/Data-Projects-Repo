# 🚀 05.01 Extractors: Ingesta de Datos Multifuente

Este directorio contiene la fase **Extract** de mis pipelines de ingeniería de datos. Aquí se demuestra la transición desde los fundamentos de protocolos de red hasta la creación de extractores industriales automatizados.

## 📌 Resumen del Módulo
En esta sección, he desarrollado una serie de scripts que cubren el espectro completo de la recuperación de información digital:
* **Protocolos de Bajo Nivel:** Manejo directo de Sockets TCP/IP.
* **Web Scraping & Crawling:** Navegación por el DOM y árboles XML/HTML.
* **Consumo de APIs REST:** Procesamiento de estructuras JSON y GeoJSON.
* **Extracción Dinámica:** Automatización con Selenium para SPAs (Single Page Applications).

---

## 🏆 Proyecto Destacado (HITO)

### [08_milestone_esios_price_extractor.py](./scripts/08_milestone_esios_price_extractor.py)
**Este es el componente más robusto y profesional de la colección.** Representa un extractor de grado industrial diseñado para el sector energético.

* **Fuente:** API oficial de Red Eléctrica de España (ESIOS).
* **Diferenciadores Técnicos:**
    * **Autenticación:** Implementación de cabeceras seguras (Headers) y tokens.
    * **Limpieza Crítica:** Normalización de tipos (conversión de decimales europeos a floats de ingeniería).
    * **Integridad de Datos:** Manejo avanzado de excepciones y validación de esquemas JSON.
    * **Transformación Temporal:** Normalización de fechas a estándar ISO-8601 para futura inyección en SQL.

---

## 📂 Inventario de Scripts

A continuación, se detallan los scripts que forman la base técnica de este módulo:

| Archivo | Foco Técnico | Descripción |
| :--- | :--- | :--- |
| **[01_http_socket_connector.py](./scripts/01_http_socket_connector.py)** | Sockets & TCP/IP | Conexión manual a nivel de socket y envío de peticiones GET crudas. |
| **[02_web_scraping_aggregator.py](./scripts/02_web_scraping_aggregator.py)** | BS4 & SSL | Análisis del DOM HTML para agregación de datos numéricos. |
| **[03_recursive_web_crawler.py](./scripts/03_recursive_web_crawler.py)** | Crawling Recursivo | Navegación automatizada a través de hipervínculos con profundidad controlada. |
| **[04_xml_data_aggregator.py](./scripts/04_xml_data_aggregator.py)** | ElementTree & XPath | Extracción selectiva en archivos XML utilizando selectores de ruta. |
| **[05_json_data_extractor.py](./scripts/05_json_data_extractor.py)** | Requests & List Comp | Consumo optimizado de APIs JSON utilizando comprensiones de lista. |
| **[06_api_json_geo_processor.py](./scripts/06_api_json_geo_processor.py)** | GeoJSON & URL Encoding | Procesamiento de coordenadas y Plus Codes mediante APIs de geolocalización. |
| **[07_selenium_dynamic_extractor.py](./scripts/07_selenium_dynamic_extractor.py)** | Selenium & Headless | Extracción de contenido renderizado por JavaScript (contenido dinámico). |

---

## 🛠️ Stack Tecnológico Utilizado
* **Lenguaje:** Python 3.12+ (WSL2 Ubuntu)
* **Librerías Clave:** `requests`, `BeautifulSoup4`, `selenium`, `lxml`.
* **Herramientas:** Chromium Driver (Headless mode), DB Browser.

## ⚡ Cómo ejecutar los extractores
1.  Asegúrate de tener instalado el entorno de Python y las dependencias:
    ```bash
    pip install requests beautifulsoup4 selenium
    ```
2.  Ejecutar el script deseado:
    ```bash
    python3 scripts/08_milestone_esios_price_extractor.py
    ```

---
**Ingeniero:** Aitor | Industrial Systems Engineer turned Data Engineer.  
