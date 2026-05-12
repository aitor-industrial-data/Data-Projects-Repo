# ☀️ SunSaver ETL · Plataforma de Inteligencia Energética Industrial
## 04 Framework de Calidad del Dato

> **Clasificación:** INTERNA &nbsp;|&nbsp; **Estado:** ACTIVO — Entorno DEV &nbsp;|&nbsp; **Pipeline:** `SunSaver_ETL`  
> **Propietario técnico:** Equipo de Data Engineering — SunSaver &nbsp;|&nbsp; **Última actualización:** 2026-05-12

---

## Tabla de Contenidos

1. [Filosofía de Calidad del Dato](#1-filosofía-de-calidad-del-dato)
   - 1.1 [Dimensiones de Calidad Adoptadas](#11-dimensiones-de-calidad-adoptadas)
   - 1.2 [Niveles de Severidad](#12-niveles-de-severidad)
   - 1.3 [Política de Tolerancia](#13-política-de-tolerancia-cuándo-bloquear-vs-alertar-vs-registrar)
2. [Reglas de Validación por Capa](#2-reglas-de-validación-por-capa)
   - 2.1 [Validaciones en Bronze](#21-validaciones-en-bronze)
   - 2.2 [Validaciones en Silver](#22-validaciones-en-silver)
   - 2.3 [Validaciones en Gold](#23-validaciones-en-gold)
3. [Catálogo de Reglas de Calidad](#3-catálogo-de-reglas-de-calidad)
   - 3.1 [Reglas Bronze](#31-reglas-bronze)
   - 3.2 [Reglas Silver — Clientes](#32-reglas-silver--clientes)
   - 3.3 [Reglas Silver — Meteorología](#33-reglas-silver--meteorología)
   - 3.4 [Reglas Silver — Precios](#34-reglas-silver--precios)
   - 3.5 [Reglas Silver — Cálculos PV](#35-reglas-silver--cálculos-pv)
   - 3.6 [Reglas Gold](#36-reglas-gold)
4. [Métricas y Monitorización de Calidad](#4-métricas-y-monitorización-de-calidad)
   - 4.1 [Quality Score por Tabla](#41-quality-score-por-tabla)
   - 4.2 [Quality Score por Pipeline Run](#42-quality-score-por-pipeline-run)
   - 4.3 [Tendencias Históricas](#43-tendencias-históricas-de-calidad)
   - 4.4 [Dashboard de Calidad](#44-dashboard-de-calidad)
5. [Alertas y Notificaciones](#5-alertas-y-notificaciones)
   - 5.1 [Canales de Alerta](#51-canales-de-alerta)
   - 5.2 [Matriz Severidad → Canal → Destinatario](#52-matriz-severidad--canal--destinatario)
   - 5.3 [Plantillas de Alerta](#53-plantillas-de-alerta)
   - 5.4 [Escalado de Incidencias](#54-escalado-de-incidencias)
6. [Reconciliación y Auditoría](#6-reconciliación-y-auditoría)
   - 6.1 [Row Counts por Capa](#61-row-counts-por-capa-reconciliación-bronze--silver--gold)
   - 6.2 [Sum Checks de Métricas Críticas](#62-sum-checks-de-métricas-financieras--industriales-críticas)
   - 6.3 [Registro de Auditoría](#63-registro-de-auditoría)
7. [Proceso de Remediación](#7-proceso-de-remediación)
   - 7.1 [Flujo de Trabajo para Datos Erróneos](#71-flujo-de-trabajo-para-datos-erróneos)
   - 7.2 [Política de Backfill tras Corrección](#72-política-de-backfill-tras-corrección)
   - 7.3 [Post-Mortem de Incidencias](#73-post-mortem-de-incidencias-de-calidad)

---

## 1. Filosofía de Calidad del Dato

En SunSaver, la calidad del dato no es un proceso posterior al pipeline: es una **responsabilidad distribuida en cada capa** de la arquitectura Medallion. Un dato incorrecto en este sistema tiene consecuencias directas y cuantificables:

- Un precio PVPC erróneo puede llevar a cargar baterías en el período más caro del día
- Una irradiancia sobreestimada puede provocar un arranque de maquinaria con déficit energético real
- Coordenadas incorrectas de una instalación generan previsiones meteorológicas de otra ubicación, invalidando todos los cálculos PV

El framework adopta el principio **"fail fast, fail loudly"**: los errores de calidad deben detectarse lo antes posible en el pipeline, registrarse con contexto suficiente para la remediación, y nunca propagarse silenciosamente a capas posteriores.

---

### 1.1 Dimensiones de Calidad Adoptadas

El framework se estructura en torno a las **seis dimensiones canónicas de calidad del dato** (DAMA DMBOK), adaptadas al contexto energético-industrial de SunSaver:

| Dimensión | Definición en SunSaver | Ejemplo de violación |
|-----------|----------------------|---------------------|
| **Completeness** *(Completitud)* | Todos los campos obligatorios tienen valor en todos los registros esperados | `pv_peak_power_kw` nulo en un cliente; ausencia de precios para una hora del día |
| **Accuracy** *(Precisión)* | Los valores reflejan la realidad física o económica con la precisión necesaria | Temperatura de -999°C en un slot meteorológico; precio PVPC de 50.000 €/MWh |
| **Consistency** *(Consistencia)* | Los mismos datos tienen el mismo valor en todas las tablas donde aparecen | `client_id` en `gold_fact` no existe en `gold_dim_client`; `unix_time` sin correspondencia en `gold_dim_datetime` |
| **Timeliness** *(Oportunidad)* | Los datos están disponibles cuando el proceso los necesita | Precios REE no publicados a las 21:30 CET; previsión meteorológica con antigüedad > 24h |
| **Uniqueness** *(Unicidad)* | No existen registros duplicados que representen la misma entidad o evento | Dos filas para `(client_id=C001, unix_time=1746874800)` en `clean_weather` |
| **Validity** *(Validez)* | Los valores cumplen los rangos, formatos y reglas de negocio definidos | `angle=150°` (imposible físicamente); `aspect=-10°` (fuera de rango); `efficiency=1.5` |

---

### 1.2 Niveles de Severidad

| Nivel | Código | Definición | Impacto en negocio |
|-------|--------|-----------|-------------------|
| **Crítico** | `CRITICAL` | El dato es inusable. Propagarlo generaría decisiones activamente erróneas o corrupciones en base de datos. | Decisiones de gestión energética invertidas; pérdida económica directa |
| **Alto** | `HIGH` | El dato es sospechoso. La decisión basada en él puede ser subóptima aunque no catastrófica. | Suboptimización del momento de carga de baterías o arranque de maquinaria |
| **Medio** | `MEDIUM` | El dato tiene una anomalía menor que no afecta a la toma de decisión inmediata pero debe corregirse. | Métricas de KPI ligeramente sesgadas; informes con pequeñas imprecisiones |
| **Bajo** | `LOW` | Aviso informativo. El dato es válido pero presenta una característica inesperada que merece seguimiento. | Sin impacto inmediato; relevante para tendencias a largo plazo |

---

### 1.3 Política de Tolerancia: Cuándo Bloquear vs Alertar vs Registrar

La política de respuesta ante una violación de calidad depende de la combinación de severidad y umbral de registros afectados:

| Severidad | % registros afectados | Acción | Efecto en pipeline |
|-----------|----------------------|--------|-------------------|
| `CRITICAL` | Cualquiera (≥ 1 registro) | **BLOQUEAR** | El step falla; el orquestador marca `FAILED` o `PARTIAL SUCCESS` según el stage |
| `HIGH` | > 5% | **BLOQUEAR** | Igual que CRITICAL |
| `HIGH` | ≤ 5% | **ALERTAR** | El step continúa; se registra en log y `etl_metadata.error_message` |
| `MEDIUM` | > 20% | **ALERTAR** | El step continúa con advertencia en log |
| `MEDIUM` | ≤ 20% | **REGISTRAR** | Log nivel WARNING; sin impacto en flujo |
| `LOW` | Cualquiera | **REGISTRAR** | Log nivel INFO; sin impacto en flujo |

**Regla especial para fuentes externas:**  
Cuando la fuente externa (REE, OWM) devuelve datos vacíos o no disponibles, la política es **continuar en modo degradado** (`PARTIAL SUCCESS`) en lugar de abortar. La ausencia de precio PVPC no impide calcular la generación PV ni cargar las dimensiones Gold; sólo deja `price_pvpc_eur_mwh = NULL` en la tabla de hechos hasta que los datos lleguen.

---

## 2. Reglas de Validación por Capa

### 2.1 Validaciones en Bronze

Las validaciones Bronze son deliberadamente **mínimas y no destructivas**: el objetivo es detectar payloads completamente inútiles, no filtrar datos. La filosofía Bronze es "persiste todo, valida en Silver".

| Tipo de validación | Descripción | Acción si falla |
|-------------------|-------------|-----------------|
| **No vacío** | El payload JSON contiene al menos 1 registro / valor | Log ERROR; task → `error` en manifest; no se crea fichero Bronze |
| **Parseable** | El JSON es sintácticamente válido y parseable | Log ERROR; task → `error` en manifest |
| **Campos mínimos presentes** | El payload contiene la clave raíz esperada (`included[]` para REE, `list[]` para OWM) | Log WARNING; fichero se persiste igualmente para auditoría |
| **Fichero sellado** | El fichero Bronze tiene permisos `444` tras la escritura | Log ERROR si `os.chmod` falla; alerta al equipo de operaciones |
| **Manifest actualizado** | El manifest refleja el nuevo fichero en estado `pending` | Log ERROR; riesgo de pérdida de trazabilidad |

---

### 2.2 Validaciones en Silver

Silver es la **capa de validación principal**. Aquí se aplican todas las reglas de negocio, rangos físicos y constraints de integridad. Ver el catálogo completo en la [Sección 3](#3-catálogo-de-reglas-de-calidad).

**Categorías de validación Silver:**

| Categoría | Ejemplos |
|-----------|---------|
| **Tipos de dato** | `latitude` debe ser REAL; `client_id` debe ser STRING no vacío |
| **Rangos físicos** | `angle ∈ [0, 90]`; `efficiency ∈ [0, 1]`; `clouds_pct ∈ [0, 100]` |
| **Rangos económicos** | `price_euro_mwh ∈ [-100, 2000]` |
| **Completitud de campos críticos** | `client_id`, `latitude`, `longitude`, `pv_peak_power_kw` no pueden ser NULL |
| **Unicidad de PK** | No duplicados en `(client_id)`, `(client_id, unix_time)`, `(datetime_utc, price_type)` |
| **Consistencia temporal** | `unix_time` debe corresponder a `forecast_time_utc`; timestamps deben ser UTC |
| **Coherencia física PV** | `pv_power_gen_kw ≥ 0`; `pv_power_gen_kw ≤ pv_peak_power_kw × 1.1` (margen del 10%) |

---

### 2.3 Validaciones en Gold

Gold valida la **integridad referencial del Star Schema** y la coherencia de los KPIs de negocio.

| Categoría | Ejemplos |
|-----------|---------|
| **Integridad referencial** | Todo `client_id` en `gold_fact` existe en `gold_dim_client` |
| **Completitud dimensional** | Todo `unix_time` en `gold_fact` existe en `gold_dim_datetime` |
| **Coherencia de KPIs** | `pv_power_gen_kw` nunca supera `pv_peak_power_kw` (from dim_client) |
| **Cobertura temporal** | La tabla de hechos cubre al menos 24h de previsión tras la carga |
| **Valores tarifarios** | `tariff_period ∈ {P1, P2, P3, P6}`; `tariff_label ∈ {punta, llano, valle, super-valle}` |
| **Consistencia económica** | Si `price_pvpc_eur_mwh IS NOT NULL`, debe estar en rango `[-100, 2000]` |

---

## 3. Catálogo de Reglas de Calidad

### 3.1 Reglas Bronze

---

#### DQ-B001 — Payload REE no vacío

| Atributo | Valor |
|----------|-------|
| **ID** | `DQ-B001` |
| **Nombre** | Payload REE contiene valores PVPC |
| **Tabla / campo** | `prices_*.json` → `included[0].attributes.values` |
| **Descripción** | El array de valores horarios de la API REE debe contener al menos 1 elemento tras el filtro por `id=1001` |
| **Expresión lógica** | `len(pvpc_item["attributes"]["values"]) > 0` |
| **Dimensión** | Completeness |
| **Severidad** | `HIGH` |
| **Acción si falla** | `return False` → pipeline continúa en `PARTIAL SUCCESS`; task no se registra en manifest |
| **Umbral de tolerancia** | 0% — cualquier fallo activa la acción |

---

#### DQ-B002 — Payload OWM contiene forecast list

| Atributo | Valor |
|----------|-------|
| **ID** | `DQ-B002` |
| **Nombre** | Payload OpenWeatherMap contiene lista de previsiones |
| **Tabla / campo** | `weather_{client_id}_*.json` → `list[]` |
| **Descripción** | El objeto JSON de OWM debe contener la clave `list` con al menos 1 entrada de previsión |
| **Expresión lógica** | `len(raw_json.get("list", [])) > 0` |
| **Dimensión** | Completeness |
| **Severidad** | `HIGH` |
| **Acción si falla** | Log ERROR; cliente omitido (`error_count += 1`); pipeline continúa con los demás clientes |
| **Umbral de tolerancia** | 0% por cliente — si falla para > 50% de clientes → escalar a CRITICAL |

---

#### DQ-B003 — Fichero Bronze sellado correctamente

| Atributo | Valor |
|----------|-------|
| **ID** | `DQ-B003` |
| **Nombre** | Permisos de inmutabilidad aplicados |
| **Tabla / campo** | Todos los ficheros `*.json` en `bronze/` |
| **Descripción** | Tras la escritura, el fichero Bronze debe tener permisos `444` (lectura para todos, sin escritura) |
| **Expresión lógica** | `oct(os.stat(full_path).st_mode)[-3:] == '444'` |
| **Dimensión** | Validity |
| **Severidad** | `MEDIUM` |
| **Acción si falla** | Log ERROR; fichero marcado en manifest pero con aviso de integridad |
| **Umbral de tolerancia** | 0% |

---

### 3.2 Reglas Silver — Clientes

---

#### DQ-S001 — client_id no nulo

| Atributo | Valor |
|----------|-------|
| **ID** | `DQ-S001` |
| **Nombre** | Clave primaria de cliente presente |
| **Tabla / campo** | `clean_clients.client_id` |
| **Descripción** | Ningún registro de cliente puede tener `client_id` nulo, vacío o igual a las cadenas `'None'`, `'nan'`, `'null'` |
| **Expresión lógica** | `client_id IS NOT NULL AND client_id != '' AND client_id NOT IN ('None','nan','null')` |
| **Dimensión** | Completeness |
| **Severidad** | `CRITICAL` |
| **Acción si falla** | `dropna(subset=['client_id'])` — registro descartado antes de la carga |
| **Umbral de tolerancia** | 0% — cualquier registro sin PK es descartado |

---

#### DQ-S002 — Coordenadas geográficas válidas

| Atributo | Valor |
|----------|-------|
| **ID** | `DQ-S002` |
| **Nombre** | Latitud y longitud en rango WGS84 |
| **Tabla / campo** | `clean_clients.latitude`, `clean_clients.longitude` |
| **Descripción** | Las coordenadas de la instalación deben ser geográficamente válidas. Coordenadas incorrectas generan previsiones meteorológicas de una ubicación diferente, invalidando todos los cálculos PV |
| **Expresión lógica** | `latitude BETWEEN -90 AND 90 AND longitude BETWEEN -180 AND 180` |
| **Dimensión** | Validity, Accuracy |
| **Severidad** | `CRITICAL` |
| **Acción si falla** | Registro descartado completamente — sin coordenadas válidas no se puede llamar a la API OWM ni calcular posición solar |
| **Umbral de tolerancia** | 0% |

---

#### DQ-S003 — Potencia pico PV positiva

| Atributo | Valor |
|----------|-------|
| **ID** | `DQ-S003` |
| **Nombre** | pv_peak_power_kw mayor que cero |
| **Tabla / campo** | `clean_clients.pv_peak_power_kw` |
| **Descripción** | La potencia pico del parque fotovoltaico debe ser estrictamente positiva. Un valor de 0 o negativo indica que la instalación no tiene parque PV o que el dato es erróneo |
| **Expresión lógica** | `pv_peak_power_kw > 0` |
| **Dimensión** | Validity, Completeness |
| **Severidad** | `CRITICAL` |
| **Acción si falla** | Registro descartado — sin potencia PV no hay cálculo de generación posible |
| **Umbral de tolerancia** | 0% |

---

#### DQ-S004 — Ángulo de inclinación en rango físico

| Atributo | Valor |
|----------|-------|
| **ID** | `DQ-S004` |
| **Nombre** | Ángulo de panel en rango [0°, 90°] |
| **Tabla / campo** | `clean_clients.angle` |
| **Descripción** | El ángulo de inclinación del panel respecto a la horizontal debe estar entre 0° (horizontal) y 90° (vertical). Valores fuera de rango son errores de entrada del fichero Excel |
| **Expresión lógica** | `angle BETWEEN 0 AND 90` |
| **Dimensión** | Validity |
| **Severidad** | `MEDIUM` |
| **Acción si falla** | Imputar con valor por defecto `30°` (inclinación óptima para España) + log WARNING |
| **Umbral de tolerancia** | ≤ 10% de registros — si > 10% necesitan imputación, revisar el fichero Excel de origen |

---

#### DQ-S005 — Eficiencia de panel en rango físico

| Atributo | Valor |
|----------|-------|
| **ID** | `DQ-S005` |
| **Nombre** | Eficiencia de panel en rango [0, 1] |
| **Tabla / campo** | `clean_clients.efficiency` |
| **Descripción** | La eficiencia del panel solar debe estar entre 0 y 1 (0% a 100%). Los paneles comerciales típicos están entre 0.15 y 0.24. Un valor de 1.5 o 20 indica que se introdujo como porcentaje en lugar de fracción |
| **Expresión lógica** | `efficiency BETWEEN 0 AND 1` |
| **Dimensión** | Validity, Accuracy |
| **Severidad** | `MEDIUM` |
| **Acción si falla** | Imputar con `0.15` (eficiencia típica monoSi) + log WARNING con el valor original |
| **Umbral de tolerancia** | ≤ 10% |

---

#### DQ-S006 — Sin duplicados por client_id

| Atributo | Valor |
|----------|-------|
| **ID** | `DQ-S006` |
| **Nombre** | Unicidad de cliente en clean_clients |
| **Tabla / campo** | `clean_clients.client_id` |
| **Descripción** | No pueden existir dos filas con el mismo `client_id` en `clean_clients`. Si el mismo cliente aparece en múltiples ficheros Bronze (re-ejecuciones), sólo debe mantenerse la ingesta más reciente |
| **Expresión lógica** | `COUNT(*) = COUNT(DISTINCT client_id)` |
| **Dimensión** | Uniqueness |
| **Severidad** | `HIGH` |
| **Acción si falla** | `drop_duplicates(subset=['client_id'], keep='first')` tras `sort_values('_ingested_at_utc', ascending=False)` |
| **Umbral de tolerancia** | 0% tras deduplicación |

---

### 3.3 Reglas Silver — Meteorología

---

#### DQ-S007 — Temperatura en rango plausible

| Atributo | Valor |
|----------|-------|
| **ID** | `DQ-S007` |
| **Nombre** | Temperatura ambiente en rango climatológico |
| **Tabla / campo** | `clean_weather.temp_celsius` |
| **Descripción** | La temperatura en España peninsular no puede ser inferior a -30°C ni superior a 55°C. Valores fuera de este rango son errores de la API o de la unidad de medida |
| **Expresión lógica** | `temp_celsius BETWEEN -30 AND 55` |
| **Dimensión** | Accuracy, Validity |
| **Severidad** | `HIGH` |
| **Acción si falla** | Registrar como NULL + aplicar interpolación lineal desde valores vecinos; log ERROR con el valor recibido |
| **Umbral de tolerancia** | ≤ 1% de registros |

---

#### DQ-S008 — Cobertura nubosa en rango [0, 100]

| Atributo | Valor |
|----------|-------|
| **ID** | `DQ-S008` |
| **Nombre** | clouds_pct entre 0% y 100% |
| **Tabla / campo** | `clean_weather.clouds_pct` |
| **Descripción** | El porcentaje de cobertura nubosa es una fracción de 0 a 100. Es uno de los inputs más críticos del motor GHI: un valor fuera de rango generaría una irradiancia negativa o irreal |
| **Expresión lógica** | `clouds_pct BETWEEN 0 AND 100` |
| **Dimensión** | Validity, Accuracy |
| **Severidad** | `HIGH` |
| **Acción si falla** | Clamp al rango `[0, 100]` + log WARNING; si el valor supera 200 → NULL + interpolación |
| **Umbral de tolerancia** | 0% — crítico para el motor PV |

---

#### DQ-S009 — Probabilidad de lluvia en rango [0, 1]

| Atributo | Valor |
|----------|-------|
| **ID** | `DQ-S009` |
| **Nombre** | rain_prob_norm normalizado entre 0 y 1 |
| **Tabla / campo** | `clean_weather.rain_prob_norm` |
| **Descripción** | La probabilidad de precipitación (OWM `pop`) debe estar entre 0 y 1. OWM ya la devuelve normalizada; una anomalía indicaría un cambio de API |
| **Expresión lógica** | `rain_prob_norm BETWEEN 0 AND 1` |
| **Dimensión** | Validity |
| **Severidad** | `MEDIUM` |
| **Acción si falla** | Clamp al rango `[0, 1]` + log WARNING |
| **Umbral de tolerancia** | ≤ 2% |

---

#### DQ-S010 — Resolución horaria completa en clean_weather

| Atributo | Valor |
|----------|-------|
| **ID** | `DQ-S010` |
| **Nombre** | Cobertura horaria completa del forecast |
| **Tabla / campo** | `clean_weather` — por `(client_id, date)` |
| **Descripción** | Tras el resample a 1h, cada cliente debe tener exactamente 24 filas por día de previsión durante los 5 días del horizonte. Huecos en la cobertura horaria implican que la interpolación no fue suficiente para cubrir un gap grande en los datos originales de OWM |
| **Expresión lógica** | `COUNT(*) per (client_id, date) = 24` |
| **Dimensión** | Completeness, Timeliness |
| **Severidad** | `MEDIUM` |
| **Acción si falla** | Log WARNING con el número de horas faltantes por cliente y fecha; los huecos restantes reciben `ffill` como último recurso |
| **Umbral de tolerancia** | ≤ 2 horas faltantes por cliente por día |

---

#### DQ-S011 — Unicidad de (client_id, unix_time) en clean_weather

| Atributo | Valor |
|----------|-------|
| **ID** | `DQ-S011` |
| **Nombre** | No duplicados en PK de meteorología |
| **Tabla / campo** | `clean_weather (client_id, unix_time)` |
| **Descripción** | La combinación `(client_id, unix_time)` es la clave primaria de `clean_weather` y debe ser única. Duplicados provocarían filas duplicadas en `gold_fact_energy_forecast` |
| **Expresión lógica** | `COUNT(*) = COUNT(DISTINCT client_id || unix_time)` |
| **Dimensión** | Uniqueness |
| **Severidad** | `CRITICAL` |
| **Acción si falla** | `INSERT OR REPLACE` garantiza idempotencia en SQLite; log WARNING si se detectan duplicados antes de la carga |
| **Umbral de tolerancia** | 0% tras upsert |

---

### 3.4 Reglas Silver — Precios

---

#### DQ-S012 — Precio PVPC en rango económico válido

| Atributo | Valor |
|----------|-------|
| **ID** | `DQ-S012` |
| **Nombre** | price_euro_mwh en rango plausible |
| **Tabla / campo** | `clean_prices.price_euro_mwh` |
| **Descripción** | El precio PVPC en el mercado español ha oscilado históricamente entre valores negativos (excedentes renovables) hasta máximos históricos cercanos a 700 €/MWh durante la crisis energética de 2022. El rango `[-100, 2000]` cubre escenarios extremos con margen suficiente para detectar errores de escala (ej. valor en €/kWh en lugar de €/MWh) |
| **Expresión lógica** | `price_euro_mwh BETWEEN -100 AND 2000` |
| **Dimensión** | Accuracy, Validity |
| **Severidad** | `HIGH` |
| **Acción si falla** | Registro filtrado y descartado + log WARNING con valor original |
| **Umbral de tolerancia** | 0% — cualquier precio fuera de rango es descartado |

---

#### DQ-S013 — Cobertura completa de 24 horas PVPC

| Atributo | Valor |
|----------|-------|
| **ID** | `DQ-S013` |
| **Nombre** | Precios PVPC para las 24 horas del día D+1 |
| **Tabla / campo** | `clean_prices` — por fecha D+1 |
| **Descripción** | El precio PVPC debe cubrir las 24 horas del día siguiente (D+1). Una cobertura parcial (ej. 22 de 24 horas) indica un problema en la publicación de REE o en el parser |
| **Expresión lógica** | `COUNT(*) per (date, price_type) = 24` |
| **Dimensión** | Completeness, Timeliness |
| **Severidad** | `HIGH` |
| **Acción si falla** | Interpolación lineal para rellenar horas faltantes + log WARNING indicando qué horas faltan |
| **Umbral de tolerancia** | ≤ 2 horas faltantes (interpoladas automáticamente) |

---

#### DQ-S014 — Unicidad temporal de precios

| Atributo | Valor |
|----------|-------|
| **ID** | `DQ-S014` |
| **Nombre** | No duplicados en PK de precios |
| **Tabla / campo** | `clean_prices (datetime_utc, price_type)` |
| **Descripción** | La combinación `(datetime_utc, price_type)` es la PK de `clean_prices`. Si REE publica una corrección de precios el mismo día, la segunda ejecución del pipeline debe sobreescribir los valores anteriores, no crear duplicados |
| **Expresión lógica** | `COUNT(*) = COUNT(DISTINCT datetime_utc || price_type)` |
| **Dimensión** | Uniqueness |
| **Severidad** | `CRITICAL` |
| **Acción si falla** | `INSERT OR REPLACE` garantiza idempotencia; si duplicados persisten → log CRITICAL + alerta |
| **Umbral de tolerancia** | 0% |

---

### 3.5 Reglas Silver — Cálculos PV

---

#### DQ-S015 — Potencia generada no negativa

| Atributo | Valor |
|----------|-------|
| **ID** | `DQ-S015` |
| **Nombre** | pv_power_gen_kw ≥ 0 |
| **Tabla / campo** | `clean_calculations.pv_power_gen_kw` |
| **Descripción** | Un parque fotovoltaico no puede generar potencia negativa. Un valor negativo indicaría un error en el motor de cálculo físico (`engine_pv_physics.py`), posiblemente en el cálculo del Performance Ratio con pérdidas extremas |
| **Expresión lógica** | `pv_power_gen_kw >= 0` |
| **Dimensión** | Accuracy, Validity |
| **Severidad** | `CRITICAL` |
| **Acción si falla** | `max(0, p_out)` aplicado en `calculate_power_output()` — nunca debería llegar a Silver como negativo; si llega, log CRITICAL + investigación inmediata |
| **Umbral de tolerancia** | 0% — un valor negativo en generación PV es imposible físicamente |

---

#### DQ-S016 — Potencia generada no supera el pico instalado

| Atributo | Valor |
|----------|-------|
| **ID** | `DQ-S016` |
| **Nombre** | pv_power_gen_kw ≤ pv_peak_power_kw × 1.1 |
| **Tabla / campo** | `clean_calculations.pv_power_gen_kw` vs `clean_clients.pv_peak_power_kw` |
| **Descripción** | La potencia AC generada no puede superar la potencia pico nominal del inversor en más de un 10% (margen para sobredimensionamiento DC/AC típico). Una violación indica un error en el cálculo de irradiancia o de PR |
| **Expresión lógica** | `pv_power_gen_kw <= pv_peak_power_kw * 1.1` |
| **Dimensión** | Accuracy |
| **Severidad** | `HIGH` |
| **Acción si falla** | Log WARNING con los valores; registro se carga igualmente (puede ser un escenario válido de sobredimensionamiento extremo) |
| **Umbral de tolerancia** | ≤ 0.5% de registros diurnos |

---

#### DQ-S017 — Performance Ratio en rango físico

| Atributo | Valor |
|----------|-------|
| **ID** | `DQ-S017` |
| **Nombre** | pv_performance_ratio en rango [0.3, 1.0] |
| **Tabla / campo** | `clean_calculations.pv_performance_ratio` |
| **Descripción** | El Performance Ratio de un sistema PV real varía entre 0.5 (sistema muy degradado o muy caliente) y 0.95 (sistema nuevo en condiciones óptimas). El rango `[0.3, 1.0]` cubre casos extremos. Un PR de 0.1 o 1.5 indica un error de cálculo |
| **Expresión lógica** | `pv_performance_ratio BETWEEN 0.3 AND 1.0 OR pv_performance_ratio = 0` |
| **Dimensión** | Accuracy, Validity |
| **Severidad** | `MEDIUM` |
| **Acción si falla** | Log WARNING; registro se carga igualmente para trazabilidad |
| **Umbral de tolerancia** | ≤ 2% de registros diurnos (excluyendo noche donde PR = 0) |

---

#### DQ-S018 — Consumo industrial no negativo

| Atributo | Valor |
|----------|-------|
| **ID** | `DQ-S018` |
| **Nombre** | power_con_kw ≥ 0 |
| **Tabla / campo** | `clean_calculations.power_con_kw` |
| **Descripción** | El consumo industrial simulado nunca puede ser negativo. El modelo de consumo incluye carga base, HVAC y variabilidad gaussiana; en ningún escenario el resultado debería ser negativo |
| **Expresión lógica** | `power_con_kw >= 0` |
| **Dimensión** | Accuracy, Validity |
| **Severidad** | `HIGH` |
| **Acción si falla** | `max(0, consumption)` aplicado en `calculate_industrial_consumption()` — si llega negativo a Silver, log CRITICAL |
| **Umbral de tolerancia** | 0% |

---

### 3.6 Reglas Gold

---

#### DQ-G001 — Integridad referencial fact → dim_client

| Atributo | Valor |
|----------|-------|
| **ID** | `DQ-G001` |
| **Nombre** | Todo client_id en fact existe en dim_client |
| **Tabla / campo** | `gold_fact_energy_forecast.client_id` → `gold_dim_client.client_id` |
| **Descripción** | La tabla de hechos no puede tener filas huérfanas sin dimensión de cliente. Si `client_id` existe en `clean_calculations` pero no en `gold_dim_client`, significa que el full rebuild de la dimensión falló |
| **Expresión lógica** | `SELECT COUNT(*) FROM gold_fact f LEFT JOIN gold_dim_client c ON f.client_id = c.client_id WHERE c.client_id IS NULL = 0` |
| **Dimensión** | Consistency |
| **Severidad** | `CRITICAL` |
| **Acción si falla** | Bloquear carga de `gold_fact`; re-ejecutar `load_dim_client()` primero |
| **Umbral de tolerancia** | 0% huérfanos |

---

#### DQ-G002 — Integridad referencial fact → dim_datetime

| Atributo | Valor |
|----------|-------|
| **ID** | `DQ-G002` |
| **Nombre** | Todo unix_time en fact existe en dim_datetime |
| **Tabla / campo** | `gold_fact_energy_forecast.unix_time` → `gold_dim_datetime.unix_time` |
| **Descripción** | Cada slot horario de la tabla de hechos debe tener su correspondiente registro de dimensión temporal con el período tarifario calculado. Sin esta dimensión, los análisis de coste por período son imposibles |
| **Expresión lógica** | `SELECT COUNT(*) FROM gold_fact f LEFT JOIN gold_dim_datetime d ON f.unix_time = d.unix_time WHERE d.unix_time IS NULL = 0` |
| **Dimensión** | Consistency |
| **Severidad** | `CRITICAL` |
| **Acción si falla** | Bloquear carga de `gold_fact`; re-ejecutar `load_dim_datetime()` primero |
| **Umbral de tolerancia** | 0% huérfanos |

---

#### DQ-G003 — Cobertura mínima de previsión en gold_fact

| Atributo | Valor |
|----------|-------|
| **ID** | `DQ-G003` |
| **Nombre** | gold_fact cubre al menos 24h de previsión por cliente |
| **Tabla / campo** | `gold_fact_energy_forecast` — por `client_id` |
| **Descripción** | Tras cada ejecución exitosa del pipeline, la tabla de hechos debe contener al menos 24 filas futuras por cliente activo (ventana mínima de toma de decisiones = 1 día). Si hay menos, el horizonte de decisión es insuficiente |
| **Expresión lógica** | `COUNT(*) per client_id WHERE unix_time > now >= 24` |
| **Dimensión** | Completeness, Timeliness |
| **Severidad** | `HIGH` |
| **Acción si falla** | Log ERROR; alerta al equipo; revisar si OWM devolvió datos suficientes |
| **Umbral de tolerancia** | 100% de clientes activos deben tener ≥ 24h de cobertura |

---

#### DQ-G004 — Período tarifario válido en dim_datetime

| Atributo | Valor |
|----------|-------|
| **ID** | `DQ-G004` |
| **Nombre** | tariff_period sólo contiene valores P1/P2/P3/P6 |
| **Tabla / campo** | `gold_dim_datetime.tariff_period` |
| **Descripción** | El campo `tariff_period` sólo puede contener los cuatro valores definidos por la tarifa 3.0TD española. Cualquier otro valor indica un bug en la función `get_tariff_period()` |
| **Expresión lógica** | `tariff_period IN ('P1','P2','P3','P6')` |
| **Dimensión** | Validity |
| **Severidad** | `CRITICAL` |
| **Acción si falla** | Bloquear carga de `gold_dim_datetime`; investigar bug en lógica tarifaria |
| **Umbral de tolerancia** | 0% |

---

#### DQ-G005 — KPI de generación coherente con potencia instalada

| Atributo | Valor |
|----------|-------|
| **ID** | `DQ-G005` |
| **Nombre** | pv_power_gen_kw coherente con pv_peak_power_kw de la dimensión |
| **Tabla / campo** | `gold_fact_energy_forecast.pv_power_gen_kw` vs `gold_dim_client.pv_peak_power_kw` |
| **Descripción** | Validación cruzada entre hecho y dimensión: la generación reportada en la tabla de hechos no debe superar el 110% de la potencia pico configurada en la dimensión de cliente |
| **Expresión lógica** | `f.pv_power_gen_kw <= c.pv_peak_power_kw * 1.1 OR f.pv_power_gen_kw = 0` |
| **Dimensión** | Accuracy, Consistency |
| **Severidad** | `HIGH` |
| **Acción si falla** | Log WARNING con `client_id`, `unix_time`, valor calculado y valor máximo esperado |
| **Umbral de tolerancia** | ≤ 0.5% de registros diurnos |

---

## 4. Métricas y Monitorización de Calidad

### 4.1 Quality Score por Tabla

El **Quality Score (QS)** de una tabla es el porcentaje ponderado de registros que superan todas las reglas de calidad aplicables, donde cada regla contribuye con un peso proporcional a su severidad.

**Fórmula del Quality Score:**

```
QS_tabla = Σ(peso_i × tasa_aprobación_i) / Σ(peso_i)

donde:
  tasa_aprobación_i = registros_que_pasan_regla_i / total_registros
  peso CRITICAL = 4
  peso HIGH     = 3
  peso MEDIUM   = 2
  peso LOW      = 1
```

**Umbrales de calidad por tabla:**

| Tabla | QS mínimo aceptable | QS objetivo | Justificación |
|-------|--------------------|-----------|--------------| 
| `clean_clients` | 95% | 99% | Datos maestros — errores se propagan a todos los cálculos |
| `clean_weather` | 90% | 97% | Interpolación OWM introduce variabilidad; 3% de huecos aceptable |
| `clean_prices` | 95% | 99% | Impacto económico directo; alta precisión requerida |
| `clean_calculations` | 92% | 98% | Depende de clean_clients y clean_weather; hereda su calidad |
| `gold_dim_client` | 98% | 100% | Dimensión estable; full rebuild garantiza consistencia |
| `gold_dim_datetime` | 100% | 100% | Dimensión calculada determinísticamente; 0 errores esperados |
| `gold_dim_weather` | 95% | 99% | Catálogo pequeño; alta estabilidad |
| `gold_fact_energy_forecast` | 90% | 96% | `price_pvpc_eur_mwh` puede ser NULL legítimamente |

**Implementación del quality check en SQL:**

```sql
-- Ejemplo: QS de clean_clients
SELECT
    'clean_clients'                                               AS tabla,
    ROUND(100.0 * SUM(CASE
        WHEN client_id IS NOT NULL
         AND latitude  BETWEEN -90   AND 90
         AND longitude BETWEEN -180  AND 180
         AND pv_peak_power_kw > 0
         AND angle     BETWEEN 0     AND 90
         AND efficiency BETWEEN 0    AND 1
        THEN 1 ELSE 0
    END) / COUNT(*), 2)                                           AS quality_score_pct,
    COUNT(*)                                                      AS total_registros,
    SUM(CASE WHEN client_id IS NULL THEN 1 ELSE 0 END)           AS nulos_client_id,
    SUM(CASE WHEN pv_peak_power_kw <= 0 THEN 1 ELSE 0 END)       AS pv_power_invalido,
    SUM(CASE WHEN angle NOT BETWEEN 0 AND 90 THEN 1 ELSE 0 END)  AS angle_invalido
FROM clean_clients;
```

---

### 4.2 Quality Score por Pipeline Run

Al finalizar cada ejecución, el orquestador calcula y registra el **Quality Score global del run**, agregando los scores de todas las tablas producidas:

```python
# Roadmap: integrar en audit_metadata.py
def calculate_run_quality_score(db_path: str) -> dict:
    """
    Calcula el QS global de la ejecución como media ponderada de los QS
    de todas las tablas Silver y Gold, con pesos por criticidad de tabla.
    """
    table_weights = {
        "clean_clients":             4.0,   # datos maestros — mayor peso
        "clean_prices":              3.5,   # impacto económico directo
        "clean_weather":             3.0,
        "clean_calculations":        3.0,
        "gold_fact_energy_forecast": 2.5,
        "gold_dim_client":           2.0,
        "gold_dim_datetime":         1.5,
        "gold_dim_weather":          1.0,
    }
    # ... consultas SQL por tabla + media ponderada ...
    return {
        "run_quality_score": weighted_avg,
        "table_scores":      individual_scores,
        "tables_below_threshold": [t for t, s in individual_scores.items()
                                   if s < QUALITY_THRESHOLDS[t]],
    }
```

**Clasificación del run por Quality Score global:**

| QS global | Estado de calidad | Acción |
|-----------|------------------|--------|
| ≥ 97% | ✅ **EXCELENTE** | Ninguna |
| 90–97% | ✅ **BUENO** | Registrar en log; revisar en próxima sprint |
| 80–90% | ⚠️ **DEGRADADO** | Alerta HIGH al equipo; investigar dentro de 24h |
| < 80% | 🔴 **CRÍTICO** | Alerta CRITICAL inmediata; considerar no publicar datos Gold |

---

### 4.3 Tendencias Históricas de Calidad

El seguimiento de tendencias permite detectar **degradación gradual de la calidad** antes de que alcance umbrales críticos (ej. una fuente que progresivamente devuelve más valores nulos).

**Query de tendencia semanal (sobre etl_metadata + quality_scores):**

```sql
-- Evolución del quality score por tabla en los últimos 30 días
-- (requiere tabla quality_scores_history — roadmap)
SELECT
    date(executed_at)  AS fecha,
    tabla,
    AVG(quality_score) AS qs_medio,
    MIN(quality_score) AS qs_minimo,
    COUNT(*)           AS n_ejecuciones
FROM quality_scores_history
WHERE executed_at >= date('now', '-30 days')
GROUP BY date(executed_at), tabla
ORDER BY fecha DESC, tabla;
```

**Señales de alerta temprana (tendencias):**

| Señal | Umbral | Acción recomendada |
|-------|--------|-------------------|
| QS de una tabla cae > 5 puntos en 7 días | Tendencia descendente | Revisar si la fuente cambió su schema o calidad |
| % de nulos en `price_pvpc_eur_mwh` > 20% en últimos 3 días | Problema de disponibilidad REE | Verificar horario de publicación; configurar segundo re-intento |
| Número de clientes en `clean_weather` < número en `clean_clients` | Fallos en OWM por algunos clientes | Revisar API key; comprobar coordenadas de los clientes afectados |
| `rows_affected` en `etl_metadata` cae > 30% respecto a la media | Pérdida de datos en pipeline | Revisar logs del pipeline; posible cambio de API |

---

### 4.4 Dashboard de Calidad

**Especificación del dashboard de calidad** (a implementar con herramienta BI):

```
+-----------------------------------------------------------------------------+
|  SUNSAVER — QUALITY DASHBOARD            Última actualización: 2026-05-10   |
+-----------------------------------------------------------------------------+
|                                                                             |
|  QUALITY SCORE GLOBAL: 96.2%  ✅ BUENO                                      |
|  ███████████████████████░  Pipeline: PARTIAL SUCCESS                        |
|                                                                             |
+---------------------+----------------+----------------+---------------------+
| TABLA               | QS HOY         | QS AYER        | TREND               |
+---------------------+----------------+----------------+---------------------+
| clean_clients       | 99.1%  ✅      | 99.3%  ✅      | → estable           |
| clean_weather       | 95.4%  ✅      | 96.1%  ✅      | ↓ -0.7%             |
| clean_prices        | N/A (PARTIAL)  | 99.8%  ✅      | ⚠️ sin dato         |
| clean_calculations  | 94.8%  ✅      | 95.2%  ✅      | → estable           |
| gold_fact           | 91.2%  ✅      | 94.1%  ✅      | ↓ -2.9%             |
| gold_dim_client     | 100.0% ✅      | 100.0% ✅      | → estable           |
| gold_dim_datetime   | 100.0% ✅      | 100.0% ✅      | → estable           |
| gold_dim_weather    | 98.7%  ✅      | 98.7%  ✅      | → estable           |
+---------------------+----------------+----------------+---------------------+
|                                                                             |
|  ALERTAS ACTIVAS: 1                                                         |
|  ⚠️ [HIGH] clean_prices: PARTIAL SUCCESS — precios REE no disponibles       |
|     en ejecución de 20:00 UTC. Re-intento programado: 22:00 UTC             |
|                                                                             |
|  ÚLTIMAS 7 EJECUCIONES: ✅ ✅ ✅ ⚠️ ✅ ✅ ✅                                |
+-----------------------------------------------------------------------------+
```

**Herramientas recomendadas para implementación:**

| Herramienta | Caso de uso | Complejidad |
|-------------|------------|-------------|
| **Grafana + SQLite datasource** | Dashboard en tiempo real sobre SQLite | Baja |
| **Apache Superset** | BI completo sobre SQLite/PostgreSQL | Media |
| **Metabase** | Dashboard sin código, fácil de mantener | Muy baja |
| **Jupyter + Plotly** | Análisis ad-hoc de calidad | Baja (ya en el stack Python) |

---

## 5. Alertas y Notificaciones

### 5.1 Canales de Alerta

| Canal | Uso | Latencia | Implementación |
|-------|-----|---------|---------------|
| **Log file** (`sunsaver_YYYY-MM-DD.log`) | Todos los eventos; base de auditoría | Tiempo real | `logger.error()` / `logger.warning()` — ya implementado |
| **Stderr / consola** | Visibilidad inmediata en ejecución manual o cron | Tiempo real | `StreamHandler` — ya implementado |
| **Slack webhook** | Alertas HIGH y CRITICAL al equipo técnico | < 1 min | Roadmap — webhook POST en `finally` del orquestador |
| **Email** | Resumen diario del pipeline + alertas CRITICAL | < 5 min | Roadmap — `smtplib` o servicio SMTP externo |
| **PagerDuty** | Fallos CRITICAL que requieren acción inmediata fuera de horario | < 2 min | Roadmap — integración vía API REST |

---

### 5.2 Matriz Severidad → Canal → Destinatario

| Evento | Severidad | Log | Slack | Email | PagerDuty | Destinatario |
|--------|-----------|-----|-------|-------|-----------|-------------|
| REE sin datos (PARTIAL SUCCESS) | `HIGH` | ✅ | ✅ | ❌ | ❌ | Canal `#data-alerts` |
| OWM falla para > 50% clientes | `CRITICAL` | ✅ | ✅ | ✅ | ✅ | Data Eng + On-call |
| Precio PVPC fuera de rango | `HIGH` | ✅ | ✅ | ❌ | ❌ | Canal `#data-alerts` |
| QS global < 80% | `CRITICAL` | ✅ | ✅ | ✅ | ✅ | Data Eng + Data Science |
| QS global 80–90% | `HIGH` | ✅ | ✅ | ✅ | ❌ | Data Eng |
| `etl_metadata.status = FAILED` | `CRITICAL` | ✅ | ✅ | ✅ | ✅ | Data Eng + On-call |
| `etl_metadata.status = PARTIAL SUCCESS` | `MEDIUM` | ✅ | ✅ | ❌ | ❌ | Canal `#data-alerts` |
| Integridad referencial rota en Gold | `CRITICAL` | ✅ | ✅ | ✅ | ✅ | Data Eng + Data Science |
| Fichero Bronze sin permisos 444 | `MEDIUM` | ✅ | ⚠️ | ❌ | ❌ | Canal `#data-ops` |
| `rows_affected` cae > 30% vs media | `HIGH` | ✅ | ✅ | ✅ | ❌ | Data Eng |
| Pipeline completado con éxito | `INFO` | ✅ | ✅ (resumen diario) | ❌ | ❌ | Canal `#data-status` |

---

### 5.3 Plantillas de Alerta

#### Plantilla CRITICAL — Fallo total de pipeline

```
🔴 [CRITICAL] SunSaver ETL — PIPELINE FAILED
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Pipeline    : SunSaver_ETL
Status      : FAILED AT STAGE {stage_num}
Timestamp   : {executed_at} UTC
Duration    : {duration_seconds}s
Step failed : {failed_step_name}
Error       : {error_message}

Rows processed before failure: {rows_affected}

⚡ Acción requerida: revisar logs en logs/sunsaver_{date}.log
   Comando de re-intento: python src/pipeline_runner.py --stage {stage_num}
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

#### Plantilla HIGH — Partial Success (REE sin datos)

```
⚠️ [HIGH] SunSaver ETL — PARTIAL SUCCESS
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Pipeline  : SunSaver_ETL
Status    : PARTIAL SUCCESS
Timestamp : {executed_at} UTC
Causa     : Precios PVPC REE no disponibles aún (habitual antes de 21:00 CET)

Datos cargados  : Meteorología ✅ | Cálculos PV ✅ | Gold dims ✅ | Gold fact ✅
Datos faltantes : price_pvpc_eur_mwh = NULL para {n_slots} slots de {date_tomorrow}

Re-intento automático programado: {retry_time} UTC
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

#### Plantilla INFO — Ejecución exitosa (resumen diario)

```
✅ [INFO] SunSaver ETL — SUCCESS | Resumen diario {date}
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Pipeline     : SunSaver_ETL
Status       : SUCCESS
Duración     : {duration_seconds}s
Total rows   : {rows_affected}

Desglose por step:
  ✔ extract_clients          {rows_clients} clientes
  ✔ extract_energy_prices    {rows_prices} precios horarios (D+1)
  ✔ transform_clients        {rows_clean_clients} registros Silver
  ✔ transform_energy_prices  {rows_clean_prices} registros Silver
  ✔ extract_openweather      {rows_weather_files} ficheros Bronze
  ✔ transform_openweather    {rows_clean_weather} slots horarios Silver
  ✔ extract_generation_data  {rows_calculations} cálculos PV
  ✔ gold_dim_client          {rows_dim_client} dimensiones
  ✔ gold_dim_datetime        {rows_dim_datetime} slots temporales
  ✔ gold_dim_weather         {rows_dim_weather} condiciones
  ✔ gold_fact_energy         {rows_fact} hechos energéticos

Quality Score global: {quality_score}%
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

---

### 5.4 Escalado de Incidencias

```
Minuto 0:   Evento detectado → Log + Slack automático
            │
            ├─ ¿Resuelto en 30 min?  → Sí → Registrar en post-mortem lite
            │                          No → continuar escalado
            │
Minuto 30:  Re-intento automático del pipeline (cron --stage N)
            │
            ├─ ¿Resuelto?  → Sí → Notificar resolución a Slack
            │               No → continuar
            │
Hora 1:     Email al equipo Data Engineering + Data Science
            Incidencia abierta en sistema de tickets (Jira / GitHub Issues)
            │
            ├─ ¿Resuelto?  → Sí → Cerrar ticket + post-mortem en 48h
            │               No → continuar
            │
Hora 2:     PagerDuty on-call engineer
            Decisión: ¿publicar datos degradados o bloquear acceso a Gold?
            │
Hora 4:     Escalado a responsable de producto si impacto en decisiones
            de negocio activas (ej. carga de baterías ya en curso con datos erróneos)
```

**Criterios para bloquear acceso a datos Gold:**

| Condición | Decisión |
|-----------|---------|
| Integridad referencial rota (DQ-G001, DQ-G002) | Bloquear — datos inconsistentes |
| QS global < 70% | Bloquear — datos no fiables para decisiones |
| `price_pvpc_eur_mwh = NULL` para todo el día | No bloquear — dato faltante, no erróneo |
| `pv_power_gen_kw` negativo en > 1% registros | Bloquear — imposible físicamente; error de cálculo |

---

## 6. Reconciliación y Auditoría

### 6.1 Row Counts por Capa — Reconciliación Bronze ↔ Silver ↔ Gold

La reconciliación de recuentos entre capas es la primera verificación tras cada ejecución del pipeline. Divergencias inesperadas indican pérdida de datos, duplicados o problemas de filtrado.

**Recuentos esperados por ejecución:**

| Capa | Tabla | Recuento esperado | Fórmula |
|------|-------|------------------|---------|
| Bronze | `prices_*.json` | 24 valores | `len(pvpc_item["attributes"]["values"]) = 24` |
| Bronze | `weather_{client_id}_*.json` | 40 por cliente | `len(raw_json["list"]) = 40` |
| Silver | `clean_prices` | 24 filas (D+1) | `COUNT(*) WHERE date = tomorrow` |
| Silver | `clean_weather` | 120 por cliente | `COUNT(*) per client_id WHERE date >= today` |
| Silver | `clean_calculations` | 120 por cliente | `COUNT(*) per client_id WHERE unix_time >= now` |
| Gold | `gold_fact_energy_forecast` | ≥ 120 × N_clientes | `COUNT(*) WHERE unix_time >= now` |
| Gold | `gold_dim_datetime` | = `COUNT(DISTINCT unix_time)` en `clean_weather` | Full match |
| Gold | `gold_dim_client` | = `COUNT(*)` en `clean_clients` | Full match |

**Query de reconciliación completa:**

```sql
-- Ejecutar tras cada pipeline para verificar consistencia entre capas
WITH counts AS (
    SELECT
        (SELECT COUNT(*) FROM clean_clients)             AS silver_clients,
        (SELECT COUNT(*) FROM clean_weather
         WHERE unix_time >= strftime('%s','now'))        AS silver_weather_active,
        (SELECT COUNT(*) FROM clean_prices
         WHERE datetime_utc >= date('now'))              AS silver_prices_tomorrow,
        (SELECT COUNT(*) FROM clean_calculations
         WHERE unix_time >= strftime('%s','now'))        AS silver_calculations,
        (SELECT COUNT(*) FROM gold_dim_client)           AS gold_dim_client,
        (SELECT COUNT(*) FROM gold_dim_datetime)         AS gold_dim_datetime,
        (SELECT COUNT(*) FROM gold_fact_energy_forecast
         WHERE unix_time >= strftime('%s','now'))        AS gold_fact_active
)
SELECT
    *,
    -- Validaciones de reconciliación
    CASE WHEN gold_dim_client = silver_clients
         THEN '✅ OK' ELSE '❌ DIVERGENCIA' END          AS check_clients,
    CASE WHEN gold_fact_active >= silver_calculations * 0.95
         THEN '✅ OK' ELSE '⚠️ POSIBLE PÉRDIDA' END      AS check_fact_vs_calc
FROM counts;
```

**Umbrales de tolerancia en reconciliación:**

| Check | Tolerancia | Justificación |
|-------|-----------|---------------|
| `gold_dim_client` vs `clean_clients` | 0% — debe ser idéntico | Full rebuild; 0 pérdidas aceptables |
| `gold_fact` rows vs `clean_calculations` rows | ≤ 5% diferencia | `LEFT JOIN` con precios puede reducir ligeramente |
| `clean_weather` slots vs esperados (120/cliente) | ≤ 2 slots/cliente | Límites del resample horario |
| `clean_prices` vs 24 horas esperadas | 0 diferencia (con interpolación) | Interpolación cubre huecos |

---

### 6.2 Sum Checks de Métricas Financieras / Industriales Críticas

Los sum checks verifican que los **totales agregados** son físicamente plausibles, detectando errores que los row counts no capturan (ej. un registro con valor correcto pero 1.000 veces duplicado en energía).

```sql
-- Sum checks diarios sobre gold_fact_energy_forecast
SELECT
    c.client_id,
    c.name,
    c.pv_peak_power_kw,

    -- Generación diaria total (kWh)
    ROUND(SUM(f.pv_power_gen_kw), 2)                              AS kwh_generados_dia,

    -- Máximo esperado físicamente: pico × 8h equivalentes sol
    ROUND(c.pv_peak_power_kw * 8, 2)                             AS kwh_maximo_fisico,

    -- Flag: ¿generación supera el máximo físico plausible?
    CASE WHEN SUM(f.pv_power_gen_kw) > c.pv_peak_power_kw * 8
         THEN '❌ SUPERA MÁXIMO FÍSICO'
         ELSE '✅ OK' END                                          AS check_generacion,

    -- Consumo diario total (kWh)
    ROUND(SUM(f.power_consumption_kw), 2)                         AS kwh_consumidos_dia,

    -- Coste diario total (€) — sólo si precios disponibles
    ROUND(SUM(
        CASE WHEN f.price_pvpc_eur_mwh IS NOT NULL
             THEN (f.power_consumption_kw / 1000.0) * f.price_pvpc_eur_mwh
             ELSE 0 END
    ), 4)                                                          AS coste_red_eur_dia,

    -- Ahorro PV diario (€)
    ROUND(SUM(
        CASE WHEN f.price_pvpc_eur_mwh IS NOT NULL
             THEN (f.pv_power_gen_kw / 1000.0) * f.price_pvpc_eur_mwh
             ELSE 0 END
    ), 4)                                                          AS ahorro_pv_eur_dia,

    -- PR medio del día (sólo horas diurnas)
    ROUND(AVG(CASE WHEN f.pv_power_gen_kw > 0
                   THEN f.pv_performance_ratio END), 4)            AS pr_medio_diurno,

    -- Flag: ¿PR medio razonable?
    CASE WHEN AVG(CASE WHEN f.pv_power_gen_kw > 0
                       THEN f.pv_performance_ratio END) BETWEEN 0.5 AND 0.95
         THEN '✅ OK'
         ELSE '⚠️ PR ANÓMALO' END                                  AS check_pr

FROM gold_fact_energy_forecast f
JOIN gold_dim_client c ON f.client_id = c.client_id
JOIN gold_dim_datetime d ON f.unix_time = d.unix_time
WHERE d.date = date('now', '+1 day')   -- verificar datos de mañana tras carga nocturna
GROUP BY c.client_id, c.name, c.pv_peak_power_kw
ORDER BY c.client_id;
```

**Rangos esperados para los sum checks:**

| Métrica | Rango esperado | Flag si fuera de rango |
|---------|---------------|----------------------|
| Generación diaria / kWp instalado | 2–8 kWh/kWp (según estación) | > 10 kWh/kWp → error de cálculo |
| Performance Ratio medio diurno | 0.55–0.92 | < 0.4 o > 0.95 → revisar parámetros |
| Precio medio PVPC | 20–500 €/MWh | > 1.000 €/MWh → revisar filtro outliers |
| Coste diario por kW nominal | 0.5–15 €/kW | > 50 €/kW → error de escala en precios |

---

### 6.3 Registro de Auditoría

El sistema mantiene tres niveles de registro de auditoría:

**Nivel 1 — Registro de ejecución (`etl_metadata`):**

```sql
-- Historial de los últimos 30 días con clasificación de calidad
SELECT
    id,
    executed_at,
    status,
    duration_seconds,
    rows_affected,
    error_message,
    CASE
        WHEN status = 'SUCCESS'          THEN '✅'
        WHEN status = 'PARTIAL SUCCESS'  THEN '⚠️'
        WHEN status LIKE 'FAILED%'       THEN '❌'
        ELSE '🔴'
    END                         AS icono_estado
FROM etl_metadata
ORDER BY executed_at DESC
LIMIT 30;
```

**Nivel 2 — Trazabilidad de ficheros Bronze (manifests):**  
Cada fichero Bronze tiene su historia completa en `_process_manifest_*.json`:

```json
{
    "source": "REE",
    "path": "/data/bronze/prices_20260510_203500.json",
    "status": "success",
    "created_at": "2026-05-10 20:35:00",
    "updated_at": "2026-05-10 20:35:12"
}
```

**Nivel 3 — Trazabilidad de registros Silver (`_source_file`, `_ingested_at_utc`):**  
Cada registro en `clean_clients` y `clean_weather` lleva el nombre del fichero Bronze del que procede y el timestamp de su carga a Silver, permitiendo trazar cualquier dato Gold hasta su fichero Bronze original.

```sql
-- Trazar el origen de un registro específico en Gold hasta Bronze
SELECT
    f.client_id,
    f.unix_time,
    f.pv_power_gen_kw,
    c._source_file          AS bronze_clients_origen,
    c._ingested_at_utc      AS clients_cargado_en,
    w._source_file          AS bronze_weather_origen,
    w._ingested_at_utc      AS weather_cargado_en,
    f._loaded_at_utc        AS fact_cargado_en
FROM gold_fact_energy_forecast f
JOIN clean_calculations calc
    ON calc.client_id = f.client_id AND calc.unix_time = f.unix_time
JOIN clean_clients c
    ON c.client_id = f.client_id
JOIN clean_weather w
    ON w.client_id = f.client_id AND w.unix_time = f.unix_time
WHERE f.client_id = 'C001'
  AND f.unix_time = 1746874800;
```

---

## 7. Proceso de Remediación

### 7.1 Flujo de Trabajo para Datos Erróneos

```
DETECCIÓN DEL ERROR
        │
        ▼
¿El error afecta a datos ya consumidos por decisiones de negocio?
        │
   Sí ──┼── No
        │        │
        ▼        ▼
  Notificación  Continuar
  inmediata     flujo normal
  a Negocio
        │
        ▼
CLASIFICACIÓN DEL ERROR
  ├─ Error en fuente externa (REE / OWM)  → Esperar re-publicación o usar valor anterior
  ├─ Error en fichero Excel de clientes   → Corregir Excel + re-ingestar desde Bronze
  ├─ Bug en módulo Silver/Gold            → Hotfix en código + re-procesar desde Bronze
  └─ Corrupción en Bronze                 → Restaurar desde backup + re-procesar
        │
        ▼
REMEDIACIÓN TÉCNICA
  1. Identificar el fichero Bronze afectado (via manifest + _source_file)
  2. Cambiar status en manifest a 'error' o 'pending' según el caso
  3. Aplicar la corrección (código, datos fuente, etc.)
  4. Re-ejecutar pipeline desde el stage afectado:
     python src/pipeline_runner.py --stage N
  5. Verificar reconciliación y quality scores
  6. Notificar resolución
        │
        ▼
VERIFICACIÓN POST-REMEDIACIÓN
  □ Row counts coinciden con los esperados
  □ Sum checks dentro de rangos físicos
  □ Quality Score ≥ umbral mínimo de la tabla
  □ etl_metadata.status = 'SUCCESS'
  □ Sin registros huérfanos en Gold
```

**Comandos de remediación por tipo de error:**

```bash
# Error en precios REE — re-procesar desde Silver
python src/pipeline_runner.py --stage 2

# Error en meteorología de un cliente específico
# 1. Editar manifest: cambiar status de los tasks del cliente a 'pending'
# 2. Re-procesar desde Silver-weather
python src/pipeline_runner.py --stage 4

# Error en cálculos PV (bug en engine_pv_physics.py)
# 1. Aplicar hotfix en engine_pv_physics.py
# 2. Re-calcular desde Stage 5
python src/pipeline_runner.py --stage 5

# Reconstrucción completa de Gold desde Silver íntegra
python src/pipeline_runner.py --stage 6

# Reconstrucción completa del pipeline
python src/pipeline_runner.py --stage 1
```

---

### 7.2 Política de Backfill tras Corrección

El sistema está diseñado para que **cualquier re-ejecución sea idempotente** gracias al uso de `INSERT OR REPLACE` en Silver y Gold. Esto simplifica enormemente la política de backfill.

| Escenario | Política de backfill | Comando |
|-----------|---------------------|---------|
| Corrección de precio PVPC (REE publica corrección) | Re-procesar `clean_prices` + re-cargar `gold_fact` | `--stage 2` |
| Corrección de parámetros de cliente en Excel | Re-ingestar Excel + re-procesar todo el pipeline | `--stage 1` |
| Corrección de bug en motor PV | Re-calcular `clean_calculations` + re-cargar `gold_fact` | `--stage 5` |
| Añadir un nuevo cliente | Re-ingestar Excel + pipeline completo | `--stage 1` |
| Corrección de lógica tarifaria | Re-generar `gold_dim_datetime` + re-cargar `gold_fact` | `--stage 6` |

**Garantía de idempotencia por tabla:**

| Tabla | Mecanismo de idempotencia |
|-------|--------------------------|
| `clean_clients` | `DROP TABLE + CREATE + INSERT` — full rebuild siempre consistente |
| `clean_weather` | `INSERT OR REPLACE` por `(client_id, unix_time)` |
| `clean_prices` | `INSERT OR REPLACE` por `(datetime_utc, price_type)` |
| `clean_calculations` | `INSERT OR REPLACE` por `(client_id, unix_time)` |
| `gold_dim_*` | `DROP TABLE + CREATE + INSERT` — full rebuild |
| `gold_fact_energy_forecast` | `INSERT OR REPLACE` por `(client_id, unix_time)` |

> **Nota importante:** el backfill de datos históricos (más allá de la ventana activa de 5 días) requiere una extensión del pipeline no implementada actualmente. La arquitectura lo soporta — basta con eliminar el filtro `WHERE unix_time >= now` en `silver_calc_pv_generation.py` y `gold_fact_energy_forecast.py` — pero el volumen de datos y el tiempo de ejecución aumentan proporcionalmente.

---

### 7.3 Post-Mortem de Incidencias de Calidad

Toda incidencia de calidad con severidad `HIGH` o `CRITICAL` debe documentarse con un post-mortem en un plazo máximo de **48 horas** tras la resolución. La plantilla estándar es:

```markdown
## Post-Mortem: [ID de incidencia] — [Descripción breve]

**Fecha de detección:** YYYY-MM-DD HH:MM UTC
**Fecha de resolución:** YYYY-MM-DD HH:MM UTC
**Duración del impacto:** Xh Ymin
**Severidad:** CRITICAL / HIGH
**Pipeline run afectado:** etl_metadata.id = N

### Resumen ejecutivo
[2-3 frases describiendo qué pasó, cuánto tiempo duró y cómo se resolvió]

### Cronología
- HH:MM — Evento desencadenante
- HH:MM — Detección (manual / alerta automática)
- HH:MM — Inicio de investigación
- HH:MM — Causa raíz identificada
- HH:MM — Fix aplicado
- HH:MM — Verificación completada
- HH:MM — Incidencia cerrada

### Causa raíz
[Descripción técnica detallada de la causa]

### Impacto
- Tablas afectadas: [lista]
- Registros incorrectos: [N registros en tabla X]
- Decisiones de negocio impactadas: [Sí/No — descripción si Sí]
- Quality Score durante el incidente: [X%]

### Acciones de remediación tomadas
1. [Acción 1]
2. [Acción 2]

### Acciones preventivas (para evitar recurrencia)
| Acción | Responsable | Fecha límite |
|--------|-------------|-------------|
| [Acción] | [Equipo] | [Fecha] |

### Lecciones aprendidas
[Qué funcionó bien, qué no, qué cambiaríamos]
```

**Repositorio de post-mortems:**  
Los post-mortems se almacenan en `docs/post-mortems/YYYY-MM-DD_[descripcion].md` y se versiona en Git junto con el código del pipeline. Esto construye una **memoria institucional de calidad** que acelera la resolución de incidencias similares futuras.

---

*SunSaver ETL · Framework de Calidad del Dato v1.0.0 · Mayo 2026*  
*Clasificación: INTERNA · No distribuir fuera del equipo sin autorización*