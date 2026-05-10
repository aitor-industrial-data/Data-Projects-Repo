# 01 — Architecture Decision Record (ADR)
## SunSaver · Industrial Energy Intelligence Platform
**Version:** 1.0.0 · **Status:** Active · **Author:** Aitor Asin · **Date:** 2025-05-10

> *"This document is the single source of truth for every architectural decision made in the SunSaver platform. It exists to explain not just what was built, but why — and what was deliberately left behind."*

---

## Table of Contents

1. [Executive Summary](#1-executive-summary)
2. [Context & Problem Statement](#2-context--problem-statement)
3. [Architecture Overview](#3-architecture-overview)
4. [Medallion Architecture Rationale](#4-medallion-architecture-rationale)
5. [Technology Stack Decisions](#5-technology-stack-decisions)
6. [ADR Log — Individual Decision Records](#6-adr-log--individual-decision-records)
7. [Cross-Cutting Concerns](#7-cross-cutting-concerns)
8. [Technical Roadmap](#8-technical-roadmap)

---

## 1. Executive Summary

### 1.1 Objective of the System

SunSaver is an **industrial energy intelligence platform** designed to provide SMEs with photovoltaic installations the operational data required to make evidence-based energy management decisions.

The system ingests heterogeneous external data (Spanish electricity market prices via REE API, atmospheric forecasts via OpenWeatherMap), applies a validated chain of photovoltaic physics models, and delivers a 5-day forward-looking energy forecast with hourly granularity — covering solar generation, industrial consumption, and real-time electricity prices.

The primary output is a **Gold-layer star schema** optimised for analytical consumption: every row in `gold_fact_energy_forecast` answers the question *"for this client, at this hour, how much energy will be generated, how much will be consumed, and what will it cost?"*. This structured intelligence enables actionable decisions on flexible load management: battery charging schedules, machinery start-up windows, and peak-demand avoidance.

### 1.2 Scope and Domain

The system operates at the intersection of two domains:

**Physical domain — Photovoltaic generation modelling:**
The platform implements a full atmospheric-to-electrical physics chain: solar geometry (NREL SPA via pvlib), clear-sky irradiance (Haurwitz model), cloud attenuation (Kasten-Czeplak), irradiance decomposition (Erbs model), plane-of-array projection (Liu-Jordan isotropic + albedo), cell temperature modelling (Faiman model), and AC power output with thermal derating (−0.4 %/°C for crystalline silicon).

**Economic domain — Spanish electricity market:**
The platform integrates with the Red Eléctrica de España (REE) public API to ingest PVPC (Precio Voluntario para el Pequeño Consumidor) tariff prices and classifies each hourly slot against the 2.0TD tariff schedule (P1 Punta / P2 Llano / P3 Valle / P6 Super-Valle), enabling cost-optimal scheduling of flexible industrial loads.

**Temporal scope:** 5-day meteorological forecast horizon (OpenWeatherMap 3-hourly → upsampled to 1-hourly) and next-day electricity price forecast (REE publishes D+1 after 20:30 CET).

**Client scope:** Multi-client architecture; each client is independently characterised by geographic coordinates, PV system parameters (peak power, panel area, tilt angle, azimuth, system losses, mounting type), battery storage configuration, and industrial load profile.

### 1.3 Stakeholders and Technical Audience

| Stakeholder | Role | Primary Concern |
|---|---|---|
| Industrial Plant Manager | Primary consumer | Operational decisions: when to charge batteries, when to run heavy machinery |
| Energy Manager / Facility Engineer | Secondary consumer | KPI monitoring, cost optimisation, SLA verification |
| Data Engineer (maintainer) | System owner | Pipeline reliability, data quality, schema evolution |
| Senior Technical Recruiter | Document reader | Architecture quality, engineering judgment, professional standards |
| Future MLOps Engineer | Downstream | Feature store readiness, model training data availability |

---

## 2. Context & Problem Statement

### 2.1 Business Problem

Spanish industrial SMEs with photovoltaic installations face a persistent operational challenge: **they generate energy but cannot precisely predict when, how much, or at what market value**. This creates three compounding inefficiencies:

**Inefficiency 1 — Blind flexible load scheduling.** Battery charging, EV fleets, industrial HVAC, and non-time-critical machinery are started based on intuition or fixed schedules rather than real-time generation forecasts. The result is systematic energy waste: loads run during peak price windows (P1, P2) when solar generation is insufficient, incurring avoidable grid costs.

**Inefficiency 2 — Missed self-consumption windows.** Without an hourly generation forecast correlated against consumption profiles, facilities cannot identify the hours where net energy balance is positive — i.e., when they can run loads entirely on solar without grid draw.

**Inefficiency 3 — Reactive, not predictive, energy management.** Current tools in the SME market provide historical consumption data (rear-view mirror) but not forward-looking physics-based generation estimates correlated with market prices (windshield). SunSaver addresses this gap.

### 2.2 Key Functional Requirements

| ID | Requirement | Priority |
|---|---|---|
| FR-01 | Ingest next-day electricity prices from REE API with graceful handling of pre-20:30 unavailability | Critical |
| FR-02 | Ingest 5-day weather forecast per client from OpenWeatherMap, independently per client (failure isolation) | Critical |
| FR-03 | Apply validated PV physics chain to produce hourly AC power generation estimates | Critical |
| FR-04 | Model industrial consumption using shift-schedule profiles with HVAC thermal sensitivity | High |
| FR-05 | Classify each hourly slot against Spanish 2.0TD tariff periods (P1–P6) | High |
| FR-06 | Support multiple clients simultaneously with independent parametrisation | High |
| FR-07 | Deliver a unified analytical fact table joinable by time, client, weather, and price dimensions | High |
| FR-08 | Provide full pipeline audit trail with per-execution telemetry | Medium |
| FR-09 | Support incremental pipeline execution (resume from any stage) | Medium |
| FR-10 | Preserve raw ingested data as immutable Bronze layer for auditability and reprocessing | Medium |

### 2.3 Non-Functional Requirements

**Latency:** The pipeline is designed for scheduled batch execution (daily cadence), not real-time streaming. End-to-end pipeline execution is expected to complete within 120 seconds for up to 20 clients on commodity on-premise hardware. The observed execution time in production is approximately 1.93 seconds for the current client set (11 steps, 1,386 rows — as evidenced in the terminal output).

**Scalability:** The architecture must support horizontal scaling of the client dimension (from 1 to ~100 clients) without schema changes. The multi-client loop pattern in `bronze_ingest_weather_owm.py` and the composite primary key `(client_id, unix_time)` in all Silver and Gold tables are specifically designed for this.

**Availability:** As an on-premise daily batch system, 99.5 % daily execution success is the target SLA. The pipeline implements stage-gate abort logic: if all steps within a stage fail, execution halts to prevent corrupt data propagation. Individual step failures within a stage are tolerated (partial success state).

**Data Quality:** The Silver layer enforces strict data contracts: coordinate validation, physical constant range clipping, outlier filtering (price series: [−100, 2000] €/MWh), and null imputation with physics-informed defaults (tilt angle: 30°, azimuth: 180° South, system losses: 14 %, efficiency: 15 %).

**Idempotency:** All Silver and Gold load operations use `INSERT OR REPLACE` with composite natural keys. The pipeline can be re-run at any point without producing duplicate records or corrupting historical data.

**Reproducibility:** Bronze layer files are written with `chmod 444` (read-only, immutable) at the moment of ingestion. This ensures that any historical pipeline run can be reproduced by replaying Bronze files through the Silver and Gold layers.

### 2.4 Constraints and Assumptions

**Constraints:**
- Deployment environment is on-premise Linux (Ubuntu 24). No Kubernetes, no container orchestration, no cloud object storage.
- No proprietary data warehouse (no Snowflake, no BigQuery, no Redshift). Storage must be file-based or embedded relational.
- REE API is a public endpoint with no authentication; it is subject to availability windows (prices published after 20:30 CET for D+1). The system must handle graceful degradation when the endpoint returns no data.
- OpenWeatherMap requires a valid API key injected via environment variable (`WEATHER_API_KEY`). The free tier provides 5-day / 3-hourly forecasts.
- The physics engine requires `pvlib` (NREL's validated Python PV library) and `numpy`. These are the only computationally intensive dependencies.

**Assumptions:**
- Client PV system parameters (peak power, tilt, azimuth, losses) are provided via a master Excel file (`clients_source.xlsx`) and are relatively stable (updated infrequently).
- Industrial consumption profiles are modelled synthetically using a parameterised shift-schedule model. Real SCADA integration is out of scope for v1.0 but is a defined roadmap item.
- The platform operates in the Spanish electricity market context (REE, 2.0TD tariff, Europe/Madrid timezone). Internationalisation is a v2.0 concern.
- SQLite is the appropriate storage backend for the current scale. Migration to PostgreSQL or a columnar store (DuckDB) is a documented roadmap item with a defined trigger criterion (>50 clients or >500K rows in the fact table).

---

## 3. Architecture Overview

### 3.1 High-Level Diagram — C4 Level 1: System Context

```
┌─────────────────────────────────────────────────────────────────────┐
│                         EXTERNAL SYSTEMS                            │
│                                                                     │
│  ┌──────────────────┐     ┌──────────────────┐                     │
│  │   REE API        │     │  OpenWeatherMap   │                     │
│  │  (PVPC Prices)   │     │  Forecast API     │                     │
│  │  apidatos.ree.es │     │  api.openweather. │                     │
│  └────────┬─────────┘     └────────┬──────────┘                    │
└───────────┼──────────────────────────┼──────────────────────────────┘
            │  JSON/REST               │  JSON/REST
            ▼                          ▼
┌─────────────────────────────────────────────────────────────────────┐
│                      SUNSAVER PLATFORM                              │
│                                                                     │
│  ┌───────────────────────────────────────────────────────────────┐  │
│  │                    ETL PIPELINE (Python)                      │  │
│  │   Bronze Ingest → Silver Transform → Gold Build               │  │
│  └──────────────────────────┬────────────────────────────────────┘  │
│                             │                                       │
│  ┌──────────────────────────▼────────────────────────────────────┐  │
│  │                    SQLite DATABASE                            │  │
│  │           sunsaver.db  (Silver + Gold layers)                 │  │
│  └──────────────────────────┬────────────────────────────────────┘  │
│                             │                                       │
│  ┌──────────────────────────▼────────────────────────────────────┐  │
│  │               ANALYTICAL CONSUMERS (future)                   │  │
│  │         Power BI · Custom Dashboard · REST API                │  │
│  └───────────────────────────────────────────────────────────────┘  │
│                                                                     │
│  ┌───────────────────────────────────────────────────────────────┐  │
│  │                  DATA SOURCE (internal)                       │  │
│  │           clients_source.xlsx  (client master data)          │  │
│  └───────────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────────┘
```

### 3.2 Component Diagram — C4 Level 2: Container View

```
┌──────────────────────────────────────────────────────────────────────────────────┐
│                             SUNSAVER PIPELINE CONTAINER                          │
│                                                                                  │
│  ┌─────────────────────────────────────────────────────────────────────────────┐ │
│  │  pipeline_runner.py  ← ORCHESTRATOR (Stage-gate, Audit, CLI)               │ │
│  └───────┬─────────────────────────────────────────────────────────────────────┘ │
│          │                                                                       │
│    ┌─────▼──────────────────────────────────────────────────────────────────┐   │
│    │  STAGE 1 — BRONZE EXTRACTION (Parallel-safe, manifest-driven)         │   │
│    │  ┌─────────────────────┐  ┌──────────────────────┐                    │   │
│    │  │bronze_ingest_clients│  │bronze_ingest_prices  │                    │   │
│    │  │ Excel → JSON (444)  │  │ REE API → JSON (444) │                    │   │
│    │  └─────────────────────┘  └──────────────────────┘                    │   │
│    └───────────────────────────────────────────────────────────────────────┘   │
│          │                                                                       │
│    ┌─────▼──────────────────────────────────────────────────────────────────┐   │
│    │  STAGE 2 — SILVER TRANSFORMATION (Manifest-driven, idempotent)        │   │
│    │  ┌──────────────────────┐  ┌──────────────────────┐                   │   │
│    │  │silver_transform_     │  │silver_transform_     │                   │   │
│    │  │clients               │  │prices                │                   │   │
│    │  │ JSON → clean_clients │  │ JSON → clean_prices  │                   │   │
│    │  └──────────────────────┘  └──────────────────────┘                   │   │
│    └───────────────────────────────────────────────────────────────────────┘   │
│          │                                                                       │
│    ┌─────▼──────────────────────────────────────────────────────────────────┐   │
│    │  STAGE 3 — WEATHER BRONZE (Coord-driven loop, fault-isolated)         │   │
│    │  ┌─────────────────────────────────────────────────────────────────┐  │   │
│    │  │ bronze_ingest_weather_owm  (reads clean_clients for coords)     │  │   │
│    │  │ OWM API → JSON per client (444)                                 │  │   │
│    │  └─────────────────────────────────────────────────────────────────┘  │   │
│    └───────────────────────────────────────────────────────────────────────┘   │
│          │                                                                       │
│    ┌─────▼──────────────────────────────────────────────────────────────────┐   │
│    │  STAGE 4 — WEATHER SILVER (3h→1h resampling, feature engineering)    │   │
│    │  ┌─────────────────────────────────────────────────────────────────┐  │   │
│    │  │ silver_transform_weather → clean_weather                        │  │   │
│    │  └─────────────────────────────────────────────────────────────────┘  │   │
│    └───────────────────────────────────────────────────────────────────────┘   │
│          │                                                                       │
│    ┌─────▼──────────────────────────────────────────────────────────────────┐   │
│    │  STAGE 5 — PV PHYSICS ENGINE (Row-level simulation, vectorised)      │   │
│    │  ┌───────────────────────┐    ┌───────────────────────────────────┐  │   │
│    │  │silver_calc_pv_        │───►│ engine_pv_physics.py             │  │   │
│    │  │generation             │    │ Solar Pos → GHI → DNI/DHI →      │  │   │
│    │  │ → clean_calculations  │    │ POA → Faiman → P_AC + P_load     │  │   │
│    │  └───────────────────────┘    └───────────────────────────────────┘  │   │
│    └───────────────────────────────────────────────────────────────────────┘   │
│          │                                                                       │
│    ┌─────▼──────────────────────────────────────────────────────────────────┐   │
│    │  STAGE 6 — GOLD LAYER (Star schema, atomic rebuild)                  │   │
│    │  ┌──────────────┐ ┌──────────────┐ ┌──────────────┐ ┌────────────┐  │   │
│    │  │dim_client    │ │dim_datetime  │ │dim_weather   │ │fact_energy │  │   │
│    │  │(has_solar,   │ │(2.0TD tariff,│ │(modal desc.  │ │_forecast   │  │   │
│    │  │ has_battery) │ │ festivos)    │ │ per ID)      │ │(multi-JOIN)│  │   │
│    │  └──────────────┘ └──────────────┘ └──────────────┘ └────────────┘  │   │
│    └───────────────────────────────────────────────────────────────────────┘   │
│                                                                                  │
│  ┌─────────────────────────────────────────────────────────────────────────────┐ │
│  │  CROSS-CUTTING: config_paths.py · logger_config.py · audit_metadata.py    │ │
│  └─────────────────────────────────────────────────────────────────────────────┘ │
└──────────────────────────────────────────────────────────────────────────────────┘
```

**Filesystem layout (on-premise):**
```
project_root/
├── data/
│   ├── bronze/                  ← Immutable raw files (chmod 444)
│   │   ├── clients_YYYYMMDD_HHMMSS.json
│   │   ├── prices_YYYYMMDD_HHMMSS.json
│   │   ├── weather_{client_id}_YYYYMMDD_HHMMSS.json
│   │   ├── _process_manifest_clients.json     ← Process control
│   │   ├── _process_manifest_ree.json
│   │   └── _process_manifest_openweather.json
│   ├── sunsaver.db              ← Silver + Gold (SQLite)
│   └── clients_source.xlsx      ← Client master data
├── logs/
│   └── sunsaver_YYYY-MM-DD.log  ← Daily rotating logs
└── src/                         ← Pipeline scripts
```

### 3.3 Adopted Design Principles

**Single Responsibility Principle (SRP):** Each module has exactly one responsibility. `engine_pv_physics.py` does physics — it has no I/O. `config_paths.py` resolves paths — it has no business logic. This separation makes unit testing, replacement, and debugging deterministic.

**Immutability at ingestion (Bronze Seal):** Raw data is never modified after write. Files are sealed with `chmod 444`. This is the data engineering equivalent of write-once-read-many (WORM) storage, enabling full reprocessing from source at any time.

**Idempotency at every write boundary:** All Silver and Gold writes use `INSERT OR REPLACE` with natural composite keys. Running the pipeline twice produces identical results — no duplicates, no drift.

**Manifest-driven flow control:** Bronze-to-Silver promotion is governed by process manifests (JSON control files per data source). This decouples ingestion timing from transformation timing and provides a built-in retry mechanism for failed tasks (status: `error` → re-queued on next run).

**Fail-fast with graceful degradation:** The orchestrator implements stage-gate logic — if an entire stage fails, the pipeline aborts before corrupting downstream layers. Within a stage, individual step failures are tolerated and logged (PARTIAL SUCCESS state).

**Physics-first data modelling:** All simulation parameters use validated scientific models (pvlib, Erbs, Faiman). Empirical constants (cloud attenuation, transmittance factors) are documented inline with their academic sources. The physics engine is designed to short-circuit safely when inputs are physically impossible (solar elevation < 2° → zero output).

---

## 4. Medallion Architecture Rationale

### 4.1 Why Bronze / Silver / Gold

The Medallion Architecture (also known as the Delta Lake pattern, popularised by Databricks) was selected as the foundational data organisation paradigm. The decision was not driven by trend adoption but by a specific requirement: **the need to independently version, reprocess, and audit each transformation stage without losing the ability to trace any output value back to its raw source.**

In the industrial energy management domain, this is non-negotiable. If a client's generation forecast is incorrect, the investigation path must be deterministic: raw API response → parsed values → physics model inputs → computed output. The three-layer architecture provides this traceability natively.

**Bronze (Raw Ingestion Layer):**
- Contains the verbatim API responses and source file contents, stored as timestamped JSON files.
- Files are sealed (chmod 444) at write time — they cannot be modified, only read.
- Acts as a persistent audit log and a full reprocessing source.
- No business logic is applied at this layer. Raw data includes NaN values, inconsistent types, and partial records.

**Silver (Refined / Cleaned Layer):**
- Contains validated, typed, deduplicated, and business-rule-enforced data in SQLite tables.
- Serves as the authoritative join surface: `clean_clients`, `clean_prices`, `clean_weather`, `clean_calculations`.
- Data at this layer satisfies a defined schema contract (NOT NULL constraints, primary keys, physical range checks).
- The physics simulation runs at this layer, producing `clean_calculations` as the primary derived dataset.

**Gold (Analytical / Serving Layer):**
- Contains the star schema optimised for analytical consumption.
- `gold_fact_energy_forecast` is the denormalised fact table that joins all dimensions; it is the primary output of the platform and the direct input for dashboards and decision-support tools.
- All dimensional tables (`gold_dim_client`, `gold_dim_datetime`, `gold_dim_weather`) are atomically rebuilt on each pipeline run.
- Indexes on `unix_time` and `weather_id` ensure sub-second query response for dashboard queries.

### 4.2 Promotion Criteria Between Layers

A record is promoted from Bronze to Silver when it satisfies all of the following:

| Criterion | Validation applied |
|---|---|
| Schema completeness | Critical fields (`client_id`, `latitude`, `longitude`, `pv_peak_power_kw`) are non-null |
| Type validity | All numeric fields successfully coerced; datetime fields parsed with UTC awareness |
| Physical range validity | Coordinates within [-90,90] / [-180,180]; tilt angle within [0,90]; price within [-100, 2000] €/MWh |
| Logical consistency | `pv_peak_power_kw > 0` (clients without solar generation have no reason to be in the system) |
| Deduplication | Most recently ingested record per natural key is retained |

A Silver record is promoted to Gold when:
- It falls within the processing window (`unix_time >= now − 2 hours` for the fact table)
- All required join surfaces are available (LEFT JOINs ensure partial data is never a blocking condition)

### 4.3 Alternatives Considered and Discarded

**Lambda Architecture (batch + streaming layers):**
Rejected. SunSaver's data sources are inherently batch (REE publishes prices once daily; OWM forecast granularity is 3-hourly). Maintaining a dual-path architecture (batch + speed layer) would add operational complexity with zero benefit. The Medallion pattern covers the required latency profile entirely.

**Flat file pipeline (CSV-in, CSV-out):**
Rejected. CSV files provide no schema enforcement, no atomic transactions, no join semantics, and no audit trail. The manifest-driven + SQLite approach provides all of these at zero additional infrastructure cost.

**Full RDBMS (PostgreSQL) from day one:**
Considered and deferred. PostgreSQL would provide multi-user concurrency, extensions (TimescaleDB for time-series), and network access. However, for the current scale (single-client on-premise deployment, <50 clients, <1M rows), the operational overhead of managing a Postgres server outweighs the benefits. SQLite delivers identical query semantics, runs in-process, requires zero configuration, and supports atomic transactions. The migration path to PostgreSQL is documented in the roadmap (Section 8).

**Parquet files for Silver layer:**
Considered. Parquet would provide columnar compression and compatibility with pandas/Spark. Rejected for Silver because it adds a dependency on a columnar I/O library, loses the ability to use SQL for ad-hoc inspection, and provides no advantage at the current data volumes. Parquet is the correct choice for Bronze if the platform scales to multi-gigabyte daily ingestion — this is documented as a future migration path.

---

## 5. Technology Stack Decisions

### 5.1 Database Selection (per layer)

| Layer | Storage format | Rationale |
|---|---|---|
| Bronze | JSON files (timestamped, chmod 444) | Maximum fidelity to source; no parsing loss; immutable by OS-level permission; human-readable for debugging |
| Silver | SQLite (sunsaver.db) | Zero-configuration, file-based, full ACID, standard SQL, UPSERT semantics, composite PKs, sufficient for ≤100 clients |
| Gold | SQLite (same database) | Co-located with Silver for join efficiency; separate logical namespace via table naming convention; single-file backup |
| Process control | JSON manifests (per-source) | Human-readable, trivially version-controlled, no external dependency, append-only log semantics |
| Audit / telemetry | SQLite (etl_metadata table) | Structured, queryable, co-located; no external monitoring infrastructure required for v1.0 |

**SQLite was specifically chosen over alternatives because:**
- On-premise deployment with a single writer process eliminates the primary SQLite limitation (write concurrency).
- The SQLite file can be directly opened in DB Browser for SQLite (as evidenced in the project screenshots), enabling non-technical stakeholders to inspect data without additional tooling.
- Backup is a single `cp sunsaver.db sunsaver.db.bak` command — operationally trivial.
- SQLite supports window functions (`ROW_NUMBER() OVER PARTITION BY`) used in `gold_dim_weather.py`, confirming that the version in use is ≥ 3.25.0.

### 5.2 Orchestrator Selection

**Chosen: Custom Python orchestrator (`pipeline_runner.py`)**

A deliberate choice to build a lightweight, self-contained orchestrator rather than adopting Apache Airflow, Prefect, or Dagster.

Rationale:
- The pipeline has a fixed, acyclic topology (6 stages, 11 steps). Dynamic DAG generation provides no value at this scale.
- Airflow requires a metadata database, a web server, a scheduler process, and executor workers. This is disproportionate infrastructure for an on-premise SME deployment.
- The custom orchestrator provides `--stage N` (resume) and `--dry-run` (planning) flags, per-step timing, stage-gate abort logic, and audit persistence — covering 100 % of operational requirements.
- The orchestrator is 120 lines of idiomatic Python, fully readable and maintainable by any mid-level engineer without Airflow training.

The migration path to a managed orchestrator (Prefect Cloud or Airflow on Docker) is defined for the multi-tenant SaaS roadmap (Section 8.2).

### 5.3 Language and Frameworks

**Python 3.12** — primary language.

| Library | Role | Justification |
|---|---|---|
| `pvlib` | Solar position and irradiance | NREL-validated, industry-standard PV modelling library; peer-reviewed algorithms |
| `pandas` | Tabular data manipulation | Standard for ETL; vectorised operations; direct SQL read/write via `pd.read_sql` / `to_sql` |
| `SQLAlchemy` | Database abstraction | Engine-level transactions; parameterised queries (SQL injection prevention); ORM optional |
| `numpy` | Numerical computation | Vectorised trigonometry for physics engine; required by pvlib |
| `requests` | HTTP API calls | Lightweight, battle-tested; timeout and error handling built-in |
| `python-dotenv` | Environment variable management | Secrets never hardcoded; `.env` file pattern universally understood |
| `openpyxl` | Excel ingestion | Required by pandas for `.xlsx` parsing |

**Notable absences (justified):**
- No `celery` / `redis` — no async task queue required for sequential batch pipeline.
- No `pydantic` — data validation is performed in pandas transforms; Pydantic models would be appropriate for a REST API layer (roadmap).
- No `pytest` in core codebase — test suite is a defined roadmap item (Section 8.1).

### 5.4 Infrastructure (On-premise)

**Deployment topology (current):**
```
Single Linux server (Ubuntu 24)
├── Python 3.12 virtual environment (venv)
├── Cron job (or systemd timer) → python pipeline_runner.py
├── /data/bronze/         ← NFS-mountable for backup
├── /data/sunsaver.db     ← Single-file backup target
└── /logs/                ← Log rotation via logrotate
```

**Operational runbook (simplified):**
```bash
# Full pipeline
python pipeline_runner.py

# Resume from weather extraction (skip Bronze client/price re-ingest)
python pipeline_runner.py --stage 3

# Validate execution plan without side effects
python pipeline_runner.py --dry-run
```

**Backup strategy:** Daily `cp sunsaver.db sunsaver.db.$(date +%Y%m%d)` via cron. Bronze directory is append-only and can be archived to object storage independently of the database.

---

## 6. ADR Log — Individual Decision Records

---

### ADR-001: Medallion Architecture vs. Lambda Architecture

**Date:** 2025-04  
**Status:** Accepted  
**Deciders:** Aitor Asin

**Context:**
The system requires ingesting data from two external APIs (batch, daily) and an internal Excel source, transforming and enriching it through a physics engine, and making the results available for analytical queries. Two competing patterns were evaluated: Medallion (batch layers) and Lambda (batch + speed dual path).

**Decision:**
Adopt the Medallion Architecture (Bronze → Silver → Gold).

**Rationale:**
1. Data source latency is inherently batch (REE: daily; OWM: 3-hourly). There is no streaming data source that would justify a speed layer.
2. The Medallion pattern provides full lineage from raw API response to analytical output, enabling deterministic reprocessing.
3. Lambda architecture's operational overhead (maintaining two code paths that must produce identical results) is unjustified when the batch path alone satisfies all latency requirements.

**Consequences:**
+ Full audit trail and reprocessing capability from Bronze.
+ Simpler codebase (single code path).
− Not suitable if a real-time SCADA data feed is introduced (Lambda or Kappa would be required).

---

### ADR-002: Bronze Storage Format — JSON vs. Parquet vs. Raw API Response

**Date:** 2025-04  
**Status:** Accepted  
**Deciders:** Aitor Asin

**Context:**
The Bronze layer must store the verbatim output of two REST APIs (REE, OpenWeatherMap) and one Excel file. The format must preserve full fidelity, be human-readable for debugging, and impose no parsing loss.

**Decision:**
Store Bronze data as timestamped, immutable JSON files with `chmod 444`.

**Rationale:**
1. REST APIs return JSON natively. Storing the response verbatim requires zero parsing at ingestion time, eliminating the possibility of format-induced data loss.
2. JSON is human-readable. Debugging a Bronze file requires `cat` or any text editor — no tooling dependency.
3. `chmod 444` provides OS-level immutability guarantees without requiring a specialised storage system (Delta Lake, Iceberg).
4. The file naming convention (`{source}_{timestamp}.json`) provides implicit partitioning by ingestion date, enabling efficient Bronze-layer queries.

**Alternatives considered:**
- **Parquet:** Provides columnar compression and schema enforcement. Rejected because it requires a columnar reader, is not human-readable, and offers no advantage at current data volumes (< 1 MB per Bronze file).
- **SQLite table (raw_clients, raw_prices, raw_weather):** Would enable SQL querying of Bronze data but loses the immutability guarantee and introduces schema coupling to the raw source structure.

**Consequences:**
+ Full API response fidelity; no Bronze-level data loss.
+ OS-level immutability (chmod 444).
+ Human-readable debugging.
− Requires a manifest system to track processing state (addressed by process manifests).

---

### ADR-003: Silver Transformation Engine — pandas + SQLAlchemy vs. SQL-only vs. Spark

**Date:** 2025-04  
**Status:** Accepted  
**Deciders:** Aitor Asin

**Context:**
The Silver layer must parse nested JSON structures (OpenWeatherMap 5-day forecast with 40 slots per client), apply time-series resampling (3h → 1h via linear interpolation), enforce business rules, and persist results to SQLite. The transformation engine must be maintainable by a single engineer.

**Decision:**
Use pandas for in-memory transformation and SQLAlchemy for database I/O.

**Rationale:**
1. The OpenWeatherMap payload is a nested JSON structure with arrays. pandas' `json_normalize` and `resample` operations handle this natively; SQL CTEs would require multiple levels of JSON extraction functions that are SQLite-dialect-specific.
2. The Erbs irradiance decomposition and Faiman cell temperature model require row-level numerical operations. pandas iterrows + numpy is the correct abstraction for physics row operations; SQL cannot express these models.
3. SQLAlchemy provides parameterised query execution (protection against SQL injection) and engine-level transaction management, which is appropriate for the `INSERT OR REPLACE` upsert pattern.
4. Spark (PySpark) would provide distributed processing at scale. At the current data volume (<10,000 rows per run), Spark's JVM startup overhead would make pipeline execution slower, not faster.

**Consequences:**
+ Expressive temporal resampling (pandas resample/interpolate).
+ Row-level physics model execution.
+ SQL injection prevention via SQLAlchemy parameterisation.
− pandas memory model is row-oriented; at >10M rows, vectorisation to polars or columnar operations would be required.

---

### ADR-004: Gold Layer Dimensional Model — Star Schema vs. Flat Denormalised Table

**Date:** 2025-04  
**Status:** Accepted  
**Deciders:** Aitor Asin

**Context:**
The Gold layer must serve analytical queries efficiently: "what was the solar generation for client X at hour Y?", "what was the PVPC price during tariff period P1 last week?", "which clients have a positive net energy balance during peak hours?". The model must be accessible to non-SQL tools (Power BI, Excel) without requiring complex joins.

**Decision:**
Implement a star schema with one fact table (`gold_fact_energy_forecast`) and three dimension tables (`gold_dim_client`, `gold_dim_datetime`, `gold_dim_weather`).

**Rationale:**
1. The star schema minimises query complexity for BI tools. Power BI and Tableau natively understand star schema relationships; a fully flat table would require repeated measures for dimensional attributes.
2. `gold_dim_datetime` provides the 2.0TD tariff period classification (`P1 Punta / P2 Llano / P3 Valle / P6 Super-Valle`) as a precomputed attribute. This is expensive to compute at query time (requires timezone conversion + business rule evaluation) but trivial to join as a dimension.
3. `gold_dim_weather` uses a `ROW_NUMBER() OVER PARTITION BY` window function to resolve the many-to-one mapping between `weather_id` and weather descriptions — a pattern that demonstrates intentional use of SQL analytic functions rather than application-level deduplication.
4. The fact table uses `INSERT OR REPLACE` (upsert) with a 2-hour lookback window, enabling incremental updates without full table rebuilds.

**Consequences:**
+ BI-tool-ready model (Power BI, Tableau, Apache Superset).
+ Precomputed tariff period and holiday flags eliminate query-time computation.
+ Composite indexes on `unix_time` and `weather_id` provide sub-second analytical query response.
− Dimension tables are atomically rebuilt on each run (DROP + CREATE + INSERT in a single transaction). For tables with >1M rows this approach would require incremental SCD (Slowly Changing Dimension) handling.

---

### ADR-005: Partitioning Strategy — Time-based File Naming vs. Directory Partitioning

**Date:** 2025-04  
**Status:** Accepted  
**Deciders:** Aitor Asin

**Context:**
The Bronze layer accumulates one file per API call per run. Without partitioning, the Bronze directory becomes a flat list of files that is difficult to query or archive. A partitioning strategy is required that balances simplicity with operational usefulness.

**Decision:**
Adopt implicit timestamp partitioning via filename convention (`{source}_{YYYYMMDD_HHMMSS}.json`) in the Bronze layer. For the Silver/Gold SQLite layers, partition by composite primary keys `(client_id, unix_time)`.

**Rationale:**
1. Filename-based partitioning requires zero infrastructure. Files are sorted chronologically by `ls` and trivially filtered by date prefix.
2. The process manifest system (`_process_manifest_{source}.json`) provides an explicit index of Bronze files by status (pending / success / error), which is more useful operationally than directory-based partitioning.
3. At current data volumes (< 100 files/day), directory-based partitioning (e.g., `bronze/2025/05/10/`) adds path complexity with no query performance benefit.
4. The `(client_id, unix_time)` composite PK in Silver/Gold tables provides the functional equivalent of multi-dimensional partitioning for SQL queries.

**Consequences:**
+ Zero infrastructure overhead for Bronze partitioning.
+ Manifest provides explicit processing state without filesystem traversal.
− At high volume (>10,000 files/day), filename-based partitioning becomes unwieldy; directory hierarchy would be required.

---

### ADR-006: Secrets and API Credential Management

**Date:** 2025-04  
**Status:** Accepted  
**Deciders:** Aitor Asin

**Context:**
The pipeline requires two secrets: `WEATHER_API_KEY` (OpenWeatherMap) and optionally `DB_PATH`, `BRONZE_PATH`, `CLIENTS_SOURCE_PATH` (path overrides). These must be accessible at runtime without being hardcoded in source code.

**Decision:**
Use `.env` file + `python-dotenv` for local secret management. `.env` is excluded from version control via `.gitignore`. Path configuration is centralised in `config_paths.py`.

**Rationale:**
1. The 12-factor app methodology mandates environment-based configuration. `.env` + `python-dotenv` is the idiomatic Python implementation for local development and on-premise deployment.
2. Centralising path resolution in `config_paths.py` ensures that changing the database path (e.g., for a staging environment) requires modifying one file or one environment variable — not searching across 15 scripts.
3. The `_get_validated_path()` helper in `config_paths.py` automatically creates required directories (`mkdir -p` equivalent) and validates path resolution, eliminating `FileNotFoundError` exceptions from misconfiguration.

**Future state:** For a multi-tenant cloud deployment, this pattern would be replaced by a secrets management service (HashiCorp Vault, AWS Secrets Manager, Azure Key Vault). The `config_paths.py` interface is designed to be a drop-in replacement target — all consumers reference `config_paths.get_db_path()`, not `os.getenv("DB_PATH")` directly.

**Consequences:**
+ No hardcoded credentials in source code.
+ Single-point path management (`config_paths.py`).
+ `.gitignore` prevents accidental credential exposure.
− `.env` file on disk is a security risk if the server is compromised. For production, a dedicated secrets manager is required (roadmap item).

---

## 7. Cross-Cutting Concerns

### 7.1 Security and Access Control

**Current state (v1.0 — on-premise, single-user):**

- API keys stored in `.env` with `600` permissions (owner read/write only).
- Bronze files sealed with `chmod 444` — modification requires explicit `chmod` override, creating an audit event.
- SQLite database file access is controlled by OS-level filesystem permissions.
- No authentication layer on the data outputs (direct file/database access).

**Security boundaries:**
```
[External APIs] ──HTTPS──► [Pipeline] ──file-write──► [sunsaver.db]
                                                           │
                                                    chmod 444 (Bronze)
                                                    OS filesystem ACL (DB)
```

**Identified security gaps (v1.0, accepted risk):**
- No encryption at rest for the SQLite database. Client energy data and location coordinates are stored in plaintext. Acceptable for single-tenant on-premise deployment; unacceptable for cloud/SaaS.
- No API rate limiting or circuit breaker on outbound API calls. If REE or OWM rate-limits the client, the pipeline will fail with an HTTP error and require manual retry.
- No input sanitisation beyond pandas type coercion. The Excel client master file is implicitly trusted; a malicious Excel file with formula injection could be a vector.

### 7.2 Observability — Logs, Metrics, Traces

**Logging architecture:**

The `logger_config.py` module implements a singleton logger (`SunSaver`) with the following properties:
- **Dual-sink:** Simultaneous output to rotating daily log file (`logs/sunsaver_YYYY-MM-DD.log`) and console.
- **Structured format:** `TIMESTAMP | LEVEL | MODULE | MESSAGE` — parseable by standard log aggregation tools (Filebeat, Fluentd).
- **Log levels:** DEBUG (disabled on handlers in production), INFO (operational events), WARNING (degraded data quality), ERROR (step failure), CRITICAL (pipeline abort).
- **Singleton guard:** The `if logger.handlers: return logger` check prevents duplicate handler attachment when multiple modules import the logger in the same process.

**Module-level log prefixes (enforced convention):**
```
[INIT]      ← Stage/module start
[EXTRACT]   ← Data read operations
[TRANSFORM] ← Business logic application
[LOAD]      ← Database write operations
[BRONZE]    ← Bronze persistence
[MANIFEST]  ← Process control updates
[METADATA]  ← Audit table writes
[DONE]      ← Successful completion
[ERROR]     ← Handled error
```

**Pipeline execution telemetry (`etl_metadata` table):**

Every pipeline run persists a record to `etl_metadata` with: pipeline name, execution status (SUCCESS / PARTIAL SUCCESS / FAILED), duration in seconds, total rows affected, error detail string, environment, and UTC execution timestamp. This table is the primary SLA monitoring surface.

**Observability gaps (v1.0, documented):**
- No distributed tracing (OpenTelemetry). Per-step timing is available in logs but not structured as trace spans.
- No metrics endpoint (Prometheus). Pipeline health is observable only by querying `etl_metadata` or reading logs.
- No alerting. A failed pipeline produces a log entry and a FAILED status in `etl_metadata` but does not trigger any notification (email, Slack, PagerDuty).

### 7.3 Error Handling and Retries

**Error handling strategy:**

The pipeline implements a three-tier error handling model:

**Tier 1 — Physics engine (function-level):** Every function in `engine_pv_physics.py` wraps its computation in a `try/except` block and returns a safe default value (typically `0.0`) on any exception. This ensures that a single malformed row never crashes the pipeline — it produces a zero-generation record instead, which is a correct and conservative output.

**Tier 2 — Step-level (orchestrator):** Each pipeline step is executed inside `run_step()`, which catches all exceptions, logs them with full traceback (`exc_info=True`), and returns `(False, 0)`. The orchestrator accumulates failed step counts without propagating the exception.

**Tier 3 — Stage-level (abort gate):** If `all()` steps within a stage return `False`, the orchestrator calls `logger.critical()` and returns `False`, preventing downstream stages from executing with corrupted input data.

**Retry mechanism:**

The manifest system provides automatic retry for Bronze-to-Silver failures. Tasks with status `error` in a process manifest are re-queued on the next pipeline run alongside `pending` tasks. This covers transient failures (network timeout, API unavailability) without requiring manual intervention.

**API availability handling (REE-specific):**

The REE API returns no PVPC data before ~20:30 CET. `extract_energy_prices()` returns `False` (not an exception) when no data is available, which triggers a PARTIAL SUCCESS pipeline state rather than a hard failure. This is the correct behaviour: the pipeline can complete stages 3–6 with cached price data from a previous run.

### 7.4 Data Versioning Strategy

**Bronze versioning (implicit, via timestamped files):**
Every Bronze ingestion creates a new timestamped file. The complete history of API responses is preserved indefinitely (subject to disk capacity). This provides point-in-time reprocessing capability: any historical state of the Silver or Gold layer can be reconstructed by replaying the Bronze files from the corresponding timestamp range.

**Silver versioning (upsert-based, current state):**
Silver tables maintain the current-state view. Historical Silver records are overwritten by more recent ingestions for the same `(client_id, unix_time)` key. Point-in-time recovery requires replaying from Bronze.

**Gold versioning (atomic rebuild for dimensions, incremental for fact):**
Dimension tables are atomically rebuilt on every run (DROP + CREATE + INSERT in transaction). The fact table uses incremental upsert with a 2-hour lookback window. This means the Gold layer is always current but does not maintain historical snapshots.

**Schema versioning:**
There is no formal schema migration framework in v1.0. Schema changes require manual DDL execution. The SQLAlchemy `metadata.create_all()` pattern in `audit_metadata.py` provides additive schema evolution (new tables) but not column-level migrations. Alembic integration is a defined roadmap item.

---

## 8. Technical Roadmap

### 8.1 Known Technical Debt

| ID | Item | Impact | Effort | Priority |
|---|---|---|---|---|
| TD-01 | No automated test suite | Medium: regressions in physics engine or transformation logic are caught manually | High | High |
| TD-02 | No Alembic / schema migration framework | Medium: schema changes require manual DDL; risk of production schema drift | Medium | High |
| TD-03 | No alerting on pipeline failure | High: a failed overnight run is not detected until manual log inspection | Low | High |
| TD-04 | Industrial consumption model is synthetic (shift-schedule + Gaussian noise) | High: consumption estimates are approximations, not measured actuals | High (requires SCADA integration) | Medium |
| TD-05 | No rate limiting / circuit breaker on API calls | Low: acceptable for single-tenant; risk increases with client count | Low | Medium |
| TD-06 | SQLite single-writer constraint | Low at current scale; becomes blocking at >10 concurrent pipeline runs | Medium | Low |
| TD-07 | No data lineage graph (column-level) | Low: file-level lineage available via manifests; column-level lineage requires additional tooling | Medium | Low |
| TD-08 | `.env` file secrets (no dedicated secrets manager) | Low on-premise; High if migrated to cloud | Low | Low (until cloud migration) |

### 8.2 Planned Improvements

**Phase 1 — Reliability (Q3 2025):**
- Implement `pytest` test suite covering physics engine (unit tests with known solar geometry inputs), Silver transformation rules (data quality assertions), and Gold schema integrity (row count and primary key uniqueness checks).
- Integrate `alembic` for database schema migration management.
- Add email / Slack alerting on pipeline FAILED status via a lightweight notification hook in `pipeline_runner.py`.
- Implement OpenWeatherMap API rate limit detection and exponential backoff retry.

**Phase 2 — Intelligence (Q4 2025):**
- Replace synthetic consumption model with SCADA/Modbus data ingestion. Add `bronze_ingest_scada.py` and `silver_transform_scada.py` following the existing manifest pattern.
- Add battery state-of-charge (SoC) optimisation module: given generation forecast, consumption forecast, PVPC prices, and battery parameters, compute the optimal charging schedule for each client.
- Implement a REST API layer (FastAPI) to expose `gold_fact_energy_forecast` as a JSON endpoint, enabling integration with industrial HMI systems and custom dashboards.

**Phase 3 — Scale (Q1 2026):**
- **Database migration trigger:** When client count exceeds 50 or fact table row count exceeds 500,000 rows, migrate from SQLite to DuckDB (columnar, embedded, zero-configuration) or PostgreSQL (multi-writer, network-accessible).
- **Storage migration trigger:** When daily Bronze volume exceeds 1 GB, migrate JSON files to Parquet with Hive-style directory partitioning (`bronze/year=2026/month=01/day=15/`).
- **Orchestration migration trigger:** When pipeline is deployed for multiple independent tenants, migrate from `pipeline_runner.py` to Prefect Cloud or Apache Airflow on Docker Compose.
- **Cloud-ready packaging:** Containerise the pipeline as a Docker image with environment-variable-driven configuration, enabling deployment on any cloud provider's container runtime (AWS ECS, Azure Container Instances, GCP Cloud Run).

**Phase 4 — Platform (2026+):**
- Multi-tenant SaaS architecture: isolated databases per tenant, shared orchestration layer, web-based onboarding for new industrial clients.
- Machine learning layer: replace physics-model generation estimates with a hybrid physics + ML model trained on actual generation vs. forecast error data. The Gold layer's historical `gold_fact_energy_forecast` data is the direct training set.
- ISO 50001 Energy Management System integration: map SunSaver outputs to the energy performance indicators (EnPIs) required for ISO 50001 certification, positioning the platform as a compliance tool for industrial clients.

---

*Document maintained by: Aitor Asin*  
*Last updated: 2025-05-10*  
*Version history: [1.0.0] Initial release — complete ADR covering all architectural decisions through pipeline v1.0*

---

> **For technical questions regarding this document, refer to the source code in `/src/` and the execution logs in `/logs/`. For operational questions, consult the pipeline audit table (`etl_metadata`) in `sunsaver.db`.**
