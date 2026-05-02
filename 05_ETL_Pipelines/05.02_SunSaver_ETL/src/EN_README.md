# 📂 `/src` — Pipeline Scripts Reference

This directory contains the complete ETL pipeline for SunSaver. Each script has a single, well-defined responsibility following the **Single Responsibility Principle**. Together they form a 6-stage data pipeline orchestrated by `orchestrator.py`.

---

## 🗺️ Script Map

```
src/
├── orchestrator.py            ← Entry point. Run this.
├── db_manager.py              ← Shared utility: resolves DB path
├── pv_generation_engine.py    ← Physics engine (GHI → Power)
│
├── extract_clients.py         ← Stage 1a: Excel → raw_clients
├── extract_energy_prices.py   ← Stage 1b: REE API → raw_prices
├── extract_openweather.py     ← Stage 3:  OpenWeather → raw_weather
├── extract_power_data.py      ← Stage 5:  Silver merge → clean_calculations
│
├── transform_clients.py       ← Stage 2a: raw_clients → clean_clients
├── transform_energy_prices.py ← Stage 2b: raw_prices → clean_prices
├── transform_openweather.py   ← Stage 4:  raw_weather → clean_weather
│
├── transform_gold_dim_clients.py  ← Stage 6a: → gold_dim_client
├── transform_gold_dim_datetime.py ← Stage 6b: → gold_dim_datetime
├── transform_gold_dim_weather.py  ← Stage 6c: → gold_dim_weather
└── transform_gold_fact_energy.py  ← Stage 6d: → gold_fact_energy_forecast
```

---

## 🎛️ `orchestrator.py`

**The single entry point for the entire pipeline.**

Defines and runs all 6 stages in dependency order. Each step is wrapped in error handling with precise timing — if a stage fails completely, the pipeline aborts to prevent corrupt data from propagating to downstream stages.

**Key features:**
- `--stage N` flag to resume from any stage (e.g., `--stage 3` skips Bronze re-extraction)
- `--dry-run` flag to print the execution plan without calling any function
- Per-step `True/False` return contract — any step returning `False` is logged and counted
- Stage-level abort logic: if *all* steps of a stage fail, execution stops

```bash
python orchestrator.py              # Full pipeline
python orchestrator.py --stage 4   # Resume from Stage 4
python orchestrator.py --dry-run   # Print plan only
```

---

## 🔧 `db_manager.py`

**Shared utility that resolves the absolute path to the SQLite database.**

Reads `DB_PATH` from `.env` if set; otherwise defaults to `<project_root>/data/sunsaver.db`. Ensures the `/data` directory exists before returning the path. Imported by every script that needs database access, providing a single source of truth for the DB location.

---

## ⚡ `pv_generation_engine.py`

**The physics engine. The most technically sophisticated module in the project.**

Implements a validated chain of photovoltaic models that converts atmospheric conditions into a power generation estimate. Can be run standalone (`python pv_generation_engine.py`) to test with hardcoded inputs.

### Function chain:

| Function | Model | Output |
|----------|-------|--------|
| `calculate_solar_position()` | pvlib / Astronomical | Solar elevation (α), Azimuth |
| `calculate_ghi()` | Haurwitz clear-sky + Kasten-Czeplak cloud correction + Weather ID factor | GHI (W/m²) |
| `decompose_erbs()` | Erbs decomposition model | DNI, DHI (W/m²) |
| `calculate_total_poa()` | Liu-Jordan isotropic + Albedo | POA (W/m²) |
| `calculate_t_cell()` | Faiman thermal model | T_cell (°C) |
| `calculate_power_output()` | Thermal derating + system losses | P_AC (kW), Performance Ratio |
| `calculate_industrial_consumption()` | Shift-schedule + HVAC thermal response + Gaussian noise | P_consumption (kW) |

**Engineering safeguards built in:**
- Solar elevation < 2° → all downstream values short-circuit to 0.0 (avoids near-horizon numerical instability)
- Every function returns a safe default on exception — the ETL never crashes due to a bad row
- Weather ID codes (OpenWeather) map to transmittance factors that modify clear-sky GHI independently from cloud fraction

---

## 📥 Bronze Layer Extractors

### `extract_clients.py`

Reads `data/clients_source.xlsx` using `pandas` + `openpyxl` and appends the raw rows to `raw_clients` in SQLite, adding an `_ingested_at_utc` audit column. Uses `if_exists='append'` — the Bronze layer is an immutable log, never overwritten.

**Public function:** `extract_clients() → bool`

---

### `extract_energy_prices.py`

Queries the **REE (Red Eléctrica de España)** public API for tomorrow's electricity prices (PVPC tariff + Spot market), hour by hour. The full JSON response is serialised as a single text blob and stored in `raw_prices` alongside an ingestion timestamp.

Handles the 502 error that REE returns before ~20:30h when tomorrow's prices haven't been published yet, logging a clean warning instead of crashing.

**Public function:** `extract_energy_prices() → bool`

---

### `extract_openweather.py`

Reads coordinates from `clean_clients` and calls the **OpenWeatherMap Forecast API** (5-day / 3-hour) for each client independently. Each response is stored as a JSON blob in `raw_weather` keyed by `client_id`.

Designed for **multi-client resilience**: if the API call fails for one client, that client is skipped and the loop continues for the rest.

**Public function:** `extract_openweather(client_table, weather_table) → bool`

---

### `extract_power_data.py`

Joins `clean_clients` and `clean_weather` in SQL, then passes each row through the full physics chain in `pv_generation_engine.py`. Results are written to `clean_calculations` using an `INSERT OR REPLACE` UPSERT with a composite primary key `(client_id, unix_time)`.

This is technically a **Transform** step that lives in the Extract naming convention because it computes derived data (generation estimates) rather than cleaning raw data.

**Public function:** `extract_generation_data() → bool`

---

## 🔄 Silver Layer Transformers

### `transform_clients.py`

Reads all rows from `raw_clients`, applies full data quality enforcement, and writes a clean, deduplicated table to `clean_clients` (with `client_id` as PRIMARY KEY).

**Transformations applied:**
- Numeric coercion with `errors='coerce'` (invalid values → NaN, not crash)
- Coordinate validation (lat ∈ [-90, 90], lon ∈ [-180, 180])
- Range clipping for physical constants (`angle`, `loss_pct`, `efficiency`, `soc_min_pct`)
- Negative value guard for power, area and cost fields
- Duplicate resolution: keeps the most recently ingested record per `client_id`
- Null fill with engineering defaults (angle=30°, aspect=180° South, efficiency=15%, etc.)

**Public function:** `transform_clients() → bool`

---

### `transform_energy_prices.py`

Parses the stored REE JSON blob, flattens the PVPC and Spot price series into tabular rows, and loads them into `clean_prices` with a composite PK `(datetime_utc, price_type)`.

**Transformations applied:**
- Datetime parsing with UTC-awareness
- Outlier filtering: prices outside [-100, 2000] €/MWh are flagged and removed
- Linear interpolation + forward/backward fill for any missing hourly values
- Unix timestamp column generated for join compatibility with weather data

**Public function:** `transform_energy_prices() → bool`

---

### `transform_openweather.py`

Unpacks the nested OpenWeather JSON for each client's latest ingestion, flattens the 40 forecast slots (5 days × 8 intervals/day) into rows, and loads them into `clean_weather` with PK `(client_id, unix_time)`.

**Transformations applied:**
- `is_daylight` flag derived from OpenWeather's `pod` (part of day) field
- Rain probability normalised from the `pop` field
- Deduplication by `(client_id, forecast_time_utc)` keeping the most recently ingested forecast
- UPSERT ensures historical slots are never duplicated even if the pipeline runs multiple times per day

**Public function:** `transform_openweather() → bool`

---

## 🥇 Gold Layer Builders

The Gold layer implements a **star schema** optimised for BI tools and analytical queries. All four scripts are run as part of Stage 6 in the orchestrator, in dependency order (dimensions first, fact table last).

### `transform_gold_dim_clients.py`

Reads `clean_clients` and materialises `gold_dim_client`, adding two derived boolean fields:
- `has_solar` (1 if `pv_peak_power_kw > 0`)
- `has_battery` (1 if `battery_capacity_kwh > 0`)

Each run drops and recreates the table atomically within a single transaction.

**Public function:** `load_dim_client() → None`

---

### `transform_gold_dim_datetime.py`

Generates a **rich time dimension** from the distinct `unix_time` values in `clean_weather`. For each timestamp it computes:
- UTC and local (Europe/Madrid) datetime strings
- Spanish electricity **tariff period** (P1 Punta / P2 Llano / P3 Valle / P6 Super-Valle) — critical for cost analysis
- `is_weekend`, `is_festivo` (national holidays hardcoded), `is_daylight`

**Public function:** `load_dim_datetime() → None`

---

### `transform_gold_dim_weather.py`

Builds a lookup table of distinct OpenWeather condition codes from `clean_weather`. When multiple descriptions exist for the same `weather_id`, resolves to the most frequent one using a **SQL window function** (`ROW_NUMBER() OVER PARTITION BY`).

**Public function:** `load_dim_weather() → None`

---

### `transform_gold_fact_energy.py`

The final, most complex step. Assembles `gold_fact_energy_forecast` via a single multi-JOIN INSERT:

- `clean_calculations` → solar generation, consumption, cell temperature, POA
- `clean_weather` → meteorological conditions
- `clean_prices` (PVPC) → PVPC price at exact unix_time
- `clean_prices` (Spot) → **hour-averaged** Spot price (Spot data is sub-hourly; aggregated with `AVG() GROUP BY hour_unix`)

Creates performance indexes on `unix_time` and `weather_id` after insertion.

**Public function:** `load_fact_energy_forecast() → bool`

---

## 🔌 Inter-Script Dependencies

```
db_manager ◄─────────────────────── all scripts
pv_generation_engine ◄──────────── extract_power_data

extract_clients ──────────────────► transform_clients
                                          │
                                          ▼
extract_energy_prices ────────────► transform_energy_prices
                                          │
extract_openweather ◄─────────────── clean_clients (coords)
        │
        ▼
transform_openweather ──────────────────────────────┐
                                                     ▼
extract_power_data (PV calc) ◄──── clean_clients + clean_weather
        │
        ▼
 clean_calculations ──┐
 clean_clients ───────┼──► Gold Layer (dims + fact)
 clean_weather ───────┤
 clean_prices ────────┘
```

---

## 📋 Return Contract

All public pipeline functions return `bool`:

| Return | Meaning |
|--------|---------|
| `True` | Step completed successfully (data may be 0 rows but no error) |
| `False` | Step failed — check logs for details |
| `None` | Gold dim functions (they raise on failure; orchestrator catches) |

The orchestrator treats `False` returns and unhandled exceptions equivalently — both count as step failures.
