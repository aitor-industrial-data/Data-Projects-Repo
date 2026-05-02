# ☀️ SunSaver ETL — Plataforma de Inteligencia Fotovoltaica

> **Transformando datos brutos de generación solar y meteorología en decisiones energéticas respaldadas por datos para instalaciones industriales.**

---

## 🏭 El Problema Industrial

Las instalaciones industriales con sistemas fotovoltaicos se enfrentan cada día a un problema crítico y costoso: **operan a ciegas**.

Los paneles están generando energía. La red la está tarifando de forma diferente cada hora. El cielo está cambiando. Pero el responsable de operaciones no dispone de una visión unificada y en tiempo real que conecte todo esto.

El resultado:

- Compresores y hornos funcionan en hora punta cuando la electricidad de red cuesta 3× más
- Las baterías permanecen inactivas mientras el excedente solar se vierte a la red a precios casi nulos
- El mantenimiento es reactivo, nunca predictivo
- El departamento financiero es incapaz de verificar si la instalación solar está entregando el ROI prometido

**SunSaver ETL resuelve esto.** Es un pipeline de datos de calidad productiva que ingesta, transforma y estructura cada variable que determina el coste energético y el rendimiento solar — proporcionando a los operadores industriales la base analítica que necesitan para actuar, no solo para observar.

---

## 🔬 Qué Hace

SunSaver es un **pipeline ETL multi-etapa** construido sobre la arquitectura medallón (Bronce → Plata → Oro). Cada 24 horas:

1. **Lee la configuración de las instalaciones** desde un fichero Excel maestro (especificaciones de paneles, coordenadas GPS, coeficientes de pérdidas, configuración de batería)
2. **Descarga los precios de electricidad del día siguiente** desde la API pública de REE (PVPC + Mercado Spot, hora a hora)
3. **Obtiene previsiones meteorológicas a 5 días** desde OpenWeatherMap para las coordenadas exactas de cada cliente
4. **Ejecuta un modelo físico de generación FV** que calcula, para cada ventana de pronóstico de 3 horas:
   - Irradiancia Global Horizontal (GHI) con el modelo de cielo despejado de Haurwitz + corrección por nubosidad y código meteorológico
   - Descomposición beam/difusa mediante el **modelo de Erbs**
   - Irradiancia en el Plano del Array (POA) considerando inclinación del panel, azimut y albedo del suelo
   - Temperatura de célula con el **modelo de Faiman**
   - Potencia AC de salida con derating térmico y coeficientes de pérdidas del sistema
   - Simulación dinámica del consumo industrial (turnos, carga HVAC, ruido estocástico)
5. **Puebla la capa Gold** con un star schema listo para dashboards BI o modelos ML

Todo esto se ejecuta de forma desatendida, idempotente y con logging estructurado en cada paso.

---

## 🏗️ Arquitectura

```
┌─────────────────────────────────────────────────────────────────┐
│                      FUENTES DE DATOS                           │
│  Excel (clientes)  │  API REE (precios)  │  API OpenWeather    │
└────────┬───────────┴────────┬────────────┴────────┬────────────┘
         │                    │                      │
         ▼                    ▼                      ▼
┌─────────────────────────────────────────────────────────────────┐
│                    🥉 CAPA BRONCE                               │
│   raw_clients  │  raw_prices  │  raw_weather                   │
│   (append-only, trazabilidad completa, _ingested_at_utc)       │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│                    🥈 CAPA PLATA                                │
│  clean_clients │ clean_prices │ clean_weather │ clean_calcs     │
│  (tipado, validado, deduplicado, PK forzada)                    │
│                        │                                        │
│          ┌─────────────┘                                        │
│          ▼                                                       │
│   ⚡ MOTOR DE GENERACIÓN FV (pvlib + Haurwitz + Erbs + Faiman) │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│                    🥇 CAPA ORO (Star Schema)                    │
│  gold_dim_client  │  gold_dim_datetime  │  gold_dim_weather     │
│                   gold_fact_energy_forecast                      │
│  (listo para BI, FK forzadas, indexado)                         │
└─────────────────────────────────────────────────────────────────┘
```

### Orden de Ejecución del Pipeline

| Stage | Paso | Entrada → Salida |
|-------|------|-----------------|
| 1 | `extract_clients` | Excel → `raw_clients` |
| 1 | `extract_energy_prices` | API REE → `raw_prices` |
| 2 | `transform_clients` | `raw_clients` → `clean_clients` |
| 2 | `transform_energy_prices` | `raw_prices` → `clean_prices` |
| 3 | `extract_openweather` | API OpenWeather → `raw_weather` |
| 4 | `transform_openweather` | `raw_weather` → `clean_weather` |
| 5 | `extract_generation_data` | `clean_clients` + `clean_weather` → `clean_calculations` |
| 6 | `gold_dim_*` + `gold_fact_energy_forecast` | Plata → Oro |

---

## ⚡ El Motor de Física

El diferenciador técnico de SunSaver es que no depende de tablas de consulta de irradiancia simplificadas. Implementa una **cadena de modelos fotovoltaicos validados**:

```
Posición Solar (pvlib) → GHI (Haurwitz + Corrección por Nubosidad)
    → DNI + DHI (Descomposición Erbs)
        → POA (Liu-Jordan + Albedo)
            → T_célula (Faiman)
                → P_AC (Derating Térmico + Pérdidas del Sistema)
```

Cada paso degrada con seguridad: si el sol está por debajo de 2° de elevación, todos los cálculos posteriores cortocircuitan a cero, eliminando la inestabilidad numérica característica de los cálculos cerca del horizonte.

El modelo de consumo simula un perfil de carga industrial real — picos de arranque de turno, valle del mediodía, respuesta HVAC a la temperatura ambiente — produciendo cifras de balance energético neto que los equipos de operaciones pueden utilizar directamente.

---

## 🗄️ Esquema Gold (Star Schema)

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
    ├── has_solar / has_battery   (flags booleanos derivados)
    └── installation_cost_eur

gold_dim_weather
    ├── weather_id (códigos OpenWeather)
    ├── weather_main / weather_description
    └── (resuelto por frecuencia cuando existen múltiples descripciones para el mismo ID)
```

---

## 🛠️ Stack Tecnológico

| Capa | Tecnología |
|------|------------|
| Lenguaje | Python 3.11+ |
| Modelado FV | `pvlib` (estándar de la industria) |
| Manipulación de datos | `pandas`, `numpy` |
| Base de datos | SQLite (portable, sin configuración) |
| ORM/SQL | `sqlalchemy` (UPSERT, DDL) |
| APIs externas | `requests` (REE, OpenWeather) |
| Configuración | `python-dotenv` |
| Planificación | Cron / cualquier scheduler |

---

## 🚀 Inicio Rápido

```bash
# 1. Clonar e instalar
git clone https://github.com/tu-usuario/sunsaver-etl.git
cd sunsaver-etl
pip install -r requirements.txt

# 2. Configurar el entorno
cp .env.example .env
# Editar .env → añadir WEATHER_API_KEY (OpenWeatherMap)
#             → opcionalmente configurar DB_PATH

# 3. Añadir las instalaciones
# Editar data/clients_source.xlsx con los datos de cada cliente

# 4. Ejecutar el pipeline completo
cd src
python orchestrator.py

# O reanudar desde un stage concreto (p.ej., tras un fallo de la API meteorológica)
python orchestrator.py --stage 3

# Dry-run para validar el plan de ejecución sin ejecutar nada
python orchestrator.py --dry-run
```

---

## 📁 Estructura del Proyecto

```
05.02_SunSaver_ETL/
├── data/
│   ├── clients_source.xlsx     # Configuración maestra de instalaciones
│   └── sunsaver.db             # Base de datos SQLite (creada automáticamente)
├── docs/                       # Diagramas de arquitectura y documentación de referencia
├── logs/                       # Logs de ejecución del pipeline
├── src/
│   ├── orchestrator.py         # Controlador del pipeline
│   ├── db_manager.py           # Resolución de la ruta a la base de datos
│   ├── pv_generation_engine.py # Modelos físicos (GHI, DNI, POA, Faiman)
│   ├── extract_*.py            # Extractores capa Bronce
│   ├── transform_*.py          # Transformadores capa Plata
│   └── transform_gold_*.py     # Constructores capa Oro
├── venv/
├── requirements.txt
└── README.md
```

---

## 🔧 Variables de Entorno

| Variable | Obligatoria | Descripción |
|----------|-------------|-------------|
| `WEATHER_API_KEY` | ✅ Sí | Clave API de OpenWeatherMap (nivel gratuito suficiente) |
| `DB_PATH` | ❌ Opcional | Sobrescribe la ruta por defecto de SQLite (`data/sunsaver.db`) |

---

## 📈 Valor de Negocio

| Capacidad | Impacto |
|-----------|---------|
| Previsión hora a hora de generación + precio | Permite desplazamiento de cargas para ahorrar un 20–40% en coste de red eléctrica |
| Arquitectura multi-cliente | Un solo pipeline sirve a N instalaciones industriales simultáneamente |
| Etiquetado de periodos tarifarios españoles (P1–P6) | Integración directa con sistemas de facturación y gestión de demanda |
| Capa Bronce con auditoría completa | Cumplimiento regulatorio y capacidad de replay histórico |
| Modelo de generación basado en física (no en ML) | Fiable incluso para instalaciones nuevas sin datos históricos |
| Patrón UPSERT idempotente | Seguro de re-ejecutar sin corrupción de datos |

---

## 📄 Licencia

MIT — ver `LICENSE` para más detalles.

---

> *Construido para responsables de energía industrial que están hartos de hojas de cálculo y listos para ingeniería de datos real.*
