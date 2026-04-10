# 🚀 05.01 Extractors: Ingesta de Datos Multifuente

## 📂 Descripción del Proyecto

Este directorio constituye la fase de **Ingesta (Extract)** dentro del ciclo de vida de un Pipeline ETL. El enfoque en este bloque se centra en la recuperación de activos digitales desde fuentes externas, evolucionando desde la comunicación por sockets de bajo nivel hasta la interacción avanzada con APIs gubernamentales y contenido web dinámico.

El objetivo es dominar las técnicas de extracción que permiten a un Ingeniero de Datos recolectar información de forma masiva y segura, gestionando protocolos de red, parseo de estructuras semi-estructuradas (XML/JSON) y la normalización crítica de tipos de datos para asegurar la integridad en las fases posteriores de carga.

---

## 🛠️ Stack Técnico

* **Lenguaje:** Python 3.12+
* **Entorno:** Visual Studio Code con WSL2 (Ubuntu)
* **Librerías Clave:** `requests`, `BeautifulSoup4`, `selenium`, `urllib`, `xml.etree`.
* **Conceptos Clave:** API REST, Web Scraping, Autenticación por Headers, XPath, DOM Parsing y Headless Browsing.
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

## 📜 Inventario de Scripts

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
| **[08_milestone_esios_price_extractor.py](./scripts/08_milestone_esios_price_extractor.py)** | Requests & API Auth | Extractor de grado industrial diseñado para el sector energético. |

---

## 📈 Hitos de Aprendizaje

* **Ingesta Profesional (script 08):** Implementación de un extractor de grado industrial que gestiona autenticación, limpieza de decimales europeos y normalización de fechas a ISO-8601, preparándolo para el Robot ETL.
* **Gestión de APIs y Seguridad:** Configuración de cabeceras de autorización y manejo de parámetros de consulta seguros (URL Encoding) para la interacción con servicios externos.
* **Procesamiento Semi-estructurado:** Dominio del parseo de archivos XML y JSON, transformando respuestas complejas de servidores en estructuras de datos de Python listas para análisis.
* **Extracción de Contenido Dinámico:** Uso de técnicas de automatización de navegadores para superar las barreras de sitios web que utilizan carga asíncrona de datos.

---
Este bloque es la base fundamental para alimentar cualquier almacén de datos. 
