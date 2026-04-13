# 🚀 05.01 Extractors: Ingesta de Datos Multifuente

## 📂 Descripción del Proyecto

Este directorio constituye el núcleo práctico del **Modulo 5**, cubriendo el ciclo de vida completo de un Pipeline ETL (Extract, Transform, Load). El enfoque en este bloque ha evolucionado desde la recuperación técnica de activos digitales mediante protocolos de red hasta la construcción de sistemas robustos que orquestan el flujo de datos desde APIs externas hacia almacenes de datos relacionales (SQLite/SQL).

El objetivo es dominar la arquitectura de datos: recolectar información de forma masiva y segura, gestionar protocolos de red, parsear estructuras semi-estructuradas (XML/JSON) y aplicar una normalización crítica de tipos de datos para asegurar la integridad en las fases de carga y persistencia.
---

## 🛠️ Stack Técnico

* **Lenguaje:** Python 3.12+
* **Entorno:** Visual Studio Code con WSL2 (Ubuntu)
* **Librerías Clave:** `requests`, `SQLAlchemy`, `pandas`, `BeautifulSoup4`, `selenium`, `sqlite3`, `xml.etree`.
* **Conceptos Clave:** API REST, Modelado Relacional (SQL), ORM (Object-Relational Mapping), CRUD Lifecycle, Bulk Loading y Arquitectura ETL.
---

## 🏆 Proyecto Destacado (HITO)


### [14_crypto_etl_pipeline.py](./scripts/14_crypto_etl_pipeline.py)

Este proyecto es la culminación del **Mes 5** e integra un flujo completo de ingeniería de datos, desde la comunicación con protocolos de red hasta la persistencia en bases de datos relacionales.

#### 🏗️ Estructura del Pipeline

* **Extract (Ingesta Resiliente):** * Consumo de la API de CoinGecko mediante **paginación dinámica** (`page` y `per_page`).
    * Gestión activa de **Rate Limiting (Error 429)**: El robot detecta la saturación y aplica pausas inteligentes (*Backoff*) basadas en los headers del servidor.
* **Transform (Data Wrangling):** * Limpieza y normalización de tipos: conversión de strings financieros a `float` y fechas a estándar **ISO-8601**.
    * Tratamiento de nulos y redondeo para asegurar la integridad del esquema SQL.
* **Load (Persistencia Optimizada):** * Uso de **SQLAlchemy ORM** para el mapeo de objetos.
    * Implementación de **Batch Loading**: inserción por lotes para minimizar el impacto de entrada/salida (I/O) en disco.

#### 🚀 Diferenciadores Técnicos

* **Targeted Execution:** Permite ejecutar el pipeline por fases (solo extraer, solo transformar, etc.) para facilitar el mantenimiento.
* **Observabilidad:** Sistema de *logging* profesional que registra el estado, errores y latencias de cada ejecución.
* **Idempotencia:** El diseño permite ejecuciones recurrentes sin generar duplicados ni inconsistencias en la base de datos `crypto_market.db`.
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
| **[09_email_domain_counter.py](./scripts/09_email_domain_counter.py)** | Data Wrangling | Procesamiento de archivos de texto planos para conteo y agregación de dominios. |
| **[10_relational_database_builder.py](./scripts/10_relational_database_builder.py)** | SQLite3 Schema | Creación programática de bases de datos relacionales y gestión de tablas. |
| **[11_json_to_sql_pipeline.py](./scripts/11_json_to_sql_pipeline.py)** | Pipeline de Carga | Transformación de objetos JSON locales en registros persistentes de SQL. |
| **[12_sqlalchemy_crud_lifecycle.py](./scripts/12_sqlalchemy_crud_lifecycle.py)** | ORM Fundamentals | Gestión del ciclo de vida de datos (Create, Read, Update, Delete) mediante SQLAlchemy. |
| **[13_sqlalchemy_bulk_load.py](./scripts/13_sqlalchemy_bulk_load.py)** | Batch Processing | Técnicas de carga masiva (Bulk) para optimizar la eficiencia en grandes volúmenes de datos. |
| **[14_crypto_etl_pipeline.py](./scripts/14_crypto_etl_pipeline.py)** | **Full ETL Robot** | Sistema final de monitorización: extracción de API, transformación y persistencia SQL. |


---

## 📈 Hitos de Aprendizaje

* **Ingesta Profesional:** Implementación de extractores que gestionan autenticación, limpieza de decimales europeos y normalización de fechas a ISO-8601, preparándolos para procesos de análisis.
* **Persistencia Relacional:** Transición de la manipulación de datos en memoria hacia la persistencia en bases de datos SQL, dominando el uso de `sqlite3` y el ORM `SQLAlchemy`.
* **Procesamiento de Datos Complejos:** Dominio del parseo de archivos XML, JSON y GeoJSON, transformando respuestas de servidores en estructuras de Python listas para la carga.
* **Arquitectura de Pipelines:** Capacidad para diseñar flujos de datos asíncronos o secuenciales que integran la extracción de contenido dinámico (Selenium) con la carga masiva (Bulk Load).

---
Este bloque es la base fundamental para alimentar cualquier almacén de datos. 
