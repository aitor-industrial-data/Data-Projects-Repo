# ☀️ SunSaver ETL — Photovoltaic Intelligence Platform

> **Transforming raw solar and weather data into bankable energy decisions for industrial facilities.**

---

## 🏭 The Industrial Problem

Industrial facilities with photovoltaic installations face a critical, costly problem every single day: **they are flying blind**.

The solar panels are generating energy. The grid is pricing that energy differently every hour. The sky is changing. But the operations manager has no unified, real-time picture that ties all of it together.

The result?

- Compressors and furnaces run at peak hours when grid electricity costs 3× more
- Batteries sit idle when surplus solar is being curtailed to the grid at near-zero prices
- Maintenance is reactive, not predicted
- The CFO cannot verify whether the solar installation is delivering its promised ROI

**SunSaver ETL solves this.** It is a production-grade data pipeline that ingests, transforms, and structures every variable that drives energy cost and solar yield — giving industrial operators the analytical foundation they need to act, not just observe.

---

## 🔬 What It Does

SunSaver is a **multi-stage ETL pipeline** built around the medallion architecture (Bronze → Silver → Gold). Every 24 hours it:

1. **Reads client installation data** from a master Excel file (panel specs, coordinates, loss coefficients, battery config)
2. **Fetches tomorrow's electricity prices** from the Spanish grid operator REE via their public API (PVPC + Spot market, hour by hour)
3. **Pulls 5-day weather forecasts** from OpenWeatherMap for each client's exact GPS coordinates
4. **Runs a physics-based PV generation model** that calculates, for every 3-hour forecast window:
   - Global Horizontal Irradiance (GHI) using the Haurwitz clear-sky model + cloud and weather correction
   - Beam/diffuse decomposition via the **Erbs model**
   - Plane-of-Array irradiance (POA) considering panel tilt, azimuth and ground albedo
   - Cell temperature correction using the **Faiman model**
   - AC power output with thermal derating and system loss coefficients
   - Dynamic industrial consumption simulation (shift schedules, HVAC thermal load, stochastic noise)
5. **Populates a Gold layer** star schema ready for BI dashboards or ML models

All of this runs unattended, idempotently, and with structured logging at every step.

---

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                        DATA SOURCES                             │
│  Excel (clients) │  REE API (prices) │  OpenWeather API (wx)   │
└────────┬─────────┴────────┬──────────┴────────┬────────────────┘
         │                  │                   │
         ▼                  ▼                   ▼
┌─────────────────────────────────────────────────────────────────┐
│                    🥉 BRONZE LAYER                              │
│   raw_clients  │  raw_prices  │  raw_weather                   │
│   (append-only, full audit trail, _ingested_at_utc)            │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│                    🥈 SILVER LAYER                              │
│  clean_clients │ clean_prices │ clean_weather │ clean_calcs     │
│  (typed, validated, deduplicated, PK-enforced)                  │
│                        │                                        │
│          ┌─────────────┘                                        │
│          ▼                                                       │
│   ⚡ PV GENERATION ENGINE (pvlib + Haurwitz + Erbs + Faiman)   │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│                    🥇 GOLD LAYER (Star Schema)                  │
│  gold_dim_client  │  gold_dim_datetime  │  gold_dim_weather     │
│                   gold_fact_energy_forecast                      │
│  (BI-ready, FK-enforced, indexed)                               │
└─────────────────────────────────────────────────────────────────┘
```

### Pipeline Execution Order

| Stage | Step | Input → Output |
|-------|------|----------------|
| 1 | `extract_clients` | Excel → `raw_clients` |
| 1 | `extract_energy_prices` | REE API → `raw_prices` |
| 2 | `transform_clients` | `raw_clients` → `clean_clients` |
| 2 | `transform_energy_prices` | `raw_prices` → `clean_prices` |
| 3 | `extract_openweather` | OpenWeather API → `raw_weather` |
| 4 | `transform_openweather` | `raw_weather` → `clean_weather` |
| 5 | `extract_generation_data` | `clean_clients` + `clean_weather` → `clean_calculations` |
| 6 | `gold_dim_*` + `gold_fact_energy_forecast` | Silver → Gold |

---

## ⚡ The Physics Engine

The core differentiator of SunSaver is that it does not rely on simplistic irradiance look-up tables. It implements a **chain of validated photovoltaic models**:

```
Solar Position (pvlib) → GHI (Haurwitz + Cloud Correction)
    → DNI + DHI (Erbs Decomposition)
        → POA (Liu-Jordan + Albedo)
            → T_cell (Faiman)
                → P_AC (Thermal Derating + System Losses)
```

Each step degrades gracefully: if the sun is below 2° of elevation, all downstream calculations short-circuit to zero, eliminating the numerical instability that plagues near-horizon calculations.

The consumption model simulates a real industrial load profile — shift start surges, lunch valley, HVAC thermal response to ambient temperature — producing net energy balance figures that operations teams can actually use.

---

## 🗄️ Gold Schema (Star Schema)

```sql
gold_fact_energy_forecast
    ├── client_id          (FK → gold_dim_client)
    ├── unix_time          (FK → gold_dim_datetime)
    ├── weather_id         (FK → gold_dim_weather)
    ├── pv_power_gen_kw
    ├── power_consumption_kw
    ├── poa_wm2
    ├── t_cell_celsius
    ├── temp_celsius / humidity_pct / clouds_pct / wind_speed_mps
    ├── price_pvpc_eur_mwh
    └── price_spot_eur_mwh

gold_dim_datetime
    ├── datetime_utc / datetime_local
    ├── tariff_period      (P1 Punta / P2 Llano / P3 Valle / P6 Super-Valle)
    ├── is_weekend / is_festivo / is_daylight
    └── hour_utc / hour_local / day_of_week / month / year

gold_dim_client
    ├── pv_peak_power_kw / panel_type / efficiency / loss_pct
    ├── angle / aspect / mounting
    ├── battery_capacity_kwh / soc_min_pct
    ├── has_solar / has_battery   (derived boolean flags)
    └── installation_cost_eur

gold_dim_weather
    ├── weather_id (OpenWeather codes)
    ├── weather_main / weather_description
    └── (resolved by frequency when multiple descriptions exist for same ID)
```

---

## 🛠️ Tech Stack

| Layer | Technology |
|-------|------------|
| Language | Python 3.11+ |
| PV Modelling | `pvlib` (industry standard) |
| Data Manipulation | `pandas`, `numpy` |
| Database | SQLite (portable, zero-config) |
| ORM/SQL | `sqlalchemy` (UPSERT, DDL) |
| External APIs | `requests` (REE, OpenWeather) |
| Config | `python-dotenv` |
| Scheduling | Cron / any scheduler |

---

## 🚀 Quick Start

```bash
# 1. Clone and install
git clone https://github.com/your-user/sunsaver-etl.git
cd sunsaver-etl
pip install -r requirements.txt

# 2. Configure environment
cp .env.example .env
# Edit .env → add WEATHER_API_KEY (OpenWeatherMap)
#           → optionally set DB_PATH

# 3. Add your clients
# Edit data/clients_source.xlsx with your facility data

# 4. Run the full pipeline
cd src
python orchestrator.py

# Or resume from a specific stage (e.g., after a weather API failure)
python orchestrator.py --stage 3

# Dry-run to validate the execution plan
python orchestrator.py --dry-run
```

---

## 📁 Project Structure

```
05.02_SunSaver_ETL/
├── data/
│   ├── clients_source.xlsx     # Master client configuration
│   └── sunsaver.db             # SQLite database (auto-created)
├── docs/                       # Architecture diagrams and reference docs
├── logs/                       # Pipeline execution logs
├── src/
│   ├── orchestrator.py         # Pipeline controller
│   ├── db_manager.py           # Database path resolution
│   ├── pv_generation_engine.py # Physics models (GHI, DNI, POA, Faiman)
│   ├── extract_*.py            # Bronze layer extractors
│   ├── transform_*.py          # Silver layer transformers
│   └── transform_gold_*.py     # Gold layer builders
├── venv/
├── requirements.txt
└── README.md
```

---

## 🔧 Environment Variables

| Variable | Required | Description |
|----------|----------|-------------|
| `WEATHER_API_KEY` | ✅ Yes | OpenWeatherMap API key (free tier sufficient) |
| `DB_PATH` | ❌ Optional | Override default SQLite path (`data/sunsaver.db`) |

---

## 📈 Business Value

| Capability | Impact |
|------------|--------|
| Hour-by-hour price + generation forecast | Enables load shifting to save 20–40% on grid electricity cost |
| Multi-client architecture | Single pipeline serves N industrial facilities simultaneously |
| Spanish tariff period labelling (P1–P6) | Direct integration with billing and demand management systems |
| Audit-complete Bronze layer | Regulatory compliance and historical replay capability |
| Physics-based (not ML-guessed) generation model | Reliable even for new installations with no historical data |
| Idempotent UPSERT pattern | Safe to re-run without data corruption |

---


> *Built for industrial energy managers who are tired of spreadsheets and ready for real data engineering.*
