# ☀️ SunSaver · Plataforma de Inteligencia Energética Industrial
# 01 Registro de Decisiones de Arquitectura (ADR)

> **Clasificación:** INTERNA &nbsp;|&nbsp; **Estado:** ACTIVO — Entorno DEV &nbsp;|&nbsp; **Pipeline:** `SunSaver_ETL`  
> **Propietario:** Equipo de Datos — SunSaver &nbsp;|&nbsp; **Última actualización:** 2026-05-10

> *"Este documento es la fuente única de verdad de cada decisión arquitectónica tomada en la plataforma SunSaver. Existe para explicar no solo qué se construyó, sino por qué — y qué se descartó deliberadamente."*

---

## Tabla de Contenidos

1. [Resumen Ejecutivo](#1-resumen-ejecutivo)
2. [Contexto y Planteamiento del Problema](#2-contexto-y-planteamiento-del-problema)
3. [Visión General de la Arquitectura](#3-visión-general-de-la-arquitectura)
4. [Justificación de la Arquitectura Medallion](#4-justificación-de-la-arquitectura-medallion)
5. [Decisiones sobre el Stack Tecnológico](#5-decisiones-sobre-el-stack-tecnológico)
6. [Registro ADR — Decisiones Individuales de Arquitectura](#6-registro-adr--decisiones-individuales-de-arquitectura)
7. [Preocupaciones Transversales](#7-preocupaciones-transversales)
8. [Hoja de Ruta Técnica](#8-hoja-de-ruta-técnica)

---

## 1. Resumen Ejecutivo

### 1.1 Objetivo del Sistema

SunSaver es una **plataforma de inteligencia energética industrial** diseñada para proporcionar a las PYMES con instalaciones fotovoltaicas los datos operativos necesarios para tomar decisiones de gestión energética basadas en evidencia.

El sistema ingesta datos externos heterogéneos (precios del mercado eléctrico español vía API de REE, previsiones atmosféricas vía OpenWeatherMap), aplica una cadena validada de modelos de física fotovoltaica, y entrega una previsión energética de 5 días con granularidad horaria — cubriendo generación solar, consumo industrial y precios de electricidad en tiempo real.

El producto final es un **esquema en estrella en la capa Gold** optimizado para consumo analítico: cada fila de `gold_fact_energy_forecast` responde a la pregunta *"para este cliente, en esta hora, ¿cuánta energía se generará, cuánta se consumirá y cuánto costará?"*. Esta inteligencia estructurada permite tomar decisiones accionables sobre la gestión de cargas flexibles: programas de carga de baterías, ventanas óptimas de arranque de maquinaria y evitación de picos de demanda.

### 1.2 Alcance y Dominio

El sistema opera en la intersección de dos dominios:

**Dominio físico — Modelado de generación fotovoltaica:**
La plataforma implementa una cadena física completa de atmósfera a electricidad: geometría solar (NREL SPA vía pvlib), irradiancia de cielo despejado (modelo Haurwitz), atenuación por nubes (Kasten-Czeplak), descomposición de irradiancia (modelo de Erbs), proyección en el plano del array (Liu-Jordan isotrópico + albedo), modelado de temperatura de célula (modelo de Faiman) y potencia AC de salida con derating térmico (−0,4 %/°C para silicio cristalino).

**Dominio económico — Mercado eléctrico español:**
La plataforma se integra con la API pública de Red Eléctrica de España (REE) para ingestar los precios de la tarifa PVPC (Precio Voluntario para el Pequeño Consumidor) y clasifica cada franja horaria según el esquema tarifario 2.0TD (P1 Punta / P2 Llano / P3 Valle / P6 Super-Valle), habilitando la programación óptima en costes de cargas industriales flexibles.

**Alcance temporal:** Horizonte de previsión meteorológica de 5 días (OpenWeatherMap 3 horas → remuestreado a 1 hora) y previsión de precios de electricidad del día siguiente (REE publica D+1 después de las 20:30 CET).

**Alcance de clientes:** Arquitectura multi-cliente; cada cliente se caracteriza de forma independiente por coordenadas geográficas, parámetros del sistema FV (potencia pico, área de panel, ángulo de inclinación, azimut, pérdidas del sistema, tipo de montaje), configuración de almacenamiento en batería y perfil de carga industrial.

### 1.3 Partes Interesadas y Audiencia Técnica

| Parte interesada | Rol | Preocupación principal |
|---|---|---|
| Responsable de Planta Industrial | Consumidor primario | Decisiones operativas: cuándo cargar baterías, cuándo arrancar maquinaria pesada |
| Energy Manager / Técnico de Instalaciones | Consumidor secundario | Monitorización de KPIs, optimización de costes, verificación de SLA |
| Ingeniero de Datos (mantenedor) | Propietario del sistema | Fiabilidad del pipeline, calidad del dato, evolución del esquema |
| Reclutador Técnico Senior | Lector del documento | Calidad arquitectónica, criterio de ingeniería, estándares profesionales |
| Futuro Ingeniero MLOps | Downstream | Disponibilidad del feature store, datos de entrenamiento de modelos |

---

## 2. Contexto y Planteamiento del Problema

### 2.1 Problema de Negocio

Las PYMES industriales españolas con instalaciones fotovoltaicas se enfrentan a un reto operativo persistente: **generan energía pero no pueden predecir con precisión cuándo, cuánta ni a qué valor de mercado**. Esto genera tres ineficiencias compuestas:

**Ineficiencia 1 — Programación ciega de cargas flexibles.** La carga de baterías, flotas de vehículos eléctricos, climatización industrial (HVAC) y maquinaria no crítica en el tiempo se arrancan basándose en la intuición o en horarios fijos, en lugar de en previsiones reales de generación. El resultado es un despilfarro energético sistemático: las cargas funcionan durante ventanas de precio pico (P1, P2) cuando la generación solar es insuficiente, incurriendo en costes de red evitables.

**Ineficiencia 2 — Ventanas de autoconsumo desaprovechadas.** Sin una previsión de generación horaria correlacionada con los perfiles de consumo, las instalaciones no pueden identificar las horas en que el balance energético neto es positivo — es decir, cuando pueden funcionar cargas enteramente con solar sin tirar de red.

**Ineficiencia 3 — Gestión energética reactiva, no predictiva.** Las herramientas actuales disponibles para PYMES proporcionan datos históricos de consumo (espejo retrovisor) pero no estimaciones de generación basadas en física hacia el futuro, correlacionadas con precios de mercado (parabrisas). SunSaver aborda este vacío.

### 2.2 Requisitos Funcionales Clave

| ID | Requisito | Prioridad |
|---|---|---|
| RF-01 | Ingestar precios de electricidad del día siguiente desde la API de REE con gestión elegante de la indisponibilidad previa a las 20:30 | Crítico |
| RF-02 | Ingestar previsión meteorológica de 5 días por cliente desde OpenWeatherMap, de forma independiente por cliente (aislamiento de fallos) | Crítico |
| RF-03 | Aplicar cadena de física FV validada para producir estimaciones horarias de potencia AC generada | Crítico |
| RF-04 | Modelar el consumo industrial mediante perfiles de turnos con sensibilidad térmica del HVAC | Alto |
| RF-05 | Clasificar cada franja horaria según los períodos tarifarios 2.0TD españoles (P1–P6) | Alto |
| RF-06 | Dar soporte a múltiples clientes simultáneamente con parametrización independiente | Alto |
| RF-07 | Entregar una tabla de hechos analítica unificada con joins por tiempo, cliente, meteorología y precio | Alto |
| RF-08 | Proporcionar trazabilidad completa del pipeline con telemetría por ejecución | Medio |
| RF-09 | Soportar ejecución incremental del pipeline (reanudar desde cualquier etapa) | Medio |
| RF-10 | Preservar los datos brutos ingestados como capa Bronze inmutable para auditoría y reprocesamiento | Medio |

### 2.3 Requisitos No Funcionales

**Latencia:** El pipeline está diseñado para ejecución batch programada (cadencia diaria), no para streaming en tiempo real. Se espera que la ejecución completa del pipeline finalice en menos de 120 segundos para hasta 20 clientes en hardware on-premise estándar. El tiempo de ejecución observado en producción es de aproximadamente 1,93 segundos para el conjunto de clientes actual (11 pasos, 1.386 filas — evidenciado en la salida del terminal).

**Escalabilidad:** La arquitectura debe soportar escalado horizontal de la dimensión cliente (de 1 a ~100 clientes) sin cambios de esquema. El patrón de bucle multi-cliente en `bronze_ingest_weather_owm.py` y la clave primaria compuesta `(client_id, unix_time)` en todas las tablas Silver y Gold están específicamente diseñados para esto.

**Disponibilidad:** Como sistema batch diario on-premise, el objetivo de SLA es un 99,5 % de éxito de ejecución diaria. El pipeline implementa lógica de aborte por etapa: si todos los pasos de una etapa fallan, la ejecución se detiene para evitar la propagación de datos corruptos. Los fallos individuales de pasos dentro de una etapa se toleran (estado de éxito parcial).

**Calidad del dato:** La capa Silver aplica contratos de datos estrictos: validación de coordenadas, recorte de rangos de constantes físicas, filtrado de outliers (serie de precios: [−100, 2.000] €/MWh) e imputación de nulos con valores por defecto informados por la física (ángulo de inclinación: 30°, azimut: 180° Sur, pérdidas del sistema: 14 %, eficiencia: 15 %).

**Idempotencia:** Todas las operaciones de escritura en Silver y Gold usan `INSERT OR REPLACE` con claves naturales compuestas. El pipeline puede re-ejecutarse en cualquier momento sin producir registros duplicados ni corromper datos históricos.

**Reproducibilidad:** Los archivos de la capa Bronze se escriben con `chmod 444` (solo lectura, inmutables) en el momento de la ingesta. Esto garantiza que cualquier ejecución histórica del pipeline pueda reproducirse reproduciendo los archivos Bronze a través de las capas Silver y Gold.

### 2.4 Restricciones y Asunciones

**Restricciones:**
- El entorno de despliegue es Linux on-premise (Ubuntu 24). Sin Kubernetes, sin orquestación de contenedores, sin almacenamiento de objetos en cloud.
- Sin almacén de datos propietario (sin Snowflake, BigQuery ni Redshift). El almacenamiento debe ser basado en ficheros o relacional embebido.
- La API de REE es un endpoint público sin autenticación; está sujeta a ventanas de disponibilidad (precios publicados después de las 20:30 CET para D+1). El sistema debe manejar la degradación elegante cuando el endpoint no devuelve datos.
- OpenWeatherMap requiere una clave API válida inyectada vía variable de entorno (`WEATHER_API_KEY`). El plan gratuito proporciona previsiones de 5 días con intervalos de 3 horas.
- El motor de física requiere `pvlib` (biblioteca Python de modelado FV validada por NREL) y `numpy`. Estas son las únicas dependencias computacionalmente intensivas.

**Asunciones:**
- Los parámetros del sistema FV de cada cliente (potencia pico, inclinación, azimut, pérdidas) se proporcionan mediante un archivo Excel maestro (`clients_source.xlsx`) y son relativamente estables (actualizados con poca frecuencia).
- Los perfiles de consumo industrial se modelan de forma sintética usando un modelo paramétrico de turnos. La integración real con SCADA está fuera del alcance de v1.0 pero es un elemento definido en la hoja de ruta.
- La plataforma opera en el contexto del mercado eléctrico español (REE, tarifa 2.0TD, zona horaria Europe/Madrid). La internacionalización es una preocupación de v2.0.
- SQLite es el backend de almacenamiento adecuado para la escala actual. La migración a PostgreSQL o a un almacén columnar (DuckDB) es un elemento documentado en la hoja de ruta con un criterio de activación definido (>50 clientes o >500K filas en la tabla de hechos).

---

## 3. Visión General de la Arquitectura

### 3.1 Diagrama de Alto Nivel — C4 Nivel 1: Contexto del Sistema

```
┌─────────────────────────────────────────────────────────────────────┐
│                        SISTEMAS EXTERNOS                            │
│                                                                     │
│  ┌──────────────────┐       ┌───────────────────┐                   │
│  │   API REE        │       │  OpenWeatherMap   │                   │
│  │  (Precios PVPC)  │       │  API de Previsión │                   │
│  │  apidatos.ree.es │       │  api.openweather. │                   │
│  └────────┬─────────┘       └────────┬──────────┘                   │
└───────────┼──────────────────────────┼──────────────────────────────┘
            │  JSON/REST               │  JSON/REST
            ▼                          ▼
┌─────────────────────────────────────────────────────────────────────┐
│                       PLATAFORMA SUNSAVER                           │
│                                                                     │
│  ┌───────────────────────────────────────────────────────────────┐  │
│  │             PIPELINE ETL (Python)                             │  │
│  │  Ingesta Bronze → Transformación Silver → Construcción Gold   │  │
│  └──────────────────────────┬────────────────────────────────────┘  │
│                             │                                       │
│  ┌──────────────────────────▼────────────────────────────────────┐  │
│  │                  BASE DE DATOS SQLite                         │  │
│  │           sunsaver.db  (capas Silver + Gold)                  │  │
│  └──────────────────────────┬────────────────────────────────────┘  │
│                             │                                       │
│  ┌──────────────────────────▼────────────────────────────────────┐  │
│  │           CONSUMIDORES ANALÍTICOS (futuro)                    │  │
│  │       Power BI · Dashboard Personalizado · API REST           │  │
│  └───────────────────────────────────────────────────────────────┘  │
│                                                                     │
│  ┌───────────────────────────────────────────────────────────────┐  │
│  │                FUENTE DE DATOS (interna)                      │  │
│  │        clients_source.xlsx  (datos maestros de clientes)      │  │
│  └───────────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────────┘
```

### 3.2 Diagrama de Componentes — C4 Nivel 2: Vista de Contenedores

```
┌──────────────────────────────────────────────────────────────────────────────────┐
│                          CONTENEDOR: PIPELINE SUNSAVER                           │
│                                                                                  │
│  ┌─────────────────────────────────────────────────────────────────────────────┐ │
│  │  pipeline_runner.py  ← ORQUESTADOR (Stage-gate, Auditoría, CLI)             │ │
│  └───────┬─────────────────────────────────────────────────────────────────────┘ │
│          │                                                                       │
│    ┌─────▼───────────────────────────────────────────────────────────────────┐   │
│    │  ETAPA 1 — EXTRACCIÓN BRONZE (Segura en paralelo, basada en manifiestos)│   │
│    │  ┌─────────────────────┐      ┌──────────────────────┐                  │   │
│    │  │bronze_ingest_clients│      │bronze_ingest_prices  │                  │   │
│    │  │ Excel → JSON (444)  │      │ API REE → JSON (444) │                  │   │
│    │  └─────────────────────┘      └──────────────────────┘                  │   │
│    └─────────────────────────────────────────────────────────────────────────┘   │
│          │                                                                       │
│    ┌─────▼───────────────────────────────────────────────────────────────────┐   │
│    │  ETAPA 2 — TRANSFORMACIÓN SILVER (Basada en manifiestos, idempotente)   │   │
│    │  ┌──────────────────────┐      ┌──────────────────────┐                 │   │
│    │  │silver_transform_     │      │silver_transform_     │                 │   │
│    │  │clients               │      │prices                │                 │   │
│    │  │ JSON → clean_clients │      │ JSON → clean_prices  │                 │   │
│    │  └──────────────────────┘      └──────────────────────┘                 │   │
│    └─────────────────────────────────────────────────────────────────────────┘   │
│          │                                                                       │
│    ┌─────▼───────────────────────────────────────────────────────────────────┐   │
│    │  ETAPA 3 — WEATHER BRONZE (Bucle por coordenadas, fallos aislados)      │   │
│    │  ┌─────────────────────────────────────────────────────────────────┐    │   │
│    │  │ bronze_ingest_weather_owm (lee clean_clients para coordenadas)  │    │   │
│    │  │ API OWM → JSON por cliente (444)                                │    │   │
│    │  └─────────────────────────────────────────────────────────────────┘    │   │
│    └─────────────────────────────────────────────────────────────────────────┘   │
│          │                                                                       │
│    ┌─────▼───────────────────────────────────────────────────────────────────┐   │
│    │  ETAPA 4 — WEATHER SILVER (Remuestreo 3h→1h, ingeniería de atributos)   │   │
│    │  ┌─────────────────────────────────────────────────────────────────┐    │   │
│    │  │ silver_transform_weather → clean_weather                        │    │   │
│    │  └─────────────────────────────────────────────────────────────────┘    │   │
│    └─────────────────────────────────────────────────────────────────────────┘   │
│          │                                                                       │
│    ┌─────▼───────────────────────────────────────────────────────────────────┐   │
│    │  ETAPA 5 — MOTOR DE FÍSICA FV (Simulación por fila, vectorizada)        │   │
│    │  ┌───────────────────────┐    ┌───────────────────────────────────┐     │   │
│    │  │silver_calc_pv_        │───►│ engine_pv_physics.py              │     │   │
│    │  │generation             │    │ Pos. Solar → GHI → DNI/DHI →      │     │   │
│    │  │ → clean_calculations  │    │ POA → Faiman → P_AC + P_carga     │     │   │
│    │  └───────────────────────┘    └───────────────────────────────────┘     │   │
│    └─────────────────────────────────────────────────────────────────────────┘   │
│          │                                                                       │
│    ┌─────▼───────────────────────────────────────────────────────────────────┐   │
│    │  ETAPA 6 — CAPA GOLD (Esquema en estrella, reconstrucción atómica)      │   │
│    │  ┌──────────────┐ ┌──────────────┐ ┌──────────────┐ ┌────────────┐      │   │
│    │  │dim_client    │ │dim_datetime  │ │dim_weather   │ │fact_energy │      │   │
│    │  │(has_solar,   │ │(tarifa 2.0TD,│ │(desc. modal  │ │_forecast   │      │   │
│    │  │ has_battery) │ │ festivos)    │ │ por ID)      │ │(multi-JOIN)│      │   │
│    │  └──────────────┘ └──────────────┘ └──────────────┘ └────────────┘      │   │
│    └─────────────────────────────────────────────────────────────────────────┘   │
│                                                                                  │
│  ┌─────────────────────────────────────────────────────────────────────────────┐ │
│  │  TRANSVERSALES: config_paths.py · logger_config.py · audit_metadata.py      │ │
│  └─────────────────────────────────────────────────────────────────────────────┘ │
└──────────────────────────────────────────────────────────────────────────────────┘
```

**Estructura de ficheros (on-premise):**
```
project_root/
├── data/
│   ├── bronze/                  ← Ficheros brutos inmutables (chmod 444)
│   │   ├── clients_YYYYMMDD_HHMMSS.json
│   │   ├── prices_YYYYMMDD_HHMMSS.json
│   │   ├── weather_{client_id}_YYYYMMDD_HHMMSS.json
│   │   ├── _process_manifest_clients.json     ← Control de procesos
│   │   ├── _process_manifest_ree.json
│   │   └── _process_manifest_openweather.json
│   ├── sunsaver.db              ← Silver + Gold (SQLite)
│   └── clients_source.xlsx      ← Datos maestros de clientes
├── logs/
│   └── sunsaver_YYYY-MM-DD.log  ← Logs con rotación diaria
└── src/                         ← Scripts del pipeline
```

### 3.3 Principios de Diseño Adoptados

**Principio de Responsabilidad Única (SRP):** Cada módulo tiene exactamente una responsabilidad. `engine_pv_physics.py` hace física — no tiene E/S. `config_paths.py` resuelve rutas — no tiene lógica de negocio. Esta separación hace que los tests unitarios, el reemplazo y la depuración sean deterministas.

**Inmutabilidad en la ingesta (Sellado Bronze):** Los datos brutos nunca se modifican tras la escritura. Los ficheros se sellan con `chmod 444`. Es el equivalente en ingeniería de datos del almacenamiento WORM (write-once-read-many), permitiendo el reprocesamiento completo desde la fuente en cualquier momento.

**Idempotencia en cada frontera de escritura:** Todas las escrituras en Silver y Gold usan `INSERT OR REPLACE` con claves naturales compuestas. Ejecutar el pipeline dos veces produce resultados idénticos — sin duplicados, sin deriva.

**Control de flujo basado en manifiestos:** La promoción de Bronze a Silver está gobernada por manifiestos de proceso (ficheros JSON de control por fuente de datos). Esto desacopla el timing de la ingesta del de la transformación y proporciona un mecanismo de reintento integrado para tareas fallidas (estado `error` → vuelve a encolarse en la siguiente ejecución).

**Fallo rápido con degradación elegante:** El orquestador implementa lógica de aborte por etapa — si una etapa completa falla, el pipeline aborta antes de que las etapas posteriores se ejecuten con datos de entrada corruptos. Dentro de una etapa, los fallos individuales de pasos se toleran y se registran (estado de ÉXITO PARCIAL).

**Modelado de datos orientado a la física:** Todos los parámetros de simulación usan modelos científicos validados (pvlib, Erbs, Faiman). Las constantes empíricas (atenuación por nubes, factores de transmitancia) están documentadas en línea con sus fuentes académicas. El motor de física está diseñado para cortocircuitar de forma segura cuando los inputs son físicamente imposibles (elevación solar < 2° → salida cero).

---

## 4. Justificación de la Arquitectura Medallion

### 4.1 Por qué Bronze / Silver / Gold

La Arquitectura Medallion (también conocida como patrón Delta Lake, popularizada por Databricks) fue seleccionada como paradigma fundamental de organización del dato. La decisión no estuvo motivada por seguir una tendencia sino por un requisito específico: **la necesidad de versionar, reprocesar y auditar de forma independiente cada etapa de transformación sin perder la capacidad de trazar cualquier valor de salida hasta su fuente bruta.**

En el dominio de la gestión energética industrial, esto no es negociable. Si la previsión de generación de un cliente es incorrecta, el camino de investigación debe ser determinista: respuesta bruta de la API → valores parseados → inputs del modelo de física → salida calculada. La arquitectura de tres capas proporciona esta trazabilidad de forma nativa.

**Bronze (Capa de Ingesta Bruta):**
- Contiene las respuestas literales de las APIs y el contenido del fichero fuente, almacenados como ficheros JSON con marca temporal.
- Los ficheros se sellan (chmod 444) en el momento de la escritura — no pueden modificarse, solo leerse.
- Actúa como registro de auditoría persistente y fuente completa de reprocesamiento.
- No se aplica lógica de negocio en esta capa. Los datos brutos incluyen valores NaN, tipos inconsistentes y registros parciales.

**Silver (Capa Refinada / Limpia):**
- Contiene datos validados, tipados, deduplicados y con reglas de negocio aplicadas en tablas SQLite.
- Sirve como superficie de join autoritativa: `clean_clients`, `clean_prices`, `clean_weather`, `clean_calculations`.
- Los datos en esta capa satisfacen un contrato de esquema definido (restricciones NOT NULL, claves primarias, validaciones de rango físico).
- La simulación de física se ejecuta en esta capa, produciendo `clean_calculations` como el conjunto de datos derivado principal.

**Gold (Capa Analítica / de Servicio):**
- Contiene el esquema en estrella optimizado para consumo analítico.
- `gold_fact_energy_forecast` es la tabla de hechos desnormalizada que une todas las dimensiones; es el producto principal de la plataforma y el input directo para cuadros de mando y herramientas de apoyo a la decisión.
- Todas las tablas dimensionales (`gold_dim_client`, `gold_dim_datetime`, `gold_dim_weather`) se reconstruyen atómicamente en cada ejecución del pipeline.
- Los índices sobre `unix_time` y `weather_id` garantizan respuestas sub-segundo en las consultas de los dashboards.

### 4.2 Criterios de Promoción entre Capas

Un registro se promueve de Bronze a Silver cuando satisface todos los criterios siguientes:

| Criterio | Validación aplicada |
|---|---|
| Completitud del esquema | Los campos críticos (`client_id`, `latitude`, `longitude`, `pv_peak_power_kw`) son no nulos |
| Validez de tipo | Todos los campos numéricos se coaccionan con éxito; los campos datetime se parsean con conciencia UTC |
| Validez de rango físico | Coordenadas dentro de [-90,90] / [-180,180]; ángulo de inclinación dentro de [0,90]; precio dentro de [-100, 2.000] €/MWh |
| Consistencia lógica | `pv_peak_power_kw > 0` (los clientes sin generación solar no tienen razón de estar en el sistema) |
| Deduplicación | Se conserva el registro ingestado más recientemente por clave natural |

Un registro Silver se promueve a Gold cuando:
- Cae dentro de la ventana de procesamiento (`unix_time >= ahora − 2 horas` para la tabla de hechos)
- Todas las superficies de join requeridas están disponibles (los LEFT JOINs garantizan que los datos parciales nunca sean una condición de bloqueo)

### 4.3 Alternativas Consideradas y Descartadas

**Arquitectura Lambda (batch + streaming):**
Rechazada. Las fuentes de datos de SunSaver son inherentemente batch (REE publica precios una vez al día; la granularidad de previsión de OWM es de 3 horas). Mantener una arquitectura de doble camino (lote + velocidad) añadiría complejidad operativa sin ningún beneficio. El patrón Medallion cubre completamente el perfil de latencia requerido.

**Pipeline de ficheros planos (CSV de entrada y salida):**
Rechazada. Los ficheros CSV no proporcionan aplicación de esquema, transacciones atómicas, semántica de joins ni trazabilidad de auditoría. El enfoque de manifiestos + SQLite proporciona todo esto a coste de infraestructura adicional cero.

**SGBD completo (PostgreSQL) desde el primer día:**
Considerada y aplazada. PostgreSQL proporcionaría concurrencia multi-usuario, extensiones (TimescaleDB para series temporales) y acceso en red. Sin embargo, para la escala actual (despliegue on-premise mono-cliente, <50 clientes, <1M de filas), la sobrecarga operativa de gestionar un servidor Postgres supera los beneficios. SQLite ofrece semántica de consultas idéntica, se ejecuta en proceso, requiere configuración cero y soporta transacciones atómicas. El camino de migración a PostgreSQL está documentado en la hoja de ruta.

**Ficheros Parquet para la capa Silver:**
Considerada. Parquet proporcionaría compresión columnar y compatibilidad con pandas/Spark. Rechazada para Silver porque añade una dependencia de librería de E/S columnar, pierde la capacidad de usar SQL para inspección ad-hoc y no ofrece ninguna ventaja con los volúmenes de datos actuales. Parquet es la elección correcta para Bronze si la plataforma escala a volúmenes de ingesta diaria de varios gigabytes — esto está documentado como camino futuro de migración.

---

## 5. Decisiones sobre el Stack Tecnológico

### 5.1 Selección de Base de Datos (por capa)

| Capa | Formato de almacenamiento | Justificación |
|---|---|---|
| Bronze | Ficheros JSON (con marca temporal, chmod 444) | Máxima fidelidad a la fuente; sin pérdida de parseo; inmutable por permiso del SO; legible por humanos para depuración |
| Silver | SQLite (sunsaver.db) | Sin configuración, basado en fichero, ACID completo, SQL estándar, semántica UPSERT, PKs compuestas, suficiente para ≤100 clientes |
| Gold | SQLite (misma base de datos) | Co-ubicado con Silver para eficiencia de joins; espacio de nombres lógico separado por convención de nomenclatura de tablas; backup de un solo fichero |
| Control de procesos | Manifiestos JSON (por fuente) | Legibles por humanos, trivialmente versionables, sin dependencia externa, semántica de log de solo-adición |
| Auditoría / telemetría | SQLite (tabla etl_metadata) | Estructurado, consultable, co-ubicado; no requiere infraestructura de monitorización externa para v1.0 |

**SQLite fue elegido específicamente frente a alternativas porque:**
- El despliegue on-premise con un único proceso escritor elimina la limitación principal de SQLite (concurrencia de escritura).
- El fichero SQLite puede abrirse directamente en DB Browser for SQLite (como evidencian las capturas del proyecto), permitiendo a las partes interesadas no técnicas inspeccionar datos sin herramientas adicionales.
- El backup es un simple `cp sunsaver.db sunsaver.db.bak` — trivial operativamente.
- SQLite soporta funciones de ventana (`ROW_NUMBER() OVER PARTITION BY`) usadas en `gold_dim_weather.py`, confirmando que la versión en uso es ≥ 3.25.0.

### 5.2 Selección del Orquestador

**Elegido: Orquestador Python personalizado (`pipeline_runner.py`)**

Una decisión deliberada de construir un orquestador ligero y autocontenido en lugar de adoptar Apache Airflow, Prefect o Dagster.

Justificación:
- El pipeline tiene una topología fija y acíclica (6 etapas, 11 pasos). La generación dinámica de DAGs no aporta valor a esta escala.
- Airflow requiere una base de datos de metadatos, un servidor web, un proceso planificador y workers ejecutores. Es una infraestructura desproporcionada para un despliegue on-premise en PYME.
- El orquestador personalizado proporciona flags `--stage N` (reanudar) y `--dry-run` (planificación), temporización por paso, lógica de aborte por etapa y persistencia de auditoría — cubriendo el 100 % de los requisitos operativos.
- El orquestador son 120 líneas de Python idiomático, totalmente legible y mantenible por cualquier ingeniero de nivel medio sin formación en Airflow.

El camino de migración a un orquestador gestionado (Prefect Cloud o Airflow en Docker) está definido para la hoja de ruta SaaS multi-tenant.

### 5.3 Lenguaje y Frameworks

**Python 3.12** — lenguaje principal.

| Librería | Rol | Justificación |
|---|---|---|
| `pvlib` | Posición solar e irradiancia | Librería de modelado FV validada por NREL, estándar de la industria; algoritmos revisados por pares |
| `pandas` | Manipulación de datos tabulares | Estándar para ETL; operaciones vectorizadas; lectura/escritura SQL directa vía `pd.read_sql` / `to_sql` |
| `SQLAlchemy` | Abstracción de base de datos | Transacciones a nivel de motor; consultas parametrizadas (prevención de inyección SQL); ORM opcional |
| `numpy` | Computación numérica | Trigonometría vectorizada para el motor de física; requerido por pvlib |
| `requests` | Llamadas HTTP a APIs | Ligero, probado en producción; gestión de timeouts y errores integrada |
| `python-dotenv` | Gestión de variables de entorno | Credenciales nunca hardcodeadas; patrón de fichero `.env` universalmente conocido |
| `openpyxl` | Ingesta de Excel | Requerido por pandas para parseo de `.xlsx` |

**Ausencias notables (justificadas):**
- Sin `celery` / `redis` — no se requiere cola de tareas asíncrona para pipeline batch secuencial.
- Sin `pydantic` — la validación de datos se realiza en las transformaciones pandas; los modelos Pydantic serían apropiados para una capa API REST (hoja de ruta).
- Sin `pytest` en el código base principal — la suite de tests es un elemento definido en la hoja de ruta.

### 5.4 Infraestructura (On-premise)

**Topología de despliegue (actual):**
```
Servidor Linux único (Ubuntu 24)
├── Entorno virtual Python 3.12 (venv)
├── Tarea cron (o temporizador systemd) → python pipeline_runner.py
├── /data/bronze/         ← Montable por NFS para backup
├── /data/sunsaver.db     ← Objetivo de backup de fichero único
└── /logs/                ← Rotación de logs vía logrotate
```

**Manual operativo simplificado:**
```bash
# Pipeline completo
python pipeline_runner.py

# Reanudar desde la extracción de meteorología (omitir re-ingesta Bronze de clientes/precios)
python pipeline_runner.py --stage 3

# Validar plan de ejecución sin efectos secundarios
python pipeline_runner.py --dry-run
```

**Estrategia de backup:** `cp sunsaver.db sunsaver.db.$(date +%Y%m%d)` diario vía cron. El directorio Bronze es de solo-adición y puede archivarse en almacenamiento de objetos de forma independiente a la base de datos.

---

## 6. Registro ADR — Decisiones Individuales de Arquitectura

---

### ADR-001: Arquitectura Medallion vs. Arquitectura Lambda

**Fecha:** 2025-04
**Estado:** Aceptado
**Decisores:** Aitor Asin

**Contexto:**
El sistema requiere ingestar datos de dos APIs externas (batch, diario) y una fuente Excel interna, transformarlos y enriquecerlos a través de un motor de física, y hacer los resultados disponibles para consultas analíticas. Se evaluaron dos patrones competidores: Medallion (capas batch) y Lambda (dual batch + velocidad).

**Decisión:**
Adoptar la Arquitectura Medallion (Bronze → Silver → Gold).

**Justificación:**
1. La latencia de las fuentes de datos es inherentemente batch (REE: diario; OWM: 3 horas). No existe ninguna fuente de datos en streaming que justifique una capa de velocidad.
2. El patrón Medallion proporciona trazabilidad completa desde la respuesta bruta de la API hasta la salida analítica, permitiendo el reprocesamiento determinista.
3. La sobrecarga operativa de la arquitectura Lambda (mantener dos caminos de código que deben producir resultados idénticos) no está justificada cuando el camino batch por sí solo satisface todos los requisitos de latencia.

**Consecuencias:**
+ Trazabilidad completa y capacidad de reprocesamiento desde Bronze.
+ Base de código más simple (un único camino de código).
− No adecuado si se introduce un feed de datos SCADA en tiempo real (Lambda o Kappa serían necesarios).

---

### ADR-002: Formato de Almacenamiento Bronze — JSON vs. Parquet vs. Respuesta API Bruta

**Fecha:** 2025-04
**Estado:** Aceptado
**Decisores:** Aitor Asin

**Contexto:**
La capa Bronze debe almacenar la salida literal de dos APIs REST (REE, OpenWeatherMap) y un fichero Excel. El formato debe preservar la fidelidad completa, ser legible por humanos para depuración y no imponer pérdidas de parseo.

**Decisión:**
Almacenar datos Bronze como ficheros JSON inmutables con marca temporal y `chmod 444`.

**Justificación:**
1. Las APIs REST devuelven JSON de forma nativa. Almacenar la respuesta literalmente requiere cero parseo en el momento de la ingesta, eliminando la posibilidad de pérdida de datos inducida por el formato.
2. JSON es legible por humanos. Depurar un fichero Bronze requiere `cat` o cualquier editor de texto — sin dependencia de herramientas.
3. `chmod 444` proporciona garantías de inmutabilidad a nivel del SO sin requerir un sistema de almacenamiento especializado (Delta Lake, Iceberg).
4. La convención de nomenclatura de ficheros (`{fuente}_{marca_temporal}.json`) proporciona particionado implícito por fecha de ingesta.

**Alternativas consideradas:**
- **Parquet:** Proporciona compresión columnar y aplicación de esquema. Rechazado porque requiere un lector columnar, no es legible por humanos y no ofrece ventaja a los volúmenes de datos actuales (<1 MB por fichero Bronze).
- **Tabla SQLite (raw_clients, raw_prices, raw_weather):** Permitiría consultar los datos Bronze con SQL pero pierde la garantía de inmutabilidad e introduce acoplamiento de esquema a la estructura de la fuente bruta.

**Consecuencias:**
+ Fidelidad completa de la respuesta API; sin pérdida de datos en Bronze.
+ Inmutabilidad a nivel del SO (chmod 444).
+ Depuración legible por humanos.
− Requiere un sistema de manifiestos para rastrear el estado de procesamiento (resuelto por los manifiestos de proceso).

---

### ADR-003: Motor de Transformación Silver — pandas + SQLAlchemy vs. Solo SQL vs. Spark

**Fecha:** 2025-04
**Estado:** Aceptado
**Decisores:** Aitor Asin

**Contexto:**
La capa Silver debe parsear estructuras JSON anidadas (previsión de 5 días de OpenWeatherMap con 40 slots por cliente), aplicar remuestreo de series temporales (3h → 1h mediante interpolación lineal), aplicar reglas de negocio y persistir resultados en SQLite. El motor de transformación debe ser mantenible por un único ingeniero.

**Decisión:**
Usar pandas para transformación en memoria y SQLAlchemy para E/S de base de datos.

**Justificación:**
1. El payload de OpenWeatherMap es una estructura JSON anidada con arrays. Las operaciones `json_normalize` y `resample` de pandas manejan esto de forma nativa; las CTEs SQL requerirían múltiples niveles de funciones de extracción JSON específicas del dialecto SQLite.
2. La descomposición de irradiancia de Erbs y el modelo de temperatura de célula de Faiman requieren operaciones numéricas por fila. pandas iterrows + numpy es la abstracción correcta para operaciones de física por fila; SQL no puede expresar estos modelos.
3. SQLAlchemy proporciona ejecución de consultas parametrizadas (protección contra inyección SQL) y gestión de transacciones a nivel de motor, apropiada para el patrón de upsert `INSERT OR REPLACE`.
4. Spark (PySpark) proporcionaría procesamiento distribuido a escala. Con el volumen de datos actual (<10.000 filas por ejecución), la sobrecarga de arranque de la JVM de Spark haría la ejecución del pipeline más lenta, no más rápida.

**Consecuencias:**
+ Remuestreo temporal expresivo (pandas resample/interpolate).
+ Ejecución del modelo de física por fila.
+ Prevención de inyección SQL vía parametrización SQLAlchemy.
− El modelo de memoria de pandas está orientado a filas; con >10M filas se requeriría vectorización a polars u operaciones columnares.

---

### ADR-004: Modelo Dimensional Gold — Esquema en Estrella vs. Tabla Plana Desnormalizada

**Fecha:** 2025-04
**Estado:** Aceptado
**Decisores:** Aitor Asin

**Contexto:**
La capa Gold debe servir consultas analíticas eficientemente: "¿cuál fue la generación solar para el cliente X a la hora Y?", "¿cuál fue el precio PVPC durante el periodo tarifario P1 la semana pasada?", "¿qué clientes tienen un balance energético neto positivo durante las horas pico?". El modelo debe ser accesible para herramientas no SQL (Power BI, Excel) sin requerir joins complejos.

**Decisión:**
Implementar un esquema en estrella con una tabla de hechos (`gold_fact_energy_forecast`) y tres tablas dimensionales (`gold_dim_client`, `gold_dim_datetime`, `gold_dim_weather`).

**Justificación:**
1. El esquema en estrella minimiza la complejidad de las consultas para herramientas BI. Power BI y Tableau entienden de forma nativa las relaciones en esquema en estrella; una tabla totalmente plana requeriría medidas repetidas para los atributos dimensionales.
2. `gold_dim_datetime` proporciona la clasificación del período tarifario 2.0TD (`P1 Punta / P2 Llano / P3 Valle / P6 Super-Valle`) como atributo precalculado. Es costoso calcularlo en tiempo de consulta (requiere conversión de zona horaria + evaluación de reglas de negocio) pero trivial como join dimensional.
3. `gold_dim_weather` usa una función de ventana `ROW_NUMBER() OVER PARTITION BY` para resolver el mapeo muchos-a-uno entre `weather_id` y descripciones meteorológicas — un patrón que demuestra el uso intencional de funciones analíticas SQL en lugar de deduplicación a nivel de aplicación.
4. La tabla de hechos usa `INSERT OR REPLACE` (upsert) con una ventana de retroceso de 2 horas, permitiendo actualizaciones incrementales sin reconstrucciones completas de tabla.

**Consecuencias:**
+ Modelo listo para herramientas BI (Power BI, Tableau, Apache Superset).
+ Período tarifario y festivos precalculados eliminan el cálculo en tiempo de consulta.
+ Índices compuestos sobre `unix_time` y `weather_id` proporcionan respuesta analítica sub-segundo.
− Las tablas dimensionales se reconstruyen atómicamente en cada ejecución (DROP + CREATE + INSERT en una única transacción). Para tablas con >1M filas este enfoque requeriría gestión incremental de SCD (Dimensiones de Cambio Lento).

---

### ADR-005: Estrategia de Particionado — Nomenclatura Temporal de Ficheros vs. Particionado por Directorios

**Fecha:** 2025-04
**Estado:** Aceptado
**Decisores:** Aitor Asin

**Contexto:**
La capa Bronze acumula un fichero por llamada API por ejecución. Sin particionado, el directorio Bronze se convierte en una lista plana de ficheros difícil de consultar o archivar. Se requiere una estrategia de particionado que equilibre la simplicidad con la utilidad operativa.

**Decisión:**
Adoptar particionado implícito por marca temporal vía convención de nomenclatura de ficheros (`{fuente}_{YYYYMMDD_HHMMSS}.json`) en la capa Bronze. Para las capas Silver/Gold en SQLite, particionar por claves primarias compuestas `(client_id, unix_time)`.

**Justificación:**
1. El particionado basado en nombre de fichero no requiere infraestructura. Los ficheros se ordenan cronológicamente con `ls` y se filtran trivialmente por prefijo de fecha.
2. El sistema de manifiestos de proceso (`_process_manifest_{fuente}.json`) proporciona un índice explícito de ficheros Bronze por estado (pendiente / éxito / error), que es más útil operativamente que el particionado por directorios.
3. Con los volúmenes actuales (<100 ficheros/día), el particionado por directorios (ej. `bronze/2025/05/10/`) añade complejidad de rutas sin beneficio alguno en el rendimiento de consultas.
4. La PK compuesta `(client_id, unix_time)` en tablas Silver/Gold proporciona el equivalente funcional del particionado multidimensional para consultas SQL.

**Consecuencias:**
+ Cero sobrecarga de infraestructura para el particionado Bronze.
+ El manifiesto proporciona estado de procesamiento explícito sin traversal del sistema de ficheros.
− Con alto volumen (>10.000 ficheros/día), el particionado por nombre de fichero se vuelve inmanejable; se requeriría jerarquía de directorios.

---

### ADR-006: Gestión de Secretos y Credenciales de APIs

**Fecha:** 2025-04
**Estado:** Aceptado
**Decisores:** Aitor Asin

**Contexto:**
El pipeline requiere dos secretos: `WEATHER_API_KEY` (OpenWeatherMap) y opcionalmente `DB_PATH`, `BRONZE_PATH`, `CLIENTS_SOURCE_PATH` (sobreescrituras de rutas). Estos deben ser accesibles en tiempo de ejecución sin estar hardcodeados en el código fuente.

**Decisión:**
Usar fichero `.env` + `python-dotenv` para la gestión de secretos local. El `.env` se excluye del control de versiones vía `.gitignore`. La configuración de rutas se centraliza en `config_paths.py`.

**Justificación:**
1. La metodología de aplicaciones de 12 factores exige configuración basada en entorno. `.env` + `python-dotenv` es la implementación Python idiomática para desarrollo local y despliegue on-premise.
2. Centralizar la resolución de rutas en `config_paths.py` garantiza que cambiar la ruta de la base de datos (ej. para un entorno de staging) requiere modificar un fichero o una variable de entorno — no buscar en 15 scripts.
3. El helper `_get_validated_path()` en `config_paths.py` crea automáticamente los directorios requeridos (equivalente a `mkdir -p`) y valida la resolución de rutas, eliminando excepciones `FileNotFoundError` por mala configuración.

**Estado futuro:** Para un despliegue cloud multi-tenant, este patrón se reemplazaría por un servicio de gestión de secretos (HashiCorp Vault, AWS Secrets Manager, Azure Key Vault). La interfaz de `config_paths.py` está diseñada para ser un objetivo de sustitución directa — todos los consumidores referencian `config_paths.get_db_path()`, no `os.getenv("DB_PATH")` directamente.

**Consecuencias:**
+ Sin credenciales hardcodeadas en el código fuente.
+ Gestión centralizada de rutas (`config_paths.py`).
+ `.gitignore` previene la exposición accidental de credenciales.
− El fichero `.env` en disco es un riesgo de seguridad si el servidor se ve comprometido. Para producción, se requiere un gestor de secretos dedicado (elemento de hoja de ruta).

---

## 7. Preocupaciones Transversales

### 7.1 Seguridad y Control de Acceso

**Estado actual (v1.0 — on-premise, usuario único):**

- Claves API almacenadas en `.env` con permisos `600` (solo lectura/escritura del propietario).
- Ficheros Bronze sellados con `chmod 444` — la modificación requiere un `chmod` explícito, creando un evento de auditoría.
- El acceso al fichero de base de datos SQLite está controlado por permisos del sistema de ficheros del SO.
- Sin capa de autenticación en las salidas de datos (acceso directo a fichero/base de datos).

**Fronteras de seguridad:**
```
[APIs Externas] ──HTTPS──► [Pipeline] ──escritura fichero──► [sunsaver.db]
                                                                  │
                                                         chmod 444 (Bronze)
                                                         ACL filesystem SO (BD)
```

**Brechas de seguridad identificadas (v1.0, riesgo aceptado):**
- Sin cifrado en reposo para la base de datos SQLite. Los datos energéticos de clientes y coordenadas de ubicación se almacenan en texto plano. Aceptable para despliegue on-premise mono-tenant; inaceptable para cloud/SaaS.
- Sin limitación de tasa ni circuit breaker en llamadas API salientes. Si REE u OWM limita la tasa del cliente, el pipeline fallará con un error HTTP y requerirá reintento manual.
- Sin saneamiento de inputs más allá de la coerción de tipos de pandas. El fichero Excel maestro de clientes se confía implícitamente; un Excel malicioso con inyección de fórmulas podría ser un vector de ataque.

### 7.2 Observabilidad — Logs, Métricas, Trazas

**Arquitectura de logging:**

El módulo `logger_config.py` implementa un logger singleton (`SunSaver`) con las siguientes propiedades:
- **Doble destino:** Salida simultánea a fichero de log rotatorio diario (`logs/sunsaver_YYYY-MM-DD.log`) y consola.
- **Formato estructurado:** `MARCA_TEMPORAL | NIVEL | MÓDULO | MENSAJE` — parseable por herramientas estándar de agregación de logs (Filebeat, Fluentd).
- **Niveles de log:** DEBUG (deshabilitado en handlers en producción), INFO (eventos operativos), WARNING (calidad de dato degradada), ERROR (fallo de paso), CRITICAL (aborte del pipeline).
- **Guardia singleton:** La comprobación `if logger.handlers: return logger` evita la adición duplicada de handlers cuando múltiples módulos importan el logger en el mismo proceso.

**Prefijos de log por módulo (convención aplicada):**
```
[INIT]      ← Inicio de etapa/módulo
[EXTRACT]   ← Operaciones de lectura de datos
[TRANSFORM] ← Aplicación de lógica de negocio
[LOAD]      ← Operaciones de escritura en base de datos
[BRONZE]    ← Persistencia en Bronze
[MANIFEST]  ← Actualizaciones del control de procesos
[METADATA]  ← Escrituras en tabla de auditoría
[DONE]      ← Finalización exitosa
[ERROR]     ← Error gestionado
```

**Telemetría de ejecución del pipeline (tabla `etl_metadata`):**

Cada ejecución del pipeline persiste un registro en `etl_metadata` con: nombre del pipeline, estado de ejecución (SUCCESS / PARTIAL SUCCESS / FAILED), duración en segundos, total de filas afectadas, cadena de detalle de error, entorno y marca temporal UTC de ejecución. Esta tabla es la superficie principal de monitorización de SLA.

**Brechas de observabilidad (v1.0, documentadas):**
- Sin trazas distribuidas (OpenTelemetry). La temporización por paso está disponible en logs pero no como trazas estructuradas.
- Sin endpoint de métricas (Prometheus). La salud del pipeline solo es observable consultando `etl_metadata` o leyendo logs.
- Sin alertas. Un pipeline fallido produce una entrada de log y un estado FAILED en `etl_metadata` pero no dispara ninguna notificación (email, Slack, PagerDuty).

### 7.3 Gestión de Errores y Reintentos

**Estrategia de gestión de errores:**

El pipeline implementa un modelo de gestión de errores de tres niveles:

**Nivel 1 — Motor de física (a nivel de función):** Cada función de `engine_pv_physics.py` envuelve su computación en un bloque `try/except` y devuelve un valor seguro por defecto (típicamente `0.0`) ante cualquier excepción. Esto garantiza que una única fila malformada nunca hace caer el pipeline — produce un registro de generación cero en su lugar, que es una salida correcta y conservadora.

**Nivel 2 — A nivel de paso (orquestador):** Cada paso del pipeline se ejecuta dentro de `run_step()`, que captura todas las excepciones, las registra con traza completa (`exc_info=True`) y devuelve `(False, 0)`. El orquestador acumula recuentos de pasos fallidos sin propagar la excepción.

**Nivel 3 — A nivel de etapa (puerta de aborte):** Si `all()` los pasos dentro de una etapa devuelven `False`, el orquestador llama a `logger.critical()` y devuelve `False`, evitando que las etapas posteriores se ejecuten con datos de entrada corruptos.

**Mecanismo de reintentos:**

El sistema de manifiestos proporciona reintento automático para fallos de Bronze a Silver. Las tareas con estado `error` en un manifiesto de proceso se vuelven a encolar en la siguiente ejecución del pipeline junto con las tareas `pending`. Esto cubre fallos transitorios (timeout de red, indisponibilidad de API) sin requerir intervención manual.

**Gestión de disponibilidad de API (específica de REE):**

La API de REE no devuelve datos PVPC antes de las ~20:30 CET. `extract_energy_prices()` devuelve `False` (no una excepción) cuando no hay datos disponibles, lo que dispara un estado de ÉXITO PARCIAL del pipeline en lugar de un fallo total. Este es el comportamiento correcto: el pipeline puede completar las etapas 3–6 con datos de precios cacheados de una ejecución anterior.

### 7.4 Estrategia de Versionado de Datos

**Versionado Bronze (implícito, mediante ficheros con marca temporal):**
Cada ingesta Bronze crea un nuevo fichero con marca temporal. El historial completo de respuestas API se preserva indefinidamente (sujeto a capacidad de disco). Esto proporciona capacidad de reprocesamiento en un punto temporal: cualquier estado histórico de la capa Silver o Gold puede reconstruirse reproduciendo los ficheros Bronze del rango de marca temporal correspondiente.

**Versionado Silver (basado en upsert, estado actual):**
Las tablas Silver mantienen la vista del estado actual. Los registros Silver históricos son sobreescritos por ingestas más recientes para la misma clave `(client_id, unix_time)`. La recuperación en un punto temporal requiere reproducir desde Bronze.

**Versionado Gold (reconstrucción atómica para dimensiones, incremental para hechos):**
Las tablas dimensionales se reconstruyen atómicamente en cada ejecución (DROP + CREATE + INSERT en transacción). La tabla de hechos usa upsert incremental con una ventana de retroceso de 2 horas. Esto significa que la capa Gold está siempre actualizada pero no mantiene snapshots históricos.

**Versionado de esquema:**
No existe un framework formal de migración de esquema en v1.0. Los cambios de esquema requieren ejecución manual de DDL. El patrón `metadata.create_all()` de SQLAlchemy en `audit_metadata.py` proporciona evolución aditiva del esquema (nuevas tablas) pero no migraciones a nivel de columna. La integración de Alembic es un elemento definido en la hoja de ruta.

---

## 8. Hoja de Ruta Técnica

### 8.1 Deuda Técnica Conocida

| ID | Elemento | Impacto | Esfuerzo | Prioridad |
|---|---|---|---|---|
| DT-01 | Sin suite de tests automatizados | Medio: las regresiones en el motor de física o la lógica de transformación se detectan manualmente | Alto | Alta |
| DT-02 | Sin framework de migración de esquema (Alembic) | Medio: los cambios de esquema requieren DDL manual; riesgo de deriva del esquema en producción | Medio | Alta |
| DT-03 | Sin alertas ante fallo del pipeline | Alto: una ejecución nocturna fallida no se detecta hasta la inspección manual de logs | Bajo | Alta |
| DT-04 | El modelo de consumo industrial es sintético (turnos + ruido gaussiano) | Alto: las estimaciones de consumo son aproximaciones, no valores medidos reales | Alto (requiere integración SCADA) | Medio |
| DT-05 | Sin limitación de tasa / circuit breaker en llamadas API | Bajo: aceptable para mono-tenant; el riesgo aumenta con el número de clientes | Bajo | Medio |
| DT-06 | Restricción de escritor único de SQLite | Bajo a escala actual; se vuelve bloqueante con >10 ejecuciones de pipeline concurrentes | Medio | Bajo |
| DT-07 | Sin grafo de linaje de datos (a nivel de columna) | Bajo: linaje a nivel de fichero disponible vía manifiestos; el linaje a nivel de columna requiere herramientas adicionales | Medio | Bajo |
| DT-08 | Secretos en fichero `.env` (sin gestor de secretos dedicado) | Bajo on-premise; Alto si se migra a cloud | Bajo | Bajo (hasta migración cloud) |

### 8.2 Mejoras Planificadas

**Fase 1 — Fiabilidad (Q3 2025):**
- Implementar suite de tests `pytest` cubriendo el motor de física (tests unitarios con inputs de geometría solar conocidos), las reglas de transformación Silver (aserciones de calidad de datos) e integridad del esquema Gold (recuento de filas y unicidad de clave primaria).
- Integrar `alembic` para la gestión de migraciones del esquema de base de datos.
- Añadir alertas por email / Slack ante estado FAILED del pipeline mediante un hook ligero de notificación en `pipeline_runner.py`.
- Implementar detección de limitación de tasa de la API de OpenWeatherMap y reintento con backoff exponencial.

**Fase 2 — Inteligencia (Q4 2025):**
- Reemplazar el modelo de consumo sintético con ingesta de datos SCADA/Modbus. Añadir `bronze_ingest_scada.py` y `silver_transform_scada.py` siguiendo el patrón de manifiestos existente.
- Añadir módulo de optimización del estado de carga (SoC) de batería: dada la previsión de generación, la previsión de consumo, los precios PVPC y los parámetros de batería, calcular el programa de carga óptimo para cada cliente.
- Implementar una capa de API REST (FastAPI) para exponer `gold_fact_energy_forecast` como un endpoint JSON, habilitando la integración con sistemas HMI industriales y dashboards personalizados.

**Fase 3 — Escala (Q1 2026):**
- **Criterio de activación de migración de base de datos:** Cuando el número de clientes supere 50 o el recuento de filas de la tabla de hechos supere 500.000, migrar de SQLite a DuckDB (columnar, embebido, sin configuración) o PostgreSQL (multi-escritor, accesible en red).
- **Criterio de activación de migración de almacenamiento:** Cuando el volumen diario de Bronze supere 1 GB, migrar los ficheros JSON a Parquet con particionado al estilo Hive (`bronze/year=2026/month=01/day=15/`).
- **Criterio de activación de migración de orquestación:** Cuando el pipeline se despliegue para múltiples tenants independientes, migrar de `pipeline_runner.py` a Prefect Cloud o Apache Airflow en Docker Compose.
- **Empaquetado cloud-ready:** Contenerizar el pipeline como imagen Docker con configuración basada en variables de entorno, habilitando el despliegue en el runtime de contenedores de cualquier proveedor cloud (AWS ECS, Azure Container Instances, GCP Cloud Run).

**Fase 4 — Plataforma (2026+):**
- Arquitectura SaaS multi-tenant: bases de datos aisladas por tenant, capa de orquestación compartida, onboarding web para nuevos clientes industriales.
- Capa de machine learning: reemplazar las estimaciones de generación del modelo de física con un modelo híbrido física + ML entrenado con datos reales de error de generación vs. previsión. Los datos históricos de `gold_fact_energy_forecast` de la capa Gold son el conjunto de entrenamiento directo.
- Integración con Sistema de Gestión de Energía ISO 50001: mapear las salidas de SunSaver a los indicadores de rendimiento energético (EnPIs) requeridos para la certificación ISO 50001, posicionando la plataforma como herramienta de cumplimiento normativo para clientes industriales.

---

*Documento mantenido por: Aitor Asin*
*Última actualización: 2025-05-10*
*Historial de versiones: [1.0.0] Versión inicial — ADR completo cubriendo todas las decisiones arquitectónicas hasta pipeline v1.0*

---

> **Para preguntas técnicas sobre este documento, consultar el código fuente en `/src/` y los logs de ejecución en `/logs/`. Para preguntas operativas, consultar la tabla de auditoría del pipeline (`etl_metadata`) en `sunsaver.db`.**