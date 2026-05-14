# 05_ETL_PIPELINES

> **Módulo 5 · Data Engineering** — Ciclo de vida completo de un pipeline ETL: extracción masiva desde múltiples fuentes, transformación y normalización de datos, y persistencia en bases de datos relacionales.

---

## 📁 Estructura del módulo

```
05_ETL_Pipelines/
├── 05.01_Lab_Scripts/          # Laboratorio base: 14 scripts progresivos
│   └── scripts/
└── 05.02_SunSaver_ETL/         # Proyecto final: pipeline ETL de producción
    └── scripts/
```

---

## 🧪 [05.01 · Lab Scripts](./05.01_Lab_Scripts/)

Batería de **14 scripts progresivos** que cubren desde la conexión a nivel de socket hasta la carga masiva en SQL. Cada script aísla y domina una competencia técnica concreta.

| # | Script | Competencia |
|---|--------|-------------|
| 01 | `http_socket_connector` | Sockets TCP/IP — peticiones GET a nivel de protocolo |
| 02 | `web_scraping_aggregator` | BeautifulSoup4 — análisis del DOM y agregación numérica |
| 03 | `recursive_web_crawler` | Crawling recursivo con profundidad controlada |
| 04 | `xml_data_aggregator` | ElementTree & XPath — extracción selectiva en XML |
| 05 | `json_data_extractor` | Requests & comprensiones de lista — consumo de APIs JSON |
| 06 | `api_json_geo_processor` | GeoJSON & URL Encoding — APIs de geolocalización |
| 07 | `selenium_dynamic_extractor` | Selenium Headless — contenido renderizado por JavaScript |
| 08 | `esios_price_extractor` | API Auth — extractor de grado industrial (sector energético) |
| 09 | `email_domain_counter` | Data Wrangling — procesamiento de texto plano |
| 10 | `relational_database_builder` | SQLite3 — creación programática de esquemas relacionales |
| 11 | `json_to_sql_pipeline` | Pipeline de carga JSON → SQL |
| 12 | `sqlalchemy_crud_lifecycle` | ORM — ciclo de vida completo CRUD con SQLAlchemy |
| 13 | `sqlalchemy_bulk_load` | Batch Processing — carga masiva optimizada |
| 14 | `crypto_etl_pipeline` | **Full ETL Robot** — pipeline completo de producción |

---

## 🏗️ [05.02 · SunSaver ETL](./05.02_SunSaver_ETL/)

Proyecto de ingeniería de datos de **nivel producción**. Implementa un pipeline ETL robusto e idempotente sobre datos del mercado de criptomonedas, integrando las competencias adquiridas en el laboratorio anterior.

### Pipeline

```
[ API CoinGecko ] ──► [ Extracción + Paginación ] ──► [ Transformación ] ──► [ SQLite ]
                            Rate Limiting (429)          Normalización ISO         ORM
                            Backoff inteligente          Wrangling financiero      Batch Load
```

**Capacidades técnicas destacadas:**

- **Resiliencia en extracción** — paginación dinámica y gestión activa de rate limiting con backoff basado en headers
- **Normalización de tipos** — conversión de strings financieros a `float` y fechas a ISO-8601
- **Persistencia optimizada** — SQLAlchemy ORM con inserción por lotes (Batch Load)
- **Idempotencia** — ejecuciones recurrentes sin duplicados ni inconsistencias
- **Observabilidad** — logging profesional con registro de estado, errores y latencias
- **Ejecución segmentada** — fases Extract / Transform / Load ejecutables de forma independiente

---

## 🛠️ Stack Técnico

| Capa | Tecnologías |
|------|-------------|
| **Lenguaje** | Python 3.12+ |
| **Entorno** | VS Code + WSL2 (Ubuntu) |
| **Extracción** | `requests`, `BeautifulSoup4`, `selenium`, `xml.etree`, `socket` |
| **Transformación** | `pandas` |
| **Persistencia** | `SQLAlchemy`, `sqlite3` |
| **Conceptos** | API REST, ORM, CRUD, ETL, Batch Loading, Rate Limiting |

---

## 📈 Competencias desarrolladas

- Ingesta profesional desde APIs con autenticación, gestión de errores y normalización de datos
- Diseño de esquemas relacionales y transición de datos en memoria a persistencia SQL
- Parseo de estructuras semi-estructuradas: XML, JSON y GeoJSON
- Arquitectura de pipelines con extracción dinámica (Selenium) y carga masiva (Bulk Load)

---

*Módulo 5 de un repositorio de proyectos de Data Engineering en progresión continua.*