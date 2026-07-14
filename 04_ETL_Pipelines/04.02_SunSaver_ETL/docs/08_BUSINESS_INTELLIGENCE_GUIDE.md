# ☀️ SunSaver ETL · Plataforma de Inteligencia Energética Industrial
## 08 Guía de Business Intelligence

> **Clasificación:** INTERNA &nbsp;|&nbsp; **Estado:** ACTIVO &nbsp;|&nbsp; **Audiencia:** Analistas, Científicos de datos, Dirección, Operaciones  
> **Propietario:** Equipo de Datos — SunSaver &nbsp;|&nbsp; **Última actualización:** 2026-05-13

---

## Tabla de Contenidos

1. [Propósito del Sistema de Información](#1-propósito-del-sistema-de-información)
   - 1.1 [Casos de Uso de Toma de Decisiones](#11-casos-de-uso-de-toma-de-decisiones-cubiertos)
   - 1.2 [Dominios de Negocio](#12-dominios-de-negocio)
   - 1.3 [Usuarios Objetivo y sus Preguntas Clave](#13-usuarios-objetivo-y-sus-preguntas-clave)
2. [Semántica de Negocio](#2-semántica-de-negocio)
   - 2.1 [Glosario de Términos de Negocio](#21-glosario-de-términos-de-negocio)
   - 2.2 [Métricas Oficiales de Negocio (KPIs)](#22-métricas-oficiales-de-negocio-kpis)
   - 2.3 [Jerarquías y Perspectivas de Análisis](#23-jerarquías-y-perspectivas-de-análisis)
3. [Catálogo de Análisis](#3-catálogo-de-análisis)
   - 3.1 [Análisis de Rendimiento del Parque PV](#31-análisis-de-rendimiento-del-parque-pv)
   - 3.2 [Análisis Económico y de Costes](#32-análisis-económico-y-de-costes)
   - 3.3 [Análisis de Correlación Industrial-Económico](#33-análisis-de-correlación-industrial--económico)
   - 3.4 [Reporting Ejecutivo Periódico](#34-reporting-ejecutivo-periódico)
4. [Guía de Consumo de Datos](#4-guía-de-consumo-de-datos)
   - 4.1 [Cómo Conectar una Herramienta BI](#41-cómo-conectar-una-herramienta-bi)
   - 4.2 [Tablas Recomendadas por Tipo de Análisis](#42-tablas-recomendadas-por-tipo-de-análisis)
   - 4.3 [Tablas a Evitar en Consultas Directas](#43-tablas-a-evitar-en-consultas-directas)
   - 4.4 [Buenas Prácticas de Performance](#44-buenas-prácticas-de-performance)
   - 4.5 [Política de Acceso por Rol](#45-política-de-acceso-por-rol)
5. [Freshness y Confianza en el Dato](#5-freshness-y-confianza-en-el-dato)
   - 5.1 [Frecuencia de Actualización por Tabla Gold](#51-frecuencia-de-actualización-por-tabla-gold)
   - 5.2 [Cómo Interpretar los Timestamps de Actualización](#52-cómo-interpretar-los-timestamps-de-actualización)
   - 5.3 [Cuándo un Dato Puede Estar Incompleto](#53-cuándo-un-dato-puede-estar-incompleto)
   - 5.4 [Cómo Reportar Anomalías en el Dato](#54-cómo-reportar-anomalías-en-el-dato)
6. [Casos de Decisión Documentados](#6-casos-de-decisión-documentados)
   - 6.1 [Plantilla de Caso de Decisión](#61-plantilla-de-caso-de-decisión)
   - 6.2 [Ejemplos de Decisiones con el Sistema](#62-ejemplos-de-decisiones-tomadas-con-el-sistema)
   - 6.3 [Impacto Medido de las Decisiones](#63-impacto-medido-de-las-decisiones)
7. [Roadmap Analítico](#7-roadmap-analítico)
   - 7.1 [Nuevas Fuentes de Datos Previstas](#71-nuevas-fuentes-de-datos-previstas)
   - 7.2 [Métricas en Desarrollo](#72-métricas-en-desarrollo)
   - 7.3 [Integraciones BI Planificadas](#73-integraciones-bi-planificadas)

---

## 1. Propósito del Sistema de Información

SunSaver no es un sistema de monitorización. Es un **sistema de soporte a la decisión energética industrial**: integra física, meteorología y economía para responder, hora a hora y con 5 días de antelación, una pregunta que tiene impacto directo en la cuenta de resultados de cada instalación industrial:

> *"Dado lo que sé sobre el sol, el tiempo y el precio de la luz de las próximas 120 horas — ¿cuándo debo arrancar mis máquinas, cuándo cargar mis baterías y cuándo es mejor comprar energía de la red?"*

---

### 1.1 Casos de Uso de Toma de Decisiones Cubiertos

| # | Caso de uso | Horizonte temporal | Impacto económico directo |
|---|-------------|-------------------|--------------------------|
| CU-01 | **Programación del arranque de maquinaria pesada** | Próximas 24–48h | Reducción del coste de arranque eligiendo horas con alta generación PV y precio bajo |
| CU-02 | **Carga óptima de baterías** | Próximas 5–24h | Cargar en excedente PV + valle tarifario; descargar en punta tarifaria |
| CU-03 | **Gestión de cargas flexibles** (diferimiento) | Próximas 5 días | Mover consumos no urgentes a ventanas de menor precio neto |
| CU-04 | **Seguimiento del rendimiento del parque PV** | Diario / semanal | Detectar degradación o fallos que reducen la generación esperada |
| CU-05 | **Cálculo del retorno de inversión (ROI)** | Mensual / anual | Validar la rentabilidad de la inversión PV con datos reales |
| CU-06 | **Reporting de autosuficiencia energética** | Mensual | Seguimiento del porcentaje de consumo cubierto por generación propia |
| CU-07 | **Comparativa entre instalaciones** | Semanal / mensual | Benchmarking interno — identificar best practices entre plantas |

---

### 1.2 Dominios de Negocio

El sistema de información de SunSaver opera en la intersección de dos dominios:

**Dominio Industrial — Físico:**
El parque fotovoltaico es un activo industrial con un rendimiento calculable a partir de la física. Los datos de este dominio responden a *"¿cuánta energía genera mi instalación?"* y se expresan en vatios, kilovatios-hora, grados Celsius y metros cuadrados.

**Dominio Económico — Mercado eléctrico:**
La electricidad tiene un precio que varía hora a hora en el mercado PVPC español. Los datos de este dominio responden a *"¿cuánto vale esa energía?"* y se expresan en euros y euros por megavatio-hora.

**La intersección — Decisión:**
El valor del sistema está precisamente en cruzar ambos dominios: saber simultáneamente *cuánta energía* habrá disponible *y a qué precio* permite optimizar el consumo de una forma que ninguno de los dos dominios por separado haría posible.

```
  DOMINIO INDUSTRIAL           INTERSECCIÓN              DOMINIO ECONÓMICO
  ─────────────────────        ─────────────────────     ─────────────────────
  Irradiancia solar (W/m²)  →  Balance energético (kW) ← Precio PVPC (€/MWh)
  Temperatura de célula (°C)→  Coste neto horario (€)  ← Período tarifario
  Nubosidad (%)             →  Ahorro PV (€/hora)      ← Tarifas 3.0TD
  Performance Ratio         →  ROI (años)              ← Inversión (€)
  Consumo industrial (kW)   →  Tasa de autosuficiencia ← Coste de red (€)
```

---

### 1.3 Usuarios Objetivo y sus Preguntas Clave

| Perfil | Rol en la organización | Preguntas clave | Frecuencia de uso |
|--------|----------------------|-----------------|------------------|
| **Responsable de planta** | Operaciones industriales | ¿Cuándo arranco el turno de noche? ¿Cuándo cargo las baterías hoy? ¿Qué horas debo evitar para el compresor? | Diaria (mañana) |
| **Director de operaciones** | Dirección media | ¿Cuánto ahorramos esta semana? ¿Cuál de nuestras plantas rinde peor? ¿Vamos a cumplir el objetivo de autosuficiencia del trimestre? | Semanal |
| **Director financiero / CFO** | Dirección ejecutiva | ¿Cuándo recuperamos la inversión en los paneles? ¿Cuánto ahorramos al año versus no tener PV? ¿Es rentable ampliar la instalación? | Mensual / trimestral |
| **Analista de datos / Data Scientist** | Equipo técnico | ¿El modelo de consumo está calibrado? ¿La correlación entre nubosidad y generación sigue el patrón esperado? ¿Hay drift en el Performance Ratio? | Ad-hoc / semanal |
| **Gestor de energía** | Especialista técnico | ¿Cuál es el precio medio ponderado que pagamos? ¿Cuánta energía tomamos en período punta P1? ¿Qué porcentaje de nuestra demanda cubrimos con renovable propio? | Diaria / semanal |

---

## 2. Semántica de Negocio

### 2.1 Glosario de Términos de Negocio

| Término | Definición de negocio | Tabla Gold | Campo | Notas |
|---------|----------------------|-----------|-------|-------|
| **Potencia generada** | Energía eléctrica producida por el parque fotovoltaico en un slot horario. Expresada en kilovatios (kW). | `gold_fact_energy_forecast` | `pv_power_gen_kw` | Para obtener energía (kWh), multiplicar por 1 hora |
| **Consumo industrial** | Demanda eléctrica de la instalación en un slot horario, modelada a partir del perfil de turnos, la carga HVAC y la variabilidad del proceso. | `gold_fact_energy_forecast` | `power_consumption_kw` | Consumo simulado basado en `nominal_load_kw` de la instalación |
| **Balance energético neto** | Diferencia entre generación y consumo. Positivo = excedente (candidato a almacenar o verter). Negativo = déficit (hay que comprar de red). | Calculado | `pv_power_gen_kw - power_consumption_kw` | Campo derivado — no almacenado |
| **Precio PVPC** | Precio del kilovatio-hora en el mercado español de Precio Voluntario al Pequeño Consumidor para esa hora. Publicado por REE el día anterior. | `gold_fact_energy_forecast` | `price_pvpc_eur_mwh` | En €/MWh. Para €/kWh dividir entre 1.000. Puede ser NULL si REE no ha publicado aún |
| **Período tarifario** | Clasificación de cada hora del día en uno de los cuatro tramos de la tarifa de acceso 3.0TD española: P1 (punta), P2 (llano), P3 (valle), P6 (super-valle). Determina el precio del peaje de red. | `gold_dim_datetime` | `tariff_period`, `tariff_label` | P6 aplica sábados, domingos y festivos nacionales |
| **Performance Ratio (PR)** | Eficiencia global del sistema PV: cociente entre la energía real generada y la que generaría un sistema ideal en las mismas condiciones de irradiancia. Incluye pérdidas térmicas, de cableado, inversor y suciedad. | `gold_fact_energy_forecast` | `pv_performance_ratio` | Adimensional [0–1]. Un PR de 0.82 significa que el sistema opera al 82% de su potencial teórico |
| **Irradiancia POA** | Potencia solar por unidad de área que incide sobre el plano de los paneles. Base del cálculo de generación. | `gold_fact_energy_forecast` | `poa_wm2` | En W/m². La irradiancia de referencia STC es 1.000 W/m² |
| **Temperatura de célula** | Temperatura operativa de la célula solar. Por encima de 25°C cada grado adicional reduce la potencia un 0,4% (derating térmico). | `gold_fact_energy_forecast` | `t_cell_celsius` | Calculada con el modelo Faiman |
| **Potencia pico (kWp)** | Potencia máxima que generaría el parque fotovoltaico en condiciones estándar de prueba (STC: 1.000 W/m², 25°C). Parámetro de diseño del sistema. | `gold_dim_client` | `pv_peak_power_kw` | La generación real siempre es inferior por condiciones reales de operación |
| **Factor de capacidad** | Fracción de la energía teórica máxima (generación continua a plena potencia) que realmente se produce. Mide el rendimiento global de la ubicación. | Calculado | `SUM(gen_kw) / (peak_kw × horas)` | En España peninsular, 15–20% anual es típico para instalaciones fijas |
| **Tasa de autosuficiencia** | Porcentaje del consumo total cubierto por generación fotovoltaica propia. | Calculado | `MIN(gen, con) / consumo` | El 100% significa cero dependencia de red en ese período |
| **Tasa de autoconsumo** | Porcentaje de la generación propia que es consumida directamente (sin excedentes). | Calculado | `MIN(gen, con) / generación` | Alta tasa de autoconsumo = buena dimensión del sistema PV respecto al consumo |
| **Ahorro PV** | Valor económico de la energía autoconsumida, calculado al precio de mercado que se habría pagado si esa energía hubiera venido de red. | Calculado | `(MIN(gen, con) / 1000) × precio` | En €. Es el ahorro directo de factura eléctrica atribuible al parque PV |
| **Coste neto** | Coste de la energía tomada de red (consumo menos generación propia). Si la generación supera el consumo, el coste neto es cero (no negativo — no se cobra por verter en el modelo actual). | Calculado | `(MAX(0, con - gen) / 1000) × precio` | En €/hora |
| **Período de retorno (Payback)** | Tiempo en años necesario para recuperar la inversión inicial en la instalación PV a través de los ahorros acumulados. | Calculado | `inversión / ahorro_anual_proyectado` | En años. Un payback < 8 años es generalmente considerado rentable en el sector |
| **Horas equivalentes de sol** | Número de horas que el sistema tendría que operar a plena potencia pico para producir la misma energía que realmente produjo. | Calculado | `SUM(gen_kw) / peak_kw` | En h/día. Media anual en España peninsular: 4–5 h/día |
| **Slot horario** | Unidad mínima de tiempo del sistema: una hora identificada por su timestamp UTC en formato EPOCH. Toda la información del sistema se organiza en slots horarios. | `gold_dim_datetime` | `unix_time` | Resolución 1 hora. 120 slots = 5 días de previsión |

---

### 2.2 Métricas Oficiales de Negocio (KPIs)

| KPI | Descripción de negocio | Fórmula | Unidad | Frecuencia | Propietario |
|-----|----------------------|---------|--------|-----------|-------------|
| **Energía generada** | Total de energía fotovoltaica producida en el período | `SUM(pv_power_gen_kw × 1h)` | kWh | Diaria / mensual | Operaciones |
| **Energía consumida** | Total de energía demandada por la instalación | `SUM(power_consumption_kw × 1h)` | kWh | Diaria / mensual | Operaciones |
| **Tasa de autosuficiencia** | Fracción del consumo cubierta por generación propia | `SUM(MIN(gen,con)) / SUM(con)` | % | Diaria / mensual | Dirección |
| **Ahorro total PV** | Euros ahorrados en factura eléctrica gracias a la generación propia | `SUM(MIN(gen,con)/1000 × precio)` | € | Diaria / mensual | Finanzas |
| **Coste eléctrico real** | Gasto real en energía de red tras descontar generación propia | `SUM(MAX(0,con-gen)/1000 × precio)` | € | Diaria / mensual | Finanzas |
| **Performance Ratio medio** | Eficiencia media del sistema PV en horas de generación activa | `AVG(PR) WHERE gen > 0` | adim. [0–1] | Semanal | Mantenimiento |
| **Factor de capacidad** | Rendimiento de la ubicación respecto al máximo teórico | `SUM(gen) / (peak_kw × n_horas)` | % | Mensual | Operaciones |
| **Horas equivalentes de sol** | Producción diaria referenciada a potencia pico | `SUM(gen_día) / peak_kw` | h/día | Diaria | Operaciones |
| **Período de retorno** | Años hasta recuperar la inversión | `inversión / ahorro_anual` | años | Trimestral | Dirección / Finanzas |
| **Coste medio ponderado** | Precio efectivo pagado por la energía de red, ponderado por consumo | `SUM(con × precio) / SUM(con) / 1000` | €/MWh | Mensual | Finanzas |
| **Exposición en período P1** | Porcentaje del coste total incurrido en el período punta | `coste_P1 / coste_total` | % | Mensual | Gestor energía |

---

### 2.3 Jerarquías y Perspectivas de Análisis

#### Perspectiva Temporal

```
Año (year)
  └── Mes (month)
        └── Semana del año
              └── Día (date)
                    ├── Tipo de día (laborable / fin de semana / festivo)
                    ├── Período tarifario (P1 / P2 / P3 / P6)
                    └── Slot horario (unix_time) — granularidad mínima

Drill-down típico: Año → Mes → Día → Hora (para análisis de costes)
Drill-down típico: Año → Mes → Tipo de día (para análisis de consumo laboral vs fin de semana)
```

#### Perspectiva Geográfica / De Instalación

```
Flota completa (todas las instalaciones)
  └── Instalación / Planta (client_id, name)
        ├── Tipo de instalación (has_solar / has_battery)
        ├── Rango de potencia (< 10 kWp / 10–50 kWp / > 50 kWp)
        └── Slot horario — granularidad mínima

Drill-down típico: Flota → Región geográfica → Planta → Hora
```

#### Perspectiva de Activo Industrial

```
Sistema energético de la instalación
  ├── Parque fotovoltaico
  │     ├── Tecnología (panel_type: monoSi / polySi / bifacial)
  │     ├── Tipo de montaje (mounting: rooftop / ground / tracker)
  │     └── Rango de eficiencia (efficiency)
  └── Sistema de almacenamiento
        ├── Con batería (has_battery = 1)
        └── Sin batería (has_battery = 0)
```

#### Perspectiva Económica / Tarifaria

```
Estructura de costes energéticos
  └── Período tarifario (P1 / P2 / P3 / P6)
        ├── Coste de peaje de red (proporcional al período)
        ├── Precio PVPC del mercado (varía hora a hora)
        └── Coste neto (precio × energía de red consumida)

Segmentación económica típica:
  — Horas de punta P1: exposición máxima al coste — prioritarias para batería / PV
  — Horas de valle P3/P6: óptimas para cargar baterías y ejecutar cargas deferibles
```

---

## 3. Catálogo de Análisis

### 3.1 Análisis de Rendimiento del Parque PV

#### 3.1.1 Nombre y Descripción

**Análisis de rendimiento fotovoltaico diario** — Seguimiento del comportamiento real del parque PV frente a las condiciones meteorológicas previstas. Permite detectar degradación del sistema, suciedad de paneles, sombreado no previsto o fallos parciales de inversores antes de que tengan impacto económico significativo.

#### 3.1.2 Pregunta de Negocio que Responde

- *"¿Está generando mi instalación lo que debería según el tiempo que hace?"*
- *"¿Ha empeorado el rendimiento de mis paneles respecto al mes pasado?"*
- *"¿En qué horas del día pierdo más generación por las nubes?"*

#### 3.1.3 Tablas Gold Utilizadas

`gold_fact_energy_forecast` + `gold_dim_client` + `gold_dim_datetime` + `gold_dim_weather`

#### 3.1.4 Filtros y Dimensiones Típicos

- **Tiempo:** rango de fechas (últimos 7 / 30 / 90 días), sólo horas diurnas (`is_daylight = 1`)
- **Instalación:** por `client_id` para análisis individual; todas para benchmarking
- **Condición meteorológica:** por `weather_main` para comparar PR en cielo despejado vs nublado

#### 3.1.5 Métricas Involucradas

Performance Ratio medio, energía generada, horas equivalentes de sol, irradiancia POA media, temperatura de célula media, factor de capacidad.

#### 3.1.6 Query de Referencia

```sql
-- Análisis de rendimiento PV semanal por instalación
-- Comparativa entre semanas para detectar tendencias de degradación
SELECT
    d.year                                                          AS año,
    strftime('%W', d.date)                                         AS semana_año,
    c.client_id,
    c.name                                                          AS instalacion,
    c.pv_peak_power_kw                                             AS potencia_pico_kwp,
    c.panel_type,

    -- Producción
    ROUND(SUM(f.pv_power_gen_kw), 1)                               AS kwh_generados,
    ROUND(SUM(f.pv_power_gen_kw) / c.pv_peak_power_kw, 2)         AS horas_sol_equiv,

    -- Eficiencia del sistema
    ROUND(AVG(CASE WHEN f.pv_power_gen_kw > 0
                   THEN f.pv_performance_ratio END), 3)             AS pr_medio,
    ROUND(MIN(CASE WHEN f.pv_power_gen_kw > 0
                   THEN f.pv_performance_ratio END), 3)             AS pr_minimo,

    -- Condiciones ambientales
    ROUND(AVG(CASE WHEN f.pv_power_gen_kw > 0
                   THEN f.poa_wm2 END), 1)                         AS irradiancia_poa_media,
    ROUND(AVG(CASE WHEN f.pv_power_gen_kw > 0
                   THEN f.t_cell_celsius END), 1)                   AS temp_celula_media,
    ROUND(AVG(CASE WHEN d.is_daylight = 1
                   THEN f.clouds_pct END), 1)                       AS nubosidad_media_pct,

    -- Semáforo de rendimiento
    CASE
        WHEN AVG(CASE WHEN f.pv_power_gen_kw > 0
                      THEN f.pv_performance_ratio END) >= 0.80     THEN '🟢 Óptimo'
        WHEN AVG(CASE WHEN f.pv_power_gen_kw > 0
                      THEN f.pv_performance_ratio END) >= 0.70     THEN '🟡 Aceptable'
        ELSE                                                            '🔴 Revisar'
    END                                                             AS estado_rendimiento

FROM gold_fact_energy_forecast f
JOIN gold_dim_client   c ON f.client_id = c.client_id
JOIN gold_dim_datetime d ON f.unix_time  = d.unix_time
WHERE d.date BETWEEN date('now','-28 days') AND date('now')
  AND d.is_daylight = 1
GROUP BY d.year, strftime('%W', d.date), c.client_id, c.name, c.pv_peak_power_kw, c.panel_type
ORDER BY c.client_id, semana_año DESC;
```

---

### 3.2 Análisis Económico y de Costes

#### 3.2.1 Nombre y Descripción

**Dashboard económico de la instalación** — Cuantifica en euros el valor generado por el parque fotovoltaico y el coste real de la energía que sigue comprando a red. Proporciona la base para el cálculo del ROI y la justificación de ampliaciones.

#### 3.2.2 Pregunta de Negocio que Responde

- *"¿Cuánto dinero nos ahorra el parque solar cada mes?"*
- *"¿Cuándo recuperamos la inversión?"*
- *"¿En qué horas concentramos el mayor gasto eléctrico?"*
- *"¿Vale la pena ampliar la instalación o instalar baterías?"*

#### 3.2.3 Tablas Gold Utilizadas

`gold_fact_energy_forecast` + `gold_dim_client` + `gold_dim_datetime`

#### 3.2.4 Query de Referencia

```sql
-- Análisis económico mensual por instalación
-- KPIs de coste, ahorro y rentabilidad de la inversión PV
SELECT
    d.year                                                                   AS año,
    d.month                                                                  AS mes,
    c.client_id,
    c.name                                                                   AS instalacion,
    c.pv_peak_power_kw,
    c.installation_cost_eur,

    -- Energías
    ROUND(SUM(f.pv_power_gen_kw), 1)                                        AS kwh_generados,
    ROUND(SUM(f.power_consumption_kw), 1)                                   AS kwh_consumidos,
    ROUND(SUM(MIN(f.pv_power_gen_kw, f.power_consumption_kw)), 1)           AS kwh_autoconsumidos,
    ROUND(SUM(MAX(0, f.pv_power_gen_kw - f.power_consumption_kw)), 1)       AS kwh_excedente,

    -- Tasas de autosuficiencia / autoconsumo
    ROUND(100.0 * SUM(MIN(f.pv_power_gen_kw, f.power_consumption_kw))
          / NULLIF(SUM(f.power_consumption_kw), 0), 1)                      AS tasa_autosuficiencia_pct,
    ROUND(100.0 * SUM(MIN(f.pv_power_gen_kw, f.power_consumption_kw))
          / NULLIF(SUM(f.pv_power_gen_kw), 0), 1)                           AS tasa_autoconsumo_pct,

    -- Costes y ahorros (sólo con precio disponible)
    ROUND(SUM(CASE WHEN f.price_pvpc_eur_mwh IS NOT NULL
                   THEN (f.power_consumption_kw / 1000.0) * f.price_pvpc_eur_mwh END), 2)
                                                                             AS coste_sin_pv_eur,
    ROUND(SUM(CASE WHEN f.price_pvpc_eur_mwh IS NOT NULL
                   THEN (MAX(0, f.power_consumption_kw - f.pv_power_gen_kw)
                        / 1000.0) * f.price_pvpc_eur_mwh END), 2)           AS coste_real_eur,
    ROUND(SUM(CASE WHEN f.price_pvpc_eur_mwh IS NOT NULL
                   THEN (MIN(f.pv_power_gen_kw, f.power_consumption_kw)
                        / 1000.0) * f.price_pvpc_eur_mwh END), 2)           AS ahorro_pv_eur,

    -- Precio medio ponderado por consumo de red
    ROUND(SUM(CASE WHEN f.price_pvpc_eur_mwh IS NOT NULL
                   THEN MAX(0, f.power_consumption_kw - f.pv_power_gen_kw)
                        * f.price_pvpc_eur_mwh END)
          / NULLIF(SUM(CASE WHEN f.price_pvpc_eur_mwh IS NOT NULL
                            THEN MAX(0, f.power_consumption_kw - f.pv_power_gen_kw)
                            END), 0) / 1000, 2)                             AS precio_medio_ponderado_eur_mwh

FROM gold_fact_energy_forecast f
JOIN gold_dim_client   c ON f.client_id = c.client_id
JOIN gold_dim_datetime d ON f.unix_time  = d.unix_time
WHERE d.date BETWEEN date('now', '-90 days') AND date('now')
GROUP BY d.year, d.month, c.client_id, c.name, c.pv_peak_power_kw, c.installation_cost_eur
ORDER BY c.client_id, año DESC, mes DESC;
```

---

### 3.3 Análisis de Correlación Industrial–Económico

#### 3.3.1 Nombre y Descripción

**Análisis de correlación entre condición meteorológica, generación PV y coste energético** — Identifica patrones entre el tipo de tiempo, la producción del parque y el impacto económico. Responde a preguntas del tipo: *"¿Cuánto más caro es un día nublado que uno soleado?"*

#### 3.3.2 Pregunta de Negocio que Responde

- *"¿Cuánto impacta la nubosidad en mi factura eléctrica?"*
- *"¿Qué tipo de tiempo es el más costoso para nuestra planta?"*
- *"¿Cuándo coinciden los peores días de generación con los precios más altos?"* (riesgo de doble penalización)

#### 3.3.3 Query de Referencia

```sql
-- Correlación entre condición meteorológica, generación PV y coste
-- Permite identificar los escenarios de mayor riesgo económico
SELECT
    w.weather_main                                                       AS condicion,
    w.weather_description                                                AS descripcion,
    COUNT(*)                                                             AS n_slots_diurnos,

    -- Impacto en generación
    ROUND(AVG(f.poa_wm2), 0)                                            AS irradiancia_media_wm2,
    ROUND(AVG(f.pv_power_gen_kw), 2)                                    AS generacion_media_kw,
    ROUND(AVG(f.clouds_pct), 0)                                         AS nubosidad_media_pct,

    -- Impacto en balance y coste
    ROUND(AVG(f.pv_power_gen_kw - f.power_consumption_kw), 2)           AS balance_medio_kw,
    ROUND(AVG(CASE WHEN f.price_pvpc_eur_mwh IS NOT NULL
                   THEN MAX(0, f.power_consumption_kw - f.pv_power_gen_kw)
                        / 1000.0 * f.price_pvpc_eur_mwh END), 4)        AS coste_neto_medio_eur_h,

    -- Comparativa vs cielo despejado (en %)
    ROUND(100.0 * AVG(f.pv_power_gen_kw)
          / NULLIF((SELECT AVG(pv_power_gen_kw)
                   FROM gold_fact_energy_forecast f2
                   JOIN gold_dim_datetime d2 ON f2.unix_time = d2.unix_time
                   JOIN gold_dim_weather  w2 ON f2.weather_id = w2.weather_id
                   WHERE d2.is_daylight = 1 AND w2.weather_main = 'Clear'), 0), 0)
                                                                         AS pct_vs_cielo_despejado

FROM gold_fact_energy_forecast f
JOIN gold_dim_datetime d ON f.unix_time  = d.unix_time
JOIN gold_dim_weather  w ON f.weather_id = w.weather_id
WHERE d.is_daylight = 1
  AND f.client_id   = 'C001'   -- ajustar según la instalación de análisis
GROUP BY w.weather_main, w.weather_description
ORDER BY generacion_media_kw DESC;
```

---

### 3.4 Reporting Ejecutivo Periódico

#### 3.4.1 Nombre y Descripción

**Informe ejecutivo mensual** — Visión consolidada de la flota completa de instalaciones para la dirección. Resume los KPIs de mayor impacto en una sola query: ahorro total, autosuficiencia media, mejor y peor instalación y proyección de ROI.

#### 3.4.2 Pregunta de Negocio que Responde

- *"¿Cómo va nuestra flota este mes respecto al mes anterior?"*
- *"¿Qué instalación genera más valor?"*
- *"¿Cuándo recuperamos la inversión del parque que instalamos en Pamplona?"*

#### 3.4.3 Query de Referencia

```sql
-- INFORME EJECUTIVO MENSUAL — Consolidado de flota
WITH mensual AS (
    SELECT
        c.client_id,
        c.name,
        c.pv_peak_power_kw,
        c.installation_cost_eur,
        c.has_battery,
        SUM(f.pv_power_gen_kw)                                           AS kwh_gen,
        SUM(f.power_consumption_kw)                                      AS kwh_con,
        SUM(MIN(f.pv_power_gen_kw, f.power_consumption_kw))              AS kwh_autocon,
        SUM(CASE WHEN f.price_pvpc_eur_mwh IS NOT NULL
                 THEN (MIN(f.pv_power_gen_kw, f.power_consumption_kw)
                      / 1000.0) * f.price_pvpc_eur_mwh END)              AS ahorro_eur,
        SUM(CASE WHEN f.price_pvpc_eur_mwh IS NOT NULL
                 THEN (MAX(0, f.power_consumption_kw - f.pv_power_gen_kw)
                      / 1000.0) * f.price_pvpc_eur_mwh END)              AS coste_red_eur,
        AVG(CASE WHEN f.pv_power_gen_kw > 0
                 THEN f.pv_performance_ratio END)                        AS pr_medio
    FROM gold_fact_energy_forecast f
    JOIN gold_dim_client   c ON f.client_id = c.client_id
    JOIN gold_dim_datetime d ON f.unix_time  = d.unix_time
    WHERE d.year  = strftime('%Y', 'now')
      AND d.month = strftime('%m', 'now')
    GROUP BY c.client_id, c.name, c.pv_peak_power_kw,
             c.installation_cost_eur, c.has_battery
)
SELECT
    name                                                                 AS instalacion,
    ROUND(kwh_gen, 0)                                                    AS kwh_generados,
    ROUND(kwh_con, 0)                                                    AS kwh_consumidos,
    ROUND(100.0 * kwh_autocon / NULLIF(kwh_con, 0), 1)                   AS autosuficiencia_pct,
    ROUND(ahorro_eur, 0)                                                 AS ahorro_pv_eur,
    ROUND(coste_red_eur, 0)                                              AS coste_red_eur,
    ROUND(pr_medio, 3)                                                   AS performance_ratio,
    ROUND(kwh_gen / pv_peak_power_kw / 30.0, 2)                          AS h_sol_equiv_dia,
    -- Payback proyectado con datos del mes actual anualizado
    ROUND(installation_cost_eur / NULLIF(ahorro_eur * 12, 0), 1)         AS payback_estimado_años,
    CASE WHEN has_battery = 1 THEN '🔋 Con batería' ELSE '— Sin batería' END AS almacenamiento,
    -- Ranking de ahorro
    RANK() OVER (ORDER BY ahorro_eur DESC)                               AS ranking_ahorro
FROM mensual
ORDER BY ahorro_eur DESC;
```

---

## 4. Guía de Consumo de Datos

### 4.1 Cómo Conectar una Herramienta BI

#### Power BI

```
1. Abrir Power BI Desktop
2. Obtener datos → Más → Base de datos → SQLite
   (requiere conector ODBC para SQLite: https://www.sqlite.org/download.html)
3. Ruta del fichero: {PROJECT_ROOT}/data/sunsaver.db
4. Seleccionar las tablas Gold:
   ✅ gold_fact_energy_forecast
   ✅ gold_dim_client
   ✅ gold_dim_datetime
   ✅ gold_dim_weather
5. Importar en modo Import (no DirectQuery — SQLite no soporta DQ)
6. Configurar relaciones en la vista de modelo:
   gold_fact[client_id] → gold_dim_client[client_id]   (muchos a uno)
   gold_fact[unix_time]  → gold_dim_datetime[unix_time] (muchos a uno)
   gold_fact[weather_id] → gold_dim_weather[weather_id] (muchos a uno)
7. Programar actualización: Archivo → Opciones → Actualización de datos
   Frecuencia recomendada: diaria, tras las 22:30 CET
```

#### Apache Superset

```bash
# 1. Instalar driver SQLite (viene incluido en Python)
pip install sqlalchemy

# 2. En Superset: Settings → Database Connections → + Database
#    Seleccionar: SQLite
#    SQLAlchemy URI: sqlite:////ruta/absoluta/data/sunsaver.db

# 3. Crear datasets desde las tablas Gold:
#    Datasets → + Dataset → seleccionar sunsaver.db → gold_fact_energy_forecast
#    Repetir para las tres dimensiones

# 4. Los datasets de dimensiones se usan para filtros y etiquetas
# 5. La tabla de hechos gold_fact_energy_forecast es la base de todos los charts
```

#### Metabase

```
1. Settings → Admin → Databases → Add database
   Tipo: SQLite
   Name: SunSaver Gold
   Filename: /ruta/absoluta/data/sunsaver.db

2. Metabase sincroniza automáticamente las tablas
3. Ocultar tablas Silver (clean_*) desde Admin → Data Model
   Mantener visibles sólo las tablas gold_*
4. Crear métricas personalizadas:
   — "Ahorro PV (€)": SUM((MIN(pv_power_gen_kw, power_consumption_kw) / 1000) × price_pvpc_eur_mwh)
   — "Tasa autosuficiencia": SUM(MIN(gen,con)) / SUM(con) × 100
```

#### DuckDB + Python / Jupyter

```python
# Consultar la BD SunSaver directamente con DuckDB (muy eficiente para análisis)
import duckdb
import pandas as pd

con = duckdb.connect()

# Adjuntar la base de datos SQLite de SunSaver
con.execute("ATTACH 'data/sunsaver.db' AS sunsaver (TYPE sqlite)")

# Consulta directa sobre tablas Gold
df = con.execute("""
    SELECT
        d.date,
        c.name                              AS instalacion,
        d.tariff_label,
        SUM(f.pv_power_gen_kw)              AS kwh_gen,
        SUM(f.power_consumption_kw)         AS kwh_con,
        AVG(f.price_pvpc_eur_mwh)           AS precio_medio_eur_mwh
    FROM sunsaver.gold_fact_energy_forecast f
    JOIN sunsaver.gold_dim_client   c ON f.client_id = c.client_id
    JOIN sunsaver.gold_dim_datetime d ON f.unix_time  = d.unix_time
    WHERE d.date >= date_trunc('month', current_date)
    GROUP BY d.date, c.name, d.tariff_label
    ORDER BY d.date, c.name
""").df()

print(df.head(20))
```

---

### 4.2 Tablas Recomendadas por Tipo de Análisis

| Tipo de análisis | Tabla principal | Dimensiones necesarias | Notas |
|------------------|----------------|----------------------|-------|
| Dashboard operativo diario | `gold_fact_energy_forecast` | `gold_dim_datetime`, `gold_dim_client` | Filtrar `unix_time >= now` |
| Análisis de rendimiento PV | `gold_fact_energy_forecast` | `gold_dim_client`, `gold_dim_datetime`, `gold_dim_weather` | Filtrar `is_daylight = 1` |
| Análisis económico mensual | `gold_fact_energy_forecast` | `gold_dim_client`, `gold_dim_datetime` | Requiere `price_pvpc_eur_mwh IS NOT NULL` |
| Análisis tarifario | `gold_fact_energy_forecast` | `gold_dim_datetime` | Agrupar por `tariff_period` |
| Benchmarking de instalaciones | `gold_fact_energy_forecast` | `gold_dim_client` | Normalizar por `pv_peak_power_kw` |
| Análisis por condición meteo | `gold_fact_energy_forecast` | `gold_dim_weather`, `gold_dim_datetime` | Filtrar `is_daylight = 1` |
| Configuración de instalaciones | `gold_dim_client` | — | Tabla de referencia; no contiene métricas |
| Calendario y tarifas | `gold_dim_datetime` | — | Fuente canónica para atributos de tiempo |

---

### 4.3 Tablas a Evitar en Consultas Directas

| Tabla | Razón para evitar | Alternativa recomendada |
|-------|------------------|------------------------|
| `clean_clients` | Tabla Silver — puede tener duplicados temporales durante la carga; contiene campos de auditoría internos | Usar `gold_dim_client` |
| `clean_weather` | Tabla Silver — granularidad idéntica a Gold pero sin enrichment dimensional; contiene metadatos de ingesta | Usar `gold_fact_energy_forecast` |
| `clean_prices` | Tabla Silver — no tiene `client_id`; requiere JOIN manual con `clean_weather` | Usar `gold_fact_energy_forecast.price_pvpc_eur_mwh` |
| `clean_calculations` | Tabla Silver — subset de lo que ya está en `gold_fact_energy_forecast`; sin precio | Usar `gold_fact_energy_forecast` |
| `etl_metadata` | Tabla de auditoría técnica | No aplicable a análisis de negocio |
| Manifests Bronze | Ficheros JSON de control técnico del pipeline | No aplicable a análisis de negocio |

> **Regla de oro para analistas:** **sólo consumir tablas con prefijo `gold_`**. Las tablas `clean_*` son la cocina — las tablas `gold_*` son el plato servido.

---

### 4.4 Buenas Prácticas de Performance

**Filtros obligatorios (siempre incluir en consultas sobre `gold_fact_energy_forecast`):**

```sql
-- 1. SIEMPRE filtrar por rango temporal para evitar full scans
WHERE f.unix_time BETWEEN strftime('%s','now') AND strftime('%s','now') + 432000
-- O equivalente via dimensión:
WHERE d.date BETWEEN '2026-05-01' AND '2026-05-31'

-- 2. Para análisis de generación: filtrar sólo horas diurnas
WHERE d.is_daylight = 1 AND f.pv_power_gen_kw > 0

-- 3. Para análisis económico: excluir slots sin precio
WHERE f.price_pvpc_eur_mwh IS NOT NULL

-- 4. Para análisis de una instalación concreta: filtrar por client_id
WHERE f.client_id = 'C001'
```

**Patrones de consulta eficientes:**

```sql
-- ✅ EFICIENTE: filtrar en fact antes del JOIN
SELECT c.name, SUM(f.pv_power_gen_kw)
FROM gold_fact_energy_forecast f          -- filtrar primero
JOIN gold_dim_client c ON f.client_id = c.client_id
WHERE f.unix_time >= strftime('%s','now')   -- índice usado
  AND f.client_id = 'C001'                  -- índice usado
GROUP BY c.name;

-- ❌ INEFICIENTE: calcular en WHERE sin índice
WHERE datetime(f.unix_time, 'unixepoch') >= '2026-05-10'
-- ✅ EFICIENTE: comparar EPOCH directamente (índice disponible)
WHERE f.unix_time >= 1746835200

-- ✅ EFICIENTE: usar CTEs para reutilizar subresultados complejos
WITH base AS (
    SELECT f.*, d.tariff_period, d.date, c.pv_peak_power_kw
    FROM gold_fact_energy_forecast f
    JOIN gold_dim_datetime d ON f.unix_time = d.unix_time
    JOIN gold_dim_client   c ON f.client_id = c.client_id
    WHERE d.date = date('now', '+1 day')    -- una sola pasada
)
SELECT tariff_period, SUM(pv_power_gen_kw), AVG(price_pvpc_eur_mwh)
FROM base GROUP BY tariff_period;
```

---

### 4.5 Política de Acceso por Rol

| Rol | Tablas accesibles | Nivel de acceso | Justificación |
|-----|------------------|----------------|---------------|
| **Analista de negocio** | `gold_fact_*`, `gold_dim_*` | Lectura | Datos analíticos consolidados sin información técnica interna |
| **Data Scientist** | `gold_*`, `clean_*` | Lectura | Necesita acceso a Silver para validación de modelos |
| **Responsable de planta** | `gold_fact_energy_forecast`, `gold_dim_client` (sólo su instalación) | Lectura, filtrado por `client_id` | Acceso restringido a los datos de su instalación |
| **Director / CFO** | `gold_fact_*`, `gold_dim_*` | Lectura (vía dashboard) | Acceso via herramienta BI; sin acceso SQL directo |
| **Data Engineer** | Todas las tablas | Lectura + escritura (pipeline) | Responsable del pipeline ETL |
| **On-call / Operaciones** | `etl_metadata`, `gold_fact_*` | Lectura | Diagnóstico y monitorización operativa |

---

## 5. Freshness y Confianza en el Dato

### 5.1 Frecuencia de Actualización por Tabla Gold

| Tabla | Frecuencia | Hora habitual (CET) | Lag máximo tolerable |
|-------|-----------|--------------------|--------------------|
| `gold_dim_client` | Cuando se actualiza el Excel de clientes | Variable (manual) | 24h desde la actualización del Excel |
| `gold_dim_datetime` | Con cada ejecución del pipeline | ~21:00–22:30 CET | 26h (pipeline del día siguiente cubre) |
| `gold_dim_weather` | Con cada ejecución del pipeline | ~21:00–22:30 CET | 26h |
| `gold_fact_energy_forecast` | Con cada ejecución del pipeline | ~21:00–22:30 CET (precios a partir de las 22:00) | 26h para datos meteorológicos; precio puede llegar hasta las 22:30 |

**Ventana de datos disponibles tras cada ejecución:**

```
Ejecución nocturna (21:00–22:30 CET):
  → Meteorología: slots desde AHORA hasta +120h (5 días)
  → Precios:      slots del día siguiente D+1 (24h)
  → Gold fact:    cubre las próximas 120h para todos los clientes activos
```

---

### 5.2 Cómo Interpretar los Timestamps de Actualización

El campo `_loaded_at_utc` en `gold_fact_energy_forecast` indica cuándo fue cargado o actualizado ese registro específico.

```sql
-- Ver freshness actual de gold_fact por instalación
SELECT
    c.name                                                              AS instalacion,
    MAX(f._loaded_at_utc)                                              AS ultima_actualizacion_utc,
    ROUND((strftime('%s','now') -
           strftime('%s', MAX(f._loaded_at_utc))) / 3600.0, 1)        AS horas_desde_actualizacion,
    CASE
        WHEN (strftime('%s','now') -
              strftime('%s', MAX(f._loaded_at_utc))) < 3600           THEN '🟢 Muy fresco (< 1h)'
        WHEN (strftime('%s','now') -
              strftime('%s', MAX(f._loaded_at_utc))) < 86400          THEN '🟡 Fresco (< 24h)'
        ELSE                                                               '🔴 Desactualizado'
    END                                                                AS estado_freshness
FROM gold_fact_energy_forecast f
JOIN gold_dim_client c ON f.client_id = c.client_id
GROUP BY c.name
ORDER BY ultima_actualizacion_utc DESC;
```

**Casos especiales de interpretación:**

| Situación | `price_pvpc_eur_mwh` | `_loaded_at_utc` | Qué significa |
|-----------|---------------------|-----------------|--------------|
| Pipeline ejecutado antes de las 20:30 CET | `NULL` | Timestamp de esa ejecución | El precio de mañana aún no está publicado — normal |
| Pipeline ejecutado después de las 21:00 CET | Valor numérico | Timestamp de esa ejecución | Dato completo — precio y meteo disponibles |
| Ejecución de re-intento (22:00 CET) | Valor numérico (actualizado) | Timestamp del re-intento | El `_loaded_at_utc` es más reciente que el de meteo — el precio llegó tarde |
| `_loaded_at_utc` de ayer | Cualquiera | Ayer | Puede haber nuevas previsiones meteorológicas disponibles — pipeline no ejecutó hoy |

---

### 5.3 Cuándo un Dato Puede Estar Incompleto

| Dato | Cuándo puede estar incompleto | Cómo detectarlo | Impacto en análisis |
|------|------------------------------|----------------|-------------------|
| `price_pvpc_eur_mwh` | Antes de las ~20:30 CET del día anterior | `WHERE price_pvpc_eur_mwh IS NULL` | Los análisis económicos para D+1 están incompletos hasta las ~22:00 CET |
| Cobertura meteorológica | Si OWM falló para algún cliente | `horas_cobertura < 120` en la query de freshness | Ese cliente tendrá slots futuros sin datos de generación estimada |
| Datos de algún cliente | Si el Excel no se actualizó tras añadir una instalación | `client_id` nuevo no aparece en `gold_dim_client` | El nuevo cliente no tiene datos hasta la siguiente ejecución del pipeline |
| Performance Ratio nocturno | Siempre — por diseño | `pv_performance_ratio = 0 WHERE is_daylight = 0` | No incluir slots nocturnos en el cálculo del PR medio (usar `WHERE gen > 0`) |

**Regla de cierre de día:**  
Los datos de `gold_fact_energy_forecast` para el **día de hoy** están disponibles como previsión desde la noche anterior, pero los precios de hoy ya son del pasado (D+0) — para análisis de coste del día actual usar los precios del último pipeline exitoso, que tiene los precios de D+1 (mañana).

---

### 5.4 Cómo Reportar Anomalías en el Dato

Si un analista o usuario del sistema detecta un dato que parece incorrecto, debe seguir este proceso:

```
1. DOCUMENTAR la anomalía con precisión:
   - Tabla y campo afectado
   - client_id y unix_time / fecha del registro anómalo
   - Valor observado vs valor esperado
   - Screenshot o resultado de query

2. VERIFICAR si es una anomalía real o un caso límite esperado:
   - ¿Es un slot nocturno con gen = 0? → Normal
   - ¿Es price_pvpc_eur_mwh = NULL? → Normal antes de las 22:00 CET
   - ¿Es un día con PR muy bajo? → Verificar si hubo tormenta (weather_main = Thunderstorm)

3. REPORTAR si se confirma que es un error real:
   Canal: Slack #data-quality o email al propietario del dato
   Incluir: tabla, campo, client_id, unix_time, valor, descripción del problema

4. EL EQUIPO DE DATOS investigará el origen (Bronze → Silver → Gold)
   y aplicará el proceso de remediación de 04_DATA_QUALITY_FRAMEWORK.md
```

**Template de reporte de anomalía:**

```
ANOMALÍA DE DATO — SunSaver
──────────────────────────────────────────────────────
Tabla:          gold_fact_energy_forecast
Campo:          pv_power_gen_kw
Instalación:    C001 (Planta Norte)
Slot:           2026-05-10 14:00:00 UTC (unix_time: 1746874800)
Valor anómalo:  -3.42 kW
Valor esperado: >= 0 kW (físicamente imposible negativo)
Detectado por:  [nombre del analista]
Fecha:          2026-05-10

Contexto adicional: en ese slot, clouds_pct = 45% y weather_main = Clouds.
Se esperaría generación positiva con esas condiciones.
──────────────────────────────────────────────────────
```

---

## 6. Casos de Decisión Documentados

### 6.1 Plantilla de Caso de Decisión

```markdown
## Caso de Decisión: [Título descriptivo]

**Instalación:**     [client_id / nombre]
**Fecha:**           YYYY-MM-DD
**Responsable:**     [Rol / nombre]
**Tipo de decisión:** Programación de carga / Arranque de maquinaria / Diferimiento de carga / Otro

### Contexto
[Descripción de la situación: qué decisión había que tomar y en qué plazo]

### Datos consultados
- Tabla/campo principal: [ej. gold_fact_energy_forecast.balance_kw para las próximas 24h]
- Filtros aplicados: [ej. date = mañana, tariff_period IN ('P3','P6')]
- Métrica clave: [ej. horas con excedente PV > 5 kW y precio < 100 €/MWh]

### Decisión tomada
[Descripción concreta de la acción: ej. "Programar carga de batería de 14:00 a 17:00 y
mover el ciclo de compresores de las 10:00 a las 15:00"]

### Alternativa descartada
[Qué se habría hecho sin el sistema y por qué es subóptimo]

### Resultado medido
- Ahorro estimado: X €
- Ahorro real (medición post-facto): Y €
- Diferencia vs decisión sin sistema: Z €

### Lecciones aprendidas
[Qué funcionó bien, qué podría mejorarse en la consulta de datos]
```

---

### 6.2 Ejemplos de Decisiones Tomadas con el Sistema

#### Caso DEC-001 — Programación de carga de batería en excedente PV (Planta ficticia A)

**Instalación:** C001 (datos de demo)  
**Fecha:** 2026-05-10  
**Tipo:** Programación de carga de batería

**Contexto:**  
La instalación tiene un sistema de almacenamiento de 20 kWh con SOC mínimo del 20%. El responsable de planta quería optimizar cuándo cargar la batería para el día siguiente antes de hacer el turno de noche.

**Datos consultados:**

```sql
SELECT d.hour_local, d.tariff_label,
       ROUND(f.pv_power_gen_kw, 1)              AS gen_kw,
       ROUND(f.power_consumption_kw, 1)         AS con_kw,
       ROUND(f.pv_power_gen_kw
             - f.power_consumption_kw, 1)       AS excedente_kw,
       ROUND(f.price_pvpc_eur_mwh, 0)           AS precio_eur_mwh
FROM gold_fact_energy_forecast f
JOIN gold_dim_datetime d ON f.unix_time = d.unix_time
WHERE d.date     = date('now', '+1 day')
  AND f.client_id = 'C001'
ORDER BY d.unix_time;
```

**Resultado del análisis:**  
El sistema identificó que de 12:00 a 16:00 hora local habría un excedente de 3–6 kW en período llano (P2), con precio medio de 118 €/MWh. Entre las 20:00 y las 22:00 (período punta P1) el precio subiría a 210 €/MWh con déficit de 8 kW.

**Decisión tomada:**  
Programar carga activa de la batería de 12:00 a 15:00 (excedente PV), almacenando ~15 kWh. Descargar la batería de 20:00 a 22:00 (período P1, precio más alto) en lugar de comprar de red.

**Ahorro estimado:**  
15 kWh × (210 - 118) €/MWh / 1.000 = **1,38 €** en esa decisión puntual.  
Anualizado con frecuencia similar: ~250 € / año sólo en optimización de carga de batería.

---

#### Caso DEC-002 — Diferimiento del ciclo de lavado industrial al valle tarifario

**Instalación:** C002 (datos de demo)  
**Fecha:** 2026-05-09  
**Tipo:** Diferimiento de carga flexible

**Contexto:**  
La instalación tiene un proceso de lavado industrial de alta temperatura que consume ~18 kW durante 2 horas. Habitualmente se programa a las 10:00 (período P1). El responsable quería saber si podría ejecutarlo más tarde sin afectar a la producción.

**Datos consultados:**

```sql
-- Comparativa del coste del ciclo de lavado a distintas horas
SELECT d.hour_local, d.tariff_label, f.price_pvpc_eur_mwh,
       ROUND(f.pv_power_gen_kw, 1)                                   AS gen_kw,
       -- Coste del ciclo de lavado (18 kW × 2h = 36 kWh)
       ROUND(MAX(0, 18 - f.pv_power_gen_kw) / 1000.0
             * f.price_pvpc_eur_mwh * 2, 2)                          AS coste_ciclo_eur
FROM gold_fact_energy_forecast f
JOIN gold_dim_datetime d ON f.unix_time = d.unix_time
WHERE d.date = date('now', '+1 day') AND f.client_id = 'C002'
ORDER BY coste_ciclo_eur ASC LIMIT 8;
```

**Decisión tomada:**  
Mover el ciclo de las 10:00 (P1, precio 195 €/MWh, sin PV significativo → coste ~7,02 €) a las 14:00 (P2, precio 102 €/MWh, con 12 kW de generación PV → coste neto ~1,22 €).

**Ahorro medido:**  
7,02 € − 1,22 € = **5,80 €** por ciclo.  
Con 3 ciclos semanales: ~90 € / mes, ~1.080 € / año.

---

### 6.3 Impacto Medido de las Decisiones

> *Nota: los valores siguientes corresponden a escenarios de simulación con los datos de demo del entorno DEV. En producción, con instalaciones y consumos reales, los importes serán proporcionales a la potencia instalada y al perfil de consumo real.*

| Tipo de decisión | Ahorro unitario estimado | Frecuencia típica | Ahorro anual proyectado (por instalación) |
|-----------------|------------------------|------------------|------------------------------------------|
| Optimización de carga de batería | 1–5 € / decisión | 200 días/año | **200–1.000 €/año** |
| Diferimiento de cargas flexibles al valle | 2–10 € / evento | 150 eventos/año | **300–1.500 €/año** |
| Programación de arranque de maquinaria pesada | 5–20 € / arranque | 50 arranques/año | **250–1.000 €/año** |
| Evitar consumo en punta P1 usando batería | 3–8 € / día de punta | 250 días/año | **750–2.000 €/año** |
| **Total estimado por instalación (16 kWp)** | | | **1.500–5.500 €/año** |

**Contexto de rentabilidad:**  
Para una instalación típica de 16 kWp con coste de 18.000 €, un ahorro de 3.000 €/año (punto medio) supone un **período de retorno de 6 años**, que baja a menos de 5 años si se añaden subvenciones autonómicas o estatales. El sistema de soporte a la decisión de SunSaver tiene impacto directo en acelerar ese retorno al maximizar el aprovechamiento del excedente fotovoltaico.

---

## 7. Roadmap Analítico

### 7.1 Nuevas Fuentes de Datos Previstas

| Fuente | Tipo de dato | Valor de negocio | Prioridad | Estado |
|--------|-------------|-----------------|-----------|--------|
| **OMIE — Mercado spot (OMIE API)** | Precio del mercado mayorista hora a hora | Alternativa / complemento al PVPC para instalaciones > 10 kW | 🔴 Alta | Pendiente |
| **Medición real de producción PV** (inversor / datalogger) | Potencia AC real generada, en tiempo real | Validar el modelo físico contra la realidad; detectar fallos reales | 🔴 Alta | Pendiente |
| **Medición real de consumo** (contador inteligente) | Consumo real hora a hora | Sustituir el modelo de consumo simulado por datos reales | 🔴 Alta | Pendiente |
| **API REE — Indicadores de red** | % renovable en el mix eléctrico hora a hora | KPI de huella de carbono: saber cuándo la red es más verde | 🟡 Media | Planificado |
| **Datos de mantenimiento** (CMMS) | Incidencias, limpiezas, sustituciones de componentes | Correlacionar eventos de mantenimiento con caídas del PR | 🟡 Media | Conceptual |
| **Previsión de demanda propia** (ML) | Consumo futuro basado en histórico + calendar features | Mejorar el modelo de consumo industrial con ML propio | 🟡 Media | Conceptual |
| **Precios de la batería** (coste de ciclo) | Coste por kWh almacenado/descargado según la tecnología | Optimización real del arbitraje batería vs red | 🟢 Baja | Conceptual |

---

### 7.2 Métricas en Desarrollo

| Métrica | Descripción | Datos necesarios | Estado |
|---------|-------------|-----------------|--------|
| **PR real vs PR simulado** | Comparativa entre el Performance Ratio calculado por el modelo y el medido por el inversor real | Medición real del inversor (pendiente) | Bloqueado por falta de datos reales |
| **Huella de carbono evitada** | kg de CO₂ evitados por la generación PV propia, calculados usando el factor de emisión del mix eléctrico español hora a hora | Datos de mix renovable de REE (planificado) | En planificación |
| **Índice de flexibilidad** | Medida de cuánta carga flexible se diferió realmente (cargas que se movieron de P1 a P3/P6) | Datos reales de consumo (pendiente) | Bloqueado |
| **Valor de la batería (VPP proxy)** | Valor económico del sistema de almacenamiento calculado como diferencia entre coste con y sin batería en el período analizado | Datos reales de carga/descarga (pendiente) | Bloqueado |
| **Degradación anual del parque PV** | Tasa de reducción del PR interanual — proxy del envejecimiento de los paneles | 12+ meses de histórico de PR | En desarrollo (necesita más datos históricos) |
| **Forecast de factura mensual** | Proyección del gasto eléctrico del mes en curso con los datos de previsión disponibles | Disponible ya (datos en Gold) | **Listo para implementar** |

---

### 7.3 Integraciones BI Planificadas

| Integración | Herramienta | Caso de uso principal | Prioridad | Esfuerzo estimado |
|------------|-------------|----------------------|-----------|------------------|
| **Dashboard operativo diario** | Grafana + SQLite datasource | Vista horaria del balance energético para el responsable de planta | 🔴 Alta | 2–3 días |
| **Reporting ejecutivo mensual** | Apache Superset o Metabase | Dashboard de KPIs financieros para dirección | 🔴 Alta | 3–5 días |
| **Alertas proactivas en Slack** | Webhook Slack + pipeline Python | Notificación automática de *"Mañana de 14:00 a 17:00 habrá excedente de 4 kW en período llano — buena ventana para cargar batería"* | 🔴 Alta | 2 días |
| **Notebook de análisis ad-hoc** | Jupyter + DuckDB + Plotly | Análisis exploratório para Data Scientists y gestores de energía | 🟡 Media | 1 día |
| **Exportación a Excel** | Python + openpyxl | Informe mensual para clientes sin acceso a herramienta BI | 🟡 Media | 1 día |
| **API REST de consulta** | FastAPI + SQLite | Integración con sistemas SCADA o de gestión de energía del cliente | 🟢 Baja | 5–8 días |
| **Integración con Power BI Service** | Power BI + gateway on-premise | Dashboard en la nube para empresas con ecosistema Microsoft | 🟢 Baja | 3–5 días |

**Priorización del roadmap BI:**

La secuencia recomendada para maximizar el valor percibido por el negocio es:

1. **Alertas proactivas en Slack** → valor inmediato para el responsable de planta sin necesidad de que nadie abra un dashboard
2. **Dashboard operativo diario en Grafana** → visibilidad del balance energético del día siguiente en tiempo real
3. **Reporting ejecutivo en Superset/Metabase** → justificación del ROI para la dirección
4. **Notebook de análisis** → habilitación del equipo de datos para análisis ad-hoc
5. **API REST** → integración con otros sistemas (proyecto más largo pero de mayor valor estratégico)

---

*SunSaver ETL · Guía de Business Intelligence v1.0.0 · Mayo 2026*  
*Clasificación: INTERNA · Este documento es el puente entre el pipeline técnico y el valor de negocio del sistema*