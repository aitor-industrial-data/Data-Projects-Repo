# ☀️ SunSaver ETL · Plataforma de Inteligencia Energética Industrial
## 07 Operations Runbook

> **Clasificación:** INTERNA &nbsp;|&nbsp; **Estado:** ACTIVO — Entorno DEV &nbsp;|&nbsp; **Pipeline:** `SunSaver_ETL`  
> **Audiencia:** Ingenieros de guardia, DevOps, SRE &nbsp;|&nbsp; **Última actualización:** 2026-05-10

---

> ### ⚡ Acciones rápidas de emergencia
>
> ```bash
> # Pipeline fallido — reiniciar desde el stage N
> python src/pipeline_runner.py --stage N
>
> # Ver el último estado de ejecución
> sqlite3 data/sunsaver.db "SELECT * FROM etl_metadata ORDER BY id DESC LIMIT 5;"
>
> # Health check de todas las APIs
> python src/utils/health_check.py
>
> # Ver logs de hoy
> tail -100 logs/sunsaver_$(date +%Y-%m-%d).log
>
> # Dry-run (ver plan sin ejecutar nada)
> python src/pipeline_runner.py --dry-run
> ```

---

## Tabla de Contenidos

1. [Visión General Operativa](#1-visión-general-operativa)
   - 1.1 [Arquitectura de Despliegue](#11-arquitectura-de-despliegue)
   - 1.2 [Entornos](#12-entornos-dev--staging--prod)
   - 1.3 [Accesos y Permisos Requeridos](#13-accesos-y-permisos-requeridos)
   - 1.4 [Contactos y Escalado](#14-contactos-y-escalado)
2. [Despliegue y CI/CD](#2-despliegue-y-cicd)
   - 2.1 [Proceso de Despliegue Paso a Paso](#21-proceso-de-despliegue-paso-a-paso)
   - 2.2 [Pipeline de CI/CD](#22-pipeline-de-cicd)
   - 2.3 [Variables de Configuración por Entorno](#23-variables-de-configuración-por-entorno)
   - 2.4 [Rollback Procedure](#24-rollback-procedure)
3. [Monitorización y Observabilidad](#3-monitorización-y-observabilidad)
   - 3.1 [Dashboard Principal](#31-dashboard-principal)
   - 3.2 [Métricas Clave](#32-métricas-clave-a-monitorizar)
   - 3.3 [Logs — Estructura, Ubicación, Retención](#33-logs--estructura-ubicación-retención)
   - 3.4 [Trazas Distribuidas](#34-trazas-distribuidas)
   - 3.5 [Alertas Activas](#35-alertas-activas)
4. [SLAs y SLOs](#4-slas-y-slos)
   - 4.1 [Objetivos de Disponibilidad del Pipeline](#41-objetivos-de-disponibilidad-del-pipeline)
   - 4.2 [Freshness SLO por Tabla Gold](#42-freshness-slo-por-tabla-gold)
   - 4.3 [RTO y RPO](#43-tiempo-de-recuperación-objetivo-rto--rpo)
   - 4.4 [Reporting de SLA](#44-reporting-de-sla)
5. [Procedimientos de Operación Habitual](#5-procedimientos-de-operación-habitual)
   - 5.1 [Reiniciar un Pipeline Fallido](#51-cómo-reiniciar-un-pipeline-fallido)
   - 5.2 [Ejecutar un Backfill Manual](#52-cómo-ejecutar-un-backfill-manual)
   - 5.3 [Pausar Ingesta de una API](#53-cómo-pausar-ingesta-de-una-api)
   - 5.4 [Forzar Recarga de una Dimensión](#54-cómo-forzar-recarga-de-una-dimensión)
   - 5.5 [Limpiar Datos Corruptos en Bronze](#55-cómo-limpiar-datos-corruptos-en-bronze)
6. [Playbooks de Incidencias](#6-playbooks-de-incidencias)
   - 6.1 [API Fuente No Disponible](#61-api-fuente-no-disponible)
   - 6.2 [Fallo de Transformación Silver](#62-fallo-de-transformación-silver)
   - 6.3 [Corrupción en Capa Gold](#63-corrupción-en-capa-gold)
   - 6.4 [Saturación de Almacenamiento](#64-saturación-de-almacenamiento)
   - 6.5 [Credenciales Expiradas](#65-credenciales-expiradas)
   - 6.6 [Pipeline Bloqueado por Dependencia](#66-pipeline-bloqueado-por-dependencia)
7. [Mantenimiento](#7-mantenimiento)
   - 7.1 [Tareas Periódicas](#71-tareas-periódicas)
   - 7.2 [Gestión de Capacidad y Scaling](#72-gestión-de-capacidad-y-scaling)
   - 7.3 [Actualización de Dependencias](#73-actualización-de-dependencias)
   - 7.4 [Rotación de Logs y Datos Históricos](#74-rotación-de-logs-y-datos-históricos)

---

## 1. Visión General Operativa

### 1.1 Arquitectura de Despliegue

```
┌───────────────────────────────────────────────────────────────────┐
│                  SERVIDOR DEV (Ubuntu 24 / Linux)                 │
│                                                                   │
│  ┌─────────────────────────────────────────────────────────────┐  │
│  │  ENTORNO PYTHON (venv)                                      │  │
│  │                                                             │  │
│  │  pipeline_runner.py ──► [Stage 1..6]                        │  │
│  │       │                                                     │  │
│  │       ├── bronze_ingest_*.py  ──► data/bronze/*.json        │  │
│  │       ├── silver_transform_*.py ──► sunsaver.db (Silver)    │  │
│  │       ├── silver_calc_pv_generation.py                      │  │
│  │       ├── gold_dim_*.py / gold_fact_*.py ──► sunsaver.db    │  │
│  │       └── audit_metadata.py ──► sunsaver.db (etl_metadata)  │  │
│  └─────────────────────────────────────────────────────────────┘  │
│                                                                   │
│  ┌───────────────┐  ┌──────────────┐  ┌────────────────────────┐  │
│  │ data/bronze/  │  │sunsaver.db   │  │ logs/                  │  │
│  │ *.json (444)  │  │ SQLite       │  │ sunsaver_YYYY-MM-DD.log│  │
│  │ manifests     │  │ Silver+Gold  │  │ (rotación diaria)      │  │
│  └───────────────┘  └──────────────┘  └────────────────────────┘  │
│                                                                   │
│  ┌─────────────────────────────────────────────────────────────┐  │
│  │  CRON (scheduling)                                          │  │
│  │  0 20 * * *  python src/pipeline_runner.py     (ejecución)  │  │
│  │  0 22 * * *  python src/pipeline_runner.py --stage 2 (retry)│  │
│  └─────────────────────────────────────────────────────────────┘  │
│                                                                   │
└───────────────────────────────────────────────────────────────────┘
         │                      │                     │
         ▼                      ▼                     ▼
  REE API (PVPC)        OWM API (meteo)        Excel clientes
  apidatos.ree.es       openweathermap.org      data/clients_source.xlsx
  (pública, sin key)    (API Key requerida)     (fichero local)
```

**Componentes del sistema:**

| Componente | Tecnología | Ubicación | Función |
|-----------|-----------|-----------|---------|
| Orquestador | Python 3.12 | `src/pipeline_runner.py` | Coordina la ejecución de los 11 steps |
| Motor PV | Python + pvlib | `src/engine_pv_physics.py` | Cálculo físico de generación fotovoltaica |
| Base de datos | SQLite 3 | `data/sunsaver.db` | Silver + Gold + auditoría |
| Almacén Bronze | JSON files | `data/bronze/` | Raw data inmutable (chmod 444) |
| Scheduler | cron | `crontab -l` | Disparo automático diario |
| Logs | Python logging | `logs/` | Fichero diario rotado |
| Config | python-dotenv | `.env` | Variables de entorno y secretos |

---

### 1.2 Entornos (DEV / Staging / Prod)

| Atributo | DEV | Staging (roadmap) | Prod (roadmap) |
|----------|-----|-------------------|---------------|
| **Host** | Máquina local / servidor DEV | Servidor dedicado o VM | Servidor producción o cloud |
| **DB** | `data/sunsaver.db` (local) | SQLite o PostgreSQL | PostgreSQL + backups automáticos |
| **Bronze** | `data/bronze/` (local) | Disco dedicado o S3 | S3 / GCS con lifecycle policies |
| **Logs** | `logs/` (local) | Centralizado (ELK / Loki) | Centralizado + retención 365d |
| **Scheduler** | cron manual | cron o systemd timer | Airflow / Prefect |
| **Alertas** | Log + stderr | Slack (dev-channel) | Slack + PagerDuty + Email |
| **OWM API Key** | `WEATHER_API_KEY` en `.env` | Variable de entorno del sistema | AWS Secrets Manager / Vault |
| **Clientes** | Datos ficticios | Datos de demo | Datos reales de instalaciones |
| **Ejecución** | Manual + cron | Automática | Automática + monitorizada |

**Variables que diferencian entornos:**

```bash
# DEV — .env
SUNSAVER_ENV=dev
WEATHER_API_KEY=dev_key_here
DB_PATH=                    # usa default: data/sunsaver.db
BRONZE_PATH=                # usa default: data/bronze/

# PROD — variables de entorno del sistema o Secrets Manager
SUNSAVER_ENV=production
WEATHER_API_KEY=            # gestionado por Secrets Manager
DB_PATH=/var/data/sunsaver/sunsaver.db
BRONZE_PATH=/var/data/sunsaver/bronze/
LOG_DIR=/var/log/sunsaver/
```

---

### 1.3 Accesos y Permisos Requeridos

| Recurso | Acceso requerido | Quién lo gestiona |
|---------|-----------------|------------------|
| Servidor / VM donde corre el pipeline | SSH con usuario `sunsaver` (sin sudo para operación normal) | DevOps |
| Directorio del proyecto | Lectura + escritura para el usuario de ejecución | DevOps |
| `data/bronze/` | Escritura para crear ficheros; los ficheros Bronze son `444` | Automático (pipeline) |
| `data/sunsaver.db` | Lectura + escritura para el usuario de ejecución | Automático (pipeline) |
| `logs/` | Escritura para el usuario de ejecución | Automático (pipeline) |
| `.env` | Lectura para el usuario de ejecución; escritura sólo para operadores autorizados | Operador / DevOps |
| REE API | Sin credenciales (API pública) | — |
| OWM API | `WEATHER_API_KEY` en `.env` / Secrets Manager | Responsable del proyecto |
| Repositorio Git | Lectura (despliegue) | DevOps |

**Verificar permisos antes de operar:**

```bash
# Verificar que el usuario tiene los permisos correctos
ls -la data/          # debe poder listar
touch data/test_write && rm data/test_write   # debe poder escribir
ls -la data/bronze/prices_*.json | head -3    # debe mostrar -r--r--r-- (444)
sqlite3 data/sunsaver.db ".tables"            # debe listar tablas sin error
```

---

### 1.4 Contactos y Escalado

| Rol | Responsabilidad | Canal de contacto | Horario |
|-----|----------------|------------------|---------|
| **Data Engineer (propietario)** | Bugs de pipeline, cambios de schema, breaking changes de API | Slack `@data-eng` | L–V 9:00–18:00 CET |
| **Data Scientist** | Validación de resultados del motor PV, anomalías en cálculos | Slack `@data-science` | L–V 9:00–18:00 CET |
| **Equipo de Operaciones** | Actualización del Excel de clientes, validación de parámetros de instalaciones | Slack `#operaciones` | L–V 8:00–17:00 CET |
| **On-call engineer** | Incidencias CRITICAL fuera de horario | PagerDuty (roadmap) | 24/7 |
| **Soporte OWM** | Problemas con API key, cambios de plan | https://home.openweathermap.org | L–V (horas de negocio UK) |

**Árbol de escalado:**

```
Incidencia detectada
        │
        ▼ 0–30 min
  Ingeniero de turno
  → Consultar logs + etl_metadata
  → Intentar resolución con este Runbook
        │
        ▼ 30 min sin resolución
  Slack #data-alerts
  → Data Engineer propietario
        │
        ▼ 2h sin resolución
  Email + Slack DM
  → Data Engineer + Data Science
        │
        ▼ 4h sin resolución / impacto en negocio
  Escalado a responsable de producto
  → Decisión de bloquear o publicar datos degradados
```

---

## 2. Despliegue y CI/CD

### 2.1 Proceso de Despliegue Paso a Paso

**Despliegue inicial (primera vez):**

```bash
# 1. Clonar el repositorio
git clone https://github.com/org/sunsaver-etl.git
cd sunsaver-etl

# 2. Crear y activar entorno virtual
python3 -m venv venv
source venv/bin/activate          # Linux/macOS
# venv\Scripts\activate           # Windows

# 3. Instalar dependencias
pip install -r requirements.txt

# 4. Configurar variables de entorno
cp .env.example .env
# Editar .env con los valores reales:
nano .env                         # añadir WEATHER_API_KEY

# 5. Verificar configuración y conectividad
python src/utils/health_check.py

# 6. Colocar el fichero de clientes
# Copiar clients_source.xlsx en data/clients_source.xlsx

# 7. Ejecutar primer pipeline completo
python src/pipeline_runner.py

# 8. Verificar resultados
sqlite3 data/sunsaver.db "
    SELECT COUNT(*) AS clientes FROM gold_dim_client;
    SELECT COUNT(*) AS hechos   FROM gold_fact_energy_forecast;
    SELECT status, duration_seconds, rows_affected
    FROM etl_metadata ORDER BY id DESC LIMIT 1;
"

# 9. Configurar cron
crontab -e
# Añadir las dos líneas siguientes:
# 0 20 * * * cd /ruta/sunsaver && venv/bin/python src/pipeline_runner.py >> logs/cron.log 2>&1
# 0 22 * * * cd /ruta/sunsaver && venv/bin/python src/pipeline_runner.py --stage 2 >> logs/cron.log 2>&1
```

**Actualización de código (despliegue de nueva versión):**

```bash
# 1. Activar entorno virtual
cd /ruta/sunsaver && source venv/bin/activate

# 2. Pausar el cron temporalmente (precaución si hay ejecución en curso)
crontab -l > /tmp/crontab_backup.txt    # backup del crontab
crontab -r                               # eliminar crontab temporalmente

# 3. Verificar que no hay pipeline en ejecución
pgrep -f pipeline_runner.py || echo "No hay pipeline en ejecución"

# 4. Pull de la nueva versión
git fetch origin
git log HEAD..origin/main --oneline     # revisar qué cambia
git pull origin main

# 5. Actualizar dependencias si requirements.txt cambió
pip install -r requirements.txt --upgrade

# 6. Verificar que la DB no requiere migración de schema
# (las tablas Gold se recrean en cada ejecución — sin migración necesaria)

# 7. Dry-run para verificar que el nuevo código arranca correctamente
python src/pipeline_runner.py --dry-run

# 8. Restaurar cron
crontab /tmp/crontab_backup.txt
echo "Cron restaurado"

# 9. Verificar cron activo
crontab -l
```

---

### 2.2 Pipeline de CI/CD

**Estado actual:** sin CI/CD automático. Despliegue manual según el proceso del apartado 2.1.

**Especificación del pipeline CI/CD recomendado (GitHub Actions):**

```yaml
# .github/workflows/pipeline.yml
name: SunSaver ETL — CI/CD

on:
  push:
    branches: [main, develop]
  pull_request:
    branches: [main]
  schedule:
    - cron: '0 20 * * *'    # ejecución diaria producción

jobs:
  # ── GATE 1: Calidad de código ─────────────────────────────────
  lint-and-type-check:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with: { python-version: '3.12' }
      - run: pip install flake8 mypy black
      - run: flake8 src/ --max-line-length=120
      - run: black --check src/
      # - run: mypy src/    # activar cuando se añadan type hints

  # ── GATE 2: Tests unitarios ───────────────────────────────────
  unit-tests:
    runs-on: ubuntu-latest
    needs: lint-and-type-check
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with: { python-version: '3.12' }
      - run: pip install -r requirements.txt pytest pytest-cov
      - run: pytest tests/unit/ -v --cov=src --cov-report=xml
      - uses: codecov/codecov-action@v4    # publicar cobertura

  # ── GATE 3: Tests de integración (sólo en main) ──────────────
  integration-tests:
    runs-on: ubuntu-latest
    needs: unit-tests
    if: github.ref == 'refs/heads/main'
    env:
      WEATHER_API_KEY: ${{ secrets.WEATHER_API_KEY_DEV }}
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with: { python-version: '3.12' }
      - run: pip install -r requirements.txt pytest
      - run: pytest tests/integration/ -v --timeout=60

  # ── DESPLIEGUE (sólo en main tras gates ─────────────────────
  deploy:
    runs-on: ubuntu-latest
    needs: [unit-tests, integration-tests]
    if: github.ref == 'refs/heads/main'
    environment: production    # requiere aprobación manual en GitHub
    steps:
      - name: Deploy to production server
        uses: appleboy/ssh-action@v1
        with:
          host:     ${{ secrets.PROD_HOST }}
          username: ${{ secrets.PROD_USER }}
          key:      ${{ secrets.PROD_SSH_KEY }}
          script: |
            cd /opt/sunsaver
            git pull origin main
            source venv/bin/activate
            pip install -r requirements.txt
            python src/pipeline_runner.py --dry-run
            echo "Despliegue completado: $(date)"
```

**Gates del pipeline CI/CD:**

| Gate | Condición de paso | Bloquea merge |
|------|------------------|--------------|
| Lint (flake8) | 0 errores de estilo | ✅ SÍ |
| Formato (black) | Sin cambios pendientes | ✅ SÍ |
| Unit tests | 100% tests pasan, cobertura > 70% | ✅ SÍ |
| Integration tests | 100% tests pasan (sólo en `main`) | ✅ SÍ |
| Aprobación manual | ≥ 1 revisor aprueba el PR | ✅ SÍ (para despliegue a prod) |

---

### 2.3 Variables de Configuración por Entorno

```bash
# ── DEV (.env) ───────────────────────────────────────────────────
SUNSAVER_ENV=dev
WEATHER_API_KEY=owm_dev_key
DB_PATH=                        # default: {PROJECT_ROOT}/data/sunsaver.db
BRONZE_PATH=                    # default: {PROJECT_ROOT}/data/bronze/

# ── STAGING (variables de sistema) ───────────────────────────────
SUNSAVER_ENV=staging
WEATHER_API_KEY=owm_staging_key
DB_PATH=/var/data/sunsaver-staging/sunsaver.db
BRONZE_PATH=/var/data/sunsaver-staging/bronze/

# ── PROD (Secrets Manager / variables de sistema) ────────────────
SUNSAVER_ENV=production
WEATHER_API_KEY=                # gestionado por AWS Secrets Manager
DB_PATH=/var/data/sunsaver/sunsaver.db
BRONZE_PATH=/var/data/sunsaver/bronze/
```

**Diferencias de comportamiento por entorno:**

| Comportamiento | DEV | Staging | Prod |
|----------------|-----|---------|------|
| Clientes | Ficticios (2–5) | Demo (10–20) | Reales |
| Alertas | Log + stderr | Slack #staging | Slack + PagerDuty + Email |
| Retención Bronze | Sin política | 30 días | 365 días |
| Backup DB | Manual | Diario | Horario + offsite |
| OWM rate limit | Free tier | Free/Startup | Startup/Pro según N clientes |

---

### 2.4 Rollback Procedure

**Rollback de código (nueva versión rompe el pipeline):**

```bash
# 1. Identificar el commit anterior estable
git log --oneline -10

# 2. Hacer rollback al commit anterior
git revert HEAD                   # crea un nuevo commit de reversión
# o si es urgente:
git checkout HEAD~1 -- src/       # sólo los ficheros src/

# 3. Verificar con dry-run
python src/pipeline_runner.py --dry-run

# 4. Re-ejecutar el pipeline
python src/pipeline_runner.py

# 5. Notificar al equipo del rollback
```

**Rollback de datos (ejecución produjo datos incorrectos en Gold):**

```bash
# Las tablas Gold son idempotentes — basta con re-ejecutar Stage 6
# Si Silver también está corrupto, re-ejecutar desde el stage afectado

# Opción A: Reconstruir sólo Gold desde Silver íntegra
python src/pipeline_runner.py --stage 6

# Opción B: Reconstruir desde Silver (si también está corrupto)
python src/pipeline_runner.py --stage 2

# Opción C: Pipeline completo (si Bronze también está afectado)
python src/pipeline_runner.py --stage 1

# Verificar resultado
sqlite3 data/sunsaver.db "
    SELECT COUNT(*) FROM gold_fact_energy_forecast WHERE unix_time >= strftime('%s','now');
    SELECT status FROM etl_metadata ORDER BY id DESC LIMIT 1;
"
```

**Rollback de base de datos (corrupción severa):**

```bash
# 1. Detener cualquier proceso que use la DB
pgrep -f pipeline_runner.py | xargs kill -9

# 2. Hacer copia de seguridad del estado corrupto para análisis
cp data/sunsaver.db data/sunsaver_corrupted_$(date +%Y%m%d_%H%M%S).db

# 3. Restaurar desde backup
cp data/backups/sunsaver_$(date +%Y%m%d).db data/sunsaver.db

# 4. Re-ejecutar desde Silver para reconstruir Gold con datos frescos
python src/pipeline_runner.py --stage 4

# Si no hay backup reciente — reconstruir desde Bronze (más lento)
python src/pipeline_runner.py --stage 1
```

---

## 3. Monitorización y Observabilidad

### 3.1 Dashboard Principal

**DEV:** no hay dashboard automático. Usar las queries SQL de esta sección directamente sobre `sunsaver.db`.

**Producción recomendada:** Grafana + SQLite datasource plugin (o migrar a PostgreSQL para soporte nativo).

**Query de estado general del sistema (ejecutar para inspección rápida):**

```sql
-- Estado completo del sistema en una sola query
WITH ultima_ejecucion AS (
    SELECT id, status, duration_seconds, rows_affected,
           error_message, executed_at
    FROM etl_metadata
    ORDER BY id DESC LIMIT 1
),
cobertura_gold AS (
    SELECT
        MIN(f.unix_time)                                AS primer_slot_unix,
        MAX(f.unix_time)                                AS ultimo_slot_unix,
        datetime(MIN(f.unix_time), 'unixepoch')         AS forecast_desde,
        datetime(MAX(f.unix_time), 'unixepoch')         AS forecast_hasta,
        COUNT(DISTINCT f.client_id)                     AS clientes_activos,
        COUNT(*)                                        AS total_hechos,
        SUM(CASE WHEN f.price_pvpc_eur_mwh IS NULL
                 THEN 1 ELSE 0 END)                     AS hechos_sin_precio
    FROM gold_fact_energy_forecast f
    WHERE f.unix_time >= strftime('%s','now')
),
calidad AS (
    SELECT
        ROUND(100.0 * SUM(CASE WHEN pv_power_gen_kw >= 0 THEN 1 ELSE 0 END)
              / COUNT(*), 1)                            AS qs_generacion_pct,
        ROUND(100.0 * SUM(CASE WHEN price_pvpc_eur_mwh IS NOT NULL THEN 1 ELSE 0 END)
              / COUNT(*), 1)                            AS qs_precio_pct
    FROM gold_fact_energy_forecast
    WHERE unix_time >= strftime('%s','now')
)
SELECT
    u.status                AS ultimo_run_estado,
    u.executed_at           AS ultimo_run_hora,
    u.duration_seconds      AS duracion_s,
    u.rows_affected         AS filas_procesadas,
    u.error_message         AS errores,
    c.clientes_activos,
    c.total_hechos          AS hechos_futuros,
    c.forecast_desde,
    c.forecast_hasta,
    c.hechos_sin_precio,
    q.qs_generacion_pct     AS calidad_generacion_pct,
    q.qs_precio_pct         AS calidad_precio_pct
FROM ultima_ejecucion u, cobertura_gold c, calidad q;
```

---

### 3.2 Métricas Clave a Monitorizar

#### Latencia de ingesta por API

```bash
# Tiempo entre la publicación de REE y la ingesta en Bronze
# (proxy: hora de creación del fichero prices_*.json vs hora de datos)
ls -la data/bronze/prices_*.json | tail -3

# Verificar en log el tiempo de respuesta de REE
grep "PVPC data retrieved" logs/sunsaver_$(date +%Y-%m-%d).log | tail -5

# Tiempo de respuesta OWM por cliente
grep "Bronze file sealed" logs/sunsaver_$(date +%Y-%m-%d).log | tail -10
```

#### Registros procesados por run

```sql
-- Evolución histórica de filas procesadas por run (últimos 14 días)
SELECT
    date(executed_at)       AS fecha,
    status,
    rows_affected,
    duration_seconds,
    ROUND(rows_affected / NULLIF(duration_seconds, 0), 1) AS filas_por_segundo
FROM etl_metadata
WHERE executed_at >= date('now', '-14 days')
ORDER BY executed_at DESC;
```

#### Tasa de error por capa

```sql
-- Errores en manifests Bronze (tasks no procesados correctamente)
-- Ejecutar para cada manifest:
-- cat data/bronze/_process_manifest_ree.json | python3 -c "
-- import json,sys; data=json.load(sys.stdin)
-- errors=[t for t in data if t['status']=='error']
-- print(f'REE errors: {len(errors)}/{len(data)}')"

-- Registros nulos en Silver (proxy de calidad)
SELECT
    'clean_clients'  AS tabla,
    COUNT(*)         AS total,
    SUM(CASE WHEN pv_peak_power_kw IS NULL OR pv_peak_power_kw <= 0 THEN 1 ELSE 0 END) AS invalidos
FROM clean_clients
UNION ALL
SELECT
    'clean_weather', COUNT(*),
    SUM(CASE WHEN temp_celsius IS NULL THEN 1 ELSE 0 END)
FROM clean_weather WHERE unix_time >= strftime('%s','now')
UNION ALL
SELECT
    'clean_prices', COUNT(*),
    SUM(CASE WHEN price_euro_mwh IS NULL THEN 1 ELSE 0 END)
FROM clean_prices WHERE datetime_utc >= date('now');
```

#### Lag de datos (freshness)

```sql
-- Cuántas horas de forecast futuro hay disponibles por cliente
SELECT
    c.client_id,
    c.name,
    COUNT(*)                                                        AS slots_futuros,
    datetime(MIN(f.unix_time), 'unixepoch')                        AS primer_slot_utc,
    datetime(MAX(f.unix_time), 'unixepoch')                        AS ultimo_slot_utc,
    ROUND((MAX(f.unix_time) - strftime('%s','now')) / 3600.0, 1)   AS horas_cobertura,
    CASE
        WHEN COUNT(*) >= 100 THEN '✅ OK'
        WHEN COUNT(*) >= 24  THEN '⚠️ Degradado'
        ELSE                      '❌ Crítico'
    END                                                             AS estado_cobertura
FROM gold_fact_energy_forecast f
JOIN gold_dim_client c ON f.client_id = c.client_id
WHERE f.unix_time >= strftime('%s','now')
GROUP BY c.client_id, c.name
ORDER BY horas_cobertura ASC;
```

---

### 3.3 Logs — Estructura, Ubicación, Retención

**Ubicación:** `{PROJECT_ROOT}/logs/sunsaver_YYYY-MM-DD.log`

**Formato de línea de log:**

```
2026-05-10 20:35:12 | INFO     | bronze_ingest_prices_ree      | [EXTRACT] PVPC data retrieved — 24 hourly values for 2026-05-11
2026-05-10 20:35:13 | INFO     | bronze_ingest_prices_ree      | [BRONZE] File sealed (chmod 444): prices_20260510_203512.json
2026-05-10 20:35:14 | ERROR    | bronze_ingest_weather_owm     | [EXTRACT] Failed to fetch weather for (lat=42.8038, lon=-1.7020): timeout
│                      │          │                               │
│                      │          └─ Módulo Python (30 chars)    └─ Mensaje con [TAG]
│                      └─ Nivel: DEBUG/INFO/WARNING/ERROR/CRITICAL
└─ Timestamp (YYYY-MM-DD HH:MM:SS)
```

**Tags de log por componente:**

| Tag | Fase del pipeline | Ejemplo |
|-----|-----------------|---------|
| `[INIT]` | Inicio de módulo | `[INIT] ── extract_clients starting` |
| `[EXTRACT]` | Lectura de fuente | `[EXTRACT] 5 client(s) loaded` |
| `[BRONZE]` | Escritura en Bronze | `[BRONZE] File sealed (chmod 444)` |
| `[TRANSFORM]` | Transformación Silver | `[TRANSFORM] 120 Silver-quality records produced` |
| `[LOAD]` | Carga a Silver/Gold | `[LOAD] clean_clients rebuilt — 5 records` |
| `[MANIFEST]` | Actualización de manifest | `[MANIFEST] REE manifest updated — pending: 1` |
| `[METADATA]` | Auditoría pipeline | `[METADATA] Audit record committed` |
| `[DONE]` | Fin de módulo | `[DONE] extract_clients finished — records: 5` |
| `[ERROR]` | Error controlado | `[ERROR] Transform failed: empty DataFrame` |
| `[CIRCUIT]` | Circuit breaker | `[CIRCUIT] OWM OPEN — skipping client C003` |
| `[RETRY]` | Reintento | `[RETRY] extract_weather — 1/3 failed. Retrying in 2s` |

**Comandos de inspección de logs:**

```bash
# Ver todo el log de hoy
cat logs/sunsaver_$(date +%Y-%m-%d).log

# Filtrar sólo errores y críticos
grep -E "ERROR|CRITICAL" logs/sunsaver_$(date +%Y-%m-%d).log

# Ver progreso de la última ejecución (últimas N líneas)
tail -50 logs/sunsaver_$(date +%Y-%m-%d).log

# Buscar ejecuciones fallidas en los últimos 7 días
for f in logs/sunsaver_*.log; do
    echo "=== $f ==="
    grep -c "ERROR\|CRITICAL" "$f" || echo "0 errores"
done

# Ver cuánto tardó cada step en la última ejecución
grep -E "✔|✗|completado|fallido" logs/sunsaver_$(date +%Y-%m-%d).log | tail -20
```

**Política de retención de logs:**

| Entorno | Retención | Mecanismo |
|---------|-----------|----------|
| DEV | Sin política definida — manual | `find logs/ -mtime +30 -delete` (cron semanal) |
| Prod | 90 días online + 365 días archivado | logrotate + S3 Glacier |

**Configuración de logrotate para producción:**

```
# /etc/logrotate.d/sunsaver
/var/log/sunsaver/sunsaver_*.log {
    daily
    rotate 90
    compress
    delaycompress
    missingok
    notifempty
    postrotate
        # No es necesario recargar — Python logging abre el fichero por fecha
    endscript
}
```

---

### 3.4 Trazas Distribuidas

**Estado actual:** sin trazas distribuidas formales. La trazabilidad se implementa mediante:

1. **`_source_file` en registros Silver** → traza cada dato hasta su fichero Bronze origen
2. **`_loaded_at_utc` en registros Gold** → timestamp de la última carga
3. **`_ingested_at_utc` en Silver** → timestamp de procesamiento
4. **`etl_metadata.id`** → identificador del run que produjo cada dato
5. **Manifests Bronze** → estado de cada fichero Bronze con timestamps

**Query de trazabilidad completa** (de un hecho Gold a su fuente):

```sql
-- Trazar el origen completo de un registro específico en Gold
-- hasta el fichero Bronze y el run de pipeline que lo generó
SELECT
    -- Datos del hecho
    f.client_id,
    datetime(f.unix_time, 'unixepoch')  AS slot_horario_utc,
    f.pv_power_gen_kw,
    f.price_pvpc_eur_mwh,
    f._loaded_at_utc                    AS gold_cargado_en,

    -- Origen del cliente
    c._source_file                      AS bronze_clientes_fichero,
    c._ingested_at_utc                  AS clientes_procesados_en,

    -- Origen de la meteorología
    w._source_file                      AS bronze_weather_fichero,
    w._ingested_at_utc                  AS weather_procesado_en,

    -- Run del pipeline que produjo este dato
    (SELECT id || ' (' || status || ') @ ' || executed_at
     FROM etl_metadata
     WHERE executed_at <= f._loaded_at_utc
     ORDER BY id DESC LIMIT 1)         AS pipeline_run

FROM gold_fact_energy_forecast f
JOIN clean_clients c ON c.client_id = f.client_id
JOIN clean_weather w ON w.client_id  = f.client_id
                     AND w.unix_time = f.unix_time
WHERE f.client_id = 'C001'
  AND f.unix_time = (
      SELECT unix_time FROM gold_fact_energy_forecast
      WHERE client_id = 'C001'
      ORDER BY unix_time DESC LIMIT 1
  );
```

---

### 3.5 Alertas Activas

**Estado actual DEV:** alertas vía log y stderr únicamente.

| ID | Condición | Umbral | Canal | Acción |
|----|-----------|--------|-------|--------|
| ALT-001 | `etl_metadata.status = 'FAILED'` | Cualquier fallo | Log ERROR + Slack (roadmap) | Ejecutar playbook 6.2 |
| ALT-002 | `etl_metadata.status = 'PARTIAL SUCCESS'` más de 2 días consecutivos | 2 días | Log WARNING + Slack | Verificar disponibilidad REE y OWM |
| ALT-003 | `horas_cobertura < 24` para cualquier cliente | < 24h | Log ERROR | Ejecutar playbook 6.1 |
| ALT-004 | Fichero Bronze `prices_*.json` sin crear después de las 22:00 CET | Sin fichero | Log ERROR | Ejecutar playbook 6.1 |
| ALT-005 | `rows_affected` cae > 30% respecto a la media de los 7 días anteriores | -30% | Log WARNING | Investigar fuentes |
| ALT-006 | Espacio en disco < 1 GB disponible | < 1 GB | Log CRITICAL | Ejecutar playbook 6.4 |
| ALT-007 | `WEATHER_API_KEY` no configurada o inválida (HTTP 401) | Cualquier 401 | Log CRITICAL | Ejecutar playbook 6.5 |

**Query de detección de alertas activas:**

```sql
-- Ejecutar para verificar si hay alertas activas
SELECT
    -- ALT-001/ALT-002: fallos recientes
    (SELECT COUNT(*) FROM etl_metadata
     WHERE status LIKE 'FAILED%'
       AND executed_at >= datetime('now','-24 hours'))   AS fallos_24h,

    -- ALT-003: cobertura mínima
    (SELECT COUNT(*) FROM (
        SELECT client_id, COUNT(*) AS slots
        FROM gold_fact_energy_forecast
        WHERE unix_time >= strftime('%s','now')
        GROUP BY client_id
        HAVING slots < 24
    ))                                                   AS clientes_sin_cobertura,

    -- Estado del último run
    (SELECT status FROM etl_metadata ORDER BY id DESC LIMIT 1)     AS ultimo_estado,
    (SELECT executed_at FROM etl_metadata ORDER BY id DESC LIMIT 1) AS ultimo_run;
```

---

## 4. SLAs y SLOs

### 4.1 Objetivos de Disponibilidad del Pipeline

| Métrica | SLO DEV | SLO Prod (objetivo) | Medición |
|---------|---------|---------------------|---------|
| **Disponibilidad del pipeline** (% de ejecuciones `SUCCESS` o `PARTIAL SUCCESS`) | > 90% | > 99% | `COUNT(status IN ('SUCCESS','PARTIAL SUCCESS')) / COUNT(*) × 100` en `etl_metadata` |
| **Tasa de éxito completo** (% de ejecuciones `SUCCESS`) | > 70% | > 85% | REE publica precios con retraso ~15% de los días |
| **Tiempo máximo de ejecución** | < 10 min | < 5 min | `duration_seconds` en `etl_metadata` |
| **Filas procesadas mínimas por run** | > 0 | > N_clientes × 100 | `rows_affected` en `etl_metadata` |

**Cálculo del SLO actual:**

```sql
-- SLO de disponibilidad de los últimos 30 días
SELECT
    COUNT(*)                                                             AS total_runs,
    SUM(CASE WHEN status IN ('SUCCESS','PARTIAL SUCCESS') THEN 1 END)   AS runs_ok,
    SUM(CASE WHEN status LIKE 'FAILED%' THEN 1 END)                     AS runs_fallidos,
    ROUND(100.0 * SUM(CASE WHEN status IN ('SUCCESS','PARTIAL SUCCESS')
                           THEN 1 END) / COUNT(*), 2)                   AS slo_disponibilidad_pct,
    ROUND(AVG(duration_seconds), 1)                                     AS duracion_media_s,
    MAX(duration_seconds)                                                AS duracion_max_s
FROM etl_metadata
WHERE executed_at >= date('now', '-30 days');
```

---

### 4.2 Freshness SLO por Tabla Gold

El **freshness** mide cuánto tiempo puede pasar desde que los datos están disponibles en la fuente hasta que están en Gold, sin violar el SLO.

| Tabla | Freshness SLO | Frecuencia de actualización | Ventana de tolerancia |
|-------|--------------|----------------------------|----------------------|
| `gold_dim_client` | < 24h desde actualización del Excel | Manual | No aplica scheduling |
| `gold_dim_datetime` | < 1h desde ejecución del pipeline | Con cada run | ±30 min |
| `gold_dim_weather` | < 26h (pipeline diario + margen) | 1/día | Pipeline debe correr antes de las 22:00 CET |
| `gold_fact_energy_forecast` | < 2h desde publicación de datos fuente | 1/día | Precios REE disponibles después de las 20:30 CET → Gold actualizado antes de las 22:30 CET |

**Verificación de freshness:**

```sql
-- Verificar freshness de gold_fact_energy_forecast
SELECT
    MAX(_loaded_at_utc)                                          AS ultima_carga_utc,
    ROUND((strftime('%s','now') -
           strftime('%s', MAX(_loaded_at_utc))) / 3600.0, 2)    AS horas_desde_ultima_carga,
    CASE
        WHEN (strftime('%s','now') -
              strftime('%s', MAX(_loaded_at_utc))) < 7200        THEN '✅ Fresco (< 2h)'
        WHEN (strftime('%s','now') -
              strftime('%s', MAX(_loaded_at_utc))) < 86400       THEN '⚠️ Degradado (< 24h)'
        ELSE                                                          '❌ Obsoleto (> 24h)'
    END                                                          AS estado_freshness
FROM gold_fact_energy_forecast;
```

---

### 4.3 Tiempo de Recuperación Objetivo (RTO / RPO)

| Escenario | RPO (máx. pérdida de datos) | RTO (tiempo para restaurar) |
|-----------|---------------------------|---------------------------|
| Fallo de pipeline (sin pérdida de datos) | 0 — los datos Bronze están intactos | < 30 min (re-ejecución manual) |
| Corrupción de `sunsaver.db` Silver/Gold | Hasta el último run exitoso | < 2h (restaurar backup + re-ejecutar Stage 4+) |
| Corrupción de datos Bronze | Hasta la última ejecución diaria | < 4h (re-ingestar desde fuentes externas) |
| Pérdida total del servidor | 24h de datos (último backup diario) | < 8h (provisionar servidor + despliegue + re-ejecución) |
| API fuente no disponible (REE/OWM) | N/A — los datos anteriores siguen válidos | Automático cuando la API se recupere |

---

### 4.4 Reporting de SLA

**Informe semanal de SLA** (query para informe manual o automatizado):

```sql
-- Informe de SLA semanal
SELECT
    strftime('%Y-W%W', executed_at)                             AS semana,
    COUNT(*)                                                     AS total_runs,
    SUM(CASE WHEN status = 'SUCCESS' THEN 1 ELSE 0 END)         AS success,
    SUM(CASE WHEN status = 'PARTIAL SUCCESS' THEN 1 ELSE 0 END) AS partial,
    SUM(CASE WHEN status LIKE 'FAILED%' THEN 1 ELSE 0 END)      AS failed,
    ROUND(100.0 * SUM(CASE WHEN status IN ('SUCCESS','PARTIAL SUCCESS')
                           THEN 1 ELSE 0 END) / COUNT(*), 1)    AS slo_pct,
    ROUND(AVG(duration_seconds), 0)                             AS avg_duration_s,
    ROUND(AVG(rows_affected), 0)                                AS avg_rows
FROM etl_metadata
WHERE executed_at >= date('now', '-60 days')
GROUP BY semana
ORDER BY semana DESC;
```

---

## 5. Procedimientos de Operación Habitual

### 5.1 Cómo Reiniciar un Pipeline Fallido

```bash
# PASO 1: Identificar el fallo
sqlite3 data/sunsaver.db \
  "SELECT id, status, error_message, executed_at FROM etl_metadata ORDER BY id DESC LIMIT 3;"

# PASO 2: Ver los detalles del fallo en el log
grep -E "ERROR|CRITICAL|✗" logs/sunsaver_$(date +%Y-%m-%d).log | tail -20

# PASO 3: Determinar desde qué stage reiniciar
#   Stage 1 → fallo en extracción de clientes o precios
#   Stage 2 → fallo en transformación Silver de clientes o precios
#   Stage 3 → fallo en extracción de meteorología
#   Stage 4 → fallo en transformación Silver de meteorología
#   Stage 5 → fallo en cálculo PV
#   Stage 6 → fallo en carga Gold

# PASO 4: Reiniciar desde el stage correcto
python src/pipeline_runner.py --stage N   # sustituir N por el stage adecuado

# PASO 5: Verificar resultado
sqlite3 data/sunsaver.db \
  "SELECT status, rows_affected, error_message FROM etl_metadata ORDER BY id DESC LIMIT 1;"

# PASO 6 (opcional): Si el problema es REE sin datos (PARTIAL SUCCESS esperado)
# No es necesario reiniciar — el cron de las 22:00 hará el reintento automático
```

**Árbol de decisión para el stage de reinicio:**

```
¿Qué falló?
    │
    ├─ "Failed to read Excel" o "extract_clients devuelve 0"
    │   → Verificar que clients_source.xlsx existe y es válido → --stage 1
    │
    ├─ "extract_energy_prices devolvió False" (PARTIAL SUCCESS)
    │   → Normal si son < 21:00 CET → esperar cron de las 22:00
    │   → Si ya son > 22:00 → verificar API REE manualmente → --stage 2
    │
    ├─ "Failed to read clients from clean_clients" (error en OWM)
    │   → clean_clients está vacía → --stage 2 para repoblarla, luego --stage 3
    │
    ├─ "Empty payload" o "timeout" en OWM para algunos clientes
    │   → Reintentar sólo la meteorología → --stage 3
    │
    ├─ "PV engine returned no results" o "No active forecast data"
    │   → clean_weather está vacía o fuera de ventana → --stage 4
    │
    └─ Error en carga Gold (integridad referencial, etc.)
        → --stage 6 (si Silver está íntegra)
        → --stage 5 (si clean_calculations también está afectada)
```

---

### 5.2 Cómo Ejecutar un Backfill Manual

Un backfill re-procesa datos históricos ya existentes en Bronze. Útil cuando:
- Se corrige un bug en Silver/Gold que afectó a ejecuciones pasadas
- Se añade un nuevo campo a una tabla Silver y se quiere popularlo con histórico
- Una ejecución anterior quedó en estado `error` en el manifest

```bash
# CASO 1: Re-procesar todas las tareas en estado 'error' en los manifests
# (ocurre automáticamente en la siguiente ejecución del pipeline)
python src/pipeline_runner.py --stage 2   # reprocesa pending + error de clientes y precios
python src/pipeline_runner.py --stage 4   # reprocesa pending + error de meteorología

# CASO 2: Forzar re-procesamiento de un fichero Bronze específico
# Editar manualmente el manifest para cambiar status a 'pending':
python3 -c "
import json
manifest_path = 'data/bronze/_process_manifest_ree.json'
with open(manifest_path) as f:
    tasks = json.load(f)

# Cambiar todas las tareas 'success' del día específico a 'pending'
target_date = '2026-05-10'
for t in tasks:
    if target_date in t.get('path', '') and t['status'] == 'success':
        t['status'] = 'pending'
        print(f'Marcada como pending: {t[\"path\"]}')

with open(manifest_path, 'w') as f:
    json.dump(tasks, f, indent=4)
print('Manifest actualizado')
"
# Luego re-ejecutar Silver de precios
python src/pipeline_runner.py --stage 2

# CASO 3: Reconstruir Gold completa desde Silver íntegra
python src/pipeline_runner.py --stage 6

# CASO 4: Backfill completo (lento — re-ingesta desde cero)
python src/pipeline_runner.py --stage 1
```

> **Nota sobre backfill histórico (> 5 días):** la ventana de cálculo en `silver_calc_pv_generation.py` está filtrada a `unix_time >= now`. Para backfill histórico completo hay que eliminar temporalmente ese filtro, ejecutar el pipeline, y restaurarlo. Ver el código en `silver_calc_pv_generation.py` función `get_merged_silver_data()`.

---

### 5.3 Cómo Pausar Ingesta de una API

Puede ser necesario pausar la ingesta de una API durante mantenimiento, problemas con credenciales o cambios en su schema.

```bash
# OPCIÓN A: Comentar el step en el PIPELINE de pipeline_runner.py
# Editar src/pipeline_runner.py y comentar el step correspondiente:
#   (1, "extract_energy_prices", bronze_ingest_prices_ree.extract_energy_prices),
# → El pipeline continuará omitiendo ese step

# OPCIÓN B: Usar --stage para saltarse stages completos
# Ejemplo: saltar Stage 1 (sin ingesta de clientes ni precios) e iniciar desde Silver
python src/pipeline_runner.py --stage 3   # empieza en meteorología, salta REE y clientes

# OPCIÓN C: Dry-run para verificar el plan sin ejecutar nada
python src/pipeline_runner.py --dry-run

# RESTAURAR: descomentar el step y volver a ejecución normal
python src/pipeline_runner.py
```

**Impacto de pausar cada API:**

| API pausada | Impacto inmediato | Impacto tras 24h |
|-------------|------------------|-----------------|
| REE (INT-001) | `price_pvpc_eur_mwh = NULL` en Gold | Análisis económicos sin datos de precio |
| OWM (INT-002) | Sin nuevas previsiones meteorológicas | `gold_fact` vacía para slots futuros nuevos |
| Excel clientes (INT-003) | Sin nuevos clientes ni actualizaciones | Los clientes existentes siguen funcionando |

---

### 5.4 Cómo Forzar Recarga de una Dimensión

Las dimensiones Gold se reconstruyen con `DROP + CREATE + INSERT` en cada ejecución. Para forzar una recarga aislada:

```bash
# Recargar sólo gold_dim_client (por ejemplo, tras actualizar el Excel)
python3 -c "
from gold_dim_clients import load_dim_client
rows = load_dim_client()
print(f'gold_dim_client recargada: {rows} filas')
"

# Recargar sólo gold_dim_datetime (por ejemplo, tras cambio de tarifas 3.0TD)
python3 -c "
from gold_dim_datetime import load_dim_datetime
rows = load_dim_datetime()
print(f'gold_dim_datetime recargada: {rows} filas')
"

# Recargar sólo gold_dim_weather (raramente necesario)
python3 -c "
from gold_dim_weather import load_dim_weather
rows = load_dim_weather()
print(f'gold_dim_weather recargada: {rows} filas')
"

# Recargar todas las dimensiones y la fact table (Stage 6 completo)
python src/pipeline_runner.py --stage 6

# Verificar resultado
sqlite3 data/sunsaver.db "
    SELECT 'gold_dim_client'   AS tabla, COUNT(*) AS filas FROM gold_dim_client   UNION ALL
    SELECT 'gold_dim_datetime',          COUNT(*)          FROM gold_dim_datetime  UNION ALL
    SELECT 'gold_dim_weather',           COUNT(*)          FROM gold_dim_weather;
"
```

---

### 5.5 Cómo Limpiar Datos Corruptos en Bronze

Los ficheros Bronze son inmutables (`chmod 444`), por lo que "limpiar" significa moverlos a un directorio de cuarentena y actualizar el manifest.

```bash
# PASO 1: Identificar ficheros corruptos (desde el manifest)
python3 -c "
import json, os
for source in ['ree', 'openweather', 'clients']:
    path = f'data/bronze/_process_manifest_{source}.json'
    if not os.path.exists(path): continue
    with open(path) as f:
        tasks = json.load(f)
    errors = [t for t in tasks if t['status'] == 'error']
    print(f'{source}: {len(errors)} tareas en error')
    for e in errors:
        print(f'  {e[\"path\"]} — {e.get(\"error\", \"sin detalle\")}')
"

# PASO 2: Crear directorio de cuarentena
mkdir -p data/bronze/quarantine

# PASO 3: Mover fichero corrupto a cuarentena
# (quitar chmod 444 primero)
chmod 644 data/bronze/prices_20260510_203500.json
mv data/bronze/prices_20260510_203500.json data/bronze/quarantine/

# PASO 4: Actualizar el manifest para eliminar la tarea del fichero movido
python3 -c "
import json
manifest_path = 'data/bronze/_process_manifest_ree.json'
corrupt_path  = 'data/bronze/quarantine/prices_20260510_203500.json'

with open(manifest_path) as f:
    tasks = json.load(f)

tasks = [t for t in tasks if t['path'] != corrupt_path]

with open(manifest_path, 'w') as f:
    json.dump(tasks, f, indent=4)
print(f'Tarea eliminada del manifest. Tareas restantes: {len(tasks)}')
"

# PASO 5: Re-ingestar la fuente para ese día (si los datos originales siguen disponibles)
# Para REE: re-ejecutar extracción (sólo disponible si es el día actual D+1)
python src/pipeline_runner.py --stage 1

# PASO 6: Verificar que el nuevo fichero se procesó correctamente
python src/pipeline_runner.py --stage 2
```

---

## 6. Playbooks de Incidencias

---

### 6.1 API Fuente No Disponible

**Síntomas:**
- `etl_metadata.status = 'PARTIAL SUCCESS'` con `error_message` mencionando REE u OWM
- Log con `[EXTRACT] Failed to fetch` o `HTTP 503` o `timeout`
- `gold_fact_energy_forecast` con `price_pvpc_eur_mwh = NULL` para el día siguiente
- Sin nuevos ficheros `weather_*.json` en `data/bronze/`

**Diagnóstico:**

```bash
# 1. Ver el error exacto en el log
grep -E "ERROR|CRITICAL" logs/sunsaver_$(date +%Y-%m-%d).log | tail -20

# 2. Verificar manualmente si la API responde
# REE:
curl -s "https://apidatos.ree.es/es/datos/mercados/precios-mercados-tiempo-real\
?start_date=$(date -d tomorrow +%Y-%m-%d)T00:00\
&end_date=$(date -d tomorrow +%Y-%m-%d)T23:59\
&time_trunc=hour&geo_trunc=electric_system&geo_limit=peninsular&geo_ids=8741" \
  -H "Accept: application/json" | python3 -m json.tool | head -20

# OWM:
source .env && curl -s \
  "https://api.openweathermap.org/data/2.5/forecast\
?lat=40.4&lon=-3.7&appid=$WEATHER_API_KEY&cnt=1" | python3 -m json.tool | head -10

# 3. Verificar el estado del servicio del proveedor
# REE:  https://www.ree.es (web principal)
# OWM:  https://status.openweathermap.org

# 4. Ver cuántas horas de cobertura quedan en Gold
sqlite3 data/sunsaver.db "
    SELECT client_id,
           ROUND((MAX(unix_time) - strftime('%s','now')) / 3600.0, 1) AS horas_restantes
    FROM gold_fact_energy_forecast
    WHERE unix_time >= strftime('%s','now')
    GROUP BY client_id;"
```

**Pasos de resolución:**

```bash
# CASO A: REE no ha publicado precios aún (antes de las 21:00 CET) — NORMAL
# → No hacer nada. El cron de las 22:00 UTC reintentará automáticamente.
# → Si son las 22:00 CET y sigue sin datos → CASO B

# CASO B: REE con problemas técnicos sostenidos
# → Esperar hasta las 24:00 CET.
# → Si sigue sin datos: los precios del día anterior son una aproximación útil.
# → Informar al equipo de Negocio que price_pvpc_eur_mwh = NULL para D+1.

# CASO C: OWM con problemas técnicos
# → Verificar si es un error de API key (ver playbook 6.5)
# → Esperar 30 min y reintentar manualmente:
python src/pipeline_runner.py --stage 3

# CASO D: OWM con rate limit (HTTP 429)
# → Reducir frecuencia: añadir time.sleep(2) entre clientes en bronze_ingest_weather_owm.py
# → Ejecutar manualmente en horario de menos carga:
sleep 300 && python src/pipeline_runner.py --stage 3
```

**Verificación de resolución:**

```bash
# Verificar que hay nuevos ficheros Bronze
ls -lt data/bronze/prices_*.json | head -3
ls -lt data/bronze/weather_*.json | head -5

# Verificar que Gold tiene datos con precio
sqlite3 data/sunsaver.db "
    SELECT COUNT(*) AS con_precio, SUM(CASE WHEN price_pvpc_eur_mwh IS NULL THEN 1 END) AS sin_precio
    FROM gold_fact_energy_forecast
    WHERE unix_time >= strftime('%s','now');"

# Verificar estado del pipeline
sqlite3 data/sunsaver.db "SELECT status, error_message FROM etl_metadata ORDER BY id DESC LIMIT 1;"
```

**Acciones post-incidencia:**
- Si REE estuvo más de 4h sin datos → notificar al equipo de Negocio
- Si OWM falló para algún cliente → verificar coordenadas de ese cliente
- Registrar en el log de incidencias si duró > 2h

---

### 6.2 Fallo de Transformación Silver

**Síntomas:**
- `etl_metadata.status = 'FAILED AT STAGE 2'` o `'FAILED AT STAGE 4'`
- Log con `[ERROR] Transformation failed` o `[ERROR] Silver load returned False`
- Tablas `clean_*` vacías o desactualizadas
- `gold_fact_energy_forecast` sin actualizar

**Diagnóstico:**

```bash
# 1. Ver el traceback completo del error
grep -A 10 "lanzó excepción\|exc_info" logs/sunsaver_$(date +%Y-%m-%d).log | tail -30

# 2. Verificar si las tablas Silver tienen datos
sqlite3 data/sunsaver.db "
    SELECT 'clean_clients'  AS t, COUNT(*) FROM clean_clients  UNION ALL
    SELECT 'clean_weather',         COUNT(*) FROM clean_weather  UNION ALL
    SELECT 'clean_prices',          COUNT(*) FROM clean_prices   UNION ALL
    SELECT 'clean_calculations',    COUNT(*) FROM clean_calculations;"

# 3. Verificar si el error es de datos (registros inválidos)
sqlite3 data/sunsaver.db "
    SELECT COUNT(*) AS invalidos FROM clean_clients
    WHERE pv_peak_power_kw IS NULL OR pv_peak_power_kw <= 0;"

# 4. Verificar si el error es de espacio en disco
df -h .

# 5. Verificar integridad de la base de datos SQLite
sqlite3 data/sunsaver.db "PRAGMA integrity_check;"

# 6. Intentar re-ejecutar el módulo fallido en modo debug
cd src && python3 -c "
import logging
logging.basicConfig(level=logging.DEBUG)
from silver_transform_clients import transform_clients
result = transform_clients()
print(f'Resultado: {result}')
"
```

**Pasos de resolución:**

```bash
# CASO A: Error de datos (registros inválidos en Bronze)
# → Verificar el fichero Bronze que causó el error
# → Si está corrupto: ejecutar procedimiento 5.5 (limpiar datos corruptos en Bronze)
# → Re-ejecutar:
python src/pipeline_runner.py --stage 2

# CASO B: Error de espacio en disco (OOM o disco lleno)
# → Ejecutar playbook 6.4 (saturación de almacenamiento)

# CASO C: Error de dependencia Python (librería faltante o versión incompatible)
pip install -r requirements.txt --upgrade
python src/pipeline_runner.py --stage 2

# CASO D: Bug en el código de transformación
# → Identificar el commit que introdujo el bug
# → Ejecutar rollback (sección 2.4)
# → Re-ejecutar el pipeline
python src/pipeline_runner.py --stage 2
```

**Verificación de resolución:**

```bash
sqlite3 data/sunsaver.db "
    SELECT status, rows_affected FROM etl_metadata ORDER BY id DESC LIMIT 1;
    SELECT COUNT(*) AS clientes FROM clean_clients;
    SELECT COUNT(*) AS slots_futuros FROM clean_weather WHERE unix_time >= strftime('%s','now');"
```

**Acciones post-incidencia:**
- Si fue un bug de código: abrir issue en GitHub con el traceback
- Si fue un dato inválido en Bronze: revisar el proceso de validación del Excel de clientes
- Actualizar la regla de calidad correspondiente en `04_DATA_QUALITY_FRAMEWORK.md` si procede

---

### 6.3 Corrupción en Capa Gold

**Síntomas:**
- Query sobre `gold_fact_energy_forecast` retorna resultados inconsistentes
- `pv_power_gen_kw` negativo en registros diurnos
- `client_id` en `gold_fact` que no existe en `gold_dim_client`
- Valores físicamente imposibles (temperatura de célula > 200°C, generación > 10× el pico)
- SQLite: `PRAGMA integrity_check` retorna errores

**Diagnóstico:**

```bash
# 1. Verificar integridad de SQLite
sqlite3 data/sunsaver.db "PRAGMA integrity_check;"
# Respuesta esperada: "ok"

# 2. Verificar integridad referencial del Star Schema
sqlite3 data/sunsaver.db "
    -- Huérfanos en fact (sin dimensión de cliente)
    SELECT COUNT(*) AS huerfanos_cliente
    FROM gold_fact_energy_forecast f
    LEFT JOIN gold_dim_client c ON f.client_id = c.client_id
    WHERE c.client_id IS NULL;

    -- Huérfanos en fact (sin dimensión de tiempo)
    SELECT COUNT(*) AS huerfanos_tiempo
    FROM gold_fact_energy_forecast f
    LEFT JOIN gold_dim_datetime d ON f.unix_time = d.unix_time
    WHERE d.unix_time IS NULL;

    -- Valores físicamente imposibles
    SELECT COUNT(*) AS pv_negativo FROM gold_fact_energy_forecast
    WHERE pv_power_gen_kw < 0;

    SELECT COUNT(*) AS pv_supera_pico
    FROM gold_fact_energy_forecast f
    JOIN gold_dim_client c ON f.client_id = c.client_id
    WHERE f.pv_power_gen_kw > c.pv_peak_power_kw * 1.2;"

# 3. Verificar si la corrupción está en Silver (origen del problema)
sqlite3 data/sunsaver.db "
    SELECT COUNT(*) AS calc_negativas FROM clean_calculations WHERE pv_power_gen_kw < 0;
    SELECT COUNT(*) AS nulos_criticos FROM clean_clients
    WHERE client_id IS NULL OR pv_peak_power_kw <= 0;"
```

**Pasos de resolución:**

```bash
# CASO A: Corrupción sólo en Gold (Silver íntegra)
# → Reconstruir Gold completa desde Silver
python src/pipeline_runner.py --stage 6

# Verificar inmediatamente
sqlite3 data/sunsaver.db "PRAGMA integrity_check; SELECT COUNT(*) FROM gold_fact_energy_forecast;"

# CASO B: Corrupción también en Silver (clean_calculations)
# → Reconstruir desde el motor PV
python src/pipeline_runner.py --stage 5

# CASO C: Corrupción en SQLite (PRAGMA integrity_check != "ok")
# → La base de datos SQLite está físicamente dañada
# → Intentar recuperación con SQLite:
sqlite3 data/sunsaver.db ".recover" | sqlite3 data/sunsaver_recovered.db
mv data/sunsaver.db data/sunsaver_corrupted_$(date +%Y%m%d).db
mv data/sunsaver_recovered.db data/sunsaver.db
python src/pipeline_runner.py --stage 1   # reconstruir todo

# CASO D: Corrupción en datos de Bronze (ficheros .json inválidos)
# → Ejecutar procedimiento 5.5 y re-procesar desde Stage 1
```

**Verificación de resolución:**

```bash
sqlite3 data/sunsaver.db "
    PRAGMA integrity_check;

    SELECT 'huerfanos_cliente' AS check,
           COUNT(*) AS valor
    FROM gold_fact_energy_forecast f
    LEFT JOIN gold_dim_client c ON f.client_id = c.client_id
    WHERE c.client_id IS NULL

    UNION ALL SELECT 'pv_negativo', COUNT(*) FROM gold_fact_energy_forecast
    WHERE pv_power_gen_kw < 0

    UNION ALL SELECT 'total_hechos', COUNT(*) FROM gold_fact_energy_forecast
    WHERE unix_time >= strftime('%s','now');"
```

**Acciones post-incidencia:**
- Analizar la causa raíz en el motor PV si hubo valores negativos
- Verificar que los datos Bronze originales son correctos antes de re-procesar
- Añadir un check de calidad DQ-Gxxx si la causa no estaba cubierta

---

### 6.4 Saturación de Almacenamiento

**Síntomas:**
- `OSError: [Errno 28] No space left on device` en los logs
- Pipeline falla al crear nuevos ficheros Bronze
- SQLite falla al escribir en `sunsaver.db`
- `df -h` muestra > 95% de uso en el disco donde reside `data/`

**Diagnóstico:**

```bash
# 1. Ver uso de disco general
df -h .
du -sh data/ logs/ data/bronze/ data/sunsaver.db

# 2. Ver los 10 ficheros más grandes
find . -type f -printf '%s %p\n' | sort -rn | head -10

# 3. Ver cuánto ocupa Bronze por tipo y fecha
ls -la data/bronze/*.json | awk '{print $5, $9}' | sort -rn | head -20

# 4. Ver tamaño de la base de datos SQLite
sqlite3 data/sunsaver.db "
    SELECT name, SUM(pgsize) / 1024 / 1024 AS size_mb
    FROM dbstat GROUP BY name ORDER BY size_mb DESC;"

# 5. Verificar espacio en logs
du -sh logs/ && ls logs/ | wc -l
```

**Pasos de resolución:**

```bash
# ACCIÓN INMEDIATA: liberar espacio

# 1. Comprimir logs antiguos (> 7 días)
find logs/ -name "*.log" -mtime +7 -exec gzip {} \;

# 2. Comprimir ficheros Bronze antiguos (> 30 días) — NO eliminar, sólo comprimir
find data/bronze/ -name "*.json" -mtime +30 | while read f; do
    chmod 644 "$f"          # quitar inmutabilidad para comprimir
    gzip "$f"               # comprime a .json.gz
    chmod 444 "${f}.gz"     # restaurar inmutabilidad al comprimido
done

# 3. Mover ficheros Bronze muy antiguos (> 90 días) a almacenamiento externo
# (S3, NAS, disco externo...)
find data/bronze/ -name "*.json.gz" -mtime +90 -exec mv {} /ruta/archivo_externo/ \;

# 4. VACUUM en SQLite (recuperar espacio de tablas eliminadas)
sqlite3 data/sunsaver.db "VACUUM;"

# 5. Eliminar bases de datos de backup antiguas si existen
ls data/*.db | grep -v sunsaver.db   # listar backups
# rm data/sunsaver_corrupted_*.db    # eliminar si hay espacio suficiente

# VERIFICAR: ¿suficiente espacio para continuar?
df -h .
```

**Verificación de resolución:**

```bash
# Verificar espacio disponible (objetivo: > 2 GB libres)
df -h . | awk 'NR==2 {print "Disponible:", $4, "— Uso:", $5}'

# Verificar que el pipeline puede crear ficheros
touch data/bronze/test_write && rm data/bronze/test_write && echo "✅ Escritura OK"

# Re-ejecutar el pipeline
python src/pipeline_runner.py
```

**Acciones post-incidencia:**
- Configurar alertas de espacio en disco (< 1 GB disponible → alerta)
- Implementar política automática de archivado de Bronze (ver sección 7.4)
- Revisar política de retención de logs

---

### 6.5 Credenciales Expiradas

**Síntomas:**
- Log con `[EXTRACT] WEATHER_API_KEY is not set` o `HTTP 401 Unauthorized` de OWM
- `extract_openweather` devuelve `0` para todos los clientes
- Sin nuevos ficheros `weather_*.json` en Bronze
- `clean_weather` con datos desactualizados

**Diagnóstico:**

```bash
# 1. Verificar si la variable está configurada
python3 -c "
import os
from dotenv import load_dotenv
load_dotenv()
key = os.getenv('WEATHER_API_KEY', '')
print('Key configurada:', bool(key))
print('Longitud:', len(key))
print('Primeros 4 chars:', key[:4] if key else 'N/A')
"

# 2. Probar la API key directamente
source .env && curl -s \
  "https://api.openweathermap.org/data/2.5/weather?lat=40&lon=-3&appid=$WEATHER_API_KEY" \
  | python3 -m json.tool

# Respuesta esperada: "cod": 200
# Respuesta de error: "cod": 401 con mensaje de API key inválida

# 3. Verificar si la key está en el fichero .env
cat .env | grep WEATHER_API_KEY | head -1
# (no muestra el valor completo por seguridad — sólo confirma que existe la línea)

# 4. Verificar el log del último error de autenticación
grep "401\|API_KEY\|not set\|invalid" logs/sunsaver_$(date +%Y-%m-%d).log | tail -10
```

**Pasos de resolución:**

```bash
# CASO A: Variable no configurada (primera vez o .env perdido)
cp .env.example .env
nano .env   # añadir: WEATHER_API_KEY=tu_key_aqui

# CASO B: API key inválida o expirada
# 1. Acceder a https://home.openweathermap.org/api_keys
# 2. Verificar si la key está activa (puede tardar hasta 2h en activarse tras crear una nueva)
# 3. Crear nueva key si es necesario
# 4. Actualizar .env:
sed -i 's/WEATHER_API_KEY=.*/WEATHER_API_KEY=NUEVA_KEY/' .env

# CASO C: Key correcta pero límite del plan excedido
# → Ver el plan actual en https://home.openweathermap.org/subscriptions
# → Esperar al reinicio del contador (mensual para Free tier)
# → O actualizar el plan si el volumen de clientes supera el Free tier

# VERIFICAR antes de re-ejecutar:
python src/utils/health_check.py

# RE-EJECUTAR desde Stage 3 (meteorología)
python src/pipeline_runner.py --stage 3
```

**Verificación de resolución:**

```bash
# Verificar nuevos ficheros Bronze de weather
ls -lt data/bronze/weather_*.json | head -5

# Verificar que clean_weather tiene datos frescos
sqlite3 data/sunsaver.db "
    SELECT client_id,
           MAX(forecast_time_utc) AS ultimo_slot,
           COUNT(*) AS slots_futuros
    FROM clean_weather
    WHERE unix_time >= strftime('%s','now')
    GROUP BY client_id;"
```

**Acciones post-incidencia:**
- Configurar alerta automática cuando la key esté próxima a expirar
- Documentar la nueva key en el gestor de secretos del equipo (1Password, Vault…)
- Revisar si se debe rotar la key anterior (si hubo sospecha de compromiso)

---

### 6.6 Pipeline Bloqueado por Dependencia

**Síntomas:**
- Pipeline se queda colgado sin avanzar (proceso Python activo pero sin output en log)
- `silver_calc_pv_generation` no encuentra datos a pesar de que Silver está poblada
- `gold_fact_energy_forecast` no se actualiza aunque `clean_calculations` tiene datos
- Stage 3 falla con "Failed to read clients from clean_clients" a pesar de que el Stage 2 terminó

**Diagnóstico:**

```bash
# 1. Verificar si hay un proceso pipeline_runner en ejecución
pgrep -af pipeline_runner.py
# Si hay más de uno → posible ejecución concurrente (problema de cron duplicado)

# 2. Verificar que las tablas de dependencia existen y tienen datos
sqlite3 data/sunsaver.db "
    SELECT 'clean_clients'       AS tabla, COUNT(*) AS filas FROM clean_clients
    UNION ALL
    SELECT 'clean_weather',                COUNT(*) FROM clean_weather
    WHERE unix_time >= strftime('%s','now')
    UNION ALL
    SELECT 'clean_prices',                 COUNT(*) FROM clean_prices
    WHERE datetime_utc >= date('now')
    UNION ALL
    SELECT 'clean_calculations',           COUNT(*) FROM clean_calculations
    WHERE unix_time >= strftime('%s','now');"

# 3. Verificar bloqueos de SQLite (WAL mode)
sqlite3 data/sunsaver.db "PRAGMA wal_checkpoint(FULL);"
ls data/*.db-wal data/*.db-shm 2>/dev/null   # si existen, hay un bloqueo activo

# 4. Verificar que los manifests Bronze existen y tienen tareas
python3 -c "
import json, os
for source in ['ree', 'openweather', 'clients']:
    path = f'data/bronze/_process_manifest_{source}.json'
    if not os.path.exists(path):
        print(f'{source}: manifest NO EXISTE')
        continue
    with open(path) as f: tasks = json.load(f)
    pending = sum(1 for t in tasks if t['status'] in ('pending','error'))
    print(f'{source}: {len(tasks)} tareas total, {pending} pendientes')
"

# 5. Verificar ventana temporal activa
python3 -c "
import time, sqlite3
now = int(time.time())
con = sqlite3.connect('data/sunsaver.db')
rows = con.execute(
    'SELECT COUNT(*) FROM clean_weather WHERE unix_time >= ?', (now,)
).fetchone()[0]
print(f'clean_weather rows con unix_time >= now: {rows}')
"
```

**Pasos de resolución:**

```bash
# CASO A: Ejecución concurrente (dos pipeline_runner corriendo simultáneamente)
# → Matar el proceso más antiguo (el que tiene PID menor)
pgrep -af pipeline_runner.py
kill PID_MAS_ANTIGUO
# → Esperar a que el proceso restante termine o matarlo también y reiniciar limpio
python src/pipeline_runner.py --stage N

# CASO B: clean_clients vacía (Stage 2 no generó datos)
# → Re-ejecutar Stage 2 verificando que el Excel existe
ls data/clients_source.xlsx && python src/pipeline_runner.py --stage 2

# CASO C: clean_weather sin datos futuros (ventana temporal expirada)
# → Ocurre si el pipeline se ejecuta muy tarde (> 24h después de la ingesta de OWM)
# → Re-ingestar meteorología:
python src/pipeline_runner.py --stage 3

# CASO D: Bloqueo de SQLite (WAL no completado)
sqlite3 data/sunsaver.db "PRAGMA wal_checkpoint(TRUNCATE);"
python src/pipeline_runner.py --stage N

# CASO E: Manifest no existe (primera ejecución o manifest eliminado accidentalmente)
# → Ejecutar Stage 1 completo para regenerar manifests
python src/pipeline_runner.py --stage 1
```

**Verificación de resolución:**

```bash
sqlite3 data/sunsaver.db "
    SELECT status, rows_affected, error_message
    FROM etl_metadata ORDER BY id DESC LIMIT 1;

    SELECT COUNT(*) AS hechos_futuros FROM gold_fact_energy_forecast
    WHERE unix_time >= strftime('%s','now');"
```

**Acciones post-incidencia:**
- Si fue ejecución concurrente: revisar configuración de cron para evitar solapamiento
- Si fue ventana temporal expirada: revisar la hora de ejecución del cron

---

## 7. Mantenimiento

### 7.1 Tareas Periódicas

**Tabla de tareas de mantenimiento:**

| Tarea | Frecuencia | Impacto si no se hace | Comando / Procedimiento |
|-------|-----------|----------------------|------------------------|
| VACUUM de SQLite | Semanal | La BD crece innecesariamente; consultas más lentas | `sqlite3 data/sunsaver.db "VACUUM;"` |
| Comprimir logs antiguos | Semanal (> 7 días) | Consumo creciente de disco | `find logs/ -mtime +7 -exec gzip {} \;` |
| Comprimir Bronze antiguo | Mensual (> 30 días) | Consumo creciente de disco | Ver sección 7.4 |
| Archivar Bronze muy antiguo | Trimestral (> 90 días) | Saturación de disco local | Mover a almacenamiento externo |
| Backup de sunsaver.db | Diario | Sin punto de recuperación en caso de corrupción | `cp data/sunsaver.db data/backups/sunsaver_$(date +%Y%m%d).db` |
| Verificar SLO del pipeline | Semanal | Sin visibilidad de degradación gradual | Query sección 4.4 |
| Revisar manifests Bronze huérfanos | Mensual | Tareas en estado `error` no detectadas | Python snippet sección 5.2 |
| Actualizar dependencias Python | Mensual | Vulnerabilidades de seguridad | Ver sección 7.3 |
| Rotar WEATHER_API_KEY | Trimestral | Riesgo de compromiso de credencial | Ver `06_API_INTEGRATION_SPECS.md` sección 4.2 |
| Verificar festivos nacionales en dim_datetime | Anual (enero) | Períodos tarifarios incorrectos en el nuevo año | Actualizar `FESTIVOS_NACIONALES` en `gold_dim_datetime.py` |

**Script de mantenimiento semanal automatizado:**

```bash
#!/bin/bash
# scripts/weekly_maintenance.sh
# Ejecutar via cron: 0 3 * * 0 (domingos a las 03:00)

set -e
LOG="logs/maintenance_$(date +%Y%m%d).log"
echo "=== Mantenimiento semanal: $(date) ===" >> "$LOG"

# 1. VACUUM de SQLite
echo "VACUUM de sunsaver.db..." >> "$LOG"
sqlite3 data/sunsaver.db "VACUUM;" 2>> "$LOG"
echo "VACUUM completado" >> "$LOG"

# 2. Comprimir logs > 7 días
echo "Comprimiendo logs antiguos..." >> "$LOG"
find logs/ -name "*.log" -mtime +7 ! -name "*.gz" -exec gzip {} \; 2>> "$LOG"
LOGS_COMPRIMIDOS=$(find logs/ -name "*.gz" | wc -l)
echo "Logs comprimidos: $LOGS_COMPRIMIDOS" >> "$LOG"

# 3. Backup de la base de datos
echo "Backup de sunsaver.db..." >> "$LOG"
mkdir -p data/backups
cp data/sunsaver.db "data/backups/sunsaver_$(date +%Y%m%d).db"
echo "Backup creado" >> "$LOG"

# 4. Eliminar backups más antiguos de 30 días
find data/backups/ -name "sunsaver_*.db" -mtime +30 -delete
echo "Backups antiguos eliminados" >> "$LOG"

# 5. Informe de espacio en disco
echo "Espacio en disco:" >> "$LOG"
df -h . >> "$LOG"
du -sh data/ logs/ >> "$LOG"

# 6. Informe de SLO de la semana pasada
echo "SLO última semana:" >> "$LOG"
sqlite3 data/sunsaver.db "
    SELECT status, COUNT(*) AS n,
           ROUND(AVG(duration_seconds), 1) AS avg_s
    FROM etl_metadata
    WHERE executed_at >= date('now', '-7 days')
    GROUP BY status;" >> "$LOG"

echo "=== Mantenimiento completado: $(date) ===" >> "$LOG"
```

---

### 7.2 Gestión de Capacidad y Scaling

**Proyecciones de crecimiento:**

| Métrica | Actual (5 clientes) | 50 clientes | 500 clientes |
|---------|--------------------|-----------| ------------|
| Bronze por día | ~200 KB | ~2 MB | ~20 MB |
| Bronze por año | ~70 MB | ~700 MB | ~7 GB |
| `sunsaver.db` por año | ~50 MB | ~500 MB | ~5 GB |
| Tiempo de ejecución | ~2 min | ~10 min | ~90 min |
| OWM calls/mes | ~150 | ~1.500 | ~15.000 |
| RAM necesaria (pico) | ~200 MB | ~500 MB | ~2 GB |

**Umbrales de acción para scaling:**

| Umbral | Acción recomendada |
|--------|-------------------|
| > 50 clientes | Añadir `time.sleep(1.1)` entre llamadas OWM (throttling) |
| > 100 clientes | Paralelizar Stage 1 y Stage 3 con `ThreadPoolExecutor` |
| > 200 clientes | Evaluar migración de SQLite a PostgreSQL |
| Tiempo de ejecución > 15 min | Optimizar JOINs en Silver; añadir índices; considerar DuckDB |
| `sunsaver.db` > 1 GB | Migrar a PostgreSQL + TimescaleDB; activar archivado de datos históricos |
| OWM > 33.000 calls/mes (Free tier) | Upgrade a plan Startup de OWM |

**Migración de SQLite a PostgreSQL (cuando sea necesario):**

```bash
# 1. Exportar datos actuales de SQLite
sqlite3 data/sunsaver.db ".dump" > data/sunsaver_dump.sql

# 2. Adaptar el dump para PostgreSQL (tipos de datos, sintaxis)
# Usar herramienta: pgloader (https://pgloader.io)
pgloader data/sunsaver.db postgresql://user:pass@host/sunsaver_db

# 3. Actualizar config_paths.py para usar PostgreSQL
# (cambiar create_engine de sqlite:/// a postgresql://...)

# 4. Verificar que todos los módulos funcionan con la nueva BD
python src/pipeline_runner.py --dry-run
python src/pipeline_runner.py --stage 6   # reconstruir Gold
```

---

### 7.3 Actualización de Dependencias

```bash
# Ver dependencias actuales y versiones instaladas
pip list --outdated

# Ver dependencias del proyecto
cat requirements.txt

# Actualizar una dependencia específica con precaución
pip install pvlib --upgrade   # actualizar pvlib (librería de cálculo solar)
# SIEMPRE ejecutar los tests tras actualizar pvlib:
pytest tests/unit/test_engine_pv_physics.py -v

# Actualizar todas las dependencias (hacer en rama de desarrollo, no en main)
pip install -r requirements.txt --upgrade
pytest tests/unit/ -v   # verificar que nada se rompe
pip freeze > requirements.txt   # actualizar el fichero de dependencias

# Dependencias con mayor riesgo de breaking changes:
# pvlib: cambios en APIs de cálculo solar pueden afectar a engine_pv_physics.py
# pandas: cambios de API (ej. drop de .iteritems(), cambios en .groupby())
# sqlalchemy: cambios en la forma de ejecutar queries (v1 vs v2)
```

**Matriz de riesgo por dependencia:**

| Dependencia | Riesgo de breaking change | Frecuencia de actualización | Acción si hay breaking change |
|-------------|--------------------------|---------------------------|------------------------------|
| `pvlib` | 🔴 ALTO | Semestral | Re-validar resultados del motor PV contra el escenario de referencia |
| `pandas` | 🟡 MEDIO | Trimestral | Revisar warnings de deprecación antes de actualizar |
| `sqlalchemy` | 🟡 MEDIO | Semestral | Verificar compatibilidad v1/v2 en todos los módulos Silver/Gold |
| `requests` | 🟢 BAJO | Mensual | Sin riesgo notable; actualizar libremente |
| `python-dotenv` | 🟢 BAJO | Mensual | Sin riesgo notable |
| `openpyxl` | 🟢 BAJO | Trimestral | Sólo si cambia el formato .xlsx |
| `numpy` | 🟡 MEDIO | Trimestral | Revisar deprecación de `np.float` → `float` |

---

### 7.4 Rotación de Logs y Datos Históricos

**Política de rotación de logs:**

```bash
# Script de rotación manual (ejecutar semanalmente o via cron)
# Comprimir logs > 7 días, eliminar > 90 días

# Comprimir logs de hace más de 7 días
find logs/ -name "sunsaver_*.log" -mtime +7 ! -name "*.gz" -exec gzip -9 {} \;

# Eliminar logs comprimidos de hace más de 90 días
find logs/ -name "sunsaver_*.log.gz" -mtime +90 -delete

# Verificar espacio recuperado
du -sh logs/
```

**Política de archivado de datos Bronze:**

```bash
# Script de archivado de Bronze (ejecutar mensualmente)
# Fase 1: comprimir Bronze > 30 días (mantener local)
find data/bronze/ -name "*.json" -mtime +30 | while read f; do
    chmod 644 "$f"
    gzip -9 "$f"
    chmod 444 "${f}.gz"
    echo "Comprimido: $f"
done

# Fase 2: mover Bronze comprimido > 90 días a archivo externo
ARCHIVE_DIR="/mnt/archivo_sunsaver/bronze"   # ajustar a la ruta del archivo externo
mkdir -p "$ARCHIVE_DIR"
find data/bronze/ -name "*.json.gz" -mtime +90 | while read f; do
    mv "$f" "$ARCHIVE_DIR/"
    echo "Archivado: $f"
done

# Fase 3: actualizar manifests para reflejar nuevas rutas (si es necesario)
# (los manifests referencian rutas absolutas — actualizar si cambia la ruta)
```

**Política de purga de datos Gold históricos:**

```sql
-- Gold sólo necesita la ventana activa (futuro) para decisiones operativas
-- Los datos históricos (pasados) son útiles para análisis de rendimiento
-- Purgar datos de más de 365 días (mantener 1 año de histórico)

-- PRECAUCIÓN: ejecutar sólo tras confirmar que los datos no son necesarios
-- y que existe backup de sunsaver.db

DELETE FROM gold_fact_energy_forecast
WHERE unix_time < strftime('%s', date('now', '-365 days'));

-- Reclamar espacio tras la purga
VACUUM;

-- Verificar
SELECT
    date(min(unix_time), 'unixepoch') AS dato_mas_antiguo,
    date(max(unix_time), 'unixepoch') AS dato_mas_reciente,
    COUNT(*) AS total_hechos
FROM gold_fact_energy_forecast;
```

**Retención recomendada por tipo de dato:**

| Tipo de dato | Retención local | Retención en archivo | Justificación |
|-------------|----------------|---------------------|--------------|
| Ficheros Bronze JSON | 30 días sin comprimir, 90 días comprimidos | 365 días | Re-procesamiento ante bugs |
| Logs de pipeline | 7 días sin comprimir, 90 días comprimidos | 365 días | Auditoría y diagnóstico |
| `etl_metadata` (SQLite) | Sin límite (tabla pequeña) | N/A | Historial de ejecuciones |
| `gold_fact_energy_forecast` | 365 días | Indefinido (archivo frío) | Análisis de rendimiento anual |
| `clean_*` tablas Silver | Siempre (ventana activa) | N/A | Se regenera desde Bronze |
| Backups de `sunsaver.db` | 30 días | N/A | Punto de recuperación de emergencia |

---

*SunSaver ETL · Operations Runbook v1.0.0 · Mayo 2026*  
*Clasificación: INTERNA · Mantener actualizado ante cualquier cambio operativo relevante*