# 📂 `/src` — Referencia de Scripts del Pipeline

Este directorio contiene el pipeline ETL completo de SunSaver. Cada script tiene una responsabilidad única y bien definida siguiendo el **Principio de Responsabilidad Única**. En conjunto forman un pipeline de datos de 6 etapas orquestado por `orchestrator.py`.

---

## 🗺️ Mapa de Scripts

```
src/
├── orchestrator.py            ← Punto de entrada. Ejecutar esto.
├── db_manager.py              ← Utilidad compartida: resuelve la ruta a la BD
├── pv_generation_engine.py    ← Motor de física (GHI → Potencia)
│
├── extract_clients.py         ← Etapa 1a: Excel → raw_clients
├── extract_energy_prices.py   ← Etapa 1b: API REE → raw_prices
├── extract_openweather.py     ← Etapa 3:  OpenWeather → raw_weather
├── extract_power_data.py      ← Etapa 5:  Merge Plata → clean_calculations
│
├── transform_clients.py       ← Etapa 2a: raw_clients → clean_clients
├── transform_energy_prices.py ← Etapa 2b: raw_prices → clean_prices
├── transform_openweather.py   ← Etapa 4:  raw_weather → clean_weather
│
├── transform_gold_dim_clients.py  ← Etapa 6a: → gold_dim_client
├── transform_gold_dim_datetime.py ← Etapa 6b: → gold_dim_datetime
├── transform_gold_dim_weather.py  ← Etapa 6c: → gold_dim_weather
└── transform_gold_fact_energy.py  ← Etapa 6d: → gold_fact_energy_forecast
```

---

## 🎛️ `orchestrator.py`

**El único punto de entrada para todo el pipeline.**

Define y ejecuta las 6 etapas en orden de dependencia. Cada paso está envuelto en control de errores con cronómetro preciso — si una etapa falla completamente, el pipeline aborta para evitar que datos corruptos se propaguen a etapas posteriores.

**Características clave:**
- Flag `--stage N` para reanudar desde cualquier etapa (p.ej., `--stage 3` omite la re-extracción Bronce)
- Flag `--dry-run` para imprimir el plan de ejecución sin llamar a ninguna función
- Contrato de retorno `True/False` por paso — cualquier paso que devuelva `False` se registra y contabiliza
- Lógica de aborte por etapa: si *todos* los pasos de una etapa fallan, la ejecución se detiene

```bash
python orchestrator.py              # Pipeline completo
python orchestrator.py --stage 4   # Reanudar desde la Etapa 4
python orchestrator.py --dry-run   # Imprimir plan únicamente
```

---

## 🔧 `db_manager.py`

**Utilidad compartida que resuelve la ruta absoluta a la base de datos SQLite.**

Lee `DB_PATH` del `.env` si está configurado; en caso contrario usa por defecto `<raíz_del_proyecto>/data/sunsaver.db`. Garantiza que el directorio `/data` exista antes de devolver la ruta. Importado por todos los scripts que necesitan acceso a la base de datos, proporcionando una única fuente de verdad para la ubicación de la BD.

---

## ⚡ `pv_generation_engine.py`

**El motor de física. El módulo técnicamente más sofisticado del proyecto.**

Implementa una cadena validada de modelos fotovoltaicos y atmosféricos que convierte las condiciones atmosféricas en una estimación de potencia generada. Puede ejecutarse de forma independiente (`python pv_generation_engine.py`) para probar con entradas hardcodeadas.

### Cadena de funciones:

| Función | Modelo | Salida |
|----------|-------|--------|
| `calculate_solar_position()` | pvlib / Astronómico | Elevación solar (α), Azimut |
| `calculate_ghi()` | Haurwitz cielo despejado + corrección Kasten-Czeplak + factor weather_id | GHI (W/m²) |
| `decompose_erbs()` | Modelo de descomposición de Erbs | DNI, DHI (W/m²) |
| `calculate_total_poa()` | Liu-Jordan isotrópico + Albedo | POA (W/m²) |
| `calculate_t_cell()` | Modelo térmico de Faiman | T_célula (°C) |
| `calculate_power_output()` | Derating térmico + pérdidas del sistema | P_AC (kW), Performance Ratio |
| `calculate_industrial_consumption()` | Turnos + respuesta HVAC + ruido gaussiano | P_consumo (kW) |

**Salvaguardas de ingeniería integradas:**
- Elevación solar < 2° → todos los valores posteriores cortocircuitan a 0.0 (evita inestabilidad numérica cerca del horizonte)
- Cada función devuelve un valor seguro por defecto ante cualquier excepción — el ETL nunca se interrumpe por una fila incorrecta
- Los códigos weather_id (OpenWeather) se mapean a factores de transmitancia que modifican el GHI de cielo despejado de forma independiente a la fracción nubosa

---

## 📥 Extractores Capa Bronce

### `extract_clients.py`

Lee `data/clients_source.xlsx` con `pandas` + `openpyxl` y añade las filas brutas a `raw_clients` en SQLite, incorporando la columna de auditoría `_ingested_at_utc`. Usa `if_exists='append'` — la capa Bronce es un log inmutable, nunca se sobreescribe.

**Función pública:** `extract_clients() → bool`

---

### `extract_energy_prices.py`

Consulta la **API pública de REE (Red Eléctrica de España)** para obtener los precios de electricidad del día siguiente (tarifa PVPC + Mercado Spot), hora a hora. La respuesta JSON completa se serializa como un blob de texto y se almacena en `raw_prices` junto a la marca temporal de ingesta.

Gestiona el error 502 que devuelve REE antes de las ~20:30h cuando los precios del día siguiente aún no han sido publicados, registrando un aviso claro en lugar de lanzar una excepción.

**Función pública:** `extract_energy_prices() → bool`

---

### `extract_openweather.py`

Lee las coordenadas de `clean_clients` y llama a la **API Forecast de OpenWeatherMap** (5 días / 3 horas) para cada cliente de forma independiente. Cada respuesta se almacena como un blob JSON en `raw_weather` identificado por `client_id`.

Diseñado para **resiliencia multi-cliente**: si la llamada a la API falla para un cliente, ese cliente se omite y el bucle continúa con el resto.

**Función pública:** `extract_openweather(client_table, weather_table) → bool`

---

### `extract_power_data.py`

Combina `clean_clients` y `clean_weather` mediante una JOIN en SQL, luego pasa cada fila por la cadena de física completa de `pv_generation_engine.py`. Los resultados se escriben en `clean_calculations` usando UPSERT `INSERT OR REPLACE` con clave primaria compuesta `(client_id, unix_time)`.

Técnicamente es un paso de **Transformación** que usa nomenclatura Extract porque calcula datos derivados (estimaciones de generación) en lugar de limpiar datos brutos.

**Función pública:** `extract_generation_data() → bool`

---

## 🔄 Transformadores Capa Plata

### `transform_clients.py`

Lee todas las filas de `raw_clients`, aplica control de calidad completo y escribe una tabla limpia y deduplicada en `clean_clients` (con `client_id` como PRIMARY KEY).

**Transformaciones aplicadas:**
- Coerción numérica con `errors='coerce'` (valores inválidos → NaN, sin excepciones)
- Validación de coordenadas (lat ∈ [-90, 90], lon ∈ [-180, 180])
- Recorte de rango para constantes físicas (`angle`, `loss_pct`, `efficiency`, `soc_min_pct`)
- Guardia contra valores negativos en campos de potencia, área y coste
- Resolución de duplicados: conserva el registro más recientemente ingestado por `client_id`
- Relleno de nulos con valores por defecto de ingeniería (ángulo=30°, orientación=180° Sur, eficiencia=15%, etc.)

**Función pública:** `transform_clients() → bool`

---

### `transform_energy_prices.py`

Parsea el blob JSON de REE almacenado, aplana las series de precios PVPC y Spot en filas tabulares y las carga en `clean_prices` con PK compuesta `(datetime_utc, price_type)`.

**Transformaciones aplicadas:**
- Parseo de fechas con conciencia UTC
- Filtrado de outliers: precios fuera de [-100, 2000] €/MWh se marcan y eliminan
- Interpolación lineal + relleno hacia delante/atrás para valores horarios faltantes
- Columna unix_time generada para compatibilidad de join con datos meteorológicos

**Función pública:** `transform_energy_prices() → bool`

---

### `transform_openweather.py`

Desempaqueta el JSON anidado de OpenWeather para la última ingesta de cada cliente, aplana las 40 ventanas de pronóstico (5 días × 8 intervalos/día) en filas y las carga en `clean_weather` con PK `(client_id, unix_time)`.

**Transformaciones aplicadas:**
- Flag `is_daylight` derivado del campo `pod` (part of day) de OpenWeather
- Probabilidad de precipitación normalizada desde el campo `pop`
- Deduplicación por `(client_id, forecast_time_utc)` conservando el pronóstico más recientemente ingestado
- UPSERT garantiza que los slots históricos nunca se duplican aunque el pipeline se ejecute varias veces al día

**Función pública:** `transform_openweather() → bool`

---

## 🥇 Constructores Capa Oro

La capa Oro implementa un **star schema** optimizado para herramientas BI y consultas analíticas. Los cuatro scripts se ejecutan como parte de la Etapa 6 en el orquestador, en orden de dependencia (dimensiones primero, tabla de hechos al final).

### `transform_gold_dim_clients.py`

Lee `clean_clients` y materializa `gold_dim_client`, añadiendo dos campos booleanos derivados:
- `has_solar` (1 si `pv_peak_power_kw > 0`)
- `has_battery` (1 si `battery_capacity_kwh > 0`)

Cada ejecución elimina y recrea la tabla de forma atómica dentro de una única transacción.

**Función pública:** `load_dim_client() → None`

---

### `transform_gold_dim_datetime.py`

Genera una **dimensión temporal enriquecida** a partir de los valores únicos de `unix_time` en `clean_weather`. Para cada marca temporal calcula:
- Strings de fecha/hora UTC y local (Europe/Madrid)
- **Periodo tarifario** español (P1 Punta / P2 Llano / P3 Valle / P6 Super-Valle) — clave para el análisis de costes
- `is_weekend`, `is_festivo` (festivos nacionales hardcodeados), `is_daylight`

**Función pública:** `load_dim_datetime() → None`

---

### `transform_gold_dim_weather.py`

Construye una tabla de lookup de códigos de condición meteorológica de OpenWeather a partir de `clean_weather`. Cuando existen múltiples descripciones para el mismo `weather_id`, resuelve a la más frecuente usando una **window function SQL** (`ROW_NUMBER() OVER PARTITION BY`).

**Función pública:** `load_dim_weather() → None`

---

### `transform_gold_fact_energy.py`

El paso final y más complejo. Ensambla `gold_fact_energy_forecast` mediante un INSERT con múltiples JOINs:

- `clean_calculations` → generación solar, consumo, temperatura de célula, POA
- `clean_weather` → condiciones meteorológicas
- `clean_prices` (PVPC) → precio PVPC en el unix_time exacto
- `clean_prices` (Spot) → precio Spot **promediado por hora** (los datos Spot son sub-horarios; se agregan con `AVG() GROUP BY hour_unix`)

Crea índices de rendimiento sobre `unix_time` y `weather_id` tras la inserción.

**Función pública:** `load_fact_energy_forecast() → bool`

---

## 🔌 Dependencias entre Scripts

```
db_manager ◄──────────────────────── todos los scripts
pv_generation_engine ◄────────────── extract_power_data

extract_clients ───────────────────► transform_clients
                                           │
                                           ▼
extract_energy_prices ─────────────► transform_energy_prices
                                           │
extract_openweather ◄──────────────── clean_clients (coordenadas)
        │
        ▼
transform_openweather ─────────────────────────────────┐
                                                        ▼
extract_power_data (cálculo FV) ◄──── clean_clients + clean_weather
        │
        ▼
 clean_calculations ──┐
 clean_clients ────────┼──► Capa Oro (dims + fact)
 clean_weather ────────┤
 clean_prices ─────────┘
```

---

## 📋 Contrato de Retorno

Todas las funciones públicas del pipeline devuelven `bool`:

| Retorno | Significado |
|---------|-------------|
| `True` | Paso completado con éxito (puede haber 0 filas pero sin error) |
| `False` | Paso fallido — revisar los logs para más detalle |
| `None` | Funciones de dimensiones Gold (lanzan excepción ante fallo; el orquestador la captura) |

El orquestador trata los retornos `False` y las excepciones no capturadas de forma equivalente — ambos cuentan como fallos de paso.
