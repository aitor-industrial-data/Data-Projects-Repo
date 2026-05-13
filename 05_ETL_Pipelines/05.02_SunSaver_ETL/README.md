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
![License](https://img.shields.io/badge/License-MIT-6B7280?style=flat-square)

**Pipeline ETL de predicción energética solar para instalaciones industriales fotovoltaicas.**

</div>

---

## 01 · Descripción del proyecto

SunSaver es un pipeline ETL de producción que ingiere datos meteorológicos en tiempo real (OpenWeatherMap), precios horarios del mercado eléctrico español (REE/PVPC) y parámetros de instalación por cliente, para generar **predicciones de generación fotovoltaica y consumo industrial** en un horizonte de 5 días. El resultado alimenta un modelo de datos dimensional (Gold) listo para reporting o toma de decisiones de optimización energética.

Diseñado para escalar de 1 a N instalaciones sin cambios en el código: añadir un cliente nuevo al Excel de origen es suficiente.

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
│  STAGE 1 · BRONZE  ── Raw ingestion · JSON inmutable (chmod 444)             │
│  bronze_ingest_clients  ·  bronze_ingest_prices_ree  ·  bronze_ingest_weather│
│  Process manifests por fuente · trazabilidad completa de archivos            │
└───────────────────────────────────┬──────────────────────────────────────────┘
                                    │
                                    ▼
┌──────────────────────────────────────────────────────────────────────────────┐
│  STAGE 2–4 · SILVER  ── Validación · deduplicación · imputación              │
│  silver_transform_clients  ·  silver_transform_prices  ·  silver_transform   │
│  Tipos forzados · reglas de negocio · resampleo horario con interpolación    │
└───────────────────────────────────┬──────────────────────────────────────────┘
                                    │
                                    ▼
┌──────────────────────────────────────────────────────────────────────────────┐
│  STAGE 5 · FÍSICA PV  ── Motor de simulación físico (pvlib)                  │
│  Posición solar · GHI/DNI/DHI · POA · T_cell Faiman · Potencia AC            │
│  Modelo de consumo industrial con turnos + carga térmica + variabilidad      │
└───────────────────────────────────┬──────────────────────────────────────────┘
                                    │
                                    ▼
┌──────────────────────────────────────────────────────────────────────────────┐
│  STAGE 6 · GOLD  ── Modelo dimensional para análisis y reporting             │
│  dim_client · dim_datetime (tarifas P1-P6) · dim_weather · fact_energy       │
└──────────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
                        📁 SQLite  ·  sunsaver.db
                        📋 etl_metadata  (auditoría de ejecuciones)
```

---

## 03 · Stack tecnológico

| Herramienta | Versión | Rol en el proyecto |
|---|---|---|
| **Python** | 3.11+ | Lenguaje del pipeline completo |
| **pvlib** | 0.11 | Cálculo de posición solar, GHI, Erbs, POA, Faiman |
| **pandas** | 2.x | Transformación, resampleo e imputación de datos |
| **SQLAlchemy** | 2.x | ORM/core para escritura idempotente en SQLite |
| **SQLite** | 3.x | Almacén analítico embebido (Bronze→Silver→Gold) |
| **requests** | 2.x | Clientes HTTP para REE y OpenWeatherMap |
| **python-dotenv** | 1.x | Gestión de secretos y configuración de entorno |

---

## 04 · Funcionalidades principales

- ✅ **Arquitectura Medallion completa** — Bronze → Silver → Gold con trazabilidad de linaje en cada capa
- ✅ **Idempotente por diseño** — reejecutar el pipeline no duplica registros (upsert con clave compuesta en Silver y Gold)
- ✅ **Motor físico PV de alta fidelidad** — irradiancia Haurwitz + Kasten-Czeplak + descomposición Erbs + modelo Faiman para temperatura de célula
- ✅ **Resiliencia ante fallos parciales** — REE sin publicar precios devuelve `PARTIAL SUCCESS`, no aborta el pipeline
- ✅ **Multi-cliente escalable** — el pipeline itera sobre todos los clientes activos; añadir uno no requiere cambios de código
- ✅ **Auditoría automática** — cada ejecución persiste estado, duración, filas procesadas y errores en `etl_metadata`
- ✅ **Tarifas eléctricas españolas** — clasificación automática P1/P2/P3/P6 con festivos nacionales y franjas horarias oficiales

---

## 05 · Estructura del repositorio

```
sunsaver/
├── src/
│   ├── bronze_ingest_clients.py      # Extracción Excel → JSON Bronze (clientes)
│   ├── bronze_ingest_prices_ree.py   # Extracción API REE → JSON Bronze (PVPC)
│   ├── bronze_ingest_weather_owm.py  # Extracción OWM → JSON Bronze (meteorología)
│   ├── silver_transform_clients.py   # Validación y carga Silver de clientes
│   ├── silver_transform_prices.py    # Validación y carga Silver de precios
│   ├── silver_transform_weather.py   # Validación, resampleo y carga Silver de clima
│   ├── silver_calc_pv_generation.py  # Simulación física PV → clean_calculations
│   ├── gold_dim_clients.py           # Dimensión cliente (flags has_solar, has_battery)
│   ├── gold_dim_datetime.py          # Dimensión tiempo (calendario + tarifas P1–P6)
│   ├── gold_dim_weather.py           # Dimensión condición meteorológica (tipo 2)
│   ├── gold_fact_energy_forecast.py  # Fact table: generación · consumo · precio
│   ├── engine_pv_physics.py          # Librería física PV reutilizable (pvlib)
│   ├── config_paths.py               # Rutas absolutas resolubles con override .env
│   ├── logger_config.py              # Logger centralizado con rotación diaria
│   ├── audit_metadata.py             # Persistencia de métricas de ejecución
│   └── pipeline_runner.py            # Orquestador CLI con --stage y --dry-run
├── data/
│   ├── bronze/                       # JSONs raw inmutables (chmod 444)
│   ├── clients_source.xlsx           # Master de instalaciones (fuente de verdad)
│   └── sunsaver.db                   # Base de datos SQLite (todas las capas)
├── logs/                             # Logs diarios: sunsaver_YYYY-MM-DD.log
├── .env.example                      # Plantilla de variables de entorno
├── requirements.txt
└── README.md
```

---

## 06 · Instalación y configuración

**Prerequisitos:** Python 3.11+, pip, acceso a las APIs de REE y OpenWeatherMap.

```bash
# 1. Clonar el repositorio
git clone https://github.com/tu-usuario/sunsaver.git
cd sunsaver

# 2. Crear entorno virtual e instalar dependencias
python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -r requirements.txt

# 3. Configurar variables de entorno
cp .env.example .env
# Editar .env con las claves de API y rutas opcionales
```

Las variables de entorno necesarias están documentadas en `.env.example`. Las dos imprescindibles son `WEATHER_API_KEY` (OpenWeatherMap) y opcionalmente `DB_PATH` si se quiere un SQLite fuera del directorio por defecto.

---

## 07 · Uso rápido

```bash
# Pipeline completo (recomendado para producción)
python src/pipeline_runner.py

# Dry-run: ver el plan de ejecución sin tocar datos
python src/pipeline_runner.py --dry-run

# Reanudar desde un stage concreto (ej: recalcular desde PV en adelante)
python src/pipeline_runner.py --stage 5
```

**Salida esperada (fragmento):**

```
2026-05-13 08:00:01 | INFO     | pipeline_runner               | ── STAGE 1 ────────────────────────────
2026-05-13 08:00:02 | INFO     | pipeline_runner               |   ✔  extract_clients completado (1.2s) | Filas: 12
2026-05-13 08:00:03 | INFO     | pipeline_runner               |   ✔  extract_energy_prices completado (0.8s) | Filas: 24
...
2026-05-13 08:01:47 | INFO     | pipeline_runner               | PIPELINE FINALIZADO en 106.43s
2026-05-13 08:01:47 | INFO     | pipeline_runner               | Total Filas: 3.847  |  Steps OK: 11  |  Steps KO: 0
```

---

## 08 · Configuración avanzada

| Parámetro | Defecto | Descripción |
|---|---|---|
| `--stage N` | `1` | Stage desde el que arrancar el pipeline (1–6) |
| `--dry-run` | `false` | Muestra el plan sin ejecutar ninguna función |
| `DB_PATH` | `data/sunsaver.db` | Ruta absoluta a la base de datos SQLite |
| `BRONZE_PATH` | `data/bronze/` | Directorio de almacenamiento de archivos Bronze |
| `WEATHER_API_KEY` | — | API key de OpenWeatherMap (obligatoria) |

**Modos de ejecución:**

- **Completo** — `pipeline_runner.py` sin argumentos. Reprocesa todo desde Stage 1.
- **Incremental** — `--stage 5` o superior. Útil cuando solo cambian los datos de generación.
- **Dry-run** — validación de configuración y dependencias sin efectos secundarios.

Los manifests de Bronze (`_process_manifest_*.json`) actúan como cola de trabajo: las tareas con estado `pending` o `error` se reintentarán automáticamente en la siguiente ejecución.

---

## 09 · Testing y calidad de datos

```bash
# Ejecutar tests unitarios
pytest tests/ -v --tb=short

# Test standalone del motor físico PV (sin base de datos)
python src/engine_pv_physics.py
```

Las validaciones de calidad están integradas en cada capa Silver:

- **Tipos** — coerción con `pd.to_numeric` y `pd.to_datetime`; valores no parseables pasan a `NaN` antes de ser descartados o imputados.
- **Rangos geográficos** — latitud `[-90, 90]`, longitud `[-180, 180]`; registros fuera de rango se eliminan.
- **Reglas de negocio** — ángulo `[0°–90°]`, pérdidas `[0%–90%]`, eficiencia `[0–1]`; fuera de rango se imputan con valores de referencia de la industria.
- **Precios** — outliers fuera de `[-100, 2 000] EUR/MWh` filtrados; huecos interpolados linealmente por tipo de precio.

---

## 10 · Observabilidad y errores

Los logs se escriben simultáneamente en consola y en `logs/sunsaver_YYYY-MM-DD.log` con rotación diaria automática. El formato es `TIMESTAMP | LEVEL | MODULE | MESSAGE`, lo que facilita el filtrado con `grep` o cualquier agregador de logs.

Ante un fallo en una tarea individual, el orquestador **no aborta**: marca la tarea como `error` en el manifest y continúa. Si un stage completo falla (todos los pasos del stage devuelven `False`), el pipeline se detiene con `FAILED AT STAGE N`. En cualquier caso, la ejecución se registra en `etl_metadata` con estado `PARTIAL SUCCESS` o `FAILED`, duración y resumen del error.

Los archivos Bronze (chmod 444) son **inmutables** una vez escritos: garantía de que el dato raw original nunca se modifica, solo se vuelve a procesar desde Silver hacia arriba.

---

## 11 · Decisiones de diseño

**Arquitectura Medallion sobre un data warehouse convencional** — La separación Bronze/Silver/Gold permite reejecutar cualquier transformación sin perder el dato original. Con un DWH clásico habríamos necesitado tablas de staging adicionales y lógica de rollback.

**SQLite sobre PostgreSQL para la capa analítica** — El volumen actual (decenas de clientes, horizonte de 5 días) no justifica la complejidad operacional de un servidor. SQLite permite entregar el proyecto completo como un único fichero portable; la migración a PostgreSQL es trivial porque SQLAlchemy abstrae el dialecto.

**Motor físico propio (pvlib) sobre APIs de terceros de predicción solar** — El cálculo determinista garantiza reproducibilidad completa: dado el mismo input meteorológico, el output es idéntico. Una API externa añadiría latencia, coste y una caja negra en el modelo.

**Manifests JSON como cola de trabajo en Bronze** — Evita una dependencia de infraestructura (Redis, Celery, Airflow) manteniendo la capacidad de reintentar tareas fallidas individualmente. La solución es suficientemente robusta para el volumen actual y trivial de entender.

**Roadmap:**
- Scheduler con APScheduler o cron para ejecución autónoma diaria
- Exportación de resultados a Parquet para integración con herramientas BI (Power BI, Metabase)
- Soporte multi-zona horaria para instalaciones fuera de España peninsular
- Contenerización con Docker para despliegue reproducible

---

## 12 · Licencia

MIT License · © 2026 SunSaver Project