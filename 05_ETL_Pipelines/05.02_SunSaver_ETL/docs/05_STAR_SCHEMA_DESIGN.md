# ☀️ SunSaver ETL · Plataforma de Inteligencia Energética Industrial
## 05 Diseño del Star Schema (Gold Layer)

> **Clasificación:** INTERNA &nbsp;|&nbsp; **Estado:** ACTIVO — Entorno DEV &nbsp;|&nbsp; **Capa:** Gold  
> **Audiencia principal:** Analistas de datos, Científicos de datos, Ingenieros BI &nbsp;|&nbsp; **Última actualización:** 2026-05-10

---

## Tabla de Contenidos

1. [Introducción al Modelo Dimensional](#1-introducción-al-modelo-dimensional)
   - 1.1 [Metodología Adoptada — Kimball](#11-metodología-adoptada--kimball)
   - 1.2 [Diagrama Entidad-Relación del Star Schema](#12-diagrama-entidad-relación-del-star-schema)
   - 1.3 [Convenciones de Nomenclatura](#13-convenciones-de-nomenclatura)
   - 1.4 [Gestión de Slowly Changing Dimensions](#14-gestión-de-slowly-changing-dimensions-scd)
2. [Tablas de Hechos](#2-tablas-de-hechos)
   - 2.1 [gold_fact_energy_forecast](#21-gold_fact_energy_forecast)
3. [Tablas de Dimensiones](#3-tablas-de-dimensiones)
   - 3.1 [gold_dim_client](#31-gold_dim_client)
   - 3.2 [gold_dim_datetime](#32-gold_dim_datetime)
   - 3.3 [gold_dim_weather](#33-gold_dim_weather)
4. [Dimensiones Conformadas](#4-dimensiones-conformadas)
   - 4.1 [Listado y Definición Canónica](#41-listado-y-definición-canónica)
   - 4.2 [Guía de Uso para Análisis Cruzados](#42-guía-de-uso-para-análisis-cruzados)
5. [Métricas de Negocio Derivadas](#5-métricas-de-negocio-derivadas)
   - 5.1 [KPIs Industriales](#51-kpis-industriales)
   - 5.2 [KPIs Económicos](#52-kpis-económicos)
   - 5.3 [Métricas Calculadas vs Almacenadas](#53-métricas-calculadas-vs-almacenadas)
   - 5.4 [Guía de Aditividad](#54-guía-de-aditividad-aditivas-semi-aditivas-no-aditivas)
6. [Queries de Referencia](#6-queries-de-referencia)
   - 6.1 [Consultas Tipo por Caso de Uso](#61-consultas-tipo-por-caso-de-uso)
   - 6.2 [Patrones de Filtrado Temporal](#62-patrones-de-filtrado-temporal)
   - 6.3 [Joins Recomendados y Anti-Patrones](#63-joins-recomendados-y-anti-patrones)
   - 6.4 [Consideraciones de Performance](#64-consideraciones-de-performance)

---

## 1. Introducción al Modelo Dimensional

### 1.1 Metodología Adoptada — Kimball

El modelo dimensional de SunSaver sigue la **metodología Kimball** (Bottom-Up Data Warehouse Design), implementando un Star Schema sobre SQLite que organiza los datos en:

- **Una tabla de hechos central** que registra los eventos de negocio medibles (generación PV, consumo, precio por slot horario)
- **Tres tablas de dimensiones** que describen el contexto de cada hecho (quién, cuándo, bajo qué condición meteorológica)

**Principios Kimball aplicados:**

| Principio | Aplicación en SunSaver |
|-----------|----------------------|
| **Grain declaration** | La granularidad es exactamente 1 fila por `(instalación, hora UTC)`. Nunca se almacenan dos hechos para el mismo cliente y slot horario. |
| **Conformed dimensions** | `gold_dim_datetime` y `gold_dim_client` son dimensiones conformadas: cualquier fact table futura que se añada al modelo debe reutilizarlas tal cual, sin crear versiones paralelas. |
| **Surrogate keys** | El sistema usa las claves naturales de las fuentes como PKs (no surrogate keys artificiales), justificado por el contexto single-source y el volumen reducido. En producción multi-fuente se recomienda migrar a surrogate keys enteras. |
| **Slowly Changing Dimensions** | SCD Tipo 1 para clientes (sobreescritura), dimensión estática para tiempo, SCD Tipo 2 lightweight para condiciones meteorológicas. |
| **Fact table additive measures** | Las medidas de potencia (kW), coste (€) y energía (kWh) son aditivas a lo largo de todas las dimensiones. El PR y la eficiencia son no-aditivas (ver sección 5.4). |

---

### 1.2 Diagrama Entidad-Relación del Star Schema

```
                    ┌──────────────────────────────────────┐
                    │          gold_dim_datetime           │
                    │──────────────────────────────────────│
                    │ PK  unix_time        INTEGER         │
                    │     datetime_utc     TEXT            │
                    │     datetime_local   TEXT            │
                    │     date             TEXT            │
                    │     hour_utc         INTEGER         │
                    │     hour_local       INTEGER         │
                    │     day_of_week      TEXT            │
                    │     is_daylight      INTEGER         │
                    │     is_weekend       INTEGER         │
                    │     is_festivo       INTEGER         │
                    │     month            INTEGER         │
                    │     year             INTEGER         │
                    │     tariff_period    TEXT            │
                    │     tariff_label     TEXT            │
                    └──────────────┬───────────────────────┘
                                   │ unix_time
                                   │ (FK)
┌───────────────────────┐          │          ┌─────────────────────────────┐
│    gold_dim_client    │          │          │      gold_dim_weather       │
│───────────────────────│          │          │─────────────────────────────│
│ PK client_id   TEXT   │          │          │ PK weather_id    INTEGER    │
│    name        TEXT   │          │          │    weather_main  TEXT       │
│    latitude    REAL   │          │          │    weather_desc  TEXT       │
│    longitude   REAL   │          │          │    _loaded_at    TEXT       │
│    timezone    TEXT   │          │          └──────────────┬──────────────┘
│    pv_peak_kw  REAL   │          │                         │ weather_id
│    panel_type  TEXT   │          │                         │ (FK)
│    has_solar   INT    │          │                         │
│    has_battery INT    │          │                         │
│    ...         ...    │          │                         │
└──────────┬────────────┘          │                         │
           │ client_id             │                         │
           │ (FK)                  │                         │
           │          ┌────────────┴─────────────────────────┴───────┐
           └──────────┤        gold_fact_energy_forecast             │
                      │──────────────────────────────────────────────│
                      │ PK1 client_id             TEXT    FK→dim_cli │
                      │ PK2 unix_time             INTEGER FK→dim_dt  │
                      │     forecast_time_utc     TEXT               │
                      │ ── MEDIDAS FÍSICAS ───────────────────────── │
                      │     pv_power_gen_kw        REAL   [kW]       │
                      │     pv_performance_ratio   REAL   [0-1]      │
                      │     poa_wm2                REAL   [W/m²]     │
                      │     t_cell_celsius         REAL   [°C]       │
                      │     power_consumption_kw   REAL   [kW]       │
                      │ ── MEDIDAS METEOROLÓGICAS ────────────────── │
                      │     temp_celsius           REAL   [°C]       │
                      │     humidity_pct           REAL   [%]        │
                      │     clouds_pct             REAL   [%]        │
                      │     rain_prob_norm         REAL   [0-1]      │
                      │     wind_speed_mps         REAL   [m/s]      │
                      │ ── MEDIDAS ECONÓMICAS ────────────────────── │
                      │     weather_id             INT    FK→dim_wx  │
                      │     price_pvpc_eur_mwh     REAL   [€/MWh]    │
                      │ ── TÉCNICAS ──────────────────────────────── │
                      │     _loaded_at_utc         TEXT              │
                      └──────────────────────────────────────────────┘
```

---

### 1.3 Convenciones de Nomenclatura

| Ámbito | Patrón | Ejemplo |
|--------|--------|---------|
| Tablas de hechos | `gold_fact_{proceso_negocio}` | `gold_fact_energy_forecast` |
| Tablas de dimensiones | `gold_dim_{entidad}` | `gold_dim_client`, `gold_dim_datetime` |
| Clave primaria de dimensión | `{entidad}_id` o clave natural descriptiva | `client_id`, `unix_time`, `weather_id` |
| Claves foráneas en fact | Mismo nombre que la PK de la dimensión referenciada | `client_id`, `unix_time`, `weather_id` |
| Medidas físicas | `{magnitud}_{unidad_abreviada}` | `pv_power_gen_kw`, `poa_wm2`, `t_cell_celsius` |
| Medidas económicas | `{magnitud}_{moneda}_{unidad}` | `price_pvpc_eur_mwh` |
| Campos de auditoría | Prefijo `_` + nombre descriptivo + sufijo `_utc` | `_loaded_at_utc`, `_ingested_at_utc` |
| Flags booleanos | `is_{condición}` o `has_{capacidad}` | `is_weekend`, `is_festivo`, `has_solar`, `has_battery` |
| Períodos tarifarios | `P{número}` (estándar regulatorio español) | `P1`, `P2`, `P3`, `P6` |

**Unidades de medida en campos:**

| Sufijo | Unidad | Magnitud |
|--------|--------|---------|
| `_kw` | Kilovatios (kW) | Potencia instantánea |
| `_kwh` | Kilovatios-hora (kWh) | Energía (potencia × tiempo) |
| `_wm2` | Vatios por metro cuadrado (W/m²) | Irradiancia |
| `_celsius` | Grados Celsius (°C) | Temperatura |
| `_mps` | Metros por segundo (m/s) | Velocidad de viento |
| `_pct` | Porcentaje (%) | Fracciones de 100 |
| `_norm` | Adimensional [0–1] | Fracciones de 1 |
| `_eur_mwh` | Euros por megavatio-hora (€/MWh) | Precio de energía |

---

### 1.4 Gestión de Slowly Changing Dimensions (SCD)

| Dimensión | Tipo SCD | Estrategia | Justificación |
|-----------|---------|-----------|---------------|
| `gold_dim_client` | **Tipo 1** — Sobreescritura | `DROP + CREATE + INSERT` en cada ejecución | Los parámetros de instalación cambian raramente y cuando cambian (ej. ampliación de potencia PV), el nuevo valor es el correcto para todos los análisis futuros. No se necesita historial en DEV. |
| `gold_dim_datetime` | **Estática** — Sin cambios | `DROP + CREATE + INSERT` generando slots desde `clean_weather` | La dimensión de tiempo es determinista: la misma hora UTC siempre tiene los mismos atributos (período tarifario, día de semana, festivo). Si cambia la tarifa eléctrica (3.0TD), se regenera completa. |
| `gold_dim_weather` | **Tipo 2 lightweight** | Resolución por frecuencia con `ROW_NUMBER()` | Los `weather_id` de OWM son estables, pero el par `(main, description)` puede variar entre llamadas para el mismo código. La estrategia selecciona el par más frecuentemente observado, produciendo una dimensión estable. |

**Roadmap SCD Tipo 2 completo para `gold_dim_client` en producción:**

```sql
-- Estructura futura para gold_dim_client con SCD Tipo 2
CREATE TABLE gold_dim_client_scd2 (
    surrogate_key        INTEGER PRIMARY KEY AUTOINCREMENT,
    client_id            TEXT    NOT NULL,
    -- ... resto de atributos ...
    pv_peak_power_kw     REAL    NOT NULL,
    valid_from           TEXT    NOT NULL,   -- '2026-01-01 00:00:00'
    valid_to             TEXT,               -- NULL = registro vigente
    is_current           INTEGER NOT NULL,   -- 1 = vigente, 0 = histórico
    _changed_reason      TEXT                -- descripción del cambio
);
-- Índice para consultas de versión vigente
CREATE INDEX idx_dim_client_current ON gold_dim_client_scd2 (client_id, is_current);
```

---

## 2. Tablas de Hechos

### 2.1 `gold_fact_energy_forecast`

#### 2.1.1 Nombre y Descripción de Negocio

**Nombre:** `gold_fact_energy_forecast`  
**Módulo de carga:** `gold_fact_energy_forecast.py` → `build_fact_energy_forecast()`

Esta tabla es el **corazón analítico de SunSaver**. Registra, para cada instalación industrial y cada hora del horizonte de previsión (5 días), el estado energético completo: cuánta energía fotovoltaica se generará, cuánta energía consumirá la instalación, bajo qué condiciones meteorológicas y a qué precio. Es la tabla a partir de la cual se toman todas las decisiones de gestión energética flexible.

Cada fila responde a la pregunta: *"Para la instalación X, en la hora H, ¿cuánto generaré, cuánto consumiré y cuánto me costará o me ahorrará ese equilibrio?"*

#### 2.1.2 Grain — Nivel de Granularidad

> **Una fila = una instalación (cliente) × un slot horario UTC**

```
Grain: (client_id, unix_time)
       └─ Instalación fotovoltaica industrial
                       └─ Hora exacta UTC (EPOCH integer, resolución 1 hora)
```

No existe ninguna fila que agregue datos de múltiples horas ni de múltiples clientes. Toda agregación es responsabilidad de la capa de consulta (BI, Python, SQL).

#### 2.1.3 Proceso de Negocio que Representa

El proceso de negocio modelado es la **previsión y optimización del balance energético horario** de instalaciones industriales con generación fotovoltaica propia. Las decisiones habilitadas por este proceso son:

- **Gestión de carga de baterías:** cargar en las horas con excedente PV y precio bajo; descargar en las horas punta de precio y déficit solar
- **Programación de arranque de maquinaria:** identificar las ventanas de menor coste neto (precio bajo + alta generación PV)
- **Demand-side management:** diferir cargas flexibles a períodos valle (P3, P6) cuando la generación PV cubre el consumo base
- **Reporting de autosuficiencia:** medir qué fracción del consumo industrial es cubierta por generación propia hora a hora

#### 2.1.4 Medidas — Métricas con Descripción y Unidad

**Medidas físicas — Generación PV:**

| Campo | Tipo | Unidad | Descripción | Aditiva |
|-------|------|--------|-------------|---------|
| `pv_power_gen_kw` | REAL | kW | Potencia AC estimada generada por el parque fotovoltaico en ese slot horario. Calculada por el motor físico `engine_pv_physics.py` mediante la cadena GHI → Erbs → POA → Faiman → PR. **0 si el sol está bajo el horizonte (alfa < 2°).** | ✅ Aditiva |
| `pv_performance_ratio` | REAL | adimensional [0–1] | Eficiencia global del sistema PV respecto a las condiciones ideales de referencia (STC). Incluye derating térmico (γ = −0.4%/°C) y pérdidas de sistema (cableado, inversor, suciedad). Fórmula: `PR = f_temp × (1 - loss_pct/100)`. | ❌ No aditiva — usar media ponderada |
| `poa_wm2` | REAL | W/m² | Irradiancia total sobre el Plano del Array (Plane of Array). Suma de componente directa (beam), difusa isótropa (Liu-Jordan) y reflexión del suelo (albedo ρ=0.2). Input directo del cálculo de potencia. | ✅ Aditiva |
| `t_cell_celsius` | REAL | °C | Temperatura operativa de la célula solar estimada por el modelo Faiman (U0=24.9, U1=6.1). Determinante del derating térmico. Fórmula: `T_cell = T_amb + POA / (U0 + U1·v_viento)`. | ❌ No aditiva — usar media |

**Medidas físicas — Consumo industrial:**

| Campo | Tipo | Unidad | Descripción | Aditiva |
|-------|------|--------|-------------|---------|
| `power_consumption_kw` | REAL | kW | Consumo industrial simulado de la instalación. Modela patrones de turnos (picos en horario laboral, base nocturna y fin de semana), carga HVAC proporcional a la desviación de temperatura respecto a la zona de confort (15–25°C) y variabilidad gaussiana (σ=3%) para simular ruido de proceso real. | ✅ Aditiva |

**Medidas meteorológicas:**

| Campo | Tipo | Unidad | Descripción | Aditiva |
|-------|------|--------|-------------|---------|
| `temp_celsius` | REAL | °C | Temperatura ambiente prevista (°C). Input del modelo de consumo HVAC y de la temperatura de célula. | ❌ No aditiva — usar media |
| `humidity_pct` | REAL | % | Humedad relativa prevista. Contexto meteorológico; no se usa directamente en los modelos físicos actuales. | ❌ No aditiva — usar media |
| `clouds_pct` | REAL | % | Cobertura nubosa prevista. Input crítico del modelo de irradiancia GHI (Kasten-Czeplak). | ❌ No aditiva — usar media |
| `rain_prob_norm` | REAL | [0–1] | Probabilidad de precipitación normalizada. Contexto de fiabilidad de la previsión. | ❌ No aditiva — usar media |
| `wind_speed_mps` | REAL | m/s | Velocidad de viento prevista. Input del modelo de temperatura de célula (Faiman) y del modelo de consumo HVAC. | ❌ No aditiva — usar media |

**Medidas económicas:**

| Campo | Tipo | Unidad | Descripción | Aditiva |
|-------|------|--------|-------------|---------|
| `price_pvpc_eur_mwh` | REAL | €/MWh | Precio PVPC (Precio Voluntario al Pequeño Consumidor) del mercado eléctrico español para ese slot horario. Publicado por REE para el día siguiente. **Puede ser NULL si REE no ha publicado aún los precios D+1.** | ❌ No aditiva — precio unitario, no suma |

> **Nota sobre `price_pvpc_eur_mwh`:** este campo es un precio unitario (€ por MWh), no un importe absoluto. Para calcular el coste o ahorro económico en € de un slot horario, multiplicar por la energía consumida o generada: `(kW / 1000) × price_pvpc_eur_mwh = €`.

#### 2.1.5 Claves Foráneas a Dimensiones

| Campo FK | Dimensión referenciada | Campo PK | Tipo de relación |
|----------|----------------------|---------|-----------------|
| `client_id` | `gold_dim_client` | `client_id` | N:1 — muchos hechos por cliente |
| `unix_time` | `gold_dim_datetime` | `unix_time` | N:1 — muchos hechos por slot temporal |
| `weather_id` | `gold_dim_weather` | `weather_id` | N:1 — muchos hechos con la misma condición meteorológica |

#### 2.1.6 Columnas Técnicas

| Campo | Tipo | Descripción |
|-------|------|-------------|
| `_loaded_at_utc` | TEXT | Timestamp UTC de la última carga o actualización de este registro en Gold. Se actualiza en cada upsert, permitiendo identificar cuándo se actualizó un precio PVPC tardío. |

> No existe `batch_id` explícito en la versión actual. El `_loaded_at_utc` combinado con `etl_metadata.id` (tabla de auditoría) permite identificar el run exacto que produjo cada registro.

#### 2.1.7 Volumen Estimado y Crecimiento Esperado

| Parámetro | Valor | Cálculo |
|-----------|-------|---------|
| Filas por ejecución | N_clientes × 120 | 120h de forecast a 1h de resolución |
| Filas con 5 clientes | ~600 filas/ejecución | 5 × 120 |
| Filas con 50 clientes | ~6.000 filas/ejecución | 50 × 120 |
| Retención activa | Solo ventana futura | `unix_time >= now - 2h` en upsert |
| Crecimiento anual (5 clientes) | ~219.000 filas/año | 600 × 365 |
| Crecimiento anual (50 clientes) | ~2.190.000 filas/año | 6.000 × 365 |
| Tamaño estimado por fila | ~350 bytes | 16 columnas REAL + 2 TEXT |
| Tamaño total (50 clientes, 1 año) | ~730 MB | Sin compresión, SQLite |

> La tabla de hechos usa `INSERT OR REPLACE` sobre ventana activa, lo que significa que registros históricos (pasados) **no se eliminan automáticamente**. En producción, implementar una política de archivado para registros con `unix_time < now - 30d`.

#### 2.1.8 Particionado e Índices Recomendados

**Índices actualmente implementados:**

```sql
-- Índice sobre unix_time para filtros temporales (el más frecuente)
CREATE INDEX IF NOT EXISTS idx_gold_fact_unix_time
    ON gold_fact_energy_forecast (unix_time);

-- Índice sobre weather_id para JOIN con gold_dim_weather
CREATE INDEX IF NOT EXISTS idx_gold_fact_weather_id
    ON gold_fact_energy_forecast (weather_id);
```

**Índices adicionales recomendados para producción:**

```sql
-- Para filtros por cliente (análisis de instalación individual)
CREATE INDEX IF NOT EXISTS idx_gold_fact_client_id
    ON gold_fact_energy_forecast (client_id);

-- Índice compuesto para el patrón de consulta más común:
-- filtrar por cliente + rango temporal
CREATE INDEX IF NOT EXISTS idx_gold_fact_client_time
    ON gold_fact_energy_forecast (client_id, unix_time);

-- Para análisis de períodos tarifarios (via dim_datetime)
-- Este índice va en la dimensión, no en la fact:
CREATE INDEX IF NOT EXISTS idx_dim_datetime_tariff
    ON gold_dim_datetime (tariff_period, unix_time);
```

**Particionado recomendado en producción (migración a PostgreSQL/DuckDB):**

```sql
-- Particionado por rango de fecha para consultas históricas eficientes
CREATE TABLE gold_fact_energy_forecast (...)
PARTITION BY RANGE (unix_time);

CREATE TABLE gold_fact_energy_forecast_2026_q2
    PARTITION OF gold_fact_energy_forecast
    FOR VALUES FROM (1746057600) TO (1753920000);  -- Apr-Jun 2026
```

---

## 3. Tablas de Dimensiones

### 3.1 `gold_dim_client`

#### 3.1.1 Nombre y Descripción

**Nombre:** `gold_dim_client`  
**Módulo de carga:** `gold_dim_clients.py` → `build_dim_client()`

La **dimensión de cliente** describe las características técnicas y económicas de cada instalación fotovoltaica industrial registrada en el sistema. Es la dimensión más rica del modelo: contiene los parámetros físicos del parque PV (necesarios para interpretar los valores de generación), la configuración del sistema de almacenamiento (para análisis de flexibilidad) y el coste de inversión (para análisis de retorno).

En SunSaver, *"cliente"* es sinónimo de *"instalación industrial"*: una nave logística, una planta de producción o un centro de datos con parque fotovoltaico propio.

#### 3.1.2 Tipo de SCD Aplicado

**SCD Tipo 1 — Sobreescritura.**  
Cuando los parámetros de una instalación cambian (ej. ampliación del parque PV de 16 kWp a 25 kWp), el registro se sobreescribe con el nuevo valor. No se mantiene historial de configuraciones anteriores en la versión actual.

Ver sección 1.4 para la especificación del SCD Tipo 2 recomendado en producción.

#### 3.1.3 Atributos Descriptivos Completos

| Campo | Tipo SQL | Nullable | Descripción | Ejemplo |
|-------|----------|----------|-------------|---------|
| `client_id` | TEXT PK | NO | Identificador único de la instalación | `C001` |
| `name` | TEXT | NO | Nombre en mayúsculas (normalizado en Silver) | `PLANTA NORTE` |
| `description` | TEXT | SÍ | Descripción libre del proceso industrial | `Nave logística climatizada` |
| `latitude` | REAL | NO | Latitud WGS84, 6 decimales. Determina la posición solar calculada por pvlib | `42.803852` |
| `longitude` | REAL | NO | Longitud WGS84, 6 decimales | `-1.701962` |
| `timezone` | TEXT | NO | Zona horaria IANA para conversión de hora local | `Europe/Madrid` |
| `nominal_load_kw` | REAL | NO | Consumo nominal máximo de la instalación (kW). Base del modelo de consumo industrial | `20.8` |
| `pv_peak_power_kw` | REAL | NO | Potencia pico del parque PV en condiciones STC (kWp). Denominador del factor de capacidad | `16.0` |
| `panel_area_m2` | REAL | NO | Superficie total de paneles (m²) | `80.0` |
| `efficiency` | REAL | NO | Eficiencia del panel solar [0–1] en condiciones STC | `0.20` |
| `panel_type` | TEXT | NO | Tecnología del panel: `monoSi`, `polySi`, `thin-film`, `bifacial`… | `monoSi` |
| `loss_pct` | REAL | NO | Pérdidas totales del sistema (%). Incluye cableado, inversores, suciedad y degradación. Típicamente 10–20% | `14.0` |
| `angle` | REAL | NO | Inclinación del panel respecto al plano horizontal (°). 0° = horizontal, 90° = vertical | `30.0` |
| `aspect` | REAL | NO | Orientación azimutal del panel (°). 180° = Sur (óptimo en hemisferio norte) | `180.0` |
| `mounting` | TEXT | NO | Tipo de montaje: `rooftop`, `ground`, `carport`, `tracker`… | `rooftop` |
| `battery_capacity_kwh` | REAL | NO | Capacidad total del sistema de almacenamiento (kWh). `0` si la instalación no tiene batería | `20.0` |
| `soc_min_pct` | REAL | NO | Estado de carga mínimo operativo de la batería (%). Por debajo de este valor no se descarga | `20.0` |
| `installation_cost_eur` | REAL | NO | Coste total de la instalación PV (€). Base para el cálculo del período de retorno (ROI) | `18000.0` |
| `has_solar` | INTEGER | NO | **Flag derivado.** `1` si `pv_peak_power_kw > 0`. Facilita filtros rápidos sin condición numérica | `1` |
| `has_battery` | INTEGER | NO | **Flag derivado.** `1` si `battery_capacity_kwh > 0`. Identifica instalaciones con capacidad de almacenamiento | `1` |

#### 3.1.4 Jerarquías — Drill-Down Paths

La dimensión de cliente soporta dos jerarquías de análisis:

**Jerarquía geográfica:**
```
Región geográfica (implícita en lat/lon)
    └── Instalación (client_id)
            └── Slot horario (via fact table)
```

**Jerarquía de capacidad:**
```
Tipo de instalación
    ├── has_solar = 1, has_battery = 1  (solar + almacenamiento)
    ├── has_solar = 1, has_battery = 0  (solar sin almacenamiento)
    └── has_solar = 0                   (sin solar — caso excepcional)
        └── Rango de potencia
                ├── < 10 kWp   (pequeña instalación)
                ├── 10–50 kWp  (mediana instalación)
                └── > 50 kWp   (gran instalación)
```

#### 3.1.5 Valores Especiales

| Campo | Valor especial | Significado |
|-------|---------------|-------------|
| `description` | `'unknown'` | El campo no fue informado en el Excel de clientes. No indica error. |
| `panel_type` | `'unknown'` | Tecnología de panel no especificada. El motor PV funciona igualmente usando `efficiency`. |
| `mounting` | `'unknown'` | Tipo de montaje no especificado. No afecta a los cálculos actuales. |
| `battery_capacity_kwh` | `0.0` | La instalación no tiene sistema de almacenamiento. `has_battery = 0`. |
| `installation_cost_eur` | `0.0` | Coste no informado; excluir del cálculo de ROI. |
| `timezone` | `'UTC'` | Zona horaria por defecto cuando no se especifica. Los cálculos de hora local usarán UTC. |

#### 3.1.6 Cardinalidad Estimada

| Entorno | Filas esperadas |
|---------|----------------|
| DEV | 3–10 instalaciones de prueba |
| Producción inicial | 10–100 instalaciones |
| Producción escalada | hasta 10.000 instalaciones (con migración a PostgreSQL) |

---

### 3.2 `gold_dim_datetime`

#### 3.2.1 Nombre y Descripción

**Nombre:** `gold_dim_datetime`  
**Módulo de carga:** `gold_dim_datetime.py` → `build_dim_datetime()`

La **dimensión de tiempo** es la columna vertebral del modelo analítico. Enriquece cada slot horario UTC con todos los atributos de negocio necesarios para el análisis energético español: hora local, día de semana, festivos nacionales y — lo más importante — el **período tarifario 3.0TD** que determina el precio de la energía de red y, por tanto, el valor económico de la generación fotovoltaica en ese momento.

Esta dimensión se genera automáticamente a partir de los `unix_time` únicos presentes en `clean_weather`, garantizando que cubre exactamente el horizonte de previsión disponible.

#### 3.2.2 Tipo de SCD Aplicado

**Estática — Sin cambios históricos.**  
La dimensión de tiempo es determinista: la misma hora UTC siempre tiene los mismos atributos. Se regenera completamente (`DROP + CREATE + INSERT`) en cada ejecución del pipeline.

**Excepción:** si cambia la estructura tarifaria 3.0TD (ej. modificación regulatoria de los períodos horarios), la dimensión completa debe regenerarse y los análisis históricos comparativos requieren revisión.

#### 3.2.3 Atributos Descriptivos Completos

| Campo | Tipo SQL | Nullable | Descripción | Ejemplo |
|-------|----------|----------|-------------|---------|
| `unix_time` | INTEGER PK | NO | EPOCH UTC en segundos. Clave de JOIN con la tabla de hechos. | `1746874800` |
| `datetime_utc` | TEXT | NO | Timestamp en UTC (`YYYY-MM-DD HH:MM:SS`) | `2026-05-10 15:00:00` |
| `datetime_local` | TEXT | NO | Timestamp en hora local Spain (`Europe/Madrid`). Incluye ajuste DST (CEST en verano, CET en invierno) | `2026-05-10 17:00:00` |
| `date` | TEXT | NO | Fecha UTC en formato `YYYY-MM-DD`. Útil para agrupaciones diarias | `2026-05-10` |
| `hour_utc` | INTEGER | NO | Hora del día en UTC [0–23] | `15` |
| `hour_local` | INTEGER | NO | Hora del día en hora local [0–23]. Usar para análisis de patrones de consumo | `17` |
| `day_of_week` | TEXT | NO | Nombre del día de la semana en inglés minúsculas: `monday`…`sunday` | `sunday` |
| `is_daylight` | INTEGER | NO | `1` si el slot cae en horario de verano (CEST, UTC+2); `0` si es horario de invierno (CET, UTC+1) | `1` |
| `is_weekend` | INTEGER | NO | `1` si `day_of_week IN ('saturday','sunday')` | `1` |
| `is_festivo` | INTEGER | NO | `1` si la fecha coincide con un festivo nacional español. Ver lista completa en sección 3.2.3a | `0` |
| `month` | INTEGER | NO | Mes del año [1–12] | `5` |
| `year` | INTEGER | NO | Año | `2026` |
| `tariff_period` | TEXT | NO | Período tarifario 3.0TD: `P1` (punta), `P2` (llano), `P3` (valle), `P6` (super-valle) | `P6` |
| `tariff_label` | TEXT | NO | Etiqueta descriptiva del período: `punta`, `llano`, `valle`, `super-valle` | `super-valle` |

**3.2.3a — Festivos nacionales españoles implementados:**

```python
FESTIVOS_NACIONALES = {
    (1,  1),   # Año Nuevo
    (1,  6),   # Reyes Magos
    (5,  1),   # Día del Trabajo
    (8, 15),   # Asunción de la Virgen
    (10, 12),  # Fiesta Nacional de España
    (11,  1),  # Todos los Santos
    (12,  6),  # Día de la Constitución
    (12,  8),  # Inmaculada Concepción
    (12, 25),  # Navidad
}
```

> Los festivos autonómicos y locales no están implementados. Para instalaciones en comunidades autónomas con festivos propios relevantes (ej. San José en Valencia, Sant Jordi en Cataluña), añadirlos al set `FESTIVOS_NACIONALES` o crear un set específico por instalación.

#### 3.2.4 Jerarquías — Drill-Down Paths

```
Año (year)
  └── Mes (month)
        └── Fecha (date)
              └── Hora UTC (hour_utc) / Hora local (hour_local)
                    └── Slot horario (unix_time)

Período tarifario (tariff_period: P1/P2/P3/P6)
  └── Hora local (hour_local)
        └── Slot horario (unix_time)

Tipo de día (is_weekend + is_festivo)
  ├── Día laborable (is_weekend=0, is_festivo=0)
  │     └── Hora local → Período tarifario
  └── No laborable (is_weekend=1 OR is_festivo=1) → Siempre P6
```

#### 3.2.5 Valores Especiales

Esta dimensión no tiene valores especiales. Es generada determinísticamente y todos los campos son siempre válidos y no nulos.

#### 3.2.6 Cardinalidad Estimada

| Horizonte | Filas |
|-----------|-------|
| 5 días de forecast (1 ejecución) | 120 filas |
| 1 año completo (histórico) | 8.760 filas |
| 10 años (máximo útil) | 87.600 filas |

La dimensión de tiempo es intrínsecamente pequeña. Cabe íntegra en memoria caché de cualquier motor de consulta moderno.

---

### 3.3 `gold_dim_weather`

#### 3.3.1 Nombre y Descripción

**Nombre:** `gold_dim_weather`  
**Módulo de carga:** `gold_dim_weather.py` → `build_dim_weather()`

La **dimensión de condición meteorológica** es un catálogo de los tipos de tiempo observados, derivado directamente de los códigos de condición de OpenWeatherMap. Permite agrupar y filtrar hechos por tipo de tiempo (ej. *"¿cuánto generé en promedio en días con cielo cubierto?"*) sin necesidad de manipular los campos de texto en la tabla de hechos.

#### 3.3.2 Tipo de SCD Aplicado

**SCD Tipo 2 lightweight por resolución de frecuencia.**  
Para cada `weather_id`, se selecciona el par `(weather_main, weather_description)` más frecuentemente observado en `clean_weather`, resolviendo inconsistencias entre distintas llamadas a la API OWM para el mismo código:

```sql
SELECT weather_id, weather_main, weather_description
FROM (
    SELECT weather_id, weather_main, weather_description,
           ROW_NUMBER() OVER (
               PARTITION BY weather_id
               ORDER BY COUNT(*) DESC
           ) AS rn
    FROM clean_weather
    WHERE weather_id IS NOT NULL
    GROUP BY weather_id, weather_main, weather_description
) WHERE rn = 1
```

#### 3.3.3 Atributos Descriptivos Completos

| Campo | Tipo SQL | Nullable | Descripción | Ejemplo |
|-------|----------|----------|-------------|---------|
| `weather_id` | INTEGER PK | NO | Código numérico de condición meteorológica OWM. Rango: 200–804. Referencia: [OWM Weather Conditions](https://openweathermap.org/weather-conditions) | `803` |
| `weather_main` | TEXT | NO | Categoría principal de la condición. Valores posibles: `Thunderstorm`, `Drizzle`, `Rain`, `Snow`, `Atmosphere`, `Clear`, `Clouds` | `Clouds` |
| `weather_description` | TEXT | NO | Descripción detallada en inglés. Ejemplos: `clear sky`, `few clouds`, `scattered clouds`, `broken clouds`, `overcast clouds` | `broken clouds` |
| `_loaded_at_utc` | TEXT | NO | Timestamp UTC de la última carga de esta dimensión | `2026-05-10 22:00:00` |

#### 3.3.4 Jerarquías — Drill-Down Paths

```
Categoría principal (weather_main)
  └── Descripción detallada (weather_description)
        └── Código numérico (weather_id)

Impacto en generación PV (implícito en weather_main):
  ├── Clear     (f_w = 1.00 — máxima irradiancia)
  ├── Clouds    (f_w = 0.80–0.95 según nivel de nubosidad)
  ├── Drizzle   (f_w = 0.85)
  ├── Rain      (f_w = 0.70)
  ├── Snow      (f_w = 0.75)
  ├── Atmosphere (f_w = 0.60 — niebla, calima…)
  └── Thunderstorm (f_w = 0.40 — mínima irradiancia)
```

#### 3.3.5 Valores Especiales

| weather_id | weather_main | weather_description | Significado |
|-----------|-------------|--------------------|-|
| `800` | `Clear` | `clear sky` | Cielo completamente despejado — condición óptima para generación PV |
| `801` | `Clouds` | `few clouds` | 11–25% nubosidad — generación casi óptima |
| `802` | `Clouds` | `scattered clouds` | 25–50% nubosidad |
| `803` | `Clouds` | `broken clouds` | 51–84% nubosidad — generación significativamente reducida |
| `804` | `Clouds` | `overcast clouds` | > 85% nubosidad — generación mínima |

> Si un `weather_id` aparece en `gold_fact` pero no existe en `gold_dim_weather`, indica un código nuevo de OWM no observado en el período de histórico de `clean_weather`. El `LEFT JOIN` en las consultas retornará `NULL` para los atributos de la dimensión en esos casos.

#### 3.3.6 Cardinalidad Estimada

| Métrica | Valor |
|---------|-------|
| Códigos OWM totales posibles | ~50 (rango 200–804) |
| Códigos observados típicamente en España peninsular | 15–25 |
| Filas en `gold_dim_weather` | 15–25 |

Es la dimensión de menor cardinalidad del modelo. Cabe completamente en caché de cualquier sistema.

---

## 4. Dimensiones Conformadas

### 4.1 Listado y Definición Canónica

Una dimensión es **conformada** cuando su definición (nombres de campos, tipos, semántica) es idéntica en todas las fact tables del data warehouse. Esto garantiza que los análisis cruzados entre distintas fact tables son consistentes y no requieren transformaciones adicionales.

En el modelo SunSaver actual, todas las dimensiones son conformadas por diseño, dado que existe una única tabla de hechos. La conformidad es un requisito explícito para cualquier fact table futura que se añada al modelo.

| Dimensión | Conformada | Clave | Uso en fact tables actuales | Uso en fact tables futuras |
|-----------|-----------|-------|---------------------------|--------------------------|
| `gold_dim_client` | ✅ SÍ | `client_id` TEXT | `gold_fact_energy_forecast` | `gold_fact_battery_ops` (futuro), `gold_fact_maintenance` (futuro) |
| `gold_dim_datetime` | ✅ SÍ | `unix_time` INTEGER | `gold_fact_energy_forecast` | Todas las fact tables con componente temporal |
| `gold_dim_weather` | ✅ SÍ | `weather_id` INTEGER | `gold_fact_energy_forecast` | `gold_fact_battery_ops` (futuro) |

**Reglas de conformidad — Contrato de uso:**

1. **Nunca crear una copia modificada de una dimensión conformada** para una nueva fact table. Si la dimensión existente no tiene los atributos necesarios, añadirlos a la dimensión canónica.
2. **Las claves foráneas en nuevas fact tables deben usar exactamente el mismo nombre de campo** que la PK de la dimensión conformada (`client_id`, `unix_time`, `weather_id`).
3. **Los joins entre fact tables deben hacerse a través de las dimensiones conformadas**, nunca directamente entre fact tables.

---

### 4.2 Guía de Uso para Análisis Cruzados

La conformidad de las dimensiones permite comparar métricas de diferentes procesos de negocio en el mismo contexto dimensional. Ejemplos de análisis cruzados habilitados:

**Análisis cruzado actual (fact única):**
```sql
-- Generación PV vs Consumo por período tarifario y tipo de instalación
SELECT
    d.tariff_label,
    c.has_battery,
    AVG(f.pv_power_gen_kw)       AS gen_media_kw,
    AVG(f.power_consumption_kw)  AS consumo_medio_kw,
    AVG(f.pv_power_gen_kw - f.power_consumption_kw) AS balance_medio_kw
FROM gold_fact_energy_forecast f
JOIN gold_dim_datetime d ON f.unix_time = d.unix_time
JOIN gold_dim_client   c ON f.client_id = c.client_id
GROUP BY d.tariff_label, c.has_battery
ORDER BY d.tariff_label, c.has_battery;
```

**Análisis cruzado futuro (múltiples facts — esquema conceptual):**
```sql
-- Comparar generación PV con operaciones de batería
-- (requiere gold_fact_battery_ops — roadmap)
SELECT
    d.date,
    d.tariff_label,
    c.client_id,
    f_energy.pv_power_gen_kw,
    f_energy.power_consumption_kw,
    f_battery.charge_kw,         -- desde gold_fact_battery_ops (futuro)
    f_battery.discharge_kw       -- desde gold_fact_battery_ops (futuro)
FROM gold_dim_datetime d
JOIN gold_fact_energy_forecast f_energy ON d.unix_time = f_energy.unix_time
-- JOIN gold_fact_battery_ops f_battery ON d.unix_time = f_battery.unix_time  -- futuro
JOIN gold_dim_client c ON f_energy.client_id = c.client_id
WHERE d.date = '2026-05-10';
```

---

## 5. Métricas de Negocio Derivadas

### 5.1 KPIs Industriales

| KPI | Descripción | Fórmula SQL | Unidad | Frecuencia de cálculo |
|-----|-------------|-------------|--------|----------------------|
| **Balance energético neto** | Excedente (>0) o déficit (<0) de energía en cada slot horario. Determinante para la decisión de carga/descarga de batería | `pv_power_gen_kw - power_consumption_kw` | kW | Por slot horario |
| **Energía generada diaria** | Total de energía fotovoltaica producida en un día (integración temporal de potencia) | `SUM(pv_power_gen_kw) × 1h` | kWh/día | Diaria por instalación |
| **Energía consumida diaria** | Total de energía consumida por la instalación en un día | `SUM(power_consumption_kw) × 1h` | kWh/día | Diaria por instalación |
| **Tasa de autoconsumo** | Fracción de la generación PV que es consumida directamente en la instalación (sin excedente a red ni uso de batería) | `SUM(MIN(pv_power_gen_kw, power_consumption_kw)) / NULLIF(SUM(pv_power_gen_kw), 0)` | % | Diaria por instalación |
| **Tasa de autosuficiencia** | Fracción del consumo total cubierta por generación PV propia | `SUM(MIN(pv_power_gen_kw, power_consumption_kw)) / NULLIF(SUM(power_consumption_kw), 0)` | % | Diaria por instalación |
| **Performance Ratio diario** | Eficiencia media del sistema PV durante las horas de generación activa | `AVG(pv_performance_ratio) WHERE pv_power_gen_kw > 0` | adimensional [0–1] | Diaria por instalación |
| **Factor de capacidad (CF)** | Fracción de la energía teórica máxima que realmente se genera | `SUM(pv_power_gen_kw) / (pv_peak_power_kw × 24)` | % | Diaria por instalación |
| **Horas equivalentes de sol** | Horas de irradiancia a potencia nominal producidas | `SUM(pv_power_gen_kw) / pv_peak_power_kw` | h/día | Diaria por instalación |
| **Temperatura de célula media** | Temperatura operativa media del parque PV durante horas diurnas | `AVG(t_cell_celsius) WHERE pv_power_gen_kw > 0` | °C | Diaria por instalación |

---

### 5.2 KPIs Económicos

| KPI | Descripción | Fórmula SQL | Unidad | Frecuencia |
|-----|-------------|-------------|--------|-----------|
| **Coste energético horario** | Coste de la energía consumida de red en un slot (sin considerar PV) | `(power_consumption_kw / 1000.0) × price_pvpc_eur_mwh` | €/hora | Por slot horario |
| **Coste neto horario** | Coste real considerando que la generación PV reduce la energía tomada de red | `(MAX(0, power_consumption_kw - pv_power_gen_kw) / 1000.0) × price_pvpc_eur_mwh` | €/hora | Por slot horario |
| **Ahorro PV horario** | Valor económico de la energía autoconsumida que no se compra a red | `(MIN(pv_power_gen_kw, power_consumption_kw) / 1000.0) × price_pvpc_eur_mwh` | €/hora | Por slot horario |
| **Coste diario sin PV** | Coste hipotético si no hubiera instalación PV (benchmark) | `SUM((power_consumption_kw / 1000.0) × price_pvpc_eur_mwh)` | €/día | Diaria |
| **Coste diario real** | Coste real con la generación PV | `SUM((MAX(0, power_consumption_kw - pv_power_gen_kw) / 1000.0) × price_pvpc_eur_mwh)` | €/día | Diaria |
| **Ahorro diario PV** | Diferencia entre coste sin PV y coste real | `coste_sin_pv - coste_real` | €/día | Diaria |
| **Ahorro anual proyectado** | Proyección del ahorro anual basada en el promedio diario reciente | `AVG(ahorro_diario) × 365` | €/año | Semanal/mensual |
| **Período de retorno (Payback)** | Años necesarios para recuperar la inversión inicial | `installation_cost_eur / ahorro_anual_proyectado` | años | Mensual |
| **Coste por período tarifario** | Desglose del coste total por período P1/P2/P3/P6 | `SUM(coste_horario) GROUP BY tariff_period` | €/período | Diaria |
| **Precio medio ponderado** | Precio medio de la energía consumida ponderado por el consumo de cada hora | `SUM(power_consumption_kw × price_pvpc_eur_mwh) / SUM(power_consumption_kw) / 1000` | €/MWh | Diaria |

---

### 5.3 Métricas Calculadas vs Almacenadas

| Métrica | Tipo | Justificación |
|---------|------|--------------|
| `pv_power_gen_kw` | **Almacenada** | Requiere cálculo costoso del motor físico PV (pvlib + modelos Erbs/Faiman). Pre-calcular evita re-ejecutar el motor en cada consulta. |
| `pv_performance_ratio` | **Almacenada** | Ídem — resultado intermedio del motor físico de alto valor analítico. |
| `poa_wm2` | **Almacenada** | Irradiancia en el plano del array — valor físico fundamental para diagnóstico de rendimiento. |
| `t_cell_celsius` | **Almacenada** | Temperatura de célula — valor físico para análisis de derating térmico. |
| `power_consumption_kw` | **Almacenada** | Requiere modelo de consumo industrial con estado temporal (turnos, variabilidad aleatoria). |
| `price_pvpc_eur_mwh` | **Almacenada** | Dato externo de API — cacheado para evitar dependencia de disponibilidad REE en cada consulta. |
| Balance neto (kW) | **Calculada** en consulta | `pv_power_gen_kw - power_consumption_kw` — operación trivial, sin beneficio de pre-calcular. |
| Coste horario (€) | **Calculada** en consulta | `(kW/1000) × precio` — derivada directamente de medidas almacenadas. |
| Ahorro PV (€) | **Calculada** en consulta | Derivada de medidas almacenadas. |
| Tasa de autoconsumo (%) | **Calculada** en consulta | Requiere `MIN()` entre dos medidas — sencillo en SQL. |
| Payback (años) | **Calculada** en consulta | Requiere `installation_cost_eur` de `dim_client` — join simple. |
| Horas equivalentes de sol | **Calculada** en consulta | `SUM(gen) / peak_power` — operación de agregación trivial. |

---

### 5.4 Guía de Aditividad: Aditivas, Semi-aditivas, No Aditivas

La aditividad determina **cómo se pueden agregar las métricas** a lo largo de las dimensiones. Usar una métrica no aditiva como si fuera aditiva produce resultados incorrectos.

#### Métricas Aditivas ✅

Se pueden sumar a lo largo de **todas las dimensiones** (tiempo, cliente, condición meteorológica):

| Métrica | Suma por tiempo | Suma por cliente | Suma por weather |
|---------|----------------|-----------------|-----------------|
| `pv_power_gen_kw` (→ kWh si × 1h) | ✅ Energía total del día | ✅ Generación total de la flota | ✅ Generación por condición |
| `power_consumption_kw` (→ kWh si × 1h) | ✅ Consumo total del día | ✅ Consumo total de la flota | ✅ Consumo por condición |
| `poa_wm2` (suma con sentido limitado) | ⚠️ Sólo si misma ubicación | ❌ Sin sentido físico | ⚠️ Con precaución |
| Coste horario (€) | ✅ Coste total del día | ✅ Coste total de la flota | ✅ Coste por condición |
| Ahorro PV (€) | ✅ Ahorro total del día | ✅ Ahorro total de la flota | ✅ Ahorro por condición |

> **Nota importante sobre potencia vs energía:** `pv_power_gen_kw` es potencia instantánea (kW), no energía (kWh). Para obtener energía, multiplicar por la duración del slot en horas (en este modelo, siempre 1h): `SUM(pv_power_gen_kw) × 1 = kWh totales`.

#### Métricas Semi-Aditivas ⚠️

Se pueden sumar a lo largo de algunas dimensiones pero **no todas**:

| Métrica | Suma por tiempo | Suma por cliente | Nota |
|---------|----------------|-----------------|------|
| Balance neto (kW) | ✅ Balance acumulado del día | ✅ Balance de la flota | Suma directa válida |
| `price_pvpc_eur_mwh` | ❌ No sumar precios | ❌ No sumar precios | **Usar media ponderada por consumo**, no suma |

#### Métricas No Aditivas ❌

**Nunca se deben sumar directamente.** Usar siempre media, media ponderada o cálculo sobre los componentes primarios:

| Métrica | Agregación correcta | Agregación incorrecta | Error que produce |
|---------|--------------------|-----------------------|------------------|
| `pv_performance_ratio` | `SUM(gen_kw) / (peak_kw × SUM(poa/1000))` (PR real) ó `AVG` ponderado por POA | `AVG` simple, `SUM` | PR inflado en horas de baja irradiancia |
| `temp_celsius` | `AVG(temp_celsius)` | `SUM(temp_celsius)` | Temperatura sin sentido físico |
| `t_cell_celsius` | `AVG(t_cell_celsius) WHERE gen > 0` | `SUM` | Temperatura de célula sin sentido |
| `clouds_pct` | `AVG(clouds_pct)` | `SUM` | Nubosidad > 100% |
| `rain_prob_norm` | `AVG(rain_prob_norm)` | `SUM` | Probabilidad > 1 |
| `humidity_pct` | `AVG(humidity_pct)` | `SUM` | Humedad > 100% |
| `wind_speed_mps` | `AVG(wind_speed_mps)` | `SUM` | Velocidad sin sentido físico |
| Tasa de autoconsumo (%) | `SUM(MIN(gen,con)) / SUM(gen)` | `AVG(ratio_horario)` | Sesgo por horas con poco sol |
| Factor de capacidad (%) | `SUM(gen) / (peak × N_horas)` | `AVG` | CF incorrecto |
| Payback (años) | Calcular sobre totales anuales | `AVG(payback_diario)` | Período de retorno incorrecto |

---

## 6. Queries de Referencia

### 6.1 Consultas Tipo por Caso de Uso

---

#### QR-01 — Balance energético horario del día siguiente por instalación

**Caso de uso:** visualizar hora a hora si habrá excedente o déficit energético en la próxima jornada. Base para la programación de cargas flexibles.

```sql
SELECT
    c.name                                                  AS instalacion,
    d.datetime_local                                        AS hora_local,
    d.hour_local                                            AS hora,
    d.tariff_label                                          AS tarifa,
    ROUND(f.pv_power_gen_kw, 2)                             AS generacion_kw,
    ROUND(f.power_consumption_kw, 2)                        AS consumo_kw,
    ROUND(f.pv_power_gen_kw - f.power_consumption_kw, 2)   AS balance_kw,
    CASE
        WHEN f.pv_power_gen_kw - f.power_consumption_kw > 0  THEN '⚡ Excedente'
        WHEN f.pv_power_gen_kw - f.power_consumption_kw < 0  THEN '🔌 Déficit'
        ELSE '⚖️ Equilibrio'
    END                                                     AS estado,
    ROUND(f.price_pvpc_eur_mwh, 2)                          AS precio_eur_mwh
FROM gold_fact_energy_forecast f
JOIN gold_dim_client   c ON f.client_id = c.client_id
JOIN gold_dim_datetime d ON f.unix_time = d.unix_time
WHERE d.date = date('now', '+1 day')
  AND f.client_id = 'C001'          -- filtrar por instalación
ORDER BY d.unix_time;
```

---

#### QR-02 — Ranking de mejores horas para arranque de maquinaria (próximas 24h)

**Caso de uso:** identificar las horas de menor coste neto energético para programar el arranque de cargas industriales de alto consumo.

```sql
SELECT
    d.datetime_local                                               AS hora_local,
    d.tariff_label                                                 AS tarifa,
    ROUND(f.pv_power_gen_kw, 2)                                    AS generacion_kw,
    ROUND(f.power_consumption_kw, 2)                               AS consumo_base_kw,
    ROUND(f.price_pvpc_eur_mwh, 2)                                 AS precio_eur_mwh,
    -- Coste neto: sólo se paga el déficit (consumo - generación propia)
    ROUND(
        MAX(0, f.power_consumption_kw - f.pv_power_gen_kw)
        / 1000.0 * f.price_pvpc_eur_mwh, 4
    )                                                              AS coste_neto_eur_h,
    -- Indicador de conveniencia
    CASE
        WHEN f.pv_power_gen_kw > f.power_consumption_kw
             AND d.tariff_period IN ('P3','P6')     THEN '🟢 Óptimo'
        WHEN f.pv_power_gen_kw > f.power_consumption_kw  THEN '🟡 Bueno'
        WHEN d.tariff_period IN ('P3','P6')         THEN '🟡 Bueno (tarifa baja)'
        ELSE                                              '🔴 Evitar'
    END                                                            AS recomendacion
FROM gold_fact_energy_forecast f
JOIN gold_dim_client   c ON f.client_id = c.client_id
JOIN gold_dim_datetime d ON f.unix_time = d.unix_time
WHERE f.unix_time BETWEEN strftime('%s','now') AND strftime('%s','now') + 86400
  AND f.price_pvpc_eur_mwh IS NOT NULL
  AND f.client_id = 'C001'
ORDER BY coste_neto_eur_h ASC, f.pv_power_gen_kw DESC
LIMIT 10;
```

---

#### QR-03 — Ventanas óptimas de carga de batería (próximos 5 días)

**Caso de uso:** programar la carga del sistema de almacenamiento en las horas con mayor excedente PV y precio más bajo.

```sql
SELECT
    d.date                                                          AS fecha,
    d.datetime_local                                                AS hora_local,
    d.tariff_label                                                  AS tarifa,
    ROUND(f.pv_power_gen_kw, 2)                                     AS generacion_kw,
    ROUND(f.power_consumption_kw, 2)                                AS consumo_kw,
    ROUND(f.pv_power_gen_kw - f.power_consumption_kw, 2)           AS excedente_kw,
    ROUND(f.price_pvpc_eur_mwh, 2)                                  AS precio_eur_mwh,
    -- Valor del excedente si se almacena para usar en punta
    ROUND(
        MAX(0, f.pv_power_gen_kw - f.power_consumption_kw)
        / 1000.0 * f.price_pvpc_eur_mwh, 4
    )                                                               AS valor_excedente_eur
FROM gold_fact_energy_forecast f
JOIN gold_dim_client   c ON f.client_id = c.client_id
JOIN gold_dim_datetime d ON f.unix_time = d.unix_time
WHERE f.unix_time >= strftime('%s','now')
  AND f.pv_power_gen_kw > f.power_consumption_kw  -- sólo horas con excedente
  AND d.tariff_period IN ('P3','P6')               -- sólo períodos valle
  AND f.client_id = 'C001'
  AND c.has_battery = 1                            -- sólo instalaciones con batería
ORDER BY valor_excedente_eur DESC;
```

---

#### QR-04 — Resumen diario de KPIs por instalación

**Caso de uso:** informe diario de rendimiento energético y económico para seguimiento operativo.

```sql
SELECT
    d.date                                                               AS fecha,
    c.client_id,
    c.name                                                               AS instalacion,
    c.pv_peak_power_kw                                                   AS potencia_pico_kwp,

    -- KPIs de generación
    ROUND(SUM(f.pv_power_gen_kw), 2)                                     AS kwh_generados,
    ROUND(AVG(CASE WHEN f.pv_power_gen_kw > 0
                   THEN f.pv_performance_ratio END), 3)                   AS pr_medio,
    ROUND(SUM(f.pv_power_gen_kw) / c.pv_peak_power_kw, 2)               AS horas_sol_equiv,

    -- KPIs de consumo
    ROUND(SUM(f.power_consumption_kw), 2)                                AS kwh_consumidos,

    -- KPIs de balance
    ROUND(SUM(f.pv_power_gen_kw) - SUM(f.power_consumption_kw), 2)      AS balance_kwh,
    ROUND(100.0 * SUM(MIN(f.pv_power_gen_kw, f.power_consumption_kw))
          / NULLIF(SUM(f.power_consumption_kw), 0), 1)                   AS tasa_autosuficiencia_pct,

    -- KPIs económicos (sólo si precio disponible)
    ROUND(SUM(
        CASE WHEN f.price_pvpc_eur_mwh IS NOT NULL
             THEN (f.power_consumption_kw / 1000.0) * f.price_pvpc_eur_mwh
             ELSE NULL END
    ), 4)                                                                 AS coste_sin_pv_eur,
    ROUND(SUM(
        CASE WHEN f.price_pvpc_eur_mwh IS NOT NULL
             THEN (MAX(0, f.power_consumption_kw - f.pv_power_gen_kw) / 1000.0)
                  * f.price_pvpc_eur_mwh
             ELSE NULL END
    ), 4)                                                                 AS coste_real_eur,
    ROUND(SUM(
        CASE WHEN f.price_pvpc_eur_mwh IS NOT NULL
             THEN (MIN(f.pv_power_gen_kw, f.power_consumption_kw) / 1000.0)
                  * f.price_pvpc_eur_mwh
             ELSE NULL END
    ), 4)                                                                 AS ahorro_pv_eur

FROM gold_fact_energy_forecast f
JOIN gold_dim_client   c ON f.client_id = c.client_id
JOIN gold_dim_datetime d ON f.unix_time = d.unix_time
WHERE d.date = date('now', '+1 day')
GROUP BY d.date, c.client_id, c.name, c.pv_peak_power_kw
ORDER BY ahorro_pv_eur DESC;
```

---

#### QR-05 — Análisis de generación PV por condición meteorológica

**Caso de uso:** entender el impacto de cada tipo de tiempo en la generación de la instalación. Útil para calibrar el modelo y validar previsiones.

```sql
SELECT
    w.weather_main                                                  AS condicion,
    w.weather_description                                           AS descripcion,
    COUNT(*)                                                        AS n_slots,
    ROUND(AVG(f.clouds_pct), 1)                                     AS nubosidad_media_pct,
    ROUND(AVG(f.poa_wm2), 1)                                        AS irradiancia_poa_media,
    ROUND(AVG(f.pv_power_gen_kw), 3)                                AS generacion_media_kw,
    ROUND(MAX(f.pv_power_gen_kw), 3)                                AS generacion_max_kw,
    ROUND(AVG(CASE WHEN f.pv_power_gen_kw > 0
                   THEN f.pv_performance_ratio END), 3)             AS pr_medio
FROM gold_fact_energy_forecast f
JOIN gold_dim_weather   w ON f.weather_id = w.weather_id
JOIN gold_dim_datetime  d ON f.unix_time  = d.unix_time
WHERE d.is_daylight = 1                  -- sólo horas diurnas
  AND f.client_id   = 'C001'
GROUP BY w.weather_main, w.weather_description
ORDER BY generacion_media_kw DESC;
```

---

#### QR-06 — Coste energético por período tarifario (análisis de exposición)

**Caso de uso:** identificar en qué períodos tarifarios se concentra el mayor gasto energético para priorizar la gestión de carga flexible.

```sql
SELECT
    d.tariff_period,
    d.tariff_label,
    COUNT(*)                                                         AS n_slots,
    ROUND(AVG(f.price_pvpc_eur_mwh), 2)                             AS precio_medio_eur_mwh,
    ROUND(SUM(f.power_consumption_kw), 2)                           AS kwh_consumidos,
    ROUND(SUM(f.pv_power_gen_kw), 2)                                AS kwh_generados,
    ROUND(SUM(
        (f.power_consumption_kw / 1000.0) * f.price_pvpc_eur_mwh
    ), 4)                                                            AS coste_bruto_eur,
    ROUND(SUM(
        (MAX(0, f.power_consumption_kw - f.pv_power_gen_kw) / 1000.0)
        * f.price_pvpc_eur_mwh
    ), 4)                                                            AS coste_neto_eur,
    ROUND(100.0 * SUM(
        (MAX(0, f.power_consumption_kw - f.pv_power_gen_kw) / 1000.0)
        * f.price_pvpc_eur_mwh
    ) / NULLIF(SUM(
        (f.power_consumption_kw / 1000.0) * f.price_pvpc_eur_mwh
    ), 0), 1)                                                        AS pct_sobre_coste_total
FROM gold_fact_energy_forecast f
JOIN gold_dim_datetime d ON f.unix_time = d.unix_time
WHERE f.price_pvpc_eur_mwh IS NOT NULL
  AND f.client_id = 'C001'
  AND d.date = date('now', '+1 day')
GROUP BY d.tariff_period, d.tariff_label
ORDER BY coste_bruto_eur DESC;
```

---

### 6.2 Patrones de Filtrado Temporal

El modelo usa `unix_time` (INTEGER EPOCH) como clave temporal. Los filtros temporales más comunes:

```sql
-- Mañana (D+1) — datos de previsión más relevantes
WHERE d.date = date('now', '+1 day')

-- Próximas 24 horas desde ahora
WHERE f.unix_time BETWEEN strftime('%s','now')
                      AND strftime('%s','now') + 86400

-- Próximos 5 días (ventana completa de forecast)
WHERE f.unix_time >= strftime('%s','now')

-- Hora actual y siguientes 2h (ventana operativa inmediata)
WHERE f.unix_time BETWEEN strftime('%s','now')
                      AND strftime('%s','now') + 7200

-- Sólo horas con luz solar (para análisis de generación PV)
WHERE d.is_daylight = 1
  AND f.pv_power_gen_kw > 0

-- Sólo período punta del día siguiente (análisis de coste máximo)
WHERE d.date = date('now', '+1 day')
  AND d.tariff_period = 'P1'

-- Sólo días laborables de la próxima semana
WHERE f.unix_time >= strftime('%s','now')
  AND d.is_weekend = 0
  AND d.is_festivo = 0

-- Comparar misma hora en todos los días del forecast
WHERE d.hour_local = 14   -- las 14:00 hora local de cada día
```

**Conversión de unix_time a datetime en SQLite:**

```sql
-- Convertir unix_time a datetime legible UTC
SELECT datetime(unix_time, 'unixepoch') AS datetime_utc FROM gold_dim_datetime;

-- Convertir unix_time a datetime en hora local España (UTC+1 en invierno)
-- Nota: SQLite no tiene soporte nativo de zonas horarias; usar datetime_local del dim
SELECT datetime_local FROM gold_dim_datetime WHERE unix_time = 1746874800;
```

---

### 6.3 Joins Recomendados y Anti-Patrones

**Joins recomendados:**

```sql
-- PATRÓN ESTÁNDAR: siempre unir fact con todas las dimensiones necesarias
SELECT f.*, c.name, d.tariff_label, w.weather_main
FROM gold_fact_energy_forecast f
JOIN gold_dim_client   c ON f.client_id = c.client_id
JOIN gold_dim_datetime d ON f.unix_time = d.unix_time
LEFT JOIN gold_dim_weather w ON f.weather_id = w.weather_id  -- LEFT por posibles NULLs
WHERE ...;

-- Para análisis que sólo necesitan atributos temporales:
SELECT f.client_id, d.tariff_label, SUM(f.pv_power_gen_kw)
FROM gold_fact_energy_forecast f
JOIN gold_dim_datetime d ON f.unix_time = d.unix_time
GROUP BY f.client_id, d.tariff_label;
```

**Anti-patrones — evitar:**

```sql
-- ❌ ANTI-PATRÓN: filtrar por hora directamente en la fact table
-- (unix_time no es intuitivo; usar dim_datetime)
WHERE f.unix_time = 1746874800

-- ✅ CORRECTO: filtrar por atributos de la dimensión de tiempo
WHERE d.date = '2026-05-10' AND d.hour_local = 15


-- ❌ ANTI-PATRÓN: calcular períodos tarifarios en la consulta
-- (lógica de negocio duplicada; puede divergir de la dimensión)
WHERE CASE WHEN strftime('%H', datetime(f.unix_time,'unixepoch','+1 hour')) BETWEEN '10' AND '14'
           THEN 'P1' END = 'P1'

-- ✅ CORRECTO: usar la dimensión conformada
WHERE d.tariff_period = 'P1'


-- ❌ ANTI-PATRÓN: JOIN directo entre dos tablas de hechos
-- (sin pasar por la dimensión conformada)
SELECT a.pv_power_gen_kw, b.charge_kw           -- hipotético
FROM gold_fact_energy_forecast a
JOIN gold_fact_battery_ops b                      -- hipotético
    ON a.client_id = b.client_id
    AND a.unix_time = b.unix_time

-- ✅ CORRECTO: drill-across via dimensiones conformadas
SELECT f.pv_power_gen_kw, b.charge_kw
FROM gold_dim_datetime d
JOIN gold_fact_energy_forecast f ON d.unix_time = f.unix_time
JOIN gold_fact_battery_ops b     ON d.unix_time = b.unix_time    -- misma dim
WHERE d.date = '2026-05-10'


-- ❌ ANTI-PATRÓN: SUM de métricas no aditivas
SELECT AVG(pv_performance_ratio) -- SIN ponderar → resultado incorrecto

-- ✅ CORRECTO: PR real = ratio de sumas
SELECT SUM(pv_power_gen_kw) / NULLIF(SUM(pv_peak_power_kw * poa_wm2 / 1000.0), 0)
-- o si no se tiene poa_wm2 accesible fácilmente:
SELECT AVG(pv_performance_ratio)    -- sólo válido si todos los poa_wm2 son similares
```

---

### 6.4 Consideraciones de Performance

**SQLite — optimizaciones aplicadas:**

```sql
-- Los índices siguientes están creados automáticamente por el pipeline Gold
-- y cubren los patrones de consulta más frecuentes:

-- 1. Filtros temporales (más frecuente)
CREATE INDEX idx_gold_fact_unix_time ON gold_fact_energy_forecast (unix_time);

-- 2. JOINs con dim_weather
CREATE INDEX idx_gold_fact_weather_id ON gold_fact_energy_forecast (weather_id);

-- Añadir para producción:
-- 3. Filtros por cliente
CREATE INDEX idx_gold_fact_client_id ON gold_fact_energy_forecast (client_id);

-- 4. Patrón más común: filtrar por cliente + rango temporal
CREATE INDEX idx_gold_fact_client_time ON gold_fact_energy_forecast (client_id, unix_time);

-- 5. Filtros en dim_datetime por período tarifario
CREATE INDEX idx_dim_datetime_tariff ON gold_dim_datetime (tariff_period);
CREATE INDEX idx_dim_datetime_date   ON gold_dim_datetime (date);
```

**Guía de performance por tipo de consulta:**

| Tipo de consulta | Estrategia recomendada | Tiempo esperado (SQLite, 5 clientes, 1 año) |
|-----------------|----------------------|------------------------------------------|
| Forecast próximas 24h (1 cliente) | Índice `(client_id, unix_time)` | < 1 ms |
| KPIs diarios todos los clientes | Índice `unix_time` + GROUP BY | < 5 ms |
| Análisis histórico 1 año por cliente | Índice `(client_id, unix_time)` | < 50 ms |
| Análisis histórico flota completa | Scan completo + GROUP BY | < 500 ms |
| Análisis histórico > 1 año, > 50 clientes | Migrar a DuckDB/PostgreSQL | — |

**Recomendaciones para consultas complejas:**

```sql
-- Usar CTEs para legibilidad y reutilización de subresultados
WITH forecast_manana AS (
    SELECT f.*, d.tariff_label, d.tariff_period, d.hour_local,
           c.name, c.pv_peak_power_kw, c.battery_capacity_kwh, c.has_battery
    FROM gold_fact_energy_forecast f
    JOIN gold_dim_datetime d ON f.unix_time  = d.unix_time
    JOIN gold_dim_client   c ON f.client_id  = c.client_id
    WHERE d.date = date('now', '+1 day')
),
resumen_por_periodo AS (
    SELECT client_id, name, tariff_period, tariff_label,
           SUM(pv_power_gen_kw)      AS gen_kwh,
           SUM(power_consumption_kw) AS con_kwh,
           AVG(price_pvpc_eur_mwh)   AS precio_medio
    FROM forecast_manana
    GROUP BY client_id, name, tariff_period, tariff_label
)
SELECT *,
       ROUND(gen_kwh - con_kwh, 2)                        AS balance_kwh,
       ROUND((con_kwh / 1000.0) * precio_medio, 4)        AS coste_bruto_eur,
       ROUND((MAX(0, con_kwh - gen_kwh) / 1000.0) * precio_medio, 4) AS coste_neto_eur
FROM resumen_por_periodo
ORDER BY client_id, tariff_period;
```

**Cuándo migrar de SQLite a un motor columnar:**

| Condición | Motor recomendado |
|-----------|-----------------|
| > 50 clientes activos | **DuckDB** — columnar en proceso, compatible con Python/pandas |
| > 5 años de histórico | **DuckDB** o **PostgreSQL + TimescaleDB** |
| Múltiples usuarios concurrentes | **PostgreSQL** |
| Integración con Spark/Databricks | **Delta Lake** (Parquet + transacciones ACID) |
| Dashboard en tiempo real | **ClickHouse** o **DuckDB + Grafana** |

---

*SunSaver ETL · Diseño del Star Schema (Gold Layer) v1.0.0 · Mayo 2026*  
*Clasificación: INTERNA · Audiencia: Analistas de datos, Científicos de datos, Ingenieros BI*