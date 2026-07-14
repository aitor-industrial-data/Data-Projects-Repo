# ☀️ SunSaver ETL · Plataforma de Inteligencia Energética Industrial
## 03 Especificación Técnica del Pipeline

> **Clasificación:** INTERNA &nbsp;|&nbsp; **Estado:** ACTIVO — Entorno DEV &nbsp;|&nbsp; **Pipeline:** `SunSaver_ETL`  
> **Propietario técnico:** Equipo de Data Engineering — SunSaver &nbsp;|&nbsp; **Última actualización:** 2026-05-11

---

## Tabla de Contenidos

1. [Pipeline Overview](#1-pipeline-overview)
   - 1.1 [Diagrama de Flujo Completo](#11-diagrama-de-flujo-completo)
   - 1.2 [Topología de Ejecución (DAG)](#12-topología-de-ejecución-dag)
   - 1.3 [Dependencias entre Stages](#13-dependencias-entre-stages)
   - 1.4 [Orquestación y Scheduling](#14-orquestación-y-scheduling)
2. [Capa de Ingesta — Bronze](#2-capa-de-ingesta--bronze)
   - 2.1 [Proceso de Extracción por Fuente](#21-proceso-de-extracción-por-fuente)
   - 2.2 [Escritura en Bronze](#22-escritura-en-bronze)
   - 2.3 [Idempotencia y Deduplicación](#23-idempotencia-y-deduplicación)
   - 2.4 [Control de Errores en Ingesta](#24-control-de-errores-en-ingesta)
3. [Capa de Transformación — Silver](#3-capa-de-transformación--silver)
   - 3.1 [Proceso de Limpieza](#31-proceso-de-limpieza)
   - 3.2 [Enriquecimiento de Datos](#32-enriquecimiento-de-datos)
   - 3.3 [Validación de Reglas de Negocio](#33-validación-de-reglas-de-negocio)
   - 3.4 [Control de Versiones de Registros](#34-control-de-versiones-de-registros-scd)
4. [Capa de Modelado — Gold](#4-capa-de-modelado--gold)
   - 4.1 [Proceso de Carga Dimensional](#41-proceso-de-carga-dimensional)
   - 4.2 [Estrategia de Actualización](#42-estrategia-de-actualización)
   - 4.3 [Gestión de Late-Arriving Data](#43-gestión-de-late-arriving-data)
5. [Control de Ejecución](#5-control-de-ejecución)
   - 5.1 [Checkpoints y Estado del Pipeline](#51-checkpoints-y-estado-del-pipeline)
   - 5.2 [Paralelismo y Concurrencia](#52-paralelismo-y-concurrencia)
   - 5.3 [Gestión de Dependencias de Datos](#53-gestión-de-dependencias-de-datos)
   - 5.4 [Watermarks y Ventanas Temporales](#54-watermarks-y-ventanas-temporales)
6. [Testing del Pipeline](#6-testing-del-pipeline)
   - 6.1 [Unit Tests — Transformaciones Individuales](#61-unit-tests--transformaciones-individuales)
   - 6.2 [Integration Tests — Flujo End-to-End](#62-integration-tests--flujo-end-to-end)
   - 6.3 [Data Contract Tests](#63-data-contract-tests)
   - 6.4 [Regression Tests con Datasets de Referencia](#64-regression-tests-con-datasets-de-referencia)

---

## 1. Pipeline Overview

### 1.1 Diagrama de Flujo Completo

El pipeline `SunSaver_ETL` se ejecuta como un proceso Python secuencial organizado en **6 stages** con dependencias explícitas entre ellos. La secuencia garantiza que los datos de capas previas estén disponibles antes de iniciar la siguiente.

```
INICIO
  |
  +--[STAGE 1: Ingesta paralela]------------------------------------------+
  |                                                                       |
  |  extract_clients()              extract_energy_prices()               |
  |  bronze_ingest_clients.py       bronze_ingest_prices_ree.py           |
  |  SRC: clients_source.xlsx       SRC: REE API (PVPC D+1)               |
  |  OUT: clients_*.json            OUT: prices_*.json                    |
  |  OUT: manifest_clients.json     OUT: manifest_ree.json                |
  |                                                                       |
  |  Resultado: int (n_records) | False (REE sin datos)                   |
  +-----------------------------------------------------------------------+
  |
  +--[STAGE 2: Transformación Bronze -> Silver (clientes y precios)]------+
  |                                                                       |
  |  transform_clients()            transform_energy_prices()             |
  |  silver_transform_clients.py    silver_transform_prices.py            |
  |  IN: manifest_clients.json      IN: manifest_ree.json                 |
  |  IN: clients_*.json             IN: prices_*.json                     |
  |  OUT: clean_clients (SQLite)    OUT: clean_prices (SQLite)            |
  +-----------------------------------------------------------------------+
  |
  +--[STAGE 3: Ingesta meteorológica (depende de clean_clients)]----------+
  |                                                                       |
  |  extract_openweather()                                                |
  |  bronze_ingest_weather_owm.py                                         |
  |  IN: clean_clients (lat, lon por cliente)                             |
  |  SRC: OWM API (5d/3h forecast)                                        |
  |  OUT: weather_{client_id}_*.json por cada cliente activo              |
  |  OUT: manifest_openweather.json                                       |
  +-----------------------------------------------------------------------+
  |
  +--[STAGE 4: Transformación meteorológica]------------------------------+
  |                                                                       |
  |  transform_openweather()                                              |
  |  silver_transform_weather.py                                          |
  |  IN: manifest_openweather.json                                        |
  |  IN: weather_{client_id}_*.json                                       |
  |  OUT: clean_weather (SQLite) — resampleado a 1h por cliente           |
  +-----------------------------------------------------------------------+
  |
  +--[STAGE 5: Motor físico PV]-------------------------------------------+
  |                                                                       |
  |  extract_generation_data()                                            |
  |  silver_calc_pv_generation.py + engine_pv_physics.py                  |
  |  IN: clean_clients JOIN clean_weather (unix_time >= now)              |
  |  CALC: posición solar (pvlib), GHI, Erbs, POA, Faiman, PR             |
  |  CALC: consumo industrial (modelo turnos + HVAC + variabilidad)       |
  |  OUT: clean_calculations (SQLite)                                     |
  +-----------------------------------------------------------------------+
  |
  +--[STAGE 6: Carga Gold — Star Schema (paralelo interno)]---------------+
  |                                                                       |
  |  load_dim_client()     load_dim_datetime()    load_dim_weather()      |
  |  gold_dim_clients.py   gold_dim_datetime.py   gold_dim_weather.py     |
  |  IN: clean_clients     IN: clean_weather       IN: clean_weather      |
  |  OUT: gold_dim_client  OUT: gold_dim_datetime  OUT: gold_dim_weather  |
  |                                                                       |
  |  load_fact_energy_forecast()                                          |
  |  gold_fact_energy_forecast.py                                         |
  |  IN: clean_calculations JOIN clean_weather JOIN clean_prices          |
  |  OUT: gold_fact_energy_forecast (upsert incremental)                  |
  +-----------------------------------------------------------------------+
  |
  +--[AUDITORÍA]----------------------------------------------------------+
  |                                                                       |
  |  save_etl_metadata()                                                  |
  |  audit_metadata.py                                                    |
  |  OUT: etl_metadata (SQLite) — status, duration, rows, errors          |
  +-----------------------------------------------------------------------+
  |
  FIN  -->  EXIT 0 (SUCCESS / PARTIAL SUCCESS) | EXIT 1 (FAILED)
```

---

### 1.2 Topología de Ejecución (DAG)

El pipeline implementa un **DAG secuencial con paralelismo lógico** en stages que no tienen dependencias de datos entre sí. La ejecución actual es monohilo (un `for` sobre la lista `PIPELINE`), pero la estructura de stages está diseñada para habilitar paralelismo real en futuras versiones.

```
Stage 1                 Stage 2                Stage 3
---------               ---------              ---------
extract_clients  -----> transform_clients
                                         \
                                          +------> extract_openweather
                                         /
extract_prices   -----> transform_prices


Stage 4                 Stage 5                Stage 6
---------               ---------              ---------
                                               load_dim_client
transform_openweather -> calc_pv_generation -> load_dim_datetime
                                               load_dim_weather
                                               load_fact_energy  (requiere los 3 dims)
```

**Reglas del DAG:**

| Stage | Puede comenzar cuando... | Falla si... |
|-------|--------------------------|-------------|
| Stage 1 | Siempre (inicio de pipeline) | Excel no existe o REE devuelve error HTTP no-5xx |
| Stage 2 | Stage 1 completado (parcial OK) | Manifest vacío o ficheros Bronze corruptos |
| Stage 3 | `clean_clients` disponible en SQLite | `clean_clients` vacía o sin coordenadas |
| Stage 4 | Stage 3 completado con al menos 1 fichero | Todos los ficheros Bronze de weather corruptos |
| Stage 5 | `clean_clients` y `clean_weather` disponibles | JOIN devuelve 0 filas para `unix_time >= now` |
| Stage 6 | Stage 5 completado con al menos 1 cálculo | `clean_calculations` vacía |

---

### 1.3 Dependencias entre Stages

```python
# pipeline_runner.py — definición del DAG
PIPELINE: list[tuple[int, str, Callable]] = [
    (1, "extract_clients",           bronze_ingest_clients.extract_clients),
    (1, "extract_energy_prices",     bronze_ingest_prices_ree.extract_energy_prices),
    (2, "transform_clients",         silver_transform_clients.transform_clients),
    (2, "transform_energy_prices",   silver_transform_prices.transform_energy_prices),
    (3, "extract_openweather",       bronze_ingest_weather_owm.extract_openweather),
    (4, "transform_openweather",     silver_transform_weather.transform_openweather),
    (5, "extract_generation_data",   silver_calc_pv_generation.extract_generation_data),
    (6, "gold_dim_clients",          gold_dim_clients.load_dim_client),
    (6, "gold_dim_datetime",         gold_dim_datetime.load_dim_datetime),
    (6, "gold_dim_weather",          gold_dim_weather.load_dim_weather),
    (6, "gold_fact_energy",          gold_fact_energy_forecast.load_fact_energy_forecast),
]
```

**Dependencias de datos implícitas:**

| Módulo consumidor | Dato requerido | Producido por |
|-------------------|---------------|---------------|
| `bronze_ingest_weather_owm` | `clean_clients` (lat, lon) | `silver_transform_clients` |
| `silver_calc_pv_generation` | `clean_clients` (parámetros PV) | `silver_transform_clients` |
| `silver_calc_pv_generation` | `clean_weather` (meteo horaria) | `silver_transform_weather` |
| `gold_fact_energy_forecast` | `clean_calculations` | `silver_calc_pv_generation` |
| `gold_fact_energy_forecast` | `clean_weather` | `silver_transform_weather` |
| `gold_fact_energy_forecast` | `clean_prices` | `silver_transform_prices` |
| `gold_dim_datetime` | `clean_weather` (unix_time únicos) | `silver_transform_weather` |
| `gold_dim_weather` | `clean_weather` (weather_id) | `silver_transform_weather` |

---

### 1.4 Orquestación y Scheduling

#### Orquestador actual

El pipeline se ejecuta mediante `pipeline_runner.py`, un orquestador ligero implementado en Python puro sin dependencias externas de scheduling.

```bash
# Ejecución completa
python src/pipeline_runner.py

# Arrancar desde un stage concreto (útil para re-procesar desde Silver)
python src/pipeline_runner.py --stage 3

# Dry-run: muestra el plan de ejecución sin ejecutar nada
python src/pipeline_runner.py --dry-run

# Combinado: dry-run desde stage 5
python src/pipeline_runner.py --stage 5 --dry-run
```

#### Scheduling recomendado (cron)

```cron
# Ejecución diaria a las 21:00 CET (20:00 UTC) — tras publicación de precios REE
0 20 * * * cd /path/to/sunsaver && venv/bin/python src/pipeline_runner.py >> logs/cron.log 2>&1

# Re-intento a las 22:00 UTC si el primero falla (precios REE pueden tardar)
0 22 * * * cd /path/to/sunsaver && venv/bin/python src/pipeline_runner.py --stage 2 >> logs/cron.log 2>&1
```

#### Scheduling en producción (roadmap)

| Herramienta | Ventaja | Caso de uso |
|-------------|---------|-------------|
| **Apache Airflow** | DAGs visuales, retry automático, alertas | Orquestación multi-tenant con múltiples pipelines |
| **Prefect** | Python-nativo, mínima infraestructura, UI moderna | Equipo pequeño, cloud-friendly |
| **GitHub Actions** | Sin infraestructura adicional | CI/CD + ejecución programada en repo |
| **cron + systemd** | Cero dependencias externas | Entorno DEV / servidor dedicado simple |

> **Decisión actual:** cron sobre servidor Linux. La interfaz CLI (`--stage`, `--dry-run`) facilita la migración futura a cualquier orquestador sin modificar el código del pipeline.

---

## 2. Capa de Ingesta — Bronze

### 2.1 Proceso de Extracción por Fuente

#### 2.1.1 SRC-001 — API REE PVPC (`bronze_ingest_prices_ree.py`)

**Estrategia de carga:** Full-load diario (D+1, 24 valores horarios).  
No existe paginación: la API devuelve el día completo en una única respuesta.

```python
# Construcción de la URL con fecha dinámica
tomorrow = (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d")
url = (
    "https://apidatos.ree.es/es/datos/mercados/precios-mercados-tiempo-real"
    f"?start_date={tomorrow}T00:00&end_date={tomorrow}T23:59"
    "&time_trunc=hour&geo_trunc=electric_system"
    "&geo_limit=peninsular&geo_ids=8741"
)
```

**Manejo de rate limits:**  
La API REE pública no documenta límites de tasa. Al ser una llamada diaria única, no existe riesgo de throttling. Si en el futuro se requieren múltiples llamadas (histórico), se recomienda un `sleep(1)` entre requests.

**Gestión de tokens / autenticación:**  
Sin autenticación requerida. La API es pública y accesible sin credenciales.

**Modo incremental vs full-load:**

| Modo | Aplicación | Justificación |
|------|-----------|---------------|
| **Full-load** | REE PVPC | El endpoint sólo devuelve D+1. No hay historial ni cursor. Cada ejecución es una carga completa del día siguiente. |

**Lógica de disponibilidad:**  
Los precios D+1 se publican típicamente después de las **20:30 CET**. El módulo detecta la indisponibilidad y retorna `False` (no lanza excepción), permitiendo que el orquestador marque la ejecución como `PARTIAL SUCCESS` y continúe con los demás stages.

```python
# Señalización de indisponibilidad sin excepción
if pvpc_item and pvpc_item["attributes"].get("values"):
    return all_data      # datos disponibles -> int
return False             # datos no publicados aún -> PARTIAL SUCCESS
```

**Códigos HTTP manejados:**

| Código | Tratamiento |
|--------|-------------|
| `200` | Procesar payload JSON |
| `500`, `502`, `503`, `504` | `return False` — datos no publicados aún |
| Otros 4xx/5xx | `return False` con log de error |
| Timeout (15s) | `return False` con log de error |

---

#### 2.1.2 SRC-002 — API OpenWeatherMap (`bronze_ingest_weather_owm.py`)

**Estrategia de carga:** Full-load diario **por cliente**. Una llamada a la API por cada instalación activa en `clean_clients`.

**Paginación:** No aplica. El endpoint `/forecast` devuelve los 40 tramos de 3h en una única respuesta JSON.

**Manejo de rate limits:**  
El plan gratuito permite 60 llamadas/minuto. Con N clientes, si N > 50, se recomienda añadir un `time.sleep(1.1)` entre llamadas para no superar el límite. Implementación actual: sin throttling explícito (adecuado para entornos DEV con pocos clientes).

```python
# Roadmap: throttling para producción con muchos clientes
import time
for _, row in df_clients.iterrows():
    raw_weather = extract_weather(row["latitude"], row["longitude"])
    time.sleep(1.1)  # Añadir en producción si N_clientes > 50
```

**Gestión de API Key:**  
La clave se carga desde el fichero `.env` mediante `python-dotenv`. La variable de entorno es `WEATHER_API_KEY`. Si no está definida, el módulo registra un error y devuelve `{}` sin lanzar excepción.

```python
API_KEY = os.getenv("WEATHER_API_KEY")
if not API_KEY:
    logger.error("[EXTRACT] WEATHER_API_KEY is not set — check .env")
    return {}
```

**Modo incremental vs full-load:**

| Modo | Aplicación | Justificación |
|------|-----------|---------------|
| **Full-load por cliente** | OWM Forecast | El endpoint devuelve siempre los próximos 5 días desde el momento de la llamada. No existe cursor ni delta. La idempotencia se garantiza en Silver mediante `INSERT OR REPLACE` por `(client_id, unix_time)`. |

---

#### 2.1.3 SRC-003 — Excel de Clientes (`bronze_ingest_clients.py`)

**Estrategia de carga:** Full-load manual. El fichero completo se lee y persiste en Bronze en cada ejecución que lo incluya.

**Paginación:** No aplica (fichero local).

**Modo incremental vs full-load:**

| Modo | Aplicación | Justificación |
|------|-----------|---------------|
| **Full-load** | Excel clientes | El fichero es pequeño (< 1.000 filas). La deduplicación por `client_id` con la ingesta más reciente se realiza en Silver. |

---

### 2.2 Escritura en Bronze

#### 2.2.1 Formato de Almacenamiento

Todos los ficheros Bronze se persisten como **JSON texto plano**, sin compresión, con indentación de 4 espacios para legibilidad en auditorías.

```python
with open(full_path, "w", encoding="utf-8") as fh:
    json.dump(records, fh, ensure_ascii=False, indent=4)

# Inmutabilidad inmediata tras escritura
os.chmod(full_path, stat.S_IRUSR | stat.S_IRGRP | stat.S_IROTH)  # 444
```

**Justificación del formato JSON:**
- Preservación exacta del schema de la fuente (sin pérdida de información)
- Legible sin herramientas especiales (auditoría directa con `cat` / editor de texto)
- Compatible con re-procesamiento desde cualquier punto del pipeline
- Sin dependencia de librerías de serialización binaria (Parquet, Avro)

> **Roadmap producción:** migrar a **JSONL comprimido (gzip)** o **Parquet** con particionado por fecha para reducir costes de almacenamiento y mejorar el rendimiento de lectura en volúmenes grandes.

#### 2.2.2 Estrategia de Particionado

El particionado actual es **plano por timestamp de ingesta** dentro de un único directorio `bronze/`:

```
bronze/
├── prices_20260510_203500.json       # partición implícita por fecha en el nombre
├── weather_C001_20260510_060000.json # partición implícita por cliente y fecha
└── clients_20260501_090000.json
```

**Particionado recomendado en producción** (Hive-style para compatibilidad con Spark/Athena):

```
bronze/
├── source=ree/
│   └── year=2026/month=05/day=10/
│       └── prices_20260510_203500.json
├── source=openweather/
│   └── year=2026/month=05/day=10/
│       ├── weather_C001_20260510_060000.json
│       └── weather_C002_20260510_060012.json
└── source=clients/
    └── year=2026/month=05/day=01/
        └── clients_20260501_090000.json
```

#### 2.2.3 Schema Evolution — Manejo de Cambios en API

La estrategia actual para gestionar cambios en el schema de las APIs externas es **schema-on-read**: los datos se persisten tal cual en Bronze y la lógica de parsing se centraliza en los módulos Silver.

| Tipo de cambio | Impacto Bronze | Acción requerida |
|----------------|---------------|-----------------|
| Campo nuevo en API | Ninguno — se persiste automáticamente | Actualizar parser Silver para aprovecharlo (opcional) |
| Campo renombrado | Los ficheros antiguos conservan el nombre viejo | Actualizar parser Silver con lógica de compatibilidad hacia atrás |
| Campo eliminado | Los ficheros nuevos ya no lo contienen | Añadir `df.get(campo, default)` en Silver; revisar campos críticos |
| Cambio de tipo | El JSON persiste el tipo nativo de la API | Silver ya aplica coerción explícita (`pd.to_numeric(errors='coerce')`) |
| Cambio de estructura raíz | Puede romper el parser Silver | Versionar el módulo Silver; re-procesar Bronze histórico si es necesario |

> **Recomendación:** ante cualquier cambio de estructura raíz en una API (ej. REE cambia `included[]` a `data[]`), crear un nuevo módulo Silver versionado (`silver_transform_prices_v2.py`) antes de desactivar el original. Los ficheros Bronze históricos siguen siendo válidos con el parser v1.

---

### 2.3 Idempotencia y Deduplicación

El pipeline garantiza **idempotencia a nivel de fichero Bronze** mediante dos mecanismos:

**Mecanismo 1 — Naming único por timestamp:**  
Cada fichero Bronze incluye el timestamp UTC de ingesta en su nombre. Si el pipeline se ejecuta dos veces en el mismo día, se crean dos ficheros distintos. La deduplicación se realiza en Silver al elegir el registro más reciente por clave primaria.

**Mecanismo 2 — Manifest de control:**  
El manifest `_process_manifest_*.json` registra el estado de cada fichero Bronze. Un fichero en estado `success` no se re-procesa en ejecuciones posteriores, evitando duplicados en Silver.

```json
// Ejemplo de entrada en _process_manifest_ree.json
{
    "source": "REE",
    "path": "/data/bronze/prices_20260510_203500.json",
    "status": "success",
    "created_at": "2026-05-10 20:35:00",
    "updated_at": "2026-05-10 20:35:12"
}
```

**Mecanismo 3 — Upsert en Silver:**  
Todas las tablas Silver utilizan `INSERT OR REPLACE` (SQLite) con claves primarias compuestas, garantizando que re-procesar el mismo fichero Bronze produzca exactamente el mismo resultado en Silver:

```python
# clean_weather: PK (client_id, unix_time)
# clean_prices:  PK (datetime_utc, price_type)
# clean_calculations: PK (client_id, unix_time)
conn.execute("INSERT OR REPLACE INTO clean_weather (...) VALUES (...)")
```

---

### 2.4 Control de Errores en Ingesta

#### 2.4.1 Dead Letter Queue / Error Store

El sistema implementa un **error store ligero** basado en el campo `status: "error"` del manifest Bronze, con el mensaje de error incluido:

```json
{
    "source": "openweather",
    "client_id": "C003",
    "path": "/data/bronze/weather_C003_20260510_060030.json",
    "status": "error",
    "error": "Transformation produced an empty DataFrame",
    "created_at": "2026-05-10 06:00:30",
    "updated_at": "2026-05-10 06:00:31"
}
```

Las tareas en estado `error` son **reintentadas automáticamente** en la siguiente ejecución del pipeline (el módulo Silver las incluye en `actionable = [t for t in all_tasks if t["status"] in ("pending", "error")]`).

> **Roadmap producción:** implementar un directorio `bronze/dead_letter/` donde se muevan los ficheros que fallen más de N reintentos, junto con un fichero de diagnóstico JSON con el stack trace completo.

#### 2.4.2 Política de Reintentos

**Comportamiento actual:**

| Módulo | Política de reintento |
|--------|----------------------|
| Bronze (extracción API) | Sin reintento automático en la misma ejecución. El fallo se registra en el manifest como `error` y se reintenta en la siguiente ejecución programada. |
| Silver (transformación) | Reintento automático en cada ejecución: todas las tareas en estado `pending` o `error` del manifest se procesan. |
| Gold (carga dimensional) | Idempotente: `DROP + CREATE + INSERT` (dims) o `INSERT OR REPLACE` (fact). Re-ejecutar siempre produce el resultado correcto. |

**Política de reintentos recomendada para producción (exponential backoff):**

```python
import time

def fetch_with_retry(url, headers, max_retries=3, base_delay=2):
    """
    Reintenta la llamada HTTP con backoff exponencial.
    Delays: 2s, 4s, 8s antes de rendirse.
    """
    for attempt in range(max_retries):
        try:
            response = requests.get(url, headers=headers, timeout=15)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.HTTPError as exc:
            if response.status_code in (429, 503):
                delay = base_delay ** (attempt + 1)
                logger.warning(
                    "[RETRY] Attempt %d/%d failed (HTTP %d) — retrying in %ds",
                    attempt + 1, max_retries, response.status_code, delay
                )
                time.sleep(delay)
            else:
                raise
    raise RuntimeError(f"Max retries ({max_retries}) exceeded for {url}")
```

#### 2.4.3 Alertas de Fallo de Fuente

**Alertas actuales (vía logger):**  
Todos los fallos de extracción se registran con nivel `ERROR` o `CRITICAL` en el fichero de log diario `logs/sunsaver_YYYY-MM-DD.log` y en `stderr` (consola).

**Alertas recomendadas en producción:**

| Evento | Nivel | Canal recomendado |
|--------|-------|-------------------|
| REE no publica precios antes de las 21:30 CET | WARNING | Slack / Email |
| OWM devuelve error para > 50% de clientes | ERROR | PagerDuty / Slack |
| Fallo total de Stage 1 (todos los extractores) | CRITICAL | PagerDuty + Email |
| `etl_metadata.status = 'FAILED'` | CRITICAL | Slack + Email |
| Fichero Bronze con 0 registros | WARNING | Slack |

```python
# Roadmap: hook de alerta al finalizar pipeline
def send_alert(status: str, error: str, channel: str = "slack"):
    if status in ("FAILED", "CRITICAL ERROR"):
        # POST a webhook de Slack / llamada a SNS / email via SES
        pass
```

---

## 3. Capa de Transformación — Silver

### 3.1 Proceso de Limpieza

#### 3.1.1 Normalización de Tipos

Todos los módulos Silver aplican coerción de tipos explícita antes de cualquier validación de negocio, evitando que tipos incorrectos del Excel o la API propaguen errores silenciosos a capas posteriores.

```python
# silver_transform_clients.py
numeric_cols = [
    "latitude", "longitude", "nominal_load_kw", "pv_peak_power_kw",
    "panel_area_m2", "efficiency", "loss_pct", "angle", "aspect",
    "battery_capacity_kwh", "soc_min_pct", "installation_cost_eur",
]
text_cols = ["client_id", "name", "description", "panel_type", "mounting", "timezone"]

for col in numeric_cols:
    df[col] = pd.to_numeric(df[col], errors="coerce")   # error -> NaN, no excepción
for col in text_cols:
    df[col] = df[col].astype(str).replace(["None", "nan", "NaN", "null"], np.nan)
```

**Tabla de conversiones por módulo:**

| Módulo Silver | Campo | Tipo Bronze | Tipo Silver | Función |
|---------------|-------|------------|------------|---------|
| `transform_clients` | `latitude` | ANY (Excel) | REAL | `pd.to_numeric(errors='coerce')` |
| `transform_clients` | `name` | STRING | TEXT (uppercase) | `str.upper().str.strip()` |
| `transform_clients` | `_ingested_at_utc` | STRING | DATETIME | `pd.to_datetime(errors='coerce')` |
| `transform_prices` | `datetime` | ISO 8601 | DATETIME (UTC-aware) | `pd.to_datetime(utc=True)` |
| `transform_prices` | `value` | FLOAT (JSON) | REAL | `float()` + validación outliers |
| `transform_weather` | `dt_txt` | STRING | DATETIME | `pd.to_datetime()` |
| `transform_weather` | `humidity` | INTEGER (JSON) | REAL | Conversión implícita en resample |

#### 3.1.2 Tratamiento de Nulos

La estrategia de nulos varía según la criticidad del campo:

| Categoría | Campos | Estrategia |
|-----------|--------|-----------|
| **Críticos — eliminar registro** | `client_id`, `name`, `latitude`, `longitude`, `pv_peak_power_kw`, `_ingested_at_utc` | `dropna(subset=críticos)` — registro descartado si alguno es nulo |
| **Numéricos PV — imputar con defecto físico** | `angle`, `aspect`, `loss_pct`, `efficiency`, `soc_min_pct` | Valor por defecto documentado (ej. `angle=30°`, `aspect=180°`) |
| **Numéricos económicos — imputar con cero** | `battery_capacity_kwh`, `installation_cost_eur`, `panel_area_m2` | `fillna(0)` — valor neutral para métricas económicas |
| **Categóricos — imputar con 'unknown'** | `description`, `panel_type`, `mounting`, `timezone` | `fillna('unknown')` o `fillna('UTC')` |
| **Meteorológicos numéricos — interpolación lineal** | `temp_celsius`, `humidity_pct`, `clouds_pct`, `wind_speed_mps` | `interpolate(method='linear')` tras resample horario |
| **Meteorológicos categóricos — forward fill** | `weather_id`, `weather_main`, `weather_description` | `ffill()` — propaga la última condición conocida |
| **Probabilidad de lluvia** | `rain_prob_norm` | `fillna(0)` — ausencia de dato = sin lluvia |

#### 3.1.3 Deduplicación Cruzada entre Fuentes

**Clientes:** deduplicación por `client_id` conservando la ingesta más reciente (última ejecución del pipeline gana).

```python
df = df.sort_values("_ingested_at_utc", ascending=False)
df = df.drop_duplicates(subset=["client_id"], keep="first")
```

**Precios:** deduplicación por `(price_type, datetime_utc)`. Si el mismo slot horario aparece en dos ficheros Bronze distintos (ej. re-ejecución), se conserva el más reciente.

**Meteorología:** deduplicación por `forecast_time_utc` antes del resample, luego `INSERT OR REPLACE` por `(client_id, unix_time)` en SQLite garantiza idempotencia en carga.

#### 3.1.4 Estandarización de Fechas y Zonas Horarias

**Regla universal del sistema:** todos los timestamps se almacenan en **UTC** en todas las capas Bronze y Silver. La conversión a hora local ocurre únicamente en Gold (`gold_dim_datetime`).

```python
# silver_transform_prices.py — normalización con UTC explícito
df["datetime_utc"] = pd.to_datetime(df["datetime_utc"], errors="coerce", utc=True)

# silver_transform_weather.py — sin tz-awareness (OWM ya devuelve UTC en dt_txt)
df_c["forecast_time_utc"] = pd.to_datetime(df_c["forecast_time_utc"])

# gold_dim_datetime.py — única conversión a hora local del sistema
SPAIN_TZ = ZoneInfo("Europe/Madrid")
dt_local  = dt_utc.astimezone(SPAIN_TZ)
```

**unix_time como clave de JOIN temporal:**  
Para evitar problemas de comparación entre timestamps con y sin timezone, todas las tablas Silver y Gold utilizan `unix_time` (INTEGER EPOCH UTC) como clave de JOIN temporal. Esto garantiza comparaciones exactas sin ambigüedad de zona horaria.

```python
# Cálculo de unix_time — mismo método en todos los módulos Silver
df["unix_time"] = (
    df["datetime_utc"]
    .dt.tz_localize(None)         # eliminar tz-awareness para conversión
    .astype("datetime64[s]")      # precisión de segundos
    .astype("int64")              # EPOCH INTEGER
)
```

---

### 3.2 Enriquecimiento de Datos

#### 3.2.1 Joins entre Fuentes

El join más crítico del sistema es el realizado en `silver_calc_pv_generation.py`:

```sql
-- JOIN clean_clients × clean_weather para ventana activa
SELECT c.*,
       w.unix_time, w.forecast_time_utc,
       w.temp_celsius, w.humidity_pct, w.clouds_pct,
       w.rain_prob_norm, w.wind_speed_mps,
       w.weather_id, w.weather_main, w.weather_description, w.is_daylight
FROM clean_clients AS c
INNER JOIN clean_weather AS w ON c.client_id = w.client_id
WHERE w.unix_time >= {now_unix}
```

**Características del JOIN:**
- Tipo: `INNER JOIN` — sólo se calculan clientes que tienen datos meteorológicos
- Clave: `client_id` (STRING) — relación 1:N (1 cliente, N slots horarios de forecast)
- Filtro temporal: `unix_time >= now` — sólo ventana activa (próximas 120h)
- Resultado: ~120 filas por cliente activo (120 horas de previsión a 1h de resolución)

**JOIN en Gold (fact table):**

```sql
-- gold_fact_energy_forecast.py — JOIN triple para enriquecimiento final
INSERT OR REPLACE INTO gold_fact_energy_forecast
SELECT
    c.client_id, c.unix_time, c.forecast_time_utc,
    c.pv_power_gen_kw, c.pv_performance_ratio, c.poa_wm2, c.t_cell_celsius,
    c.power_con_kw,
    w.temp_celsius, w.humidity_pct, w.clouds_pct, w.rain_prob_norm,
    w.wind_speed_mps, w.weather_id,
    pvpc.price_euro_mwh AS price_pvpc_eur_mwh,
    STRFTIME('%Y-%m-%d %H:%M:%S', 'now') AS _loaded_at_utc
FROM clean_calculations c
LEFT JOIN clean_weather w
    ON  w.client_id = c.client_id
    AND w.unix_time = c.unix_time
LEFT JOIN clean_prices pvpc
    ON  pvpc.unix_time  = c.unix_time
    AND pvpc.price_type = 'PVPC'
WHERE c.unix_time >= :start_unix
```

> Se usa `LEFT JOIN` para precios y meteorología: si no hay precio PVPC publicado aún (`PARTIAL SUCCESS`), el hecho se carga igualmente con `price_pvpc_eur_mwh = NULL`. El registro se actualiza automáticamente en la siguiente ejecución cuando el precio esté disponible.

#### 3.2.2 Cálculo de Campos Derivados — Motor Físico PV

El módulo `engine_pv_physics.py` implementa la cadena completa de cálculo físico de generación fotovoltaica. Es el componente de mayor complejidad técnica del sistema:

```
INPUTS (por slot horario y cliente):
  lat, lon, forecast_time_utc    → Posición solar (pvlib)
  clouds_pct, weather_id         → Irradiancia GHI (Haurwitz + Kasten-Czeplak)
  alfa, ghi                      → Descomposición DNI/DHI (modelo Erbs)
  dni, dhi, ghi, alfa, azimuth,
  angle, aspect                  → Irradiancia POA (beam + difusa + albedo)
  temp_celsius, wind_speed_mps,
  poa                            → Temperatura de célula (modelo Faiman)
  poa, t_cell, peak_power,
  loss_pct                       → Potencia AC + Performance Ratio
  forecast_time_utc, nominal_load_kw,
  temp_celsius                   → Consumo industrial (modelo turnos + HVAC)

OUTPUTS (por slot horario y cliente):
  alfa, azimuth                  → Posición solar (°)
  ghi                            → Global Horizontal Irradiance (W/m²)
  dni, dhi                       → Direct Normal / Diffuse Horizontal (W/m²)
  poa_wm2                        → Plane of Array irradiance (W/m²)
  t_cell_celsius                 → Temperatura de célula (°C)
  pv_power_gen_kw                → Potencia AC generada (kW)
  pv_performance_ratio           → Performance Ratio [0–1]
  power_con_kw                   → Consumo industrial estimado (kW)
```

**Cadena de cálculo con modelos físicos:**

| Paso | Función | Modelo físico | Librería |
|------|---------|--------------|---------|
| 1 | `calculate_solar_position()` | Algoritmo NREL SPA (pvlib) | `pvlib.solarposition` |
| 2 | `calculate_ghi()` | Haurwitz clear-sky + Kasten-Czeplak cloud attenuation + factor por código OWM | NumPy |
| 3 | `decompose_erbs()` | Modelo de Erbs (clearness index kt) | `pvlib.irradiance` |
| 4 | `calculate_total_poa()` | Liu-Jordan isotropic diffuse + beam + albedo (ρ=0.2) | `pvlib.irradiance.aoi` |
| 5 | `calculate_t_cell()` | Modelo Faiman (U0=24.9, U1=6.1) | NumPy |
| 6 | `calculate_power_output()` | Derating térmico (γ=−0.4%/°C) + pérdidas sistema | NumPy |
| 7 | `calculate_industrial_consumption()` | Modelo de turnos + HVAC + variabilidad gaussiana (σ=3%) | NumPy |

**Optimización del umbral solar:**  
Para evitar cálculos innecesarios durante la noche, se aplica un umbral de elevación solar mínima:

```python
alfa, azimuth = pvgen.calculate_solar_position(lat, lon, forecast_time_utc)

if alfa < 2:   # Umbral: elevación solar < 2° -> noche o amanecer/atardecer muy rasante
    ghi = dni = dhi = poa = p_gen = pr = 0.0
    t_cell = row["temp_celsius"]   # sin calentamiento por radiación
    # Sólo se calcula consumo (funciona 24h)
    p_con = pvgen.calculate_industrial_consumption(...)
else:
    # Cálculo completo de la cadena PV
    ...
```

#### 3.2.3 Lookup Tables y Datos de Referencia

| Lookup | Implementación | Uso |
|--------|---------------|-----|
| `weather_factors` | Dict Python en `engine_pv_physics.py` | Coeficiente de transmitancia por código OWM (thunderstorm=0.40, clear=1.00…) |
| `FESTIVOS_NACIONALES` | Set de tuplas `(mes, día)` en `gold_dim_datetime.py` | Determinación de festivos nacionales para cálculo de período tarifario P6 |
| `TARIFF_LABELS` | Dict Python en `gold_dim_datetime.py` | Mapeo `P1→punta`, `P2→llano`, `P3→valle`, `P6→super-valle` |
| `gold_dim_weather` | Tabla SQLite | Catálogo de condiciones OWM con descripción canónica (resuelta por frecuencia) |

---

### 3.3 Validación de Reglas de Negocio

Las reglas de negocio se validan en Silver antes de la carga. Los registros que no superan las reglas críticas se descartan con logging. Las reglas no críticas aplican imputación o corrección.

| ID | Regla | Severidad | Acción si falla |
|----|-------|-----------|-----------------|
| BV-01 | `pv_peak_power_kw > 0` | **CRÍTICA** | Descartar registro — no es una instalación PV válida |
| BV-02 | `latitude ∈ [-90, 90]` y `longitude ∈ [-180, 180]` | **CRÍTICA** | Descartar registro — coordenadas inválidas = sin datos meteo |
| BV-03 | `client_id` no nulo y no vacío | **CRÍTICA** | Descartar registro — sin clave primaria no se puede trackear |
| BV-04 | `angle ∈ [0, 90]` | CORRECTIVA | Imputar `30°` (inclinación estándar España) |
| BV-05 | `aspect ∈ [1, 360]` | CORRECTIVA | Imputar `180°` (orientación Sur óptima España) |
| BV-06 | `loss_pct ∈ [0, 90]` | CORRECTIVA | Imputar `14%` (valor típico de industria) |
| BV-07 | `efficiency ∈ [0, 1]` | CORRECTIVA | Imputar `0.15` (eficiencia típica panel monoSi) |
| BV-08 | `soc_min_pct ∈ [0, 90]` | CORRECTIVA | Imputar `20%` (límite mínimo típico de batería) |
| BV-09 | `price_euro_mwh ∈ [-100, 2000]` | FILTRADO | Eliminar registro — precio fuera de rango físico |
| BV-10 | `panel_area_m2 >= 0`, `battery_capacity_kwh >= 0`, `installation_cost_eur >= 0` | CORRECTIVA | Imputar `0` — valores negativos son errores de entrada |

---

### 3.4 Control de Versiones de Registros (SCD)

#### SCD Tipo 1 — Clientes (`clean_clients`, `gold_dim_client`)

Los datos de clientes implementan **Slowly Changing Dimension Tipo 1**: cuando un cliente se modifica en el Excel origen, la nueva versión sobreescribe completamente la anterior. No se mantiene historial de cambios.

```python
# Deduplicación en Silver: la ingesta más reciente gana
df = df.sort_values("_ingested_at_utc", ascending=False)
df = df.drop_duplicates(subset=["client_id"], keep="first")

# Carga en Gold: full rebuild (DROP + CREATE + INSERT)
conn.execute("DROP TABLE IF EXISTS gold_dim_client")
conn.execute("CREATE TABLE gold_dim_client (...)")
conn.execute("INSERT INTO gold_dim_client ...")
```

**Justificación:** en el contexto actual (entorno DEV, pocos clientes), el historial de cambios de configuración no es un requisito. En producción, si se necesita auditar cambios de parámetros PV (ej. sustitución de paneles), se recomienda migrar a SCD Tipo 2 añadiendo columnas `valid_from`, `valid_to` e `is_current`.

#### SCD Tipo 2 — Weather Dimension (`gold_dim_weather`)

La dimensión de condiciones meteorológicas implementa una **resolución de conflictos por frecuencia de observación** mediante `ROW_NUMBER() OVER (PARTITION BY weather_id ORDER BY COUNT(*) DESC)`:

```sql
-- gold_dim_weather.py — selección del par (main, description) más frecuente
SELECT weather_id, weather_main, weather_description
FROM (
    SELECT
        weather_id, weather_main, weather_description,
        COUNT(*) AS freq,
        ROW_NUMBER() OVER (
            PARTITION BY weather_id
            ORDER BY COUNT(*) DESC
        ) AS rn
    FROM clean_weather
    WHERE weather_id IS NOT NULL
    GROUP BY weather_id, weather_main, weather_description
)
WHERE rn = 1
```

---

## 4. Capa de Modelado — Gold

### 4.1 Proceso de Carga Dimensional

#### 4.1.1 Carga de Dimensiones — Estrategia por Tabla

| Dimensión | Estrategia | Módulo | Justificación |
|-----------|-----------|--------|---------------|
| `gold_dim_client` | `DROP + CREATE + INSERT` (full rebuild) | `gold_dim_clients.py` | Pocos registros (< 1.000). Full rebuild garantiza consistencia sin gestionar deltas. |
| `gold_dim_datetime` | `DROP + CREATE + INSERT` (full rebuild) | `gold_dim_datetime.py` | Generada a partir de los unix_time únicos de `clean_weather`. Reconstrucción determinista. |
| `gold_dim_weather` | `DROP + CREATE + INSERT` (full rebuild) | `gold_dim_weather.py` | Catálogo pequeño. La resolución de frecuencias requiere visión global de `clean_weather`. |

#### 4.1.2 Generación de Surrogate Keys

El sistema utiliza las **claves naturales de las fuentes** como claves primarias en Gold, sin surrogate keys artificiales (no hay secuencias o UUIDs generados):

| Tabla | Clave primaria | Tipo | Origen |
|-------|---------------|------|--------|
| `gold_dim_client` | `client_id` | TEXT | Excel clientes (natural key) |
| `gold_dim_datetime` | `unix_time` | INTEGER | EPOCH UTC calculado (natural key temporal) |
| `gold_dim_weather` | `weather_id` | INTEGER | Código OWM (natural key del proveedor) |
| `gold_fact_energy_forecast` | `(client_id, unix_time)` | TEXT + INTEGER | Clave compuesta natural |

> **Roadmap:** si se migra a un data warehouse con múltiples fuentes de datos de clientes, implementar surrogate keys con secuencias o hash deterministas (`MD5(client_id + source)`) para gestionar duplicados cross-source.

#### 4.1.3 Carga de la Tabla de Hechos

La tabla `gold_fact_energy_forecast` utiliza **upsert incremental** sobre una ventana temporal activa:

```python
# Ventana activa: unix_time >= now - 2h (buffer para re-procesar la hora actual)
buffer_seconds = 7200
start_unix = int(datetime.now(timezone.utc).timestamp()) - buffer_seconds

result = conn.execute("""
    INSERT OR REPLACE INTO gold_fact_energy_forecast
    SELECT ... FROM clean_calculations c
    LEFT JOIN clean_weather w ON w.client_id = c.client_id AND w.unix_time = c.unix_time
    LEFT JOIN clean_prices pvpc ON pvpc.unix_time = c.unix_time AND pvpc.price_type = 'PVPC'
    WHERE c.unix_time >= :start_unix
""", {"start_unix": start_unix})
```

**Índices para optimización de consultas:**

```sql
-- Creados de forma idempotente en cada carga Gold
CREATE INDEX IF NOT EXISTS idx_gold_fact_unix_time
    ON gold_fact_energy_forecast (unix_time);

CREATE INDEX IF NOT EXISTS idx_gold_fact_weather_id
    ON gold_fact_energy_forecast (weather_id);
```

#### 4.1.4 Agregaciones y Precálculos

El sistema no almacena tablas de agregación precalculadas en la versión actual. Las métricas de negocio se calculan en tiempo de consulta sobre `gold_fact_energy_forecast`. Ver sección [5.4 del catálogo de datos](02_DATA_CATALOG.md#54-métricas-de-negocio-precalculadas) para las fórmulas SQL disponibles.

> **Roadmap:** para dashboards con alta frecuencia de consulta, crear una tabla `gold_agg_daily_summary` con agregaciones por `(client_id, date)`: energía total generada, consumo total, coste total, horas en cada período tarifario, PR medio diario.

---

### 4.2 Estrategia de Actualización

| Tabla | Estrategia | Frecuencia | Ventana de datos |
|-------|-----------|-----------|-----------------|
| `gold_dim_client` | Full rebuild | 1/día (o al actualizar Excel) | Todos los clientes activos |
| `gold_dim_datetime` | Full rebuild | 1/día | unix_times únicos en `clean_weather` |
| `gold_dim_weather` | Full rebuild | 1/día | Todos los weather_ids en `clean_weather` |
| `gold_fact_energy_forecast` | Upsert incremental | 1/día | `unix_time >= now - 2h` (ventana activa) |

**Ventaja del upsert incremental en la tabla de hechos:**  
- Evita re-escribir registros históricos ya correctos
- Permite actualizar el precio PVPC cuando llega con retraso (el registro existente se reemplaza con el precio ya disponible)
- El buffer de 2 horas (`now - 7200s`) garantiza que la hora actual en curso también se actualiza

---

### 4.3 Gestión de Late-Arriving Data

El principal caso de datos tardíos en SunSaver es el **precio PVPC de REE**, que puede no estar disponible en la primera ejecución del pipeline (antes de las 20:30 CET).

**Flujo de gestión:**

```
Ejecución 1 (20:00 CET):
  extract_energy_prices() -> False (PARTIAL SUCCESS)
  gold_fact_energy_forecast cargado con price_pvpc_eur_mwh = NULL

Ejecución 2 (21:00 CET — re-intento cron):
  extract_energy_prices() -> 24 (datos disponibles)
  silver_transform_prices() -> clean_prices actualizada con 24 registros
  gold_fact_energy_forecast: INSERT OR REPLACE actualiza los registros
  con price_pvpc_eur_mwh ya disponible para cada unix_time
```

**Garantía:** el `INSERT OR REPLACE` sobre la clave compuesta `(client_id, unix_time)` garantiza que los registros con `price_pvpc_eur_mwh = NULL` se actualizan correctamente en la segunda ejecución sin duplicados.

---

## 5. Control de Ejecución

### 5.1 Checkpoints y Estado del Pipeline

El pipeline implementa tres niveles de checkpoint:

**Nivel 1 — Manifest Bronze (por fichero):**  
Cada fichero Bronze tiene su propio estado en el manifest JSON. Permite re-procesar ficheros individuales sin re-ejecutar el pipeline completo.

```json
{"path": "...", "status": "pending|success|error", "updated_at": "..."}
```

**Nivel 2 — Stage-level (por step del pipeline):**  
El orquestador `pipeline_runner.py` registra el resultado de cada step (`ok=True/False`, `rows=int`) y los acumula para el registro de auditoría final.

```python
stage_results.setdefault(stage_num, []).append(ok)

# Abort si todos los steps de un stage fallan
if not any(stage_results[stage_num]):
    pipeline_status = f"FAILED AT STAGE {stage_num}"
    return False
```

**Nivel 3 — Pipeline-level (registro de auditoría):**  
Al finalizar, `save_etl_metadata()` persiste el estado global en `etl_metadata`:

```
SUCCESS        -> Todos los steps completados sin errores
PARTIAL SUCCESS -> Al menos un step falló pero el pipeline continuó (ej. REE sin datos)
FAILED AT STAGE N -> Todos los steps de un stage fallaron; pipeline abortado
CRITICAL ERROR -> Excepción no controlada en el orquestador
```

**Re-arranque desde checkpoint:**

```bash
# Re-arrancar desde Silver si Bronze ya fue procesado correctamente
python src/pipeline_runner.py --stage 3

# Re-arrancar sólo Gold si Silver está íntegro
python src/pipeline_runner.py --stage 6
```

---

### 5.2 Paralelismo y Concurrencia

**Paralelismo actual:** secuencial (monohilo). El bucle `for stage_num, name, fn in PIPELINE` ejecuta cada step en serie.

**Paralelismo lógico disponible:**  
Los steps del mismo stage number no tienen dependencias de datos entre sí y podrían ejecutarse en paralelo:

| Stage | Steps paralelizables | Independencia |
|-------|---------------------|---------------|
| Stage 1 | `extract_clients` + `extract_energy_prices` | Sin dependencias entre sí |
| Stage 2 | `transform_clients` + `transform_energy_prices` | Leen manifests distintos; escriben tablas distintas |
| Stage 6 | `load_dim_client` + `load_dim_datetime` + `load_dim_weather` | Full rebuild independiente; `load_fact` debe ir después |

**Implementación de paralelismo en Stage 1 (roadmap):**

```python
from concurrent.futures import ThreadPoolExecutor, as_completed

stage_1_steps = [
    ("extract_clients",       bronze_ingest_clients.extract_clients),
    ("extract_energy_prices", bronze_ingest_prices_ree.extract_energy_prices),
]

with ThreadPoolExecutor(max_workers=2) as executor:
    futures = {executor.submit(fn): name for name, fn in stage_1_steps}
    for future in as_completed(futures):
        name = futures[future]
        result = future.result()
        # registrar resultado...
```

> **Consideración de concurrencia en SQLite:** SQLite no permite escrituras concurrentes sin `WAL mode`. Si se paraleliza la escritura en Silver o Gold, activar `PRAGMA journal_mode=WAL` antes de cualquier escritura concurrente.

---

### 5.3 Gestión de Dependencias de Datos

Las dependencias de datos entre stages se gestionan mediante **disponibilidad de tablas SQLite y ficheros en disco**, no mediante un sistema de dependencias explícito (como Airflow `XCom` o Prefect `result`).

**Verificación implícita de dependencias:**

```python
# Stage 3 depende de clean_clients — fallo controlado si está vacía
try:
    with sqlite3.connect(str(db_path)) as conn:
        df_clients = pd.read_sql("SELECT client_id, latitude, longitude FROM clean_clients", conn)
except Exception as exc:
    logger.error("[EXTRACT] Failed to read clients: %s", exc)
    return 0   # señaliza fallo al orquestador

# Stage 5 depende de clean_clients JOIN clean_weather — fallo controlado si JOIN vacío
df_merged = get_merged_silver_data()
if df_merged.empty:
    logger.warning("[INIT] No active forecast data — nothing to calculate")
    return 0
```

**Tabla de dependencias y comportamiento ante fallo upstream:**

| Stage | Depende de | Si upstream falla | Comportamiento downstream |
|-------|-----------|-------------------|--------------------------|
| Stage 3 | `clean_clients` | Stage 2 falló | `extract_openweather` devuelve `0`; pipeline continúa en `PARTIAL SUCCESS` |
| Stage 4 | `_process_manifest_openweather.json` | Stage 3 devuelve `0` | Manifest vacío → `transform_openweather` devuelve `0` |
| Stage 5 | `clean_clients` + `clean_weather` | Stages 2/4 fallaron | JOIN devuelve `0` filas → `extract_generation_data` devuelve `0` |
| Stage 6 | `clean_calculations` | Stage 5 devuelve `0` | `gold_fact_energy_forecast` carga `0` filas; dims se reconstruyen igualmente |

---

### 5.4 Watermarks y Ventanas Temporales

El pipeline gestiona dos tipos de ventanas temporales con semántica distinta:

**Ventana de previsión meteorológica (Bronze/Silver):**

```
Momento de extracción OWM: T0
Ventana de datos:          T0 → T0 + 120h (5 días)
Granularidad Bronze:       3 horas (40 tramos)
Granularidad Silver:       1 hora  (120 tramos tras interpolación)
```

**Ventana activa para cálculos PV (Silver → Gold):**

```python
# silver_calc_pv_generation.py
now_unix = int(datetime.now(timezone.utc).timestamp())
# Sólo se calculan slots futuros (unix_time >= ahora)
WHERE w.unix_time >= {now_unix}
```

**Watermark de carga Gold (con buffer):**

```python
# gold_fact_energy_forecast.py
buffer_seconds = 7200   # 2 horas de buffer
start_unix = int(datetime.now(timezone.utc).timestamp()) - buffer_seconds
# Procesa desde now-2h para incluir la hora en curso y la anterior
WHERE c.unix_time >= :start_unix
```

**Justificación del buffer de 2 horas:**  
- La hora actual puede estar a medias cuando se ejecuta el pipeline
- Los precios PVPC llegan con retraso y pueden actualizar registros recientes
- 2 horas garantiza que cualquier dato tardío de la última hora se re-procesa correctamente

**Diagrama de ventanas temporales:**

```
Timeline (UTC):
                                        NOW
                                         |
 T-2h          T-1h          T0          |          T+1h ... T+120h
  |             |             |          |             |          |
  +-------------+-------------+----------+-------------+----------+
  |<-------- Buffer Gold (2h) ---------->|
  |                                      |<---- Ventana activa PV cálculos ---->|
                                                        (forecast window: 5d)
```

---

## 6. Testing del Pipeline

> **Estado actual:** sin tests implementados. Este apartado define la **especificación técnica del plan de testing** a implementar en la siguiente iteración de desarrollo. Los ejemplos de código son plantillas listas para ejecutar con `pytest`.

---

### 6.1 Unit Tests — Transformaciones Individuales

Los unit tests verifican el comportamiento de cada función de transformación de forma aislada, usando datos sintéticos en memoria (sin acceso a APIs ni base de datos).

**Estructura de directorios propuesta:**

```
tests/
├── unit/
│   ├── test_engine_pv_physics.py       # Motor físico PV
│   ├── test_silver_transform_clients.py
│   ├── test_silver_transform_prices.py
│   ├── test_silver_transform_weather.py
│   ├── test_gold_dim_datetime.py       # Lógica tarifaria 3.0TD
│   └── conftest.py                     # Fixtures compartidos
├── integration/
│   └── test_pipeline_e2e.py
├── contracts/
│   └── test_data_contracts.py
└── regression/
    ├── fixtures/
    │   ├── sample_ree_response.json
    │   ├── sample_owm_response.json
    │   └── sample_clients.json
    └── test_regression.py
```

**Tests prioritarios del motor físico PV (`test_engine_pv_physics.py`):**

```python
import pytest
from engine_pv_physics import (
    calculate_solar_position, calculate_ghi, decompose_erbs,
    calculate_total_poa, calculate_t_cell, calculate_power_output,
    calculate_industrial_consumption
)

class TestSolarPosition:
    def test_elevation_positive_daytime(self):
        """El sol debe estar por encima del horizonte al mediodía solar en España."""
        alfa, azimuth = calculate_solar_position(
            latitude=40.0, longitude=-3.7,
            forecast_time_utc="2026-06-21 11:00:00"  # mediodía UTC, verano
        )
        assert alfa > 0, "Elevación debe ser positiva durante el día"
        assert 0 <= azimuth <= 360, "Azimut debe estar en [0, 360]"

    def test_elevation_negative_nighttime(self):
        """El sol debe estar bajo el horizonte a medianoche."""
        alfa, _ = calculate_solar_position(40.0, -3.7, "2026-06-21 00:00:00")
        assert alfa <= 0, "Elevación debe ser negativa o cero por la noche"

    def test_invalid_coordinates_returns_zero(self):
        """Coordenadas inválidas deben retornar (0.0, 0.0) sin excepción."""
        alfa, azimuth = calculate_solar_position(999.0, 999.0, "2026-06-21 12:00:00")
        assert alfa == 0.0 and azimuth == 0.0


class TestGHI:
    def test_ghi_zero_below_horizon(self):
        """GHI debe ser 0 cuando el sol está bajo el horizonte (alfa <= 0)."""
        assert calculate_ghi(alfa=-5.0, clouds_pct=0, weather_id=800) == 0.0

    def test_ghi_clear_sky_positive(self):
        """GHI debe ser positivo en cielo despejado con sol alto."""
        ghi = calculate_ghi(alfa=45.0, clouds_pct=0, weather_id=800)
        assert ghi > 0, "GHI debe ser positivo con cielo despejado"

    def test_ghi_reduced_by_clouds(self):
        """GHI con nubes debe ser menor que GHI con cielo despejado."""
        ghi_clear = calculate_ghi(45.0, clouds_pct=0, weather_id=800)
        ghi_cloudy = calculate_ghi(45.0, clouds_pct=80, weather_id=803)
        assert ghi_cloudy < ghi_clear

    @pytest.mark.parametrize("weather_id,expected_factor", [
        (800, 1.00),   # clear
        (803, 0.80),   # clouds_heavy
        (500, 0.70),   # rain
        (200, 0.40),   # thunderstorm
    ])
    def test_weather_factors(self, weather_id, expected_factor):
        """Verificar que los factores de transmitancia son correctos por tipo de tiempo."""
        ghi_clear    = calculate_ghi(45.0, 0, 800)
        ghi_weather  = calculate_ghi(45.0, 0, weather_id)
        ratio = ghi_weather / ghi_clear if ghi_clear > 0 else 0
        assert abs(ratio - expected_factor) < 0.01


class TestPowerOutput:
    def test_zero_poa_gives_zero_power(self):
        """Sin irradiancia no hay generación."""
        p_out, pr = calculate_power_output(poa=0, t_cell=25, peak_power=10, loss_pct=14)
        assert p_out == 0.0

    def test_thermal_derating_reduces_output(self):
        """A mayor temperatura de célula, menor potencia (derating térmico)."""
        p_25, _ = calculate_power_output(500, t_cell=25, peak_power=10, loss_pct=14)
        p_60, _ = calculate_power_output(500, t_cell=60, peak_power=10, loss_pct=14)
        assert p_60 < p_25, "Derating térmico debe reducir la potencia a alta temperatura"

    def test_output_never_negative(self):
        """La potencia de salida nunca puede ser negativa."""
        p_out, _ = calculate_power_output(poa=100, t_cell=80, peak_power=5, loss_pct=90)
        assert p_out >= 0.0


class TestTariffPeriod:
    """Tests para la lógica tarifaria 3.0TD en gold_dim_datetime."""
    from gold_dim_datetime import get_tariff_period
    from datetime import datetime
    from zoneinfo import ZoneInfo

    SPAIN = ZoneInfo("Europe/Madrid")

    @pytest.mark.parametrize("hour,expected_period", [
        (10, "P1"), (13, "P1"), (18, "P1"), (21, "P1"),  # punta
        ( 8, "P2"), ( 9, "P2"), (14, "P2"), (22, "P2"),  # llano
        ( 0, "P3"), ( 3, "P3"), ( 7, "P3"),              # valle
    ])
    def test_weekday_periods(self, hour, expected_period):
        """Verificar períodos tarifarios en día laborable (lunes)."""
        dt = datetime(2026, 5, 11, hour, 0, tzinfo=self.SPAIN)  # lunes
        assert get_tariff_period(dt) == expected_period

    def test_weekend_is_p6(self):
        """Sábado debe ser P6 (super-valle) a cualquier hora."""
        dt = datetime(2026, 5, 9, 14, 0, tzinfo=self.SPAIN)  # sábado
        assert get_tariff_period(dt) == "P6"

    def test_festivo_nacional_is_p6(self):
        """El 25 de diciembre debe ser P6 independientemente del día de la semana."""
        dt = datetime(2026, 12, 25, 10, 0, tzinfo=self.SPAIN)
        assert get_tariff_period(dt) == "P6"
```

**Tests de transformación Silver (`test_silver_transform_clients.py`):**

```python
import pandas as pd
import numpy as np
import pytest
from silver_transform_clients import transform_clients_bronze_to_silver

@pytest.fixture
def valid_client_df():
    return pd.DataFrame([{
        "client_id": "C001", "name": "planta norte",
        "latitude": 42.8, "longitude": -1.7,
        "pv_peak_power_kw": 16.0, "angle": 30.0, "aspect": 180.0,
        "loss_pct": 14.0, "efficiency": 0.20,
        "nominal_load_kw": 20.0, "panel_area_m2": 80.0,
        "panel_type": "monoSi", "mounting": "rooftop",
        "battery_capacity_kwh": 20.0, "soc_min_pct": 20.0,
        "installation_cost_eur": 18000.0, "timezone": "Europe/Madrid",
        "_ingested_at_utc": pd.Timestamp.now(tz="UTC"),
        "_source_file": "clients_test.json",
    }])

def test_name_uppercased(valid_client_df):
    result = transform_clients_bronze_to_silver(valid_client_df)
    assert result["name"].iloc[0] == "PLANTA NORTE"

def test_coordinates_rounded_to_6_decimals(valid_client_df):
    valid_client_df["latitude"] = 42.12345678
    result = transform_clients_bronze_to_silver(valid_client_df)
    assert result["latitude"].iloc[0] == round(42.12345678, 6)

def test_negative_pv_power_discarded():
    """Registros con pv_peak_power_kw <= 0 deben ser descartados."""
    df = pd.DataFrame([{
        "client_id": "C999", "name": "bad", "latitude": 40.0, "longitude": -3.0,
        "pv_peak_power_kw": -5.0, "_ingested_at_utc": pd.Timestamp.now(tz="UTC"),
        "angle": 30.0, "aspect": 180.0, "loss_pct": 14.0,
    }])
    result = transform_clients_bronze_to_silver(df)
    assert len(result) == 0, "Registro con potencia negativa debe ser descartado"

def test_missing_angle_imputed(valid_client_df):
    valid_client_df["angle"] = None
    result = transform_clients_bronze_to_silver(valid_client_df)
    assert result["angle"].iloc[0] == 30.0

def test_empty_dataframe_returns_empty():
    result = transform_clients_bronze_to_silver(pd.DataFrame())
    assert result.empty
```

---

### 6.2 Integration Tests — Flujo End-to-End

Los integration tests verifican el flujo completo desde Bronze hasta Gold usando datos de prueba ficticios, sin llamar a APIs reales.

```python
# tests/integration/test_pipeline_e2e.py
import os
import json
import sqlite3
import tempfile
import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock

@pytest.fixture(scope="module")
def temp_environment(tmp_path_factory):
    """Crea un entorno aislado con directorios Bronze y DB temporal."""
    base = tmp_path_factory.mktemp("sunsaver_test")
    bronze_dir = base / "bronze"
    bronze_dir.mkdir()
    db_path = base / "sunsaver_test.db"

    # Sobrescribir rutas del proyecto apuntando al entorno temporal
    with patch("config_paths.get_db_path", return_value=db_path), \
         patch("config_paths.get_bronze_path", return_value=bronze_dir):
        yield {"bronze": bronze_dir, "db": db_path, "base": base}


def test_silver_clients_loaded(temp_environment):
    """Verificar que transform_clients carga correctamente clean_clients."""
    from silver_transform_clients import transform_clients

    # Preparar fixture Bronze
    bronze_dir = temp_environment["bronze"]
    clients_data = [{"client_id": "T001", "name": "Test Plant", "latitude": 40.0,
                     "longitude": -3.0, "pv_peak_power_kw": 10.0}]
    fixture_path = bronze_dir / "clients_20260101_000000.json"
    fixture_path.write_text(json.dumps(clients_data))

    manifest = [{"source": "clients_source.xlsx", "path": str(fixture_path),
                 "status": "pending", "created_at": "2026-01-01 00:00:00",
                 "updated_at": "2026-01-01 00:00:00"}]
    (bronze_dir / "_process_manifest_clients.json").write_text(json.dumps(manifest))

    rows = transform_clients()
    assert rows > 0, "transform_clients debe retornar filas procesadas"

    with sqlite3.connect(str(temp_environment["db"])) as conn:
        count = conn.execute("SELECT COUNT(*) FROM clean_clients").fetchone()[0]
    assert count == 1


def test_gold_dim_client_matches_silver(temp_environment):
    """gold_dim_client debe tener el mismo número de registros que clean_clients."""
    from gold_dim_clients import load_dim_client

    rows_gold = load_dim_client()
    with sqlite3.connect(str(temp_environment["db"])) as conn:
        rows_silver = conn.execute("SELECT COUNT(*) FROM clean_clients").fetchone()[0]

    assert rows_gold == rows_silver


@patch("bronze_ingest_prices_ree.requests.get")
def test_partial_success_when_ree_unavailable(mock_get):
    """Cuando REE devuelve 503, el pipeline debe continuar en PARTIAL SUCCESS."""
    mock_get.return_value = MagicMock(status_code=503)
    mock_get.return_value.raise_for_status.side_effect = Exception("503")

    from bronze_ingest_prices_ree import extract_energy_prices
    result = extract_energy_prices()
    assert result is False, "extract_energy_prices debe retornar False con error 503"
```

---

### 6.3 Data Contract Tests

Los data contract tests verifican que los datos producidos por el pipeline cumplen los schemas y constraints documentados en el catálogo, actuando como guardianes de la calidad de datos en el límite entre capas.

```python
# tests/contracts/test_data_contracts.py
import sqlite3
import pytest

@pytest.fixture
def db_conn(db_path):
    """Conexión a la base de datos de test."""
    with sqlite3.connect(str(db_path)) as conn:
        conn.row_factory = sqlite3.Row
        yield conn


class TestSilverContracts:

    def test_clean_clients_no_null_primary_key(self, db_conn):
        """client_id nunca debe ser NULL en clean_clients."""
        count = db_conn.execute(
            "SELECT COUNT(*) FROM clean_clients WHERE client_id IS NULL"
        ).fetchone()[0]
        assert count == 0, f"Encontrados {count} registros con client_id NULL"

    def test_clean_clients_pv_peak_power_positive(self, db_conn):
        """pv_peak_power_kw siempre debe ser > 0."""
        count = db_conn.execute(
            "SELECT COUNT(*) FROM clean_clients WHERE pv_peak_power_kw <= 0"
        ).fetchone()[0]
        assert count == 0

    def test_clean_clients_lat_lon_valid_range(self, db_conn):
        """Coordenadas deben estar en rangos geográficos válidos."""
        count = db_conn.execute("""
            SELECT COUNT(*) FROM clean_clients
            WHERE latitude NOT BETWEEN -90 AND 90
               OR longitude NOT BETWEEN -180 AND 180
        """).fetchone()[0]
        assert count == 0

    def test_clean_weather_no_duplicate_pk(self, db_conn):
        """La PK (client_id, unix_time) debe ser única en clean_weather."""
        duplicates = db_conn.execute("""
            SELECT client_id, unix_time, COUNT(*) as cnt
            FROM clean_weather
            GROUP BY client_id, unix_time
            HAVING cnt > 1
        """).fetchall()
        assert len(duplicates) == 0, f"Duplicados en clean_weather PK: {len(duplicates)}"

    def test_clean_prices_euro_mwh_in_valid_range(self, db_conn):
        """Precios PVPC deben estar en rango físicamente plausible."""
        count = db_conn.execute("""
            SELECT COUNT(*) FROM clean_prices
            WHERE price_euro_mwh < -100 OR price_euro_mwh > 2000
        """).fetchone()[0]
        assert count == 0

    def test_clean_weather_unix_time_is_future(self, db_conn):
        """clean_weather sólo debe contener datos futuros tras el pipeline."""
        import time
        now = int(time.time()) - 86400  # tolerancia de 1 día
        count = db_conn.execute(
            "SELECT COUNT(*) FROM clean_weather WHERE unix_time < ?", (now,)
        ).fetchone()[0]
        assert count == 0, f"{count} registros en clean_weather son del pasado"


class TestGoldContracts:

    def test_gold_fact_references_valid_clients(self, db_conn):
        """Todos los client_id en gold_fact deben existir en gold_dim_client."""
        orphans = db_conn.execute("""
            SELECT COUNT(*) FROM gold_fact_energy_forecast f
            LEFT JOIN gold_dim_client c ON f.client_id = c.client_id
            WHERE c.client_id IS NULL
        """).fetchone()[0]
        assert orphans == 0, f"{orphans} filas huérfanas en gold_fact (client_id inválido)"

    def test_gold_fact_references_valid_datetime(self, db_conn):
        """Todos los unix_time en gold_fact deben existir en gold_dim_datetime."""
        orphans = db_conn.execute("""
            SELECT COUNT(*) FROM gold_fact_energy_forecast f
            LEFT JOIN gold_dim_datetime d ON f.unix_time = d.unix_time
            WHERE d.unix_time IS NULL
        """).fetchone()[0]
        assert orphans == 0

    def test_gold_dim_datetime_tariff_period_valid(self, db_conn):
        """tariff_period sólo puede contener valores P1, P2, P3 o P6."""
        invalid = db_conn.execute("""
            SELECT COUNT(*) FROM gold_dim_datetime
            WHERE tariff_period NOT IN ('P1','P2','P3','P6')
        """).fetchone()[0]
        assert invalid == 0

    def test_gold_fact_pv_power_non_negative(self, db_conn):
        """La potencia generada nunca puede ser negativa."""
        count = db_conn.execute("""
            SELECT COUNT(*) FROM gold_fact_energy_forecast
            WHERE pv_power_gen_kw < 0
        """).fetchone()[0]
        assert count == 0
```

---

### 6.4 Regression Tests con Datasets de Referencia

Los regression tests utilizan snapshots de datos reales o semirreales para verificar que los cálculos físicos del motor PV producen resultados numéricos estables ante cambios de código.

```python
# tests/regression/test_regression.py
import pytest
import json
from pathlib import Path
from engine_pv_physics import (
    calculate_solar_position, calculate_ghi, decompose_erbs,
    calculate_total_poa, calculate_t_cell, calculate_power_output
)

FIXTURES_DIR = Path(__file__).parent / "fixtures"

@pytest.fixture
def reference_scenario():
    """
    Escenario de referencia documentado:
    Instalación en Pamplona (lat=42.80, lon=-1.70)
    Fecha: 2026-05-01 15:00 UTC (verano, tarde)
    Panel: 16 kWp, angle=30°, aspect=180°, loss=14%
    Meteo: clouds=82%, weather_id=803, temp=20.29°C, wind=5.54 m/s
    """
    return {
        "lat": 42.803852, "lon": -1.701962,
        "forecast_time": "2026-05-01 15:00:00",
        "peak_power": 16.0, "loss_pct": 14.0,
        "angle": 30.0, "aspect": 180.0,
        "clouds_pct": 82.0, "weather_id": 803,
        "temp_celsius": 20.29, "wind_speed": 5.54,
        # Resultados esperados (calculados y validados manualmente)
        "expected_alfa_min": 30.0,      # elevación solar > 30° a las 15 UTC en mayo
        "expected_alfa_max": 60.0,
        "expected_ghi_min": 100.0,      # cielo parcialmente nublado -> GHI reducido
        "expected_ghi_max": 500.0,
        "expected_power_min": 1.0,      # generación positiva con cielo parcial
        "expected_power_max": 10.0,     # nunca supera el pico (16 kWp * PR)
    }


def test_regression_solar_position(reference_scenario):
    """La posición solar para el escenario de referencia debe estar en rango esperado."""
    s = reference_scenario
    alfa, azimuth = calculate_solar_position(s["lat"], s["lon"], s["forecast_time"])
    assert s["expected_alfa_min"] <= alfa <= s["expected_alfa_max"], \
        f"Elevación solar {alfa:.2f}° fuera del rango esperado"
    assert 180 <= azimuth <= 270, \
        f"Azimut {azimuth:.2f}° no corresponde a tarde (SO) en el hemisferio norte"


def test_regression_power_output(reference_scenario):
    """La potencia generada para el escenario de referencia debe estar en rango esperado."""
    s = reference_scenario
    alfa, azimuth = calculate_solar_position(s["lat"], s["lon"], s["forecast_time"])
    ghi  = calculate_ghi(alfa, s["clouds_pct"], s["weather_id"])
    dni, dhi = decompose_erbs(ghi, alfa, s["forecast_time"])
    poa  = calculate_total_poa(dni, dhi, ghi, alfa, azimuth, s["angle"], s["aspect"])
    t_cell = calculate_t_cell(s["temp_celsius"], s["wind_speed"], poa)
    p_out, pr = calculate_power_output(poa, t_cell, s["peak_power"], s["loss_pct"])

    assert s["expected_power_min"] <= p_out <= s["expected_power_max"], \
        f"Potencia {p_out:.3f} kW fuera del rango esperado [{s['expected_power_min']}, {s['expected_power_max']}]"
    assert 0.5 <= pr <= 1.0, \
        f"Performance Ratio {pr:.3f} fuera del rango físico plausible"


def test_regression_golden_dataset():
    """
    Comprueba que el motor PV produce resultados idénticos a los del dataset golden.
    El fichero golden_output.json se genera una vez y se versiona en el repositorio.
    Cualquier desviación indica un cambio de comportamiento no intencionado.
    """
    golden_path = FIXTURES_DIR / "golden_output.json"
    if not golden_path.exists():
        pytest.skip("Golden dataset no generado aún — ejecutar generate_golden.py primero")

    with open(golden_path) as f:
        golden = json.load(f)

    for record in golden:
        alfa, azimuth = calculate_solar_position(
            record["lat"], record["lon"], record["forecast_time"]
        )
        ghi = calculate_ghi(alfa, record["clouds_pct"], record["weather_id"])
        dni, dhi = decompose_erbs(ghi, alfa, record["forecast_time"])
        poa = calculate_total_poa(
            dni, dhi, ghi, alfa, azimuth, record["angle"], record["aspect"]
        )
        t_cell = calculate_t_cell(record["temp_celsius"], record["wind_speed"], poa)
        p_out, _ = calculate_power_output(poa, t_cell, record["peak_power"], record["loss_pct"])

        assert abs(p_out - record["expected_power"]) < 0.001, \
            f"Regresión detectada en {record['forecast_time']}: " \
            f"calculado={p_out:.4f}, esperado={record['expected_power']:.4f}"
```

**Comandos de ejecución del plan de testing:**

```bash
# Instalar dependencias de testing
pip install pytest pytest-cov pytest-mock --break-system-packages

# Ejecutar todos los tests
pytest tests/ -v

# Sólo unit tests (rápidos, sin BD)
pytest tests/unit/ -v

# Sólo data contracts (requiere BD poblada)
pytest tests/contracts/ -v

# Con cobertura de código
pytest tests/unit/ --cov=src --cov-report=term-missing

# Generar reporte HTML de cobertura
pytest tests/ --cov=src --cov-report=html:coverage_html/
```

**Cobertura objetivo por módulo:**

| Módulo | Cobertura objetivo | Prioridad |
|--------|-------------------|-----------|
| `engine_pv_physics.py` | > 95% | CRÍTICA — corazón del sistema |
| `silver_transform_clients.py` | > 90% | ALTA — reglas de negocio |
| `silver_transform_prices.py` | > 85% | ALTA — lógica de outliers |
| `silver_transform_weather.py` | > 85% | ALTA — interpolación crítica |
| `gold_dim_datetime.py` | > 90% | ALTA — lógica tarifaria |
| `bronze_ingest_prices_ree.py` | > 75% | MEDIA — integración externa |
| `bronze_ingest_weather_owm.py` | > 75% | MEDIA — integración externa |
| `pipeline_runner.py` | > 70% | MEDIA — orquestación |
| `audit_metadata.py` | > 80% | MEDIA — auditoría |

---

*SunSaver ETL · Especificación Técnica del Pipeline v1.0.0 · Mayo 2026*  
*Clasificación: INTERNA · No distribuir fuera del equipo sin autorización*
