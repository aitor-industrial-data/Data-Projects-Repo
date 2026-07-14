<div align="center">

```
███████╗██╗   ██╗███╗   ██╗███████╗ █████╗ ██╗   ██╗███████╗██████╗
██╔════╝██║   ██║████╗  ██║██╔════╝██╔══██╗██║   ██║██╔════╝██╔══██╗
███████╗██║   ██║██╔██╗ ██║███████╗███████║██║   ██║█████╗  ██████╔╝
╚════██║██║   ██║██║╚██╗██║╚════██║██╔══██║╚██╗ ██╔╝██╔══╝  ██╔══██╗
███████║╚██████╔╝██║ ╚████║███████║██║  ██║ ╚████╔╝ ███████╗██║  ██║
╚══════╝ ╚═════╝ ╚═╝  ╚═══╝╚══════╝╚═╝  ╚═╝  ╚═══╝  ╚══════╝╚═╝  ╚═╝
```

![Python](https://img.shields.io/badge/Python-3.11+-3776AB?style=flat-square&logo=python&logoColor=white)
![SQLite](https://img.shields.io/badge/SQLite-3-003B57?style=flat-square&logo=sqlite&logoColor=white)
![pvlib](https://img.shields.io/badge/pvlib-0.11-F7931E?style=flat-square)
![Pipeline](https://img.shields.io/badge/Pipeline-6%20stages-22C55E?style=flat-square)
![Architecture](https://img.shields.io/badge/Architecture-Medallion-8B5CF6?style=flat-square)
![Docs](https://img.shields.io/badge/Docs-8%20documentos-0EA5E9?style=flat-square)
![License](https://img.shields.io/badge/License-MIT-6B7280?style=flat-square)

**Plataforma de inteligencia energética industrial: física solar + mercado eléctrico + datos operativos, en un pipeline ETL con horizonte de 5 días y granularidad horaria.**

</div>

---

## 01 · El problema que resuelve

Una PYME industrial con instalación fotovoltaica toma hoy sus decisiones energéticas a ciegas. No sabe cuánta energía va a generar mañana, ni cuánto costará la red en cada franja horaria, ni si tiene sentido arrancar la prensa a las 10h o esperar a las 14h. Esa incertidumbre tiene un precio concreto: **cargar baterías en hora punta, arrancar maquinaria con déficit solar y perder el arbitraje entre generación propia y red**.

SunSaver elimina esa incertidumbre. Integra previsión meteorológica (OpenWeatherMap), precios horarios del mercado eléctrico español (REE/PVPC) y los parámetros físicos de cada instalación para producir, hora a hora y con 5 días de antelación, una respuesta accionable a la pregunta que importa:

> *«Dado lo que sé sobre el sol, el tiempo y el precio de la luz — ¿cuándo debo arrancar mis máquinas, cuándo cargar mis baterías y cuándo es mejor comprar energía de la red?»*

| Caso de uso | Horizonte | Impacto económico |
|---|---|---|
| **Programación de maquinaria pesada** | 24–48 h | Elegir horas de alta generación PV + precio bajo |
| **Carga óptima de baterías** | 5–24 h | Cargar en excedente PV + valle; descargar en punta |
| **Gestión de cargas diferibles** | 5 días | Mover consumos no urgentes a ventanas de menor coste neto |

---

## 02 · Arquitectura del pipeline

```
┌──────────────────────────────────────────────────────────────────────────────┐
│                          FUENTES DE ENTRADA                                  │
│   📊 clients_source.xlsx    🌤 OpenWeatherMap API    ⚡ REE API (PVPC)        │
└───────────────┬─────────────────────┬────────────────────────┬───────────────┘
                │                     │                        │
                ▼                     ▼                        ▼
┌──────────────────────────────────────────────────────────────────────────────┐
│  STAGE 1–2 · BRONZE  ── Ingesta raw · JSON inmutable (chmod 444)             │
│  Process manifests por fuente · trazabilidad completa de archivos            │
└───────────────────────────────────┬──────────────────────────────────────────┘
                                    │
                                    ▼
┌──────────────────────────────────────────────────────────────────────────────┐
│  STAGE 2–4 · SILVER  ── Validación · tipos · reglas de negocio               │
│  Deduplicación · resampleo horario con interpolación · imputación            │
└───────────────────────────────────┬──────────────────────────────────────────┘
                                    │
                                    ▼
┌──────────────────────────────────────────────────────────────────────────────┐
│  STAGE 5 · MOTOR FÍSICO PV  ── pvlib                                         │
│  Posición solar (NREL SPA) · GHI Haurwitz · Kasten-Czeplak · Erbs            │
│  POA Liu-Jordan · T_cell Faiman · Potencia AC · Consumo industrial           │
└───────────────────────────────────┬──────────────────────────────────────────┘
                                    │
                                    ▼
┌──────────────────────────────────────────────────────────────────────────────┐
│  STAGE 6 · GOLD  ── Star Schema Kimball · listo para BI                      │
│  dim_client · dim_datetime (P1/P2/P3/P6) · dim_weather · fact_energy         │
└──────────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
              📁 SQLite · sunsaver.db   +   📋 etl_metadata (auditoría)
```

Cada fila de `gold_fact_energy_forecast` responde a: *«para esta instalación, en esta hora concreta, ¿cuánta energía se genera, cuánta se consume y cuánto cuesta?»*

---

## 03 · Stack tecnológico

| Herramienta | Versión | Rol en el proyecto |
|---|---|---|
| **Python** | 3.11+ | Lenguaje del pipeline completo |
| **pvlib** | 0.11 | Geometría solar, GHI, descomposición Erbs, POA, modelo Faiman |
| **pandas** | 2.x | Transformación, resampleo e imputación de datos |
| **SQLAlchemy** | 2.x | Escritura idempotente en SQLite (upsert con clave compuesta) |
| **SQLite** | 3.x | Almacén analítico embebido, portable, sin infraestructura |
| **requests** | 2.x | Clientes HTTP para REE y OpenWeatherMap |
| **python-dotenv** | 1.x | Gestión de secretos y variables de entorno |

---

## 04 · Funcionalidades principales

- ✅ **Decisiones energéticas accionables** — cada ejecución produce un horizonte de 5 días con generación PV, consumo industrial y precio PVPC por hora y por instalación
- ✅ **Motor físico de alta fidelidad** — cadena completa atmósfera→electricidad: Haurwitz + Kasten-Czeplak + Erbs + Liu-Jordan + Faiman; determinista y reproducible
- ✅ **Tarifas eléctricas españolas integradas** — clasificación automática P1/P2/P3/P6 con festivos nacionales oficiales y franjas horarias 2.0TD
- ✅ **Arquitectura Medallion con linaje completo** — Bronze (raw inmutable) → Silver (validado) → Gold (dimensional); cada dato es trazable hasta su fuente
- ✅ **Idempotente por diseño** — reejecutar no duplica registros; upsert con clave compuesta en Silver y Gold
- ✅ **Resiliencia ante fallos parciales** — REE sin publicar precios devuelve `PARTIAL SUCCESS`, no aborta; los manifests actúan como cola de reintentos automática
- ✅ **Multi-cliente escalable** — añadir una instalación al Excel de origen es suficiente; el pipeline la procesa sin cambios de código

---

## 05 · Estructura del repositorio

```
sunsaver/
├── src/
│   ├── bronze_ingest_clients.py       # Extracción Excel → JSON Bronze (clientes)
│   ├── bronze_ingest_prices_ree.py    # Extracción API REE → JSON Bronze (PVPC)
│   ├── bronze_ingest_weather_owm.py   # Extracción OWM → JSON Bronze (meteorología)
│   ├── silver_transform_clients.py    # Validación y carga Silver de clientes
│   ├── silver_transform_prices.py     # Validación y carga Silver de precios
│   ├── silver_transform_weather.py    # Resampleo horario y carga Silver de clima
│   ├── silver_calc_pv_generation.py   # Simulación física PV → clean_calculations
│   ├── gold_dim_clients.py            # Dimensión cliente (has_solar, has_battery)
│   ├── gold_dim_datetime.py           # Dimensión tiempo + tarifas P1–P6
│   ├── gold_dim_weather.py            # Dimensión condición meteorológica (SCD-2)
│   ├── gold_fact_energy_forecast.py   # Fact table: generación · consumo · precio
│   ├── engine_pv_physics.py           # Librería física PV reutilizable (pvlib)
│   ├── config_paths.py                # Rutas absolutas con override .env
│   ├── logger_config.py               # Logger centralizado con rotación diaria
│   ├── audit_metadata.py              # Persistencia de métricas de ejecución
│   └── pipeline_runner.py             # Orquestador CLI con --stage y --dry-run
├── docs/                              # Documentación técnica y de negocio (8 docs)
│   ├── 01_ARCHITECTURE_DECISION_RECORD.md
│   ├── 02_DATA_CATALOG.md
│   ├── 03_PIPELINE_TECHNICAL_SPEC.md
│   ├── 04_DATA_QUALITY_FRAMEWORK.md
│   ├── 05_STAR_SCHEMA_DESIGN.md
│   ├── 06_API_INTEGRATION_SPECS.md
│   ├── 07_OPERATIONS_RUNBOOK.md
│   └── 08_BUSINESS_INTELLIGENCE_GUIDE.md
├── data/
│   ├── bronze/                        # JSONs raw inmutables (chmod 444)
│   ├── clients_source.xlsx            # Master de instalaciones
│   └── sunsaver.db                    # Base de datos SQLite (todas las capas)
├── logs/                              # Logs diarios: sunsaver_YYYY-MM-DD.log
├── .env.example
└── requirements.txt
```

---

## 06 · Instalación y configuración

**Prerequisitos:** Python 3.11+, acceso a las APIs de REE y OpenWeatherMap.

```bash
# 1. Clonar el repositorio
git clone https://github.com/aitor-industrial-data/Data-Projects-Repo.git
cd Data-Projects-Repo/05_ETL_Pipelines/05.02_SunSaver_ETL

# 2. Crear entorno virtual e instalar dependencias
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r requirements.txt

# 3. Configurar variables de entorno
cp .env.example .env
# Editar .env: WEATHER_API_KEY es la única variable obligatoria
```

Las variables disponibles están documentadas en `.env.example`. `DB_PATH` y `BRONZE_PATH` son opcionales y permiten redirigir el almacenamiento fuera del directorio por defecto.

---

## 07 · Uso rápido

```bash
# Pipeline completo
python src/pipeline_runner.py

# Ver el plan sin ejecutar nada
python src/pipeline_runner.py --dry-run

# Reanudar desde un stage concreto (ej: recalcular PV y Gold sin reingestar)
python src/pipeline_runner.py --stage 5
```

**Salida esperada:**

```
2026-05-13 08:00:01 | INFO | pipeline_runner | ── STAGE 1 ──────────────────────
2026-05-13 08:00:02 | INFO | pipeline_runner |   ✔  extract_clients (1.2s) | Filas: 12
2026-05-13 08:00:03 | INFO | pipeline_runner |   ✔  extract_energy_prices (0.8s) | Filas: 24
...
2026-05-13 08:01:47 | INFO | pipeline_runner | PIPELINE FINALIZADO en 106.43s
2026-05-13 08:01:47 | INFO | pipeline_runner | Total Filas: 3.847 | Steps OK: 11 | Steps KO: 0
```

---

## 08 · Configuración avanzada

| Parámetro | Defecto | Descripción |
|---|---|---|
| `--stage N` | `1` | Stage desde el que arrancar (1–6) |
| `--dry-run` | `false` | Muestra el plan sin ejecutar ninguna función |
| `DB_PATH` | `data/sunsaver.db` | Ruta absoluta a la base de datos SQLite |
| `BRONZE_PATH` | `data/bronze/` | Directorio de almacenamiento de archivos Bronze |
| `WEATHER_API_KEY` | — | API key de OpenWeatherMap (obligatoria) |

**Modos de ejecución:**

- **Completo** — sin argumentos; reprocesa todo desde Stage 1 incluyendo ingesta de APIs.
- **Incremental** — `--stage 5` o superior; recalcula PV y Gold sin tocar las capas de ingesta.
- **Dry-run** — verifica configuración y dependencias sin efectos secundarios ni llamadas a APIs.

Los manifests Bronze (`_process_manifest_*.json`) actúan como cola de trabajo: las tareas con estado `pending` o `error` se reintentarán automáticamente en la siguiente ejecución. Para playbooks operativos completos, ver [`docs/07_OPERATIONS_RUNBOOK.md`](docs/07_OPERATIONS_RUNBOOK.md).

---

## 09 · Testing y calidad de datos

```bash
# Tests unitarios
pytest tests/ -v --tb=short

# Test standalone del motor físico PV (sin base de datos ni APIs)
python src/engine_pv_physics.py
```

La calidad del dato está embebida en cada capa, no es un proceso posterior. Un precio incorrecto puede llevar a cargar baterías en hora punta; unas coordenadas erróneas generan previsiones meteorológicas de otra ubicación e invalidan todos los cálculos PV. El framework aplica el principio **"fail fast, fail loudly"**:

- **Tipos y rangos** — coerción con pandas; fuera de rango imputa valores de referencia documentados (ángulo → 30°, pérdidas → 14%, eficiencia → 0.15).
- **Reglas geográficas** — latitud `[-90, 90]` y longitud `[-180, 180]`; registros fuera de rango eliminados antes de cualquier cálculo PV.
- **Precios** — outliers fuera de `[-100, 2 000] EUR/MWh` filtrados; huecos interpolados linealmente por tipo de precio.
- **Deduplicación** — por `(client_id, unix_time)` como PK compuesta en Silver y Gold; idempotencia garantizada en toda la cadena.

Para el catálogo completo de reglas de validación, quality scores y proceso de remediación, ver [`docs/04_DATA_QUALITY_FRAMEWORK.md`](docs/04_DATA_QUALITY_FRAMEWORK.md).

---

## 10 · Observabilidad y errores

Los logs se escriben simultáneamente en consola y en `logs/sunsaver_YYYY-MM-DD.log` con rotación diaria. Formato: `TIMESTAMP | LEVEL | MODULE | MESSAGE` — filtrable con `grep` o cualquier agregador de logs.

Ante un fallo individual el orquestador **no aborta**: registra la tarea como `error` en el manifest y continúa. Si un stage completo falla, el pipeline se detiene con `FAILED AT STAGE N`. Cada ejecución persiste en `etl_metadata` con estado, duración, filas procesadas y resumen del error.

Los archivos Bronze son **inmutables** (chmod 444): el dato raw original nunca se modifica; cualquier reingesta crea un nuevo archivo y el manifest gestiona cuál procesar.

```bash
# Ver las últimas ejecuciones del pipeline
sqlite3 data/sunsaver.db "SELECT * FROM etl_metadata ORDER BY id DESC LIMIT 5;"

# Logs en tiempo real
tail -f logs/sunsaver_$(date +%Y-%m-%d).log
```

Para playbooks de incidencias y SLAs, ver [`docs/07_OPERATIONS_RUNBOOK.md`](docs/07_OPERATIONS_RUNBOOK.md).

---

## 11 · Decisiones de diseño

**Motor físico propio (pvlib) sobre APIs de predicción solar de terceros** — El cálculo determinista garantiza reproducibilidad completa: dado el mismo input meteorológico, el output es siempre idéntico. Una API externa añade latencia, coste y opacidad. El motor es testeable unitariamente y auditable línea a línea. → [`docs/01_ARCHITECTURE_DECISION_RECORD.md`](docs/01_ARCHITECTURE_DECISION_RECORD.md)

**Manifests JSON como cola de trabajo en Bronze** — Evita una dependencia de infraestructura (Redis, Celery, Airflow) manteniendo la capacidad de reintentar tareas fallidas individualmente. Comprensible sin herramientas externas; inspeccionable con un editor de texto o `cat`.

**SQLite sobre PostgreSQL en la capa analítica** — El volumen actual no justifica la complejidad operacional de un servidor. SQLite entrega el proyecto como un único fichero portable; la migración es transparente porque SQLAlchemy abstrae el dialecto.

**Star Schema Kimball con granularidad declarada** — Exactamente una fila por `(instalación, hora UTC)`. Medidas de potencia (kW) y coste (€) son aditivas a lo largo de todas las dimensiones; el Performance Ratio es no-aditivo y se documenta explícitamente. → [`docs/05_STAR_SCHEMA_DESIGN.md`](docs/05_STAR_SCHEMA_DESIGN.md)

**Roadmap:**
- Scheduler con APScheduler para ejecución autónoma diaria (publicación REE: 20:30 CET)
- Exportación a Parquet para integración con herramientas BI (Power BI, Metabase)
- Contenerización con Docker para despliegue reproducible en cualquier entorno
- API REST sobre la capa Gold para consumo por dashboards o aplicaciones externas

---

## 📚 Documentación completa

| # | Documento | Contenido |
|---|---|---|
| 01 | [`ARCHITECTURE_DECISION_RECORD`](docs/01_ARCHITECTURE_DECISION_RECORD.md) | Cada decisión arquitectónica: qué se eligió, qué se descartó y por qué |
| 02 | [`DATA_CATALOG`](docs/02_DATA_CATALOG.md) | Inventario completo de tablas, campos, tipos y linaje campo a campo |
| 03 | [`PIPELINE_TECHNICAL_SPEC`](docs/03_PIPELINE_TECHNICAL_SPEC.md) | DAG de ejecución, dependencias entre stages, estrategias de idempotencia |
| 04 | [`DATA_QUALITY_FRAMEWORK`](docs/04_DATA_QUALITY_FRAMEWORK.md) | Catálogo de reglas de validación, quality scores y proceso de remediación |
| 05 | [`STAR_SCHEMA_DESIGN`](docs/05_STAR_SCHEMA_DESIGN.md) | Modelo dimensional Kimball, guía de aditividad y queries de referencia |
| 06 | [`API_INTEGRATION_SPECS`](docs/06_API_INTEGRATION_SPECS.md) | Contratos de API, patrones de resiliencia y gestión de credenciales |
| 07 | [`OPERATIONS_RUNBOOK`](docs/07_OPERATIONS_RUNBOOK.md) | Playbooks de incidencias, SLAs, procedimientos de backfill y rollback |
| 08 | [`BUSINESS_INTELLIGENCE_GUIDE`](docs/08_BUSINESS_INTELLIGENCE_GUIDE.md) | KPIs de negocio, casos de uso de toma de decisiones y guía de consumo BI |

---

## 12 · Licencia

MIT License · © 2026 SunSaver Project
