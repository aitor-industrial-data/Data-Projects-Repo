# ☀️ SunSaver ETL — Catálogo de Datos
# 02 CATALOGO DE DATOS

> **Clasificación:** INTERNA &nbsp;|&nbsp; **Estado:** ACTIVO — Entorno DEV &nbsp;|&nbsp; **Pipeline:** `SunSaver_ETL`  
> **Propietario:** Equipo de Datos — SunSaver &nbsp;|&nbsp; **Última actualización:** 2026-05-11

---

## Tabla de Contenidos

1. [Introducción al Catálogo](#1-introducción-al-catálogo)
   - 1.1 [Propósito y Alcance](#11-propósito-y-alcance)
   - 1.2 [Convenciones de Nomenclatura](#12-convenciones-de-nomenclatura)
   - 1.3 [Proceso de Actualización del Catálogo](#13-proceso-de-actualización-del-catálogo)
2. [Fuentes de Datos](#2-fuentes-de-datos)
   - 2.1 [API REE — Precios PVPC](#21-api-ree--precios-pvpc)
   - 2.2 [API OpenWeatherMap — Previsión Meteorológica](#22-api-openweathermap--previsión-meteorológica-5-días)
   - 2.3 [Fichero Excel — Maestro de Clientes](#23-fichero-excel--maestro-de-clientes)
3. [Capa Bronze — Raw Data](#3-capa-bronze--raw-data)
   - 3.1 [Política de Retención](#31-política-de-retención)
   - 3.2 [Estructura de Directorios](#32-estructura-de-directorios-y-particionado)
   - 3.3 [Schemas Bronze por Fuente](#33-schemas-bronze-por-fuente)
   - 3.4 [Metadatos de Ingesta](#34-metadatos-de-ingesta)
4. [Capa Silver — Curated Data](#4-capa-silver--curated-data)
   - 4.1 [Reglas de Normalización](#41-reglas-de-normalización-aplicadas)
   - 4.2 [Campos Derivados y Calculados](#42-campos-derivados-y-calculados)
   - 4.3 [Mapeo Bronze → Silver](#43-mapeo-bronze--silver-por-entidad)
   - 4.4 [Schemas Silver](#44-schemas-silver-tipos-homogeneizados)
5. [Capa Gold — Star Schema](#5-capa-gold--star-schema)
   - 5.1 [Tablas de Hechos](#51-tablas-de-hechos)
   - 5.2 [Dimensiones](#52-dimensiones)
   - 5.3 [Diccionario de Datos Gold](#53-diccionario-de-datos-completo--gold)
   - 5.4 [Métricas de Negocio](#54-métricas-de-negocio-precalculadas)
6. [Data Lineage](#6-data-lineage--trazabilidad-end-to-end)
   - 6.1 [Diagrama de Linaje](#61-diagrama-de-linaje-end-to-end)
   - 6.2 [Trazabilidad Campo a Campo](#62-tabla-de-trazabilidad-campo-a-campo)
   - 6.3 [Análisis de Impacto](#63-análisis-de-impacto-de-cambios-en-fuente)
7. [Clasificación y Gobernanza](#7-clasificación-y-gobernanza-del-dato)
   - 7.1 [Clasificación por Sensibilidad](#71-clasificación-por-sensibilidad)
   - 7.2 [Datos PII o Regulados](#72-datos-pii-o-regulados)
   - 7.3 [Propietarios de Dominio](#73-propietarios-de-dominio-por-tabla)
   - 7.4 [Tabla de Auditoría del Pipeline](#74-tabla-de-auditoría-del-pipeline-etl_metadata)

---

## 1. Introducción al Catálogo

### 1.1 Propósito y Alcance

El **Catálogo de Datos de SunSaver** es el documento de referencia único *(Single Source of Truth)* para todo el inventario de datos que fluye a través del pipeline ETL del proyecto. Su objetivo es proporcionar transparencia completa sobre el origen, transformación, calidad y uso de cada dato gestionado por el sistema, habilitando una toma de decisiones basada en datos fiables y auditables.

**SunSaver** es una plataforma de gestión energética industrial que integra tres fuentes heterogéneas de información:

- **Previsiones meteorológicas** de 5 días (temperatura, irradiancia, viento, nubosidad)
- **Precios de electricidad** horarios del mercado PVPC español (D+1)
- **Configuración técnica** de instalaciones fotovoltaicas industriales

Con estos datos, el sistema calcula hora a hora la **generación exacta** de cada parque PV, el **consumo estimado** de cada instalación y el **precio exacto** de la energía en ese slot, permitiendo optimizar decisiones de gestión energética flexible:

- Cuándo cargar las baterías al menor coste
- Cuál es la mejor hora para arrancar maquinaria de alto consumo
- En qué franjas horarias el excedente fotovoltaico es suficiente para diferir cargas
- Cuánto vale económicamente la energía autoconsumida frente a la de red

**Alcance del catálogo:**

| Ámbito | Detalle |
|--------|---------|
| Fuentes externas | 3 (API REE, API OpenWeatherMap, Excel clientes) |
| Capas de almacenamiento | 3 (Bronze, Silver, Gold) |
| Tablas de base de datos | 8 tablas SQLite + 1 tabla de auditoría |
| Ficheros Bronze | 3 tipos de JSON + 3 manifests de control |
| Módulos Python cubiertos | 14 módulos del pipeline |

---

### 1.2 Convenciones de Nomenclatura

| Ámbito | Patrón | Ejemplo |
|--------|--------|---------|
| Ficheros Bronze — Precios | `prices_{YYYYmmdd_HHMMSS}.json` | `prices_20260510_203500.json` |
| Ficheros Bronze — Meteorología | `weather_{client_id}_{YYYYmmdd_HHMMSS}.json` | `weather_C001_20260510_060000.json` |
| Ficheros Bronze — Clientes | `clients_{YYYYmmdd_HHMMSS}.json` | `clients_20260501_090000.json` |
| Manifests de control | `_process_manifest_{fuente}.json` | `_process_manifest_ree.json` |
| Tablas Silver | `clean_{entidad}` | `clean_clients`, `clean_weather` |
| Tablas Gold — Dimensión | `gold_dim_{entidad}` | `gold_dim_client`, `gold_dim_datetime` |
| Tablas Gold — Hecho | `gold_fact_{proceso}` | `gold_fact_energy_forecast` |
| Módulos Python — Bronze | `bronze_ingest_{fuente}.py` | `bronze_ingest_prices_ree.py` |
| Módulos Python — Silver | `silver_transform_{entidad}.py` | `silver_transform_weather.py` |
| Módulos Python — Gold | `gold_{tipo}_{entidad}.py` | `gold_dim_clients.py` |
| Clave temporal universal | `unix_time` (INTEGER EPOCH UTC) | `1746874800` |
| Auditoría de carga | `_loaded_at_utc` / `_ingested_at_utc` | `2026-05-10 21:00:00` |

> **Regla de oro:** todos los timestamps del sistema se almacenan en **UTC**. La conversión a hora local (Europe/Madrid) se realiza únicamente en la capa Gold (`gold_dim_datetime`) para el cálculo de atributos tarifarios.

---

### 1.3 Proceso de Actualización del Catálogo

El catálogo debe actualizarse ante cualquiera de los siguientes eventos:

- Incorporación de una nueva fuente de datos o API
- Adición, renombrado o eliminación de campos en cualquier tabla Silver o Gold
- Cambio en reglas de negocio que afecten a campos derivados o calculados
- Modificación de la frecuencia de extracción o del SLA del proveedor
- Cambio en la clasificación de sensibilidad de algún dato
- Cualquier modificación en la lógica tarifaria (3.0TD)

> **Responsable de mantenimiento:** el equipo propietario del dominio de datos correspondiente debe validar y hacer merge del PR antes de publicar cambios en este catálogo. Los cambios se rastrean mediante el historial de commits de Git.

---

## 2. Fuentes de Datos

### 2.1 API REE — Precios PVPC

| Atributo | Valor |
|----------|-------|
| **Identificador** | `SRC-001 · REE-PVPC` |
| **Nombre completo** | Red Eléctrica de España — Precios Mercados Tiempo Real |
| **Proveedor** | Red Eléctrica de España (REE) — Organismo regulador del sistema eléctrico español |
| **URL base** | `https://apidatos.ree.es/es/datos/mercados/precios-mercados-tiempo-real` |
| **Tipo de dato** | Económico — Precio de electricidad PVPC horario (€/MWh) |
| **Autenticación** | Ninguna (API pública) |
| **Frecuencia de extracción** | 1 vez/día — precios D+1, disponibles a partir de las **20:30 CET** |
| **Horizonte temporal** | D+1 (mañana): 24 valores horarios (00:00–23:00 UTC) |
| **Volumen estimado** | 24 registros/día · ~8.760 registros/año |
| **Formato de respuesta** | JSON — API REST |
| **Filtro aplicado** | `id=1001` (PVPC peninsular), `geo_ids=8741`, `time_trunc=hour` |
| **Timeout** | 15 segundos |
| **Módulo de ingesta** | `bronze_ingest_prices_ree.py` → `extract_raw_json_from_ree()` |
| **SLA del proveedor** | Sin SLA publicado. Errores HTTP 500/502/503/504 tratados como *datos no disponibles aún*. El pipeline continúa en modo `PARTIAL SUCCESS`. |

#### 2.1.1 Campos extraídos de la API REE

| Campo API | Ruta JSON | Tipo nativo | Descripción |
|-----------|-----------|-------------|-------------|
| `id` | `included[].id` | STRING | Identificador de serie (siempre `"1001"` tras filtro) |
| `type` | `included[].type` | STRING | Tipo de mercado (etiqueta textual REE) |
| `datetime` | `included[].attributes.values[].datetime` | ISO 8601 | Timestamp UTC del slot horario |
| `value` | `included[].attributes.values[].value` | FLOAT | **Precio en €/MWh** para ese slot |
| `percentage` | `included[].attributes.values[].percentage` | FLOAT | Porcentaje sobre precio total (no utilizado downstream) |

> **Campos críticos de negocio:** `datetime` y `value`. Sin precio válido el pipeline opera en modo `PARTIAL SUCCESS` y continúa con las demás etapas. El precio PVPC es la referencia económica para el cálculo del coste energético horario y la decisión de carga de baterías o arranque de cargas flexibles.

---

### 2.2 API OpenWeatherMap — Previsión Meteorológica 5 días

| Atributo | Valor |
|----------|-------|
| **Identificador** | `SRC-002 · OWM-FORECAST` |
| **Nombre completo** | OpenWeatherMap — 5 Day / 3 Hour Forecast |
| **Proveedor** | OpenWeather Ltd. (openweathermap.org) |
| **URL base** | `https://api.openweathermap.org/data/2.5/forecast` |
| **Tipo de dato** | Meteorológico — Temperatura, nubosidad, viento, precipitación, humedad |
| **Autenticación** | API Key — variable de entorno `WEATHER_API_KEY` en fichero `.env` |
| **Frecuencia de extracción** | 1 vez/día **por cliente activo** |
| **Granularidad nativa** | Cada **3 horas** (40 tramos/cliente) → interpolado a **1 hora** en Silver |
| **Horizonte temporal** | 120 horas (5 días) = 40 tramos de 3h por cliente |
| **Volumen estimado** | 40 registros brutos × N_clientes/día → ~120 registros/hora tras interpolación por cliente |
| **Formato de respuesta** | JSON — REST |
| **Parámetros de llamada** | `lat`, `lon` (por instalación), `units=metric`, `lang=en` |
| **Timeout** | 15 segundos |
| **Módulo de ingesta** | `bronze_ingest_weather_owm.py` → `extract_weather()` |
| **Fichero Bronze** | `weather_{client_id}_{timestamp}.json` (chmod 444) |
| **SLA del proveedor** | Plan gratuito: 60 llamadas/min, 1.000.000 llamadas/mes. Plan de pago: 99,9%. Sin datos históricos en este endpoint. |

#### 2.2.1 Campos extraídos de OpenWeatherMap

| Campo API | Ruta JSON | Tipo nativo | Descripción |
|-----------|-----------|-------------|-------------|
| `dt_txt` | `list[].dt_txt` | STRING | Timestamp UTC de previsión (`YYYY-MM-DD HH:MM:SS`) |
| `temp` | `list[].main.temp` | FLOAT | Temperatura en °C (`units=metric`) |
| `humidity` | `list[].main.humidity` | INTEGER | Humedad relativa (%) |
| `all` | `list[].clouds.all` | INTEGER | Cobertura de nube (%) |
| `pop` | `list[].pop` | FLOAT | Probabilidad de precipitación [0–1] |
| `speed` | `list[].wind.speed` | FLOAT | Velocidad de viento (m/s) |
| `id` | `list[].weather[0].id` | INTEGER | Código de condición meteorológica OWM |
| `main` | `list[].weather[0].main` | STRING | Categoría meteorológica (Clear, Rain, Snow…) |
| `description` | `list[].weather[0].description` | STRING | Descripción detallada |
| `pod` | `list[].sys.pod` | CHAR(1) | Part of Day: `'d'` (día) / `'n'` (noche) |

> **Campos críticos de negocio:** `temp`, `clouds.all`, `wind.speed` y `weather[0].id`. Estos cuatro campos alimentan directamente el motor físico PV (`engine_pv_physics.py`) para calcular la irradiancia GHI, la temperatura de célula (modelo Faiman) y la potencia generada hora a hora.

---

### 2.3 Fichero Excel — Maestro de Clientes

| Atributo | Valor |
|----------|-------|
| **Identificador** | `SRC-003 · CLIENTS-XLSX` |
| **Nombre del fichero** | `clients_source.xlsx` |
| **Ruta** | `data/clients_source.xlsx` |
| **Tipo de dato** | Maestro — Configuración técnica de instalaciones fotovoltaicas industriales |
| **Frecuencia de actualización** | Manual — al incorporar o modificar una instalación |
| **Formato** | Excel `.xlsx` con cabecera en la primera fila. Dependencia: `openpyxl` |
| **Volumen estimado** | < 1.000 filas (una por instalación/cliente) |
| **Módulo de ingesta** | `bronze_ingest_clients.py` → `extract_clients_from_excel()` |
| **Clasificación** | INTERNA — Nombres de instalación ficticios en DEV; coordenadas geográficas reales |

#### 2.3.1 Campos del fichero de clientes

| Campo Excel | Tipo esperado | Nullable | Descripción de negocio |
|-------------|---------------|----------|------------------------|
| `client_id` | STRING | **NO** | Identificador único de la instalación (clave primaria) |
| `name` | STRING | **NO** | Nombre de la instalación (ficticio en DEV) |
| `description` | STRING | SÍ | Descripción libre de la planta o proceso industrial |
| `latitude` | FLOAT | **NO** | Latitud geográfica real de la instalación (WGS84) |
| `longitude` | FLOAT | **NO** | Longitud geográfica real de la instalación (WGS84) |
| `timezone` | STRING | SÍ | Zona horaria IANA (ej. `Europe/Madrid`) |
| `nominal_load_kw` | FLOAT | SÍ | Consumo nominal máximo de la instalación (kW) |
| `pv_peak_power_kw` | FLOAT | **NO** | Potencia pico del parque fotovoltaico (kWp) |
| `panel_area_m2` | FLOAT | SÍ | Superficie total de paneles (m²) |
| `efficiency` | FLOAT | SÍ | Eficiencia del panel [0–1], ej. `0.20` = 20% |
| `panel_type` | STRING | SÍ | Tecnología: `monoSi`, `polySi`, `thin-film`… |
| `loss_pct` | FLOAT | SÍ | Pérdidas totales del sistema (%) — cableado + inversor + suciedad |
| `angle` | FLOAT | SÍ | Inclinación del panel respecto a la horizontal (0–90°) |
| `aspect` | FLOAT | SÍ | Orientación azimutal del panel (1–360°, 180° = Sur) |
| `mounting` | STRING | SÍ | Tipo de montaje: `rooftop`, `ground`, `tracker`… |
| `battery_capacity_kwh` | FLOAT | SÍ | Capacidad del sistema de almacenamiento (kWh), `0` si no tiene |
| `soc_min_pct` | FLOAT | SÍ | Estado de carga mínimo permitido de la batería (%) |
| `installation_cost_eur` | FLOAT | SÍ | Coste total de la instalación fotovoltaica (€) |

---

## 3. Capa Bronze — Raw Data

La capa Bronze implementa el principio de **inmutabilidad total**: cada payload recibido de una fuente externa se persiste tal cual en disco, sin ninguna modificación, y se protege con permisos de sólo lectura (`chmod 444`). Es la única fuente de verdad para auditoría y re-procesamiento.

### 3.1 Política de Retención

| Política | Detalle |
|----------|---------|
| **Inmutabilidad** | Todos los ficheros Bronze tienen permisos `chmod 444`. No se modifican ni eliminan una vez escritos. |
| **Retención mínima** | 90 días en DEV. En producción: mínimo 365 días para auditorías regulatorias. |
| **Re-procesamiento** | Cualquier fichero Bronze puede re-procesarse hacia Silver en caso de fallo. El manifest controla el estado de cada tarea. |
| **Naming con timestamp UTC** | El nombre del fichero incluye el timestamp de ingesta (`YYYYmmdd_HHMMSS` UTC), garantizando unicidad y trazabilidad temporal. |
| **Formato** | JSON texto plano. Sin compresión en DEV (recomendada en producción). |

---

### 3.2 Estructura de Directorios y Particionado

```
{PROJECT_ROOT}/
└── data/
    └── bronze/                                  <- configurable via BRONZE_PATH
        ├── prices_20260510_203500.json           <- Precios REE (inmutable)
        ├── prices_20260511_204100.json
        ├── weather_C001_20260510_060000.json     <- Meteorología por cliente (inmutable)
        ├── weather_C002_20260510_060012.json
        ├── clients_20260501_090000.json          <- Maestro clientes (inmutable)
        ├── _process_manifest_ree.json            <- Control de procesamiento REE
        ├── _process_manifest_openweather.json    <- Control de procesamiento OWM
        └── _process_manifest_clients.json        <- Control de procesamiento clientes
```

| Patrón de fichero | Fuente | Frecuencia | Ejemplo |
|-------------------|--------|------------|---------|
| `prices_{YYYYmmdd_HHMMSS}.json` | REE PVPC | 1/día | `prices_20260510_203500.json` |
| `weather_{client_id}_{YYYYmmdd_HHMMSS}.json` | OpenWeatherMap | 1/día × cliente | `weather_C001_20260510_060000.json` |
| `clients_{YYYYmmdd_HHMMSS}.json` | Excel clientes | Manual | `clients_20260501_090000.json` |
| `_process_manifest_ree.json` | Control interno | Continua | *(fichero de control — NO inmutable)* |
| `_process_manifest_openweather.json` | Control interno | Continua | *(fichero de control — NO inmutable)* |
| `_process_manifest_clients.json` | Control interno | Continua | *(fichero de control — NO inmutable)* |

> Los ficheros `_process_manifest_*.json` **no son inmutables**: registran el estado de procesamiento de cada tarea Bronze → Silver. Estados posibles: `pending` → `success` | `error`.

---

### 3.3 Schemas Bronze por Fuente

#### 3.3.1 Schema Bronze — Precios REE (`prices_*.json`)

Estructura: objeto JSON raíz con el payload completo de la API REE, filtrado al item `id=1001` (PVPC peninsular).

| Campo | Tipo nativo | Nullable | Descripción |
|-------|-------------|----------|-------------|
| `included[].id` | STRING | NO | Identificador de serie (siempre `"1001"`) |
| `included[].type` | STRING | NO | Tipo de mercado (etiqueta textual REE) |
| `included[].attributes.values[].datetime` | ISO 8601 STRING | NO | Timestamp UTC del slot horario |
| `included[].attributes.values[].value` | FLOAT | NO | **Precio en €/MWh** |
| `included[].attributes.values[].percentage` | FLOAT | SÍ | Porcentaje sobre precio total (no usado downstream) |

#### 3.3.2 Schema Bronze — Meteorología OWM (`weather_{client_id}_*.json`)

Estructura: objeto JSON raíz con `"list"` (array de 40 previsiones a 3h) y metadatos de ciudad.

| Campo | Tipo nativo | Nullable | Descripción |
|-------|-------------|----------|-------------|
| `list[].dt_txt` | STRING | NO | Timestamp UTC de previsión (`YYYY-MM-DD HH:MM:SS`) |
| `list[].main.temp` | FLOAT | NO | Temperatura (°C) |
| `list[].main.humidity` | INTEGER | NO | Humedad relativa (%) |
| `list[].clouds.all` | INTEGER | NO | Cobertura nubosa (%) |
| `list[].pop` | FLOAT | NO | Probabilidad de precipitación [0.0–1.0] |
| `list[].wind.speed` | FLOAT | NO | Velocidad del viento (m/s) |
| `list[].weather[0].id` | INTEGER | NO | Código OWM de condición meteorológica |
| `list[].weather[0].main` | STRING | NO | Categoría meteorológica (Clear, Rain, Snow…) |
| `list[].weather[0].description` | STRING | NO | Descripción detallada |
| `list[].sys.pod` | CHAR(1) | SÍ | Part of day: `'d'` / `'n'` |
| `city.coord.lat` | FLOAT | NO | Latitud de la localización consultada |
| `city.coord.lon` | FLOAT | NO | Longitud de la localización consultada |

#### 3.3.3 Schema Bronze — Clientes (`clients_*.json`)

Estructura: array JSON de objetos, uno por fila del Excel origen. Contiene todos los campos del apartado [2.3.1](#231-campos-del-fichero-de-clientes) en su tipo original (pueden llegar como string si el Excel tiene celdas de texto).

---

### 3.4 Metadatos de Ingesta

| Metadato | Origen | Tipo | Descripción |
|----------|--------|------|-------------|
| Nombre del fichero | `bronze_ingest_*.py` | STRING | Incluye entidad + timestamp UTC de escritura |
| `chmod 444` | `ingest_*_to_bronze()` | PERMISOS | Protección de escritura aplicada tras crear el fichero |
| `status` en manifest | `_process_manifest_*.json` | ENUM | `pending` → `success` \| `error` |
| `created_at` en manifest | `_update_manifest()` | DATETIME UTC | Momento de registro en el manifest |
| `updated_at` en manifest | `_update_manifest()` | DATETIME UTC | Actualizado al procesar en Silver |
| `path` en manifest | `_update_manifest()` | STRING | Ruta absoluta al fichero Bronze |
| `source` en manifest | `_update_manifest()` | STRING | `'REE'`, `'openweather'`, `'clients_source.xlsx'` |
| `client_id` en manifest (OWM) | `_update_manifest()` | STRING | Identificador de cliente para trazabilidad |

---

## 4. Capa Silver — Curated Data

La capa Silver aplica transformaciones de calidad sobre los datos Bronze: limpieza tipológica, validación de reglas de negocio, deduplicación, interpolación e imputación de nulos. El resultado son tablas SQLite estructuradas y verificadas, listas para alimentar el motor de cálculo físico y la capa Gold.

### 4.1 Reglas de Normalización Aplicadas

| # | Regla | Tablas afectadas | Implementación |
|---|-------|------------------|----------------|
| R01 | **Coerción de tipos** | Todas | `pd.to_numeric(errors='coerce')` para numéricos; `astype(str) + replace(['None','nan'])` para texto |
| R02 | **Eliminación de críticos nulos** | `clean_clients` | `dropna(subset=['client_id','name','latitude','longitude','pv_peak_power_kw'])` |
| R03 | **Validación rango geográfico** | `clean_clients` | `latitude ∈ [-90, 90]`; `longitude ∈ [-180, 180]` |
| R04 | **Validación rango físico PV** | `clean_clients` | `angle ∈ [0, 90]`; `aspect ∈ [1, 360]`; `loss_pct ∈ [0, 90]`; `efficiency ∈ [0, 1]` |
| R05 | **Imputación por defecto** | `clean_clients` | `angle=30°`, `aspect=180°` (Sur), `loss_pct=14%`, `efficiency=0.15` |
| R06 | **Deduplicación por PK** | `clean_clients`, `clean_prices`, `clean_weather` | `sort(_ingested_at_utc, desc) + drop_duplicates(PK, keep='first')` |
| R07 | **Interpolación lineal horaria** | `clean_weather` | `resample('1h').asfreq()` + `interpolate('linear')` en numéricos; `ffill()` en categóricos |
| R08 | **Filtrado de outliers de precio** | `clean_prices` | Eliminación de valores `< -100` o `> 2.000 €/MWh` |
| R09 | **Normalización de nombres** | `clean_clients` | `name.str.upper().str.strip()` |
| R10 | **Coordenadas redondeadas** | `clean_clients` | `latitude/longitude.round(6)` |
| R11 | **Cálculo de unix_time** | `clean_weather`, `clean_prices` | Conversión de `datetime` a EPOCH INTEGER para JOIN eficiente |

---

### 4.2 Campos Derivados y Calculados

| Campo derivado | Tabla | Fórmula / Lógica | Propósito |
|----------------|-------|------------------|-----------|
| `unix_time` | `clean_weather`, `clean_prices` | `(datetime_utc - 1970-01-01) // 1s → INTEGER` | Clave de JOIN temporal universal entre tablas |
| `is_daylight` | `clean_weather` | `1` si `pod == 'd'`, else `0` | Flag de período diurno para cálculo de posición solar |
| `rain_prob_norm` | `clean_weather` | `pop ∈ [0, 1]` (ya normalizado por OWM); `fillna(0)` | Probabilidad de lluvia normalizada |
| `_ingested_at_utc` | `clean_clients`, `clean_weather` | `datetime.now(UTC)` en el momento del procesamiento | Trazabilidad de ingesta y deduplicación |
| `_source_file` | `clean_clients`, `clean_weather` | `os.path.basename(ruta Bronze)` | Linaje directo al fichero Bronze origen |
| `nominal_load_kw` (imputado) | `clean_clients` | `pv_peak_power_kw × 1.3` si es nulo | Estimación de consumo nominal cuando no se informa |

---

### 4.3 Mapeo Bronze → Silver por Entidad

| Campo Bronze | Campo Silver | Transformación | Entidad |
|--------------|--------------|----------------|---------|
| `included[].attributes.values[].datetime` | `datetime_utc` TEXT | `pd.to_datetime(utc=True)` + `strftime` | Precios REE |
| `included[].attributes.values[].value` | `price_euro_mwh` REAL | `float()` + interpolación lineal + `ffill/bfill` | Precios REE |
| `included[].type` | `price_type` TEXT | Pasado directamente como etiqueta de serie | Precios REE |
| *(calculado)* | `unix_time` INTEGER | Conversión `datetime_utc` → EPOCH | Precios REE |
| `list[].dt_txt` | `forecast_time_utc` TEXT | `pd.to_datetime` + `resample('1h')` | Meteorología |
| `list[].main.temp` | `temp_celsius` REAL | Interpolación lineal + `round(3)` | Meteorología |
| `list[].main.humidity` | `humidity_pct` REAL | Interpolación lineal + `round(3)` | Meteorología |
| `list[].clouds.all` | `clouds_pct` REAL | Interpolación lineal + `round(3)` | Meteorología |
| `list[].pop` | `rain_prob_norm` REAL | Interpolación lineal; `fillna(0)` | Meteorología |
| `list[].wind.speed` | `wind_speed_mps` REAL | Interpolación lineal + `round(3)` | Meteorología |
| `list[].weather[0].id` | `weather_id` INTEGER | `ffill` tras resample | Meteorología |
| `list[].sys.pod` | `is_daylight` INTEGER | `1` si `'d'`, `0` si `'n'`; drop columna `pod` | Meteorología |
| `latitude` (Excel) | `latitude` REAL | `pd.to_numeric` + `round(6)` + validación rango | Clientes |
| `pv_peak_power_kw` (Excel) | `pv_peak_power_kw` REAL | `pd.to_numeric` + validación `> 0` | Clientes |
| `name` (Excel) | `name` TEXT | `str.upper().str.strip()` | Clientes |
| `angle` (Excel) | `angle` REAL | Imputación `30°` si fuera de `[0, 90]` | Clientes |

---

### 4.4 Schemas Silver (Tipos Homogeneizados)

#### 4.4.1 `clean_clients`

> Módulo: `silver_transform_clients.py` · PK: `client_id`

| Campo | Tipo SQL | PK/FK | Nullable | Descripción |
|-------|----------|-------|----------|-------------|
| `client_id` | TEXT | **PK** | NO | Identificador único de instalación |
| `name` | TEXT | | NO | Nombre en mayúsculas y sin espacios laterales |
| `description` | TEXT | | NO | Descripción (defecto: `'unknown'`) |
| `latitude` | REAL | | NO | Latitud WGS84, redondeada a 6 decimales |
| `longitude` | REAL | | NO | Longitud WGS84, redondeada a 6 decimales |
| `nominal_load_kw` | REAL | | NO | Consumo nominal (imputado: `pv_peak_power_kw × 1.3`) |
| `pv_peak_power_kw` | REAL | | NO | Potencia pico PV (kWp). Debe ser `> 0` |
| `panel_area_m2` | REAL | | NO | Área de paneles (m²); `0` si no informado |
| `efficiency` | REAL | | NO | Eficiencia del panel [0–1]; defecto `0.15` |
| `panel_type` | TEXT | | NO | Tecnología del panel; defecto `'unknown'` |
| `loss_pct` | REAL | | NO | Pérdidas sistema (%); defecto `14.0` |
| `angle` | REAL | | NO | Inclinación (°); defecto `30.0` |
| `aspect` | REAL | | NO | Azimut (°); defecto `180.0` (Sur) |
| `mounting` | TEXT | | NO | Tipo de montaje; defecto `'unknown'` |
| `battery_capacity_kwh` | REAL | | NO | Capacidad batería (kWh); `0` si no tiene |
| `soc_min_pct` | REAL | | NO | SOC mínimo batería (%); defecto `20.0` |
| `installation_cost_eur` | REAL | | NO | Coste instalación (€); `0` si no informado |
| `timezone` | TEXT | | NO | Zona horaria IANA; defecto `'UTC'` |
| `_source_file` | TEXT | | NO | Nombre del fichero Bronze de origen |
| `_ingested_at_utc` | DATETIME | | NO | Timestamp UTC de carga a Silver |

#### 4.4.2 `clean_weather`

> Módulo: `silver_transform_weather.py` · PK: `(client_id, unix_time)`

| Campo | Tipo SQL | PK/FK | Nullable | Descripción |
|-------|----------|-------|----------|-------------|
| `client_id` | TEXT | **PK1 / FK** | NO | Referencia a `clean_clients.client_id` |
| `unix_time` | INTEGER | **PK2** | NO | EPOCH UTC del slot horario (clave de JOIN) |
| `forecast_time_utc` | TEXT | | NO | Timestamp UTC (`YYYY-MM-DD HH:MM:SS`) |
| `temp_celsius` | REAL | | SÍ | Temperatura ambiente (°C) |
| `humidity_pct` | REAL | | SÍ | Humedad relativa (%) |
| `clouds_pct` | REAL | | SÍ | Cobertura nubosa (%) |
| `rain_prob_norm` | REAL | | NO | Probabilidad de lluvia [0–1]; `0` si nulo |
| `wind_speed_mps` | REAL | | SÍ | Velocidad del viento (m/s) |
| `weather_id` | INTEGER | | SÍ | Código OWM de condición meteorológica |
| `weather_main` | TEXT | | SÍ | Categoría OWM (Clear, Rain, Clouds…) |
| `weather_description` | TEXT | | SÍ | Descripción detallada OWM |
| `is_daylight` | INTEGER | | NO | `1` = período diurno, `0` = período nocturno |
| `_source_file` | TEXT | | SÍ | Fichero Bronze de origen |
| `_ingested_at_utc` | TEXT | | NO | Timestamp UTC de carga a Silver |

#### 4.4.3 `clean_prices`

> Módulo: `silver_transform_prices.py` · PK: `(datetime_utc, price_type)`

| Campo | Tipo SQL | PK/FK | Nullable | Descripción |
|-------|----------|-------|----------|-------------|
| `unix_time` | INTEGER | | NO | EPOCH UTC del slot horario (clave de JOIN) |
| `datetime_utc` | TEXT | **PK1** | NO | Timestamp UTC de la hora de precio |
| `price_type` | TEXT | **PK2** | NO | Tipo de precio (etiqueta de serie REE) |
| `price_euro_mwh` | REAL | | SÍ | Precio PVPC (€/MWh); interpolado linealmente si hay huecos |
| `_source_file` | TEXT | | SÍ | Fichero Bronze de origen |
| `_ingested_at_utc` | TEXT | | NO | Timestamp UTC de carga a Silver |

#### 4.4.4 `clean_calculations`

> Módulo: `silver_calc_pv_generation.py` · PK: `(client_id, unix_time)`  
> Generada a partir del JOIN `clean_clients ⨝ clean_weather` para `unix_time >= now`.

| Campo | Tipo SQL | PK/FK | Nullable | Descripción |
|-------|----------|-------|----------|-------------|
| `client_id` | TEXT | **PK1 / FK** | NO | Referencia a `clean_clients.client_id` |
| `unix_time` | INTEGER | **PK2** | NO | EPOCH UTC del slot horario |
| `forecast_time_utc` | TEXT | | NO | Timestamp UTC legible |
| `pv_power_gen_kw` | REAL | | SÍ | **Potencia AC generada por el parque PV (kW)** |
| `pv_performance_ratio` | REAL | | SÍ | Performance Ratio con derating térmico (γ = −0.4%/°C) |
| `poa_wm2` | REAL | | SÍ | Irradiancia en el Plano del Array (W/m²) |
| `t_cell_celsius` | REAL | | SÍ | Temperatura de célula estimada (°C) — modelo Faiman |
| `power_con_kw` | REAL | | SÍ | **Consumo industrial simulado (kW)** |
| `calculated_at_utc` | TEXT | | NO | Timestamp UTC de ejecución del cálculo |

> `clean_calculations` es la tabla Silver **más crítica para el negocio**: combina la física del sistema PV con el modelo de consumo industrial, proporcionando la base para calcular el balance energético neto hora a hora (`generación - consumo`) y el coste/beneficio de cada decisión de gestión de carga flexible.

---

## 5. Capa Gold — Star Schema

La capa Gold implementa un modelo dimensional **Star Schema** sobre SQLite, optimizado para consultas analíticas de gestión energética. Todas las tablas Gold son **idempotentes**: pueden reconstruirse en cualquier momento a partir de las tablas Silver sin pérdida de información.

### 5.1 Tablas de Hechos

| Tabla | Granularidad | Registros estimados | Descripción |
|-------|-------------|---------------------|-------------|
| `gold_fact_energy_forecast` | 1 fila por `(client_id, unix_time)` | N_clientes × 120h | Hecho central: generación PV, consumo, meteorología y precio por slot horario y cliente |

---

### 5.2 Dimensiones

| Tabla dimensión | Clave primaria | Tipo SCD | Descripción |
|-----------------|---------------|----------|-------------|
| `gold_dim_client` | `client_id` TEXT | SCD Tipo 1 | Configuración técnica de cada instalación fotovoltaica industrial |
| `gold_dim_datetime` | `unix_time` INTEGER | Estática | Calendario enriquecido con atributos tarifarios españoles (3.0TD) |
| `gold_dim_weather` | `weather_id` INTEGER | SCD Tipo 2 | Catálogo de condiciones meteorológicas OWM; resolución por frecuencia de observación |

```
                        +-------------------------+
                        |   gold_dim_datetime     |
                        |   PK: unix_time         |
                        +----------+--------------+
                                   |
                                   | unix_time
                                   |
+----------------+     +-----------+------------------+     +-------------------------+
| gold_dim_client|     | gold_fact_energy_forecast    |     |   gold_dim_weather      |
| PK: client_id  +-----+ PK: (client_id, unix_time)   +-----+   PK: weather_id        |
+----------------+     +------------------------------+     +-------------------------+
```

---

### 5.3 Diccionario de Datos Completo — Gold

#### 5.3.1 `gold_fact_energy_forecast`

> Módulo: `gold_fact_energy_forecast.py` · Estrategia: `INSERT OR REPLACE` (upsert incremental sobre ventana activa `unix_time >= now - 2h`)

| Campo | Tipo SQL | PK/FK | Nullable | Descripción | Ejemplo |
|-------|----------|-------|----------|-------------|---------|
| `client_id` | TEXT | **PK1 / FK** | NO | Instalación → `gold_dim_client` | `C001` |
| `unix_time` | INTEGER | **PK2 / FK** | NO | Slot horario → `gold_dim_datetime` | `1746874800` |
| `forecast_time_utc` | TEXT | | NO | Timestamp UTC legible | `2026-05-10 15:00:00` |
| `pv_power_gen_kw` | REAL | | SÍ | **Potencia AC generada (kW)** | `8.742` |
| `pv_performance_ratio` | REAL | | SÍ | Performance Ratio con derating térmico | `0.821` |
| `poa_wm2` | REAL | | SÍ | Irradiancia Plano del Array (W/m²) | `612.4` |
| `t_cell_celsius` | REAL | | SÍ | Temperatura de célula — modelo Faiman (°C) | `47.3` |
| `power_consumption_kw` | REAL | | SÍ | **Consumo industrial simulado (kW)** | `12.15` |
| `temp_celsius` | REAL | | SÍ | Temperatura ambiente (°C) | `20.29` |
| `humidity_pct` | REAL | | SÍ | Humedad relativa (%) | `65.0` |
| `clouds_pct` | REAL | | SÍ | Cobertura nubosa (%) | `82.0` |
| `rain_prob_norm` | REAL | | SÍ | Probabilidad de precipitación [0–1] | `0.15` |
| `wind_speed_mps` | REAL | | SÍ | Velocidad del viento (m/s) | `5.54` |
| `weather_id` | INTEGER | **FK** | SÍ | Condición → `gold_dim_weather` | `803` |
| `price_pvpc_eur_mwh` | REAL | | SÍ | **Precio PVPC (€/MWh)** | `142.80` |
| `_loaded_at_utc` | TEXT | | NO | Timestamp de última carga Gold | `2026-05-10 22:00:00` |

#### 5.3.2 `gold_dim_client`

> Módulo: `gold_dim_clients.py` · Estrategia: `DROP + CREATE + INSERT` (full rebuild)

| Campo | Tipo SQL | PK | Nullable | Descripción | Ejemplo |
|-------|----------|----|----------|-------------|---------|
| `client_id` | TEXT | **PK** | NO | Identificador de instalación | `C001` |
| `name` | TEXT | | NO | Nombre (mayúsculas, sin espacios) | `PLANTA NORTE` |
| `description` | TEXT | | SÍ | Descripción de la instalación | `Nave logística` |
| `latitude` | REAL | | NO | Latitud WGS84 | `42.803852` |
| `longitude` | REAL | | NO | Longitud WGS84 | `-1.701962` |
| `timezone` | TEXT | | NO | Zona horaria IANA | `Europe/Madrid` |
| `nominal_load_kw` | REAL | | NO | Consumo nominal (kW) | `20.8` |
| `pv_peak_power_kw` | REAL | | NO | Potencia pico PV (kWp) | `16.0` |
| `panel_area_m2` | REAL | | NO | Área de paneles (m²) | `80.0` |
| `efficiency` | REAL | | NO | Eficiencia del panel [0–1] | `0.20` |
| `panel_type` | TEXT | | NO | Tecnología del panel | `monoSi` |
| `loss_pct` | REAL | | NO | Pérdidas sistema (%) | `14.0` |
| `angle` | REAL | | NO | Inclinación (°) | `30.0` |
| `aspect` | REAL | | NO | Azimut (°) | `180.0` |
| `mounting` | TEXT | | NO | Tipo de montaje | `rooftop` |
| `battery_capacity_kwh` | REAL | | NO | Capacidad batería (kWh) | `20.0` |
| `soc_min_pct` | REAL | | NO | SOC mínimo (%) | `20.0` |
| `installation_cost_eur` | REAL | | NO | Coste instalación (€) | `18000.0` |
| `has_solar` | INTEGER | | NO | **Flag**: `1` si `pv_peak_power_kw > 0` | `1` |
| `has_battery` | INTEGER | | NO | **Flag**: `1` si `battery_capacity_kwh > 0` | `1` |

#### 5.3.3 `gold_dim_datetime`

> Módulo: `gold_dim_datetime.py` · Estrategia: `DROP + CREATE + INSERT` (full rebuild desde `clean_weather`)

| Campo | Tipo SQL | PK | Nullable | Descripción | Ejemplo |
|-------|----------|----|----------|-------------|---------|
| `unix_time` | INTEGER | **PK** | NO | EPOCH UTC — clave de JOIN con la tabla de hechos | `1746874800` |
| `datetime_utc` | TEXT | | NO | Timestamp UTC | `2026-05-10 15:00:00` |
| `datetime_local` | TEXT | | NO | Timestamp local (Europe/Madrid) | `2026-05-10 17:00:00` |
| `date` | TEXT | | NO | Fecha (`YYYY-MM-DD` UTC) | `2026-05-10` |
| `hour_utc` | INTEGER | | NO | Hora UTC [0–23] | `15` |
| `hour_local` | INTEGER | | NO | Hora local [0–23] | `17` |
| `day_of_week` | TEXT | | NO | Día de la semana (en inglés, minúsculas) | `sunday` |
| `is_daylight` | INTEGER | | NO | `1` = horario de verano (CEST activo) | `1` |
| `is_weekend` | INTEGER | | NO | `1` si sábado o domingo | `1` |
| `is_festivo` | INTEGER | | NO | `1` si festivo nacional español | `0` |
| `month` | INTEGER | | NO | Mes [1–12] | `5` |
| `year` | INTEGER | | NO | Año | `2026` |
| `tariff_period` | TEXT | | NO | Período tarifario: `P1`, `P2`, `P3`, `P6` | `P6` |
| `tariff_label` | TEXT | | NO | Etiqueta: `punta`, `llano`, `valle`, `super-valle` | `super-valle` |

> **Lógica de períodos tarifarios (3.0TD España):**
> - **P1 (punta):** L–V `10:00–14:00` y `18:00–22:00`
> - **P2 (llano):** L–V `08:00–10:00`, `14:00–18:00`, `22:00–24:00`
> - **P3 (valle):** L–V `00:00–08:00`
> - **P6 (super-valle):** Sábados, domingos y festivos nacionales españoles

#### 5.3.4 `gold_dim_weather`

> Módulo: `gold_dim_weather.py` · Estrategia: `DROP + CREATE + INSERT` con `ROW_NUMBER()` para resolver duplicados por frecuencia de observación.

| Campo | Tipo SQL | PK | Nullable | Descripción | Ejemplo |
|-------|----------|----|----------|-------------|---------|
| `weather_id` | INTEGER | **PK** | NO | Código OWM de condición meteorológica | `803` |
| `weather_main` | TEXT | | NO | Categoría más frecuente observada para este `id` | `Clouds` |
| `weather_description` | TEXT | | NO | Descripción más frecuente para este `id` | `broken clouds` |
| `_loaded_at_utc` | TEXT | | NO | Timestamp de carga Gold | `2026-05-10 22:00:00` |

---

### 5.4 Métricas de Negocio Precalculadas

| Métrica | Fórmula SQL | Caso de uso |
|---------|-------------|-------------|
| **Balance energético neto (kW)** | `pv_power_gen_kw - power_consumption_kw` | Identifica excedente (`> 0`) o déficit (`< 0`) hora a hora |
| **Coste energético horario (€)** | `(power_consumption_kw / 1000.0) * price_pvpc_eur_mwh` | Coste si no se usa generación propia |
| **Ahorro PV horario (€)** | `(pv_power_gen_kw / 1000.0) * price_pvpc_eur_mwh` | Valor económico de la energía autoconsumida |
| **Horas óptimas de carga batería** | `WHERE balance_neto > 0 AND tariff_period IN ('P3','P6')` | Maximizar SOC en valle tarifario con excedente PV |
| **Mejor hora para arranque de maquinaria** | `ORDER BY (price_pvpc_eur_mwh - pv_contribution_eur) ASC` | Minimizar coste neto de arranque en ventana de 5 días |
| **Performance Ratio diario** | `AVG(pv_performance_ratio) GROUP BY date, client_id` | KPI de salud del parque PV por instalación |
| **Factor de capacidad (CF)** | `AVG(pv_power_gen_kw) / MAX(pv_peak_power_kw)` | Eficiencia real vs. potencia instalada |
| **Coste en período punta (P1)** | `SUM(coste_horario) WHERE tariff_period = 'P1'` | Exposición al período más caro para demand-side management |

---

## 6. Data Lineage — Trazabilidad End-to-End

### 6.1 Diagrama de Linaje End-to-End

```
+---------------------------------------------------------------------------------------+
|                                SUNSAVER -- DATA LINEAGE                               |
+---------------------------------------------------------------------------------------+

  FUENTES EXTERNAS             BRONZE                     SILVER                      GOLD
  ----------------          ------------               ------------              --------------
                                                                                 gold_dim_client
  REE API (PVPC)  ------>  prices_*.json   ------>     clean_prices     ------+
  (JSON, 24h/dia)          (chmod 444)                (interp. lin.)          |
                                                                              |  gold_fact_energy_forecast
  OWM API (5d)    ------>  weather_*.json  ------>     clean_weather    ------+> (client_id, unix_time)
  (JSON, 3h/cli.)          (chmod 444)                (resample 1h)           |   pv_power_gen_kw
                                                                              |   power_consumption_kw
  Excel clientes  ------>  clients_*.json  ------>     clean_clients    ------+   price_pvpc_eur_mwh
  (xlsx, manual)           (chmod 444)                (valid+impute)          |
                                                            |                 |  gold_dim_datetime
                                                            | pvlib engine    |  (tarifas 3.0TD)
                                                            v                 |
                                                      clean_calculations -----+  gold_dim_weather
                                                      (GHI->Erbs->POA)           (catalogo OWM)

  Auditoria: _process_manifest_*.json (Bronze)  +  etl_metadata (SQLite) por ejecución
   ```

---

### 6.2 Tabla de Trazabilidad Campo a Campo

| Campo Gold (fact) | Campo Silver | Campo Bronze | Fuente API | Transformación aplicada |
|-------------------|-------------|--------------|------------|------------------------|
| `client_id` | `clean_calculations.client_id` | `clients_*.json → client_id` | Excel clientes | Sin transformación |
| `unix_time` | `clean_weather.unix_time` | *(calculado de `dt_txt`)* | OWM API | Conversión EPOCH |
| `pv_power_gen_kw` | `clean_calculations.pv_power_gen_kw` | N/A — calculado | OWM + Excel | Motor físico PV (`pvlib`): GHI → Erbs → POA → Faiman → PR |
| `pv_performance_ratio` | `clean_calculations.pv_performance_ratio` | N/A — calculado | OWM + Excel | `PR = f_temp × (1 - loss_pct/100)` con γ = −0.4%/°C |
| `poa_wm2` | `clean_calculations.poa_wm2` | N/A — calculado | OWM + Excel | GHI → descomposición Erbs → POA (beam + diff + albedo) |
| `t_cell_celsius` | `clean_calculations.t_cell_celsius` | N/A — calculado | OWM (`temp`, `wind`) | Modelo Faiman: `T_amb + POA / (U0 + U1·v_wind)` |
| `power_consumption_kw` | `clean_calculations.power_con_kw` | N/A — calculado | Excel (`nominal_load_kw`) | Modelo consumo industrial con turnos, HVAC y variabilidad gaussiana |
| `temp_celsius` | `clean_weather.temp_celsius` | `list[].main.temp` | OWM API | Interpolación lineal 3h → 1h |
| `humidity_pct` | `clean_weather.humidity_pct` | `list[].main.humidity` | OWM API | Interpolación lineal 3h → 1h |
| `clouds_pct` | `clean_weather.clouds_pct` | `list[].clouds.all` | OWM API | Interpolación lineal 3h → 1h |
| `rain_prob_norm` | `clean_weather.rain_prob_norm` | `list[].pop` | OWM API | Interpolación lineal; `fillna(0)` |
| `wind_speed_mps` | `clean_weather.wind_speed_mps` | `list[].wind.speed` | OWM API | Interpolación lineal 3h → 1h |
| `weather_id` | `clean_weather.weather_id` | `list[].weather[0].id` | OWM API | `ffill` tras resample |
| `price_pvpc_eur_mwh` | `clean_prices.price_euro_mwh` | `included[].attributes.values[].value` | REE API | `float()` + filtro outliers + interpolación lineal |
| `tariff_period` *(dim)* | `gold_dim_datetime.tariff_period` | N/A — calculado | Calendario interno | Lógica tarifaria 3.0TD sobre `datetime_local` |

---

### 6.3 Análisis de Impacto de Cambios en Fuente

| Cambio en fuente | Bronze afectado | Silver afectado | Gold afectado | Acción recomendada |
|------------------|----------------|-----------------|---------------|-------------------|
| REE cambia estructura JSON de `included` | `prices_*.json` | `clean_prices` | `gold_fact_energy_forecast` (`price_pvpc_eur_mwh`) | Actualizar parser en `silver_transform_prices.py` y re-procesar desde Bronze |
| OWM cambia campo `dt_txt` a formato distinto | `weather_*.json` | `clean_weather`, `clean_calculations` | `gold_fact_energy_forecast`, `gold_dim_datetime` | Actualizar extractor; re-calcular Silver completo |
| Nuevo campo en Excel clientes | `clients_*.json` | `clean_clients` | `gold_dim_client` | Añadir campo al schema Silver y Gold; re-ingestar Excel |
| REE deja de publicar PVPC (cambio regulatorio) | — | `clean_prices` vacía | `gold_fact_energy_forecast` sin precio | Activar fuente alternativa (OMIE); impacta **todas** las métricas de coste |
| Cambio en tarifas horarias 3.0TD | — | — | `gold_dim_datetime` (`tariff_period`, `tariff_label`) | Actualizar `get_tariff_period()` en `gold_dim_datetime.py` y regenerar dimensión |
| Nuevo cliente en Excel | `clients_*.json` | `clean_clients`, `clean_weather` | Todas las tablas Gold | Pipeline completo; nueva fila en todas las tablas Gold para el nuevo `client_id` |

---

## 7. Clasificación y Gobernanza del Dato

### 7.1 Clasificación por Sensibilidad

| Tabla / Recurso | Capa | Clasificación | Justificación |
|-----------------|------|---------------|---------------|
| `clients_source.xlsx` (DEV) | Origen | INTERNA | Nombres ficticios. Coordenadas reales de ubicaciones industriales. |
| `prices_*.json` (Bronze) | Bronze | PÚBLICA | Precios PVPC son datos públicos de REE. Sin información sensible. |
| `weather_*.json` (Bronze) | Bronze | PÚBLICA | Datos meteorológicos públicos de OpenWeatherMap. |
| `clients_*.json` (Bronze) | Bronze | INTERNA | Copia de datos maestros. Contiene coordenadas geográficas de instalaciones. |
| `clean_clients` | Silver | INTERNA | Parámetros técnicos y económicos de instalaciones (coste, potencia, ubicación). |
| `clean_weather` | Silver | PÚBLICA | Previsiones meteorológicas procesadas. Sin datos personales. |
| `clean_prices` | Silver | PÚBLICA | Precios PVPC procesados. Dato público de REE. |
| `clean_calculations` | Silver | INTERNA | Generación y consumo estimados por instalación. Información operativa. |
| `gold_dim_client` | Gold | INTERNA | Configuración completa de la instalación incluyendo coste y capacidad. |
| `gold_dim_datetime` | Gold | PÚBLICA | Dimensión de tiempo y tarifas. Sin datos personales. |
| `gold_dim_weather` | Gold | PÚBLICA | Catálogo de condiciones meteorológicas. Sin datos personales. |
| `gold_fact_energy_forecast` | Gold | CONFIDENCIAL en producción | Combina generación, consumo y precio por instalación. Comercialmente sensible con datos reales. |
| `etl_metadata` | Control | INTERNA | Historial de ejecuciones con estados y métricas del pipeline. |
| `_process_manifest_*.json` | Control | INTERNA | Control de procesamiento. Contiene rutas del sistema de ficheros. |

---

### 7.2 Datos PII o Regulados

| Categoría | Detalle |
|-----------|---------|
| **Datos PII en entorno DEV** | **NINGUNO.** Los nombres de instalación son ficticios. Las coordenadas corresponden a ubicaciones industriales, no a personas físicas. No hay datos de empleados ni información personal identificable. |
| **Datos PII en producción** | Con clientes reales, los campos `name`, `latitude`, `longitude` y `description` de `clean_clients` podrían identificar empresas o ubicaciones reales. Se recomienda **pseudonimización** a nivel Bronze antes de persistir en producción. |
| **Datos regulados** | Los precios PVPC son datos públicos regulados por la CNMC y REE. Su uso está sujeto a los términos de la API pública de REE. |
| **GDPR** | No se identifican datos sujetos a GDPR en DEV. En producción, si se incorporan datos de personas físicas, aplicar GDPR Art. 25 (Privacy by Design). |
| **Recomendación producción** | Implementar pseudonimización de `client_id` y `name` antes de exponer datos Gold a sistemas externos o third parties. |

---

### 7.3 Propietarios de Dominio por Tabla

| Tabla / Recurso | Dominio | Propietario técnico | Operaciones permitidas |
|-----------------|---------|---------------------|------------------------|
| REE API | Precios energía | Equipo Data Engineering | Lectura (API pública) |
| OWM API | Meteorología | Equipo Data Engineering | Lectura (API con key propia) |
| Excel clientes | Maestro instalaciones | **Equipo de Operaciones / Negocio** | Lectura y actualización manual |
| Bronze (todos los ficheros) | Datos crudos | Equipo Data Engineering | Escritura única al ingestar; lectura para Silver |
| `clean_clients` | Maestro instalaciones | Equipo de Operaciones | Escritura por pipeline; lectura por motor PV y Gold |
| `clean_weather` | Meteorología procesada | Equipo Data Engineering | Escritura por pipeline; lectura por motor PV y Gold |
| `clean_prices` | Precios procesados | Equipo Data Engineering | Escritura por pipeline; lectura por Gold |
| `clean_calculations` | Cálculos físicos PV | **Equipo Data Science** | Escritura por motor PV; lectura por Gold |
| `gold_dim_client` | Dimensión instalaciones | Equipo Data Engineering | Escritura por pipeline Gold; lectura por BI |
| `gold_dim_datetime` | Dimensión tiempo/tarifa | Equipo Data Engineering | Escritura por pipeline Gold; lectura por BI |
| `gold_dim_weather` | Dimensión meteorología | Equipo Data Engineering | Escritura por pipeline Gold; lectura por BI |
| `gold_fact_energy_forecast` | Hecho energético | **Equipo Data Science / Negocio** | Escritura por pipeline Gold; lectura por BI y optimizador de cargas |
| `etl_metadata` | Auditoría pipeline | Equipo Data Engineering | Escritura por orchestrator; lectura por monitorización |

---

### 7.4 Tabla de Auditoría del Pipeline (`etl_metadata`)

> Módulo: `audit_metadata.py` · Motor: SQLite · Tabla: `etl_metadata`

| Campo | Tipo SQL | Descripción | Ejemplo |
|-------|----------|-------------|---------|
| `id` | INTEGER PK | Autoincremental | `42` |
| `pipeline_name` | TEXT | Nombre del pipeline ejecutado | `SunSaver_ETL` |
| `status` | TEXT | `SUCCESS` \| `PARTIAL SUCCESS` \| `FAILED` \| `CRITICAL ERROR` | `PARTIAL SUCCESS` |
| `duration_seconds` | REAL | Duración total de la ejecución (segundos) | `47.83` |
| `rows_affected` | INTEGER | Total de registros procesados en todos los steps | `3847` |
| `error_message` | TEXT | Resumen de fallos (`NULL` si éxito completo) | `Fallos en: extract_energy_prices` |
| `env` | TEXT | Entorno de ejecución | `DEV` |
| `executed_at` | DATETIME | Timestamp UTC de inicio de ejecución | `2026-05-10 22:00:01` |

> **Nota operativa:** `PARTIAL SUCCESS` se registra cuando `extract_energy_prices` devuelve `False` (precios REE no publicados aún, típicamente antes de las 20:30 CET). El pipeline continúa con meteorología, cálculos PV y carga Gold, garantizando **continuidad operativa** incluso sin precio eléctrico del día siguiente.

---

*SunSaver ETL · Catálogo de Datos v1.0.0 · Mayo 2026*  
*Clasificación: INTERNA · No distribuir fuera del equipo sin autorización*