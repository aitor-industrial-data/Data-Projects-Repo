# ☀️ SunSaver ETL · Plataforma de Inteligencia Energética Industrial
## 06 Especificación de Integraciones API
> **Clasificación:** INTERNA &nbsp;|&nbsp; **Estado:** ACTIVO — Entorno DEV &nbsp;|&nbsp; **Pipeline:** `SunSaver_ETL`  
> **Audiencia:** Ingenieros de Backend, Data Engineers, DevOps &nbsp;|&nbsp; **Última actualización:** 2026-05-10

---

## Tabla de Contenidos

1. [Inventario de Integraciones](#1-inventario-de-integraciones)
   - 1.1 [Tabla Resumen](#11-tabla-resumen)
   - 1.2 [Mapa de Dependencias entre APIs](#12-mapa-de-dependencias-entre-apis)
   - 1.3 [Política de Gestión de Credenciales](#13-política-de-gestión-de-credenciales)
2. [Especificación por API](#2-especificación-por-api)
   - 2.1 [API REE — Precios PVPC](#21-api-ree--precios-pvpc)
   - 2.2 [API OpenWeatherMap — Forecast](#22-api-openweathermap--forecast-5-días)
   - 2.3 [Fuente Excel — Maestro de Clientes](#23-fuente-excel--maestro-de-clientes)
3. [Patrones de Resiliencia](#3-patrones-de-resiliencia)
   - 3.1 [Circuit Breaker por API](#31-circuit-breaker-por-api)
   - 3.2 [Política de Retries con Backoff](#32-política-de-retries-con-backoff)
   - 3.3 [Fallback y Datos de Caché](#33-fallback-y-datos-de-caché)
   - 3.4 [Health Checks de Conectores](#34-health-checks-de-conectores)
4. [Configuración y Secretos](#4-configuración-y-secretos)
   - 4.1 [Variables de Entorno Requeridas](#41-variables-de-entorno-requeridas-por-integración)
   - 4.2 [Rotación de Credenciales](#42-rotación-de-credenciales)
   - 4.3 [Gestión de Secretos](#43-gestión-de-secretos)
5. [Testing de Integraciones](#5-testing-de-integraciones)
   - 5.1 [Sandbox y Entornos de Prueba](#51-sandbox--entornos-de-prueba-disponibles)
   - 5.2 [Mock Responses para Tests Unitarios](#52-mock-responses-para-tests-unitarios)
   - 5.3 [Contract Tests](#53-contract-tests-implementados)
   - 5.4 [Checklist de Nueva Integración](#54-checklist-de-validación-de-nueva-integración)

---

## 1. Inventario de Integraciones

### 1.1 Tabla Resumen

| ID | Nombre | Tipo | Proveedor | Autenticación | Criticidad | Estado | Módulo |
|----|--------|------|-----------|--------------|------------|--------|--------|
| `INT-001` | REE PVPC Prices | REST API | Red Eléctrica de España | Ninguna (pública) | 🟡 ALTA | ✅ Activo | `bronze_ingest_prices_ree.py` |
| `INT-002` | OpenWeatherMap Forecast | REST API | OpenWeather Ltd. | API Key | 🔴 CRÍTICA | ✅ Activo | `bronze_ingest_weather_owm.py` |
| `INT-003` | Maestro de Clientes | Fichero local | Equipo de Operaciones | N/A | 🔴 CRÍTICA | ✅ Activo | `bronze_ingest_clients.py` |

**Definición de criticidad:**

| Nivel | Significado | Impacto si falla |
|-------|-------------|-----------------|
| 🔴 CRÍTICA | El pipeline no puede producir resultados útiles sin esta fuente | Sin datos meteorológicos → sin cálculos PV → Gold vacío |
| 🟡 ALTA | El pipeline continúa en modo degradado (`PARTIAL SUCCESS`) | Sin precios → `price_pvpc_eur_mwh = NULL` en Gold fact |
| 🟢 MEDIA | Impacto limitado; otras fuentes compensan | — |

---

### 1.2 Mapa de Dependencias entre APIs

```
Fuentes externas               Pipeline interno              Decisiones de negocio
─────────────────              ─────────────────             ─────────────────────

INT-003 Excel clientes ──────► clean_clients ─────────────► Qué instalaciones monitorizar
         (CRÍTICA)                   │                        Parámetros del motor PV
                                     │
                                     ▼
INT-002 OpenWeatherMap ──────► clean_weather ─────────────► Generación PV por hora
         (CRÍTICA)             + clean_calculations          Consumo estimado por hora
         llamada por                 │
         cada client_id             │
                                     ▼
INT-001 REE PVPC ────────────► clean_prices ──────────────► Coste/ahorro por hora
         (ALTA)                      │                        Decisión de carga batería
                                     │                        Momento óptimo arranque
                                     ▼
                           gold_fact_energy_forecast
```

**Orden de dependencia estricto:**

1. `INT-003` (Excel clientes) debe cargarse **antes** que `INT-002` (OWM necesita las coordenadas de `clean_clients`)
2. `INT-001` (REE) y `INT-002` (OWM) son independientes entre sí y podrían ejecutarse en paralelo
3. El fallo total de `INT-002` impide calcular `clean_calculations` y vacía `gold_fact_energy_forecast`
4. El fallo de `INT-001` sólo afecta a `price_pvpc_eur_mwh`; el resto de la fact table se carga correctamente

---

### 1.3 Política de Gestión de Credenciales

**Principios:**

- **Cero credenciales en código fuente.** Ninguna API key, token ni contraseña aparece en ningún fichero `.py`, `.json` o `.yaml` del repositorio.
- **Cero credenciales en logs.** Los módulos de logging están configurados para nunca registrar valores de variables de entorno que contengan `KEY`, `SECRET`, `TOKEN` o `PASSWORD`.
- **Mínimo privilegio.** Cada credencial tiene sólo los permisos necesarios para la operación que realiza (sólo lectura en todas las APIs actuales).

**Mecanismo de carga en DEV:**

```python
# config_paths.py — carga de .env en todos los módulos
from dotenv import load_dotenv
load_dotenv()   # busca .env en el directorio raíz del proyecto

# Acceso en módulos de ingesta
API_KEY = os.getenv("WEATHER_API_KEY")
if not API_KEY:
    logger.error("[EXTRACT] WEATHER_API_KEY no configurada — revisar .env")
    return {}
```

**Estructura del fichero `.env` requerido:**

```bash
# .env — NO versionar en Git (incluido en .gitignore)
# Copiar de .env.example y rellenar con valores reales

# OpenWeatherMap API Key (INT-002)
WEATHER_API_KEY=your_owm_api_key_here

# Rutas de datos (opcionales — el sistema usa valores por defecto si no se definen)
DB_PATH=/ruta/personalizada/sunsaver.db       # opcional
BRONZE_PATH=/ruta/personalizada/bronze/       # opcional
```

**Fichero `.env.example` versionado en Git:**

```bash
# .env.example — Plantilla de variables de entorno requeridas
# Copiar como .env y completar los valores antes de ejecutar el pipeline

WEATHER_API_KEY=         # Obligatorio: API Key de OpenWeatherMap
DB_PATH=                 # Opcional: ruta a sunsaver.db (default: data/sunsaver.db)
BRONZE_PATH=             # Opcional: ruta al directorio bronze (default: data/bronze/)
```

---

## 2. Especificación por API

### 2.1 API REE — Precios PVPC

#### 2.1.1 Identificador único de integración

```
ID:          INT-001
Nombre:      REE PVPC Electricity Prices
Módulo:      bronze_ingest_prices_ree.py
Función:     extract_raw_json_from_ree()
Criticidad:  ALTA (pipeline continúa sin este dato)
```

#### 2.1.2 Proveedor y Documentación Oficial

| Atributo | Valor |
|----------|-------|
| **Proveedor** | Red Eléctrica de España (REE) — operador del sistema eléctrico español |
| **Producto** | API de datos abiertos de REE (apidatos.ree.es) |
| **Documentación oficial** | https://www.ree.es/es/apidatos |
| **Portal de datos** | https://apidatos.ree.es |
| **Términos de uso** | Datos públicos de libre acceso — sin registro ni API key requeridos |
| **Contacto soporte** | https://www.ree.es/es/contacto |

#### 2.1.3 Tipo de Autenticación

**Sin autenticación.** La API de datos abiertos de REE es pública y no requiere ningún tipo de credencial, token ni registro previo.

Los únicos headers enviados son de cortesía (simulan una petición desde el navegador del portal REE):

```python
headers = {
    "Accept":   "application/json",
    "Origin":   "https://www.ree.es",
    "Referer":  "https://www.ree.es/",
}
```

#### 2.1.4 Endpoints Consumidos

##### Endpoint: Precios Mercados Tiempo Real (PVPC)

```
URL:    https://apidatos.ree.es/es/datos/mercados/precios-mercados-tiempo-real
Método: GET
```

**Parámetros de request:**

| Parámetro | Tipo | Requerido | Valor en SunSaver | Descripción |
|-----------|------|-----------|------------------|-------------|
| `start_date` | STRING | ✅ SÍ | `{tomorrow}T00:00` | Inicio del rango temporal en formato ISO 8601 |
| `end_date` | STRING | ✅ SÍ | `{tomorrow}T23:59` | Fin del rango temporal en formato ISO 8601 |
| `time_trunc` | STRING | ✅ SÍ | `hour` | Granularidad temporal: `hour`, `day`, `month`, `year` |
| `geo_trunc` | STRING | ✅ SÍ | `electric_system` | Agrupación geográfica |
| `geo_limit` | STRING | ✅ SÍ | `peninsular` | Ámbito geográfico: `peninsular`, `canarias`, `baleares`… |
| `geo_ids` | STRING | ✅ SÍ | `8741` | ID de la zona geográfica (8741 = sistema peninsular) |

**Ejemplo de request completo:**

```bash
curl -X GET \
  "https://apidatos.ree.es/es/datos/mercados/precios-mercados-tiempo-real\
?start_date=2026-05-11T00:00\
&end_date=2026-05-11T23:59\
&time_trunc=hour\
&geo_trunc=electric_system\
&geo_limit=peninsular\
&geo_ids=8741" \
  -H "Accept: application/json" \
  -H "Origin: https://www.ree.es" \
  -H "Referer: https://www.ree.es/"
```

**Estructura de response:**

```json
{
  "data": {
    "type": "Precios mercados de tiempo real",
    "id": "pmh",
    "attributes": {
      "title": "Precios mercados de tiempo real",
      "last-update": "2026-05-10T20:35:00.000+02:00",
      "description": "..."
    }
  },
  "included": [
    {
      "type": "Precio mercados de tiempo real",
      "id": "1001",                          // ← PVPC peninsular (el que usamos)
      "groupId": "11",
      "attributes": {
        "title": "PVPC (Tarifa VPSC)",
        "last-update": "2026-05-10T20:35:00.000+02:00",
        "color": "#ffcc00",
        "type": "line",
        "magnitude": "€/MWh",
        "composite": false,
        "values": [
          {
            "value": 142.80,                 // ← precio €/MWh (CAMPO CRÍTICO)
            "percentage": 65.3,
            "datetime": "2026-05-11T00:00:00.000+02:00"  // ← timestamp (CAMPO CRÍTICO)
          },
          // ... 23 registros más (1 por hora)
        ]
      }
    },
    {
      "id": "1002",                          // ← Mercado spot (no usado en SunSaver)
      ...
    }
  ]
}
```

**Campos críticos extraídos:**

| Campo JSON | Campo Silver | Tipo | Garantizado |
|-----------|-------------|------|------------|
| `included[?id==1001].attributes.values[].datetime` | `datetime_utc` | ISO 8601 STRING | ✅ Sí (cuando hay datos) |
| `included[?id==1001].attributes.values[].value` | `price_euro_mwh` | FLOAT (€/MWh) | ✅ Sí (cuando hay datos) |
| `included[?id==1001].attributes.values[].percentage` | *(descartado)* | FLOAT (%) | ⚠️ Opcional |

**Filtro aplicado en el extractor:**

```python
# Seleccionar únicamente la serie PVPC (id="1001")
pvpc_item = next(
    (item for item in all_data.get("included", []) if item.get("id") == "1001"),
    None,
)
# Sobrescribir included para persistir sólo la serie relevante
all_data["included"] = [pvpc_item]
```

**Códigos de estado HTTP:**

| Código | Significado | Acción implementada |
|--------|-------------|-------------------|
| `200` | Éxito | Parsear JSON y verificar que `values` no está vacío |
| `200` con `values: []` | Precios no publicados aún | `return False` → `PARTIAL SUCCESS` |
| `400` | Parámetros incorrectos | Log ERROR + `return False` |
| `404` | Recurso no encontrado | Log ERROR + `return False` |
| `500`, `502`, `503`, `504` | Error servidor REE | Log ERROR "precios no publicados" + `return False` |
| Timeout (> 15s) | Sin respuesta | `requests.exceptions.Timeout` capturada + `return False` |

#### 2.1.5 Paginación

**No aplica.** El endpoint devuelve todos los valores del rango temporal solicitado en una única respuesta. Con `time_trunc=hour` y un rango de 24 horas, la respuesta contiene exactamente 24 objetos en `values[]`.

Volumen de respuesta estimado: **~8 KB** por request (24 registros horarios en JSON con indentación).

#### 2.1.6 Rate Limits

| Parámetro | Valor | Fuente |
|-----------|-------|--------|
| Límite documentado | No publicado | REE no documenta límites de tasa |
| Llamadas en SunSaver | 1 por día | Sin riesgo de throttling |
| Comportamiento observado | Sin restricción | Responde en < 2s en condiciones normales |
| Header de quota | No disponible | La API no devuelve headers `X-RateLimit-*` |

**Estrategia de throttling:** no implementada (innecesaria con 1 llamada diaria). Si en el futuro se requieren llamadas históricas masivas, implementar `time.sleep(1)` entre requests.

#### 2.1.7 Manejo de Errores Específicos

| Escenario | Detección | Acción | Efecto en pipeline |
|-----------|-----------|--------|-------------------|
| Precios D+1 no publicados (antes de ~20:30 CET) | `values: []` en el payload | `return False` | `PARTIAL SUCCESS` — pipeline continúa |
| Error servidor transitorio (5xx) | `response.status_code in (500,502,503,504)` | Log "prices not yet published" + `return False` | `PARTIAL SUCCESS` |
| Error de red / timeout | `requests.exceptions.RequestException` | Log ERROR + `return False` | `PARTIAL SUCCESS` |
| Payload malformado (no JSON) | `response.json()` lanza `JSONDecodeError` | Log ERROR + `return False` | `PARTIAL SUCCESS` |
| Estructura inesperada (sin `included`) | `pvpc_item = None` | `return False` | `PARTIAL SUCCESS` |
| Cambio de `id` de la serie PVPC | `pvpc_item = None` (no encuentra `id=1001`) | Log WARNING específico + `return False` | Requiere actualización del filtro |

#### 2.1.8 Contrato de Datos

**Campos garantizados** (cuando el endpoint devuelve datos):

```
included[].id                              → siempre presente
included[].attributes.values[].datetime   → siempre presente, formato ISO 8601
included[].attributes.values[].value      → siempre presente, tipo FLOAT
```

**Campos opcionales** (pueden estar ausentes sin indicar error):

```
included[].attributes.values[].percentage → presente en la mayoría de respuestas
data.attributes.last-update               → timestamp de última actualización
```

**Política de breaking changes del proveedor:**  
REE no tiene un programa formal de versionado de API ni un canal oficial de notificación de cambios. Los cambios observados históricamente han sido:

- Cambios en el ID de la serie PVPC (de `"1001"` a otro valor) → el filtro `id == "1001"` fallaría silenciosamente
- Cambios en el nombre del campo `value` o `datetime` → el extractor retornaría `False` o datos vacíos
- Cambios en la estructura raíz (`included` → `data`) → excepción en el parser

**Versión de API:** la API no tiene versión explícita en la URL. Se monitoriza manualmente.

**Plan de migración ante cambio de estructura:**

1. El extractor retorna `False` o lanza excepción → alerta automática
2. Inspeccionar respuesta raw en `bronze/prices_*.json` (siempre se persiste el payload completo)
3. Actualizar `extract_raw_json_from_ree()` y `transform_prices_bronze_to_silver()` con el nuevo schema
4. Re-procesar ficheros Bronze históricos con el nuevo parser

---

### 2.2 API OpenWeatherMap — Forecast 5 días

#### 2.2.1 Identificador único de integración

```
ID:          INT-002
Nombre:      OpenWeatherMap 5 Day / 3 Hour Forecast
Módulo:      bronze_ingest_weather_owm.py
Función:     extract_weather(lat, lon)
Criticidad:  CRÍTICA (sin meteo no hay cálculos PV)
```

#### 2.2.2 Proveedor y Documentación Oficial

| Atributo | Valor |
|----------|-------|
| **Proveedor** | OpenWeather Ltd. (openweathermap.org) |
| **Producto** | 5 Day / 3 Hour Forecast (Free tier disponible) |
| **Documentación oficial** | https://openweathermap.org/forecast5 |
| **Portal de API keys** | https://home.openweathermap.org/api_keys |
| **Página de planes** | https://openweathermap.org/price |
| **Soporte** | https://home.openweathermap.org/users/sign_in → Support tickets |
| **Estado del servicio** | https://status.openweathermap.org |

#### 2.2.3 Tipo de Autenticación

**API Key en parámetro de query (`appid`).** La clave se envía como parámetro GET, no en headers de autenticación.

```python
params = {
    "lat":   lat,           # latitud de la instalación
    "lon":   lon,           # longitud de la instalación
    "appid": API_KEY,       # ← API key de OpenWeatherMap
    "units": "metric",      # temperatura en °C
    "lang":  "en",          # descripción del tiempo en inglés
}
response = requests.get(
    "https://api.openweathermap.org/data/2.5/forecast",
    params=params,
    timeout=15,
)
```

> **Seguridad:** la API key **nunca debe loguearse**. El logger de SunSaver registra los parámetros de request sólo a nivel DEBUG, y el handler de fichero está configurado en INFO. En ningún caso se loguea el valor de `API_KEY`.

#### 2.2.4 Endpoints Consumidos

##### Endpoint: 5 Day / 3 Hour Forecast

```
URL:    https://api.openweathermap.org/data/2.5/forecast
Método: GET
```

**Parámetros de request:**

| Parámetro | Tipo | Requerido | Valor en SunSaver | Descripción |
|-----------|------|-----------|------------------|-------------|
| `lat` | FLOAT | ✅ SÍ | `row["latitude"]` | Latitud de la instalación en WGS84 |
| `lon` | FLOAT | ✅ SÍ | `row["longitude"]` | Longitud de la instalación en WGS84 |
| `appid` | STRING | ✅ SÍ | `os.getenv("WEATHER_API_KEY")` | API Key de autenticación |
| `units` | STRING | ✅ SÍ | `"metric"` | Sistema de unidades: `metric` (°C, m/s), `imperial` (°F, mph), `standard` (K) |
| `lang` | STRING | ❌ NO | `"en"` | Idioma de `weather[].description`. No afecta a valores numéricos |
| `cnt` | INTEGER | ❌ NO | *(no enviado)* | Limitar número de tramos devueltos. Omitir = máximo (40 tramos) |

**Ejemplo de request:**

```bash
curl -X GET \
  "https://api.openweathermap.org/data/2.5/forecast\
?lat=42.803852\
&lon=-1.701962\
&appid=TU_API_KEY\
&units=metric\
&lang=en"
```

**Estructura de response:**

```json
{
  "cod": "200",
  "message": 0,
  "cnt": 40,
  "list": [
    {
      "dt": 1746874800,
      "dt_txt": "2026-05-10 15:00:00",         // ← CAMPO CRÍTICO (timestamp UTC)
      "main": {
        "temp": 20.29,                          // ← CAMPO CRÍTICO (temperatura °C)
        "feels_like": 19.85,
        "temp_min": 18.50,
        "temp_max": 20.29,
        "pressure": 1018,
        "humidity": 65,                         // ← CAMPO CRÍTICO (humedad %)
        "temp_kf": 0
      },
      "weather": [
        {
          "id": 803,                            // ← CAMPO CRÍTICO (código condición)
          "main": "Clouds",                     // ← CAMPO CRÍTICO (categoría)
          "description": "broken clouds",       // ← CAMPO CRÍTICO (descripción)
          "icon": "04d"
        }
      ],
      "clouds": {
        "all": 82                               // ← CAMPO CRÍTICO (nubosidad %)
      },
      "wind": {
        "speed": 5.54,                          // ← CAMPO CRÍTICO (viento m/s)
        "deg": 215,
        "gust": 8.20
      },
      "visibility": 10000,
      "pop": 0.15,                              // ← CAMPO CRÍTICO (prob. lluvia [0-1])
      "sys": {
        "pod": "d"                              // ← CAMPO CRÍTICO ('d'=día, 'n'=noche)
      },
      "rain": {                                 // ← OPCIONAL (sólo si hay lluvia)
        "3h": 0.5
      },
      "snow": {                                 // ← OPCIONAL (sólo si hay nieve)
        "3h": 0.0
      }
    }
    // ... 39 objetos más (total: 40 tramos de 3h = 120h = 5 días)
  ],
  "city": {
    "id": 3114992,
    "name": "Pamplona",
    "coord": {
      "lat": 42.8038,
      "lon": -1.7020
    },
    "country": "ES",
    "population": 195853,
    "timezone": 7200,
    "sunrise": 1746848100,
    "sunset": 1746899760
  }
}
```

**Campos críticos extraídos por SunSaver:**

| Campo JSON | Campo Silver | Tipo | Garantizado | Impacto si falta |
|-----------|-------------|------|------------|-----------------|
| `list[].dt_txt` | `forecast_time_utc` | STRING UTC | ✅ Siempre | Sin timestamp → registro descartado |
| `list[].main.temp` | `temp_celsius` | FLOAT (°C) | ✅ Siempre | Interpolado desde vecinos |
| `list[].main.humidity` | `humidity_pct` | INTEGER (%) | ✅ Siempre | Interpolado desde vecinos |
| `list[].clouds.all` | `clouds_pct` | INTEGER (%) | ✅ Siempre | Motor GHI falla → `pv_power_gen_kw = 0` |
| `list[].pop` | `rain_prob_norm` | FLOAT [0–1] | ✅ Siempre | `fillna(0)` — sin impacto en cálculos PV |
| `list[].wind.speed` | `wind_speed_mps` | FLOAT (m/s) | ✅ Siempre | Modelo Faiman: `t_cell` menos precisa |
| `list[].weather[0].id` | `weather_id` | INTEGER | ✅ Siempre | Motor GHI usa factor por defecto |
| `list[].weather[0].main` | `weather_main` | STRING | ✅ Siempre | Descriptivo; no afecta cálculos |
| `list[].weather[0].description` | `weather_description` | STRING | ✅ Siempre | Descriptivo; no afecta cálculos |
| `list[].sys.pod` | `is_daylight` | CHAR | ⚠️ Opcional | `ffill` — impacto mínimo |

**Campos descartados** (presentes en la respuesta pero no consumidos por SunSaver):

```
list[].dt             → no usado (se usa dt_txt por legibilidad)
list[].main.feels_like, temp_min, temp_max, pressure, temp_kf
list[].weather[0].icon
list[].wind.deg, wind.gust
list[].visibility
list[].rain.3h, list[].snow.3h
city.*                → no usado (coordenadas ya conocidas de clean_clients)
```

**Códigos de estado HTTP:**

| Código | Significado | Acción implementada |
|--------|-------------|-------------------|
| `200` | Éxito | Parsear JSON y persistir en Bronze |
| `200` con payload vacío | Anomalía — rarísima | `raise ValueError("empty payload")` |
| `401` | API key inválida o no configurada | Log ERROR "API key error" + `raise` |
| `404` | Coordenadas sin cobertura | Log ERROR + `raise` — revisar coordenadas |
| `429` | Rate limit excedido | Log ERROR "rate limit" + `raise` (roadmap: retry con backoff) |
| `500`, `503` | Error servidor OWM | Log ERROR + `raise` — se registra como `error` en manifest |
| Timeout (> 15s) | Sin respuesta | `requests.exceptions.Timeout` + `raise` |

#### 2.2.5 Paginación

**No aplica.** El endpoint devuelve todos los tramos disponibles (máximo 40, correspondientes a 120 horas / 5 días) en una única respuesta. El parámetro `cnt` puede limitar el número de tramos pero no se usa en SunSaver.

Volumen de respuesta estimado: **~35–50 KB** por cliente (40 tramos × ~1 KB por tramo con todos los campos).

#### 2.2.6 Rate Limits

| Plan | Llamadas/minuto | Llamadas/mes | Endpoints incluidos |
|------|----------------|-------------|-------------------|
| **Free** | 60 | 1.000.000 | `/forecast`, `/weather` y otros básicos |
| **Startup** | 600 | 10.000.000 | Igual + One Call API |
| **Professional** | 3.000 | Sin límite | Todos los endpoints + SLA 99,9% |

**SunSaver en DEV (Free tier):**

```
Llamadas por ejecución: N_clientes × 1
Con 5 clientes:         5 llamadas/día     → 150 llamadas/mes  → muy por debajo del límite
Con 100 clientes:       100 llamadas/día   → 3.000 llamadas/mes → dentro del Free tier
Con 500 clientes:       500 llamadas/día   → 15.000 llamadas/mes → requiere plan Startup
Con 33.000+ clientes:   33.000 llamadas/día → límite del Free tier
```

**Headers de quota en la respuesta:**

```
X-RateLimit-Limit:     60         (llamadas/minuto permitidas)
X-RateLimit-Remaining: 55         (llamadas restantes en la ventana actual)
X-RateLimit-Reset:     1746875460 (timestamp EPOCH cuando se resetea la ventana)
```

**Estrategia de throttling implementada:**  
Ninguna explícita en la versión DEV (adecuado para < 50 clientes). Para producción con muchos clientes:

```python
# Añadir en bronze_ingest_weather_owm.py, dentro del bucle de clientes
import time

for _, row in df_clients.iterrows():
    try:
        raw_weather = extract_weather(row["latitude"], row["longitude"])
        # ... proceso normal ...
        time.sleep(1.1)   # garantiza <= 54 llamadas/minuto (< límite de 60)
    except Exception:
        # ... manejo de error ...
        time.sleep(1.1)   # throttling incluso en error
```

#### 2.2.7 Manejo de Errores Específicos

| Código OWM / Escenario | Detección | Mensaje de error OWM | Acción |
|------------------------|-----------|---------------------|--------|
| API key no configurada | `API_KEY is None` | — | Log ERROR + `return {}` |
| API key inválida | HTTP 401 | `{"cod": 401, "message": "Invalid API key"}` | Log ERROR + `raise` |
| Coordenadas fuera de cobertura | HTTP 404 | `{"cod": "404", "message": "city not found"}` | Log ERROR + `raise` — revisar coordenadas del cliente |
| Rate limit excedido | HTTP 429 | `{"cod": 429, "message": "..."}` | Log ERROR + `raise` — roadmap: retry con backoff |
| Payload vacío | `not data` | — | `raise ValueError("empty payload")` |
| Lista de forecast vacía | `len(list) == 0` | — | Registro omitido + `error_count += 1` |
| Timeout de red | `requests.Timeout` | — | Log ERROR + `raise` |
| Error de conexión | `requests.ConnectionError` | — | Log ERROR + `raise` |

#### 2.2.8 Contrato de Datos

**Campos garantizados** (presentes en toda respuesta 200 válida):

```
cod                               → "200" si éxito
cnt                               → número de tramos (máximo 40)
list[].dt_txt                     → timestamp UTC en formato "YYYY-MM-DD HH:MM:SS"
list[].main.temp                  → temperatura en °C (units=metric)
list[].main.humidity              → humedad relativa %
list[].clouds.all                 → nubosidad %
list[].pop                        → probabilidad de precipitación [0.0–1.0]
list[].wind.speed                 → velocidad del viento m/s
list[].weather[0].id              → código de condición meteorológica
list[].weather[0].main            → categoría meteorológica
list[].weather[0].description     → descripción detallada
```

**Campos opcionales** (pueden estar ausentes):

```
list[].sys.pod                    → ausente en algunos tramos nocturnos
list[].rain                       → sólo presente si hay precipitación prevista
list[].snow                       → sólo presente si hay nieve prevista
list[].visibility                 → puede estar ausente en algunos casos
```

**Política de breaking changes:**  
OpenWeatherMap tiene un historial de cambios de API con aviso previo de 6 meses vía email a usuarios registrados y en el foro de la comunidad. La versión `data/2.5/forecast` ha sido estable desde 2015.

**Versión de API en uso:** `v2.5` (URL: `/data/2.5/forecast`)  
**Próxima versión disponible:** `v3.0` (One Call API — requiere suscripción de pago incluso para uso básico)

**Plan de migración a v3.0 si se depreca v2.5:**

```python
# Cambio en URL base (v2.5 → v3.0)
# URL actual:
"https://api.openweathermap.org/data/2.5/forecast"

# URL futura (One Call API v3.0):
"https://api.openweathermap.org/data/3.0/onecall"
# Parámetros cambian: exclude, part (minutely, hourly, daily, alerts)
# Estructura de respuesta completamente diferente → requiere nuevo parser en Silver
```

---

### 2.3 Fuente Excel — Maestro de Clientes

#### 2.3.1 Identificador único de integración

```
ID:          INT-003
Nombre:      Maestro de Clientes (clients_source.xlsx)
Módulo:      bronze_ingest_clients.py
Función:     extract_clients_from_excel()
Criticidad:  CRÍTICA (sin clientes no hay pipeline)
```

#### 2.3.2 Proveedor y Documentación

| Atributo | Valor |
|----------|-------|
| **Origen** | Equipo de Operaciones / Negocio de SunSaver |
| **Formato** | Microsoft Excel (.xlsx) |
| **Librería de lectura** | `pandas` + `openpyxl` |
| **Ruta en proyecto** | `data/clients_source.xlsx` (configurable vía `get_client_path()`) |
| **Propietario del fichero** | Equipo de Operaciones — actualización manual |
| **Frecuencia de actualización** | Evento-driven (al añadir o modificar instalaciones) |

#### 2.3.3 Tipo de Autenticación

**Sin autenticación.** Fichero local en el sistema de ficheros. El acceso está controlado por permisos del sistema operativo.

#### 2.3.4 Especificación del Formato de Fichero

**Estructura esperada:**

- Primera fila: cabeceras de columna (nombres exactos requeridos por el extractor)
- Filas siguientes: un registro por instalación
- Sin celdas combinadas, sin hojas múltiples (sólo se lee la primera hoja)
- Encoding: UTF-8 (Excel default)

**Dependencia de librería:**

```python
# bronze_ingest_clients.py
try:
    df = pd.read_excel(excel_path)
except ImportError:
    logger.error("[EXTRACT] Missing dependency 'openpyxl' — run: pip install openpyxl")
    return []
```

> `openpyxl` es una dependencia **explícita y obligatoria** para leer ficheros `.xlsx`. Si no está instalada, el pipeline falla con un error claro en el log en lugar de una excepción críptica.

**Verificación de disponibilidad del fichero:**

```python
BASE_DIR   = Path(__file__).resolve().parent.parent
excel_path = BASE_DIR / "data" / "clients_source.xlsx"

if not excel_path.exists():
    logger.error("[EXTRACT] File not found: %s", excel_path)
    return []
```

**Cabeceras requeridas** (el extractor falla silenciosamente si faltan campos críticos — la validación se realiza en Silver):

```
client_id, name, description, latitude, longitude, timezone,
nominal_load_kw, pv_peak_power_kw, panel_area_m2, efficiency,
panel_type, loss_pct, angle, aspect, mounting,
battery_capacity_kwh, soc_min_pct, installation_cost_eur
```

**Códigos de error / estado:**

| Escenario | Detección | Acción |
|-----------|-----------|--------|
| Fichero no existe | `not excel_path.exists()` | Log ERROR + `return []` |
| `openpyxl` no instalado | `ImportError` | Log ERROR con instrucción de instalación + `return []` |
| Fichero corrupto / no es Excel | `Exception` en `pd.read_excel()` | Log ERROR + `return []` |
| Fichero vacío (sólo cabecera) | `df.empty` | Log WARNING + `return []` |
| Campos críticos ausentes | NaN tras `pd.to_numeric()` | Silver aplica `dropna()` — registros descartados |

#### 2.3.5 Paginación

**No aplica.** El fichero completo se carga en memoria en una única operación `pd.read_excel()`. Para ficheros > 100.000 filas, usar `pd.read_excel(chunksize=N)`.

#### 2.3.6 Rate Limits

**No aplica.** Fichero local sin límites de acceso.

#### 2.3.7 Contrato de Datos

**Campos obligatorios** (el registro se descarta en Silver si están ausentes):

```
client_id           → clave primaria — debe ser única y no nula
name                → nombre de la instalación
latitude            → latitud WGS84 — necesaria para llamar a OWM
longitude           → longitud WGS84 — necesaria para llamar a OWM
pv_peak_power_kw    → potencia pico — base del cálculo de generación
```

**Campos opcionales con imputación por defecto:**

```
angle               → defecto: 30° (inclinación óptima España)
aspect              → defecto: 180° (orientación Sur)
loss_pct            → defecto: 14% (pérdidas típicas)
efficiency          → defecto: 0.15 (eficiencia panel monoSi)
nominal_load_kw     → defecto: pv_peak_power_kw × 1.3
battery_capacity_kwh → defecto: 0 (sin batería)
soc_min_pct         → defecto: 20%
installation_cost_eur → defecto: 0 (no informado)
timezone            → defecto: 'UTC'
```

---

## 3. Patrones de Resiliencia

### 3.1 Circuit Breaker por API

Un circuit breaker detecta fallos repetidos y "abre el circuito" para evitar sobrecarga del sistema externo y esperas innecesarias en el pipeline.

**Estado actual:** no implementado formalmente. El comportamiento actual es equivalente a un circuit breaker simplificado: si la llamada falla, el módulo retorna `False` o `{}` inmediatamente (sin reintentos en la misma ejecución), y el pipeline continúa.

**Especificación del circuit breaker para producción:**

```python
# Roadmap: implementar en utils/circuit_breaker.py
import time
from enum import Enum

class CircuitState(Enum):
    CLOSED    = "CLOSED"    # normal — las llamadas pasan
    OPEN      = "OPEN"      # fallo detectado — las llamadas se bloquean
    HALF_OPEN = "HALF_OPEN" # prueba — se permite una llamada de prueba

class CircuitBreaker:
    def __init__(self, name: str, failure_threshold: int = 3,
                 recovery_timeout: int = 300):
        self.name              = name
        self.failure_threshold = failure_threshold   # fallos para abrir circuito
        self.recovery_timeout  = recovery_timeout    # segundos hasta HALF_OPEN
        self.failure_count     = 0
        self.last_failure_time = None
        self.state             = CircuitState.CLOSED

    def call(self, fn, *args, **kwargs):
        if self.state == CircuitState.OPEN:
            if time.time() - self.last_failure_time > self.recovery_timeout:
                self.state = CircuitState.HALF_OPEN
            else:
                raise RuntimeError(f"Circuit OPEN for {self.name} — skipping call")

        try:
            result = fn(*args, **kwargs)
            self._on_success()
            return result
        except Exception as exc:
            self._on_failure()
            raise exc

    def _on_success(self):
        self.failure_count = 0
        self.state = CircuitState.CLOSED

    def _on_failure(self):
        self.failure_count += 1
        self.last_failure_time = time.time()
        if self.failure_count >= self.failure_threshold:
            self.state = CircuitState.OPEN

# Uso en el extractor OWM:
owm_breaker = CircuitBreaker("openweathermap", failure_threshold=3, recovery_timeout=300)

for _, row in df_clients.iterrows():
    try:
        raw = owm_breaker.call(extract_weather, row["latitude"], row["longitude"])
    except RuntimeError as e:
        logger.warning("[CIRCUIT] %s — omitiendo cliente %s", e, row["client_id"])
        continue
```

**Configuración de circuit breaker por API:**

| API | Threshold de fallos | Timeout de recuperación | Justificación |
|-----|--------------------|-----------------------|---------------|
| `INT-001` REE | 1 fallo | 30 min | 1 sola llamada/día; si falla = datos no disponibles |
| `INT-002` OWM | 3 fallos consecutivos | 5 min | Fallos por cliente son normales; circuito se abre si > 3 seguidos |
| `INT-003` Excel | N/A | N/A | Fichero local; sin circuit breaker |

---

### 3.2 Política de Retries con Backoff

**Implementación actual:** sin retries automáticos dentro de la misma ejecución. Los fallos se registran en el manifest Bronze como `status: "error"` y se reintenta en la siguiente ejecución programada del pipeline (vía cron).

**Implementación recomendada para producción:**

```python
# utils/retry.py — decorador de retry con exponential backoff
import time
import functools
import logging

logger = logging.getLogger("SunSaver")

def retry_with_backoff(max_retries: int = 3, base_delay: float = 2.0,
                       max_delay: float = 60.0, exceptions: tuple = (Exception,)):
    """
    Decorador que reintenta una función con backoff exponencial.

    Delays: base_delay^1, base_delay^2, base_delay^3, ...
    Con base_delay=2: 2s, 4s, 8s (capped a max_delay)
    """
    def decorator(fn):
        @functools.wraps(fn)
        def wrapper(*args, **kwargs):
            last_exc = None
            for attempt in range(1, max_retries + 1):
                try:
                    return fn(*args, **kwargs)
                except exceptions as exc:
                    last_exc = exc
                    if attempt == max_retries:
                        logger.error(
                            "[RETRY] %s — %d/%d intentos agotados: %s",
                            fn.__name__, attempt, max_retries, exc
                        )
                        break
                    delay = min(base_delay ** attempt, max_delay)
                    logger.warning(
                        "[RETRY] %s — intento %d/%d fallido (%s). Reintentando en %.1fs...",
                        fn.__name__, attempt, max_retries, exc, delay
                    )
                    time.sleep(delay)
            raise last_exc
        return wrapper
    return decorator


# Aplicación en el extractor OWM:
@retry_with_backoff(
    max_retries=3,
    base_delay=2.0,
    exceptions=(requests.exceptions.RequestException,)
)
def extract_weather(lat: float, lon: float) -> dict:
    response = requests.get(
        "https://api.openweathermap.org/data/2.5/forecast",
        params={...},
        timeout=15,
    )
    response.raise_for_status()
    return response.json()
```

**Política de retries por API y tipo de error:**

| API | Error | ¿Reintentar? | Delays | Máx. intentos | Justificación |
|-----|-------|------------|-------|--------------|--------------|
| OWM | Timeout (< 15s) | ✅ SÍ | 2s, 4s, 8s | 3 | Error transitorio de red |
| OWM | HTTP 429 (rate limit) | ✅ SÍ | 60s, 120s, 300s | 3 | Esperar ventana de rate limit |
| OWM | HTTP 503 (servicio no disponible) | ✅ SÍ | 30s, 60s, 120s | 3 | Indisponibilidad transitoria |
| OWM | HTTP 401 (API key inválida) | ❌ NO | — | — | Error de configuración, no transitorio |
| OWM | HTTP 404 (coordenadas inválidas) | ❌ NO | — | — | Error de datos, no transitorio |
| REE | Timeout | ✅ SÍ | 5s, 15s, 30s | 3 | Error transitorio de red |
| REE | HTTP 5xx | ❌ NO | — | — | Datos no publicados aún — esperar siguiente ejecución |
| REE | HTTP 4xx | ❌ NO | — | — | Error de parámetros — no reintentable |

---

### 3.3 Fallback y Datos de Caché

**Estrategia de fallback actual:**

| API | Fallback implementado | Descripción |
|-----|----------------------|-------------|
| `INT-001` REE | `PARTIAL SUCCESS` | Gold se carga con `price_pvpc_eur_mwh = NULL`. Se actualiza en la siguiente ejecución cuando el precio llegue. |
| `INT-002` OWM | Datos del día anterior (implícito en Silver) | `clean_weather` retiene datos de ejecuciones anteriores gracias al `INSERT OR REPLACE`. Si OWM falla hoy, los cálculos PV usan la previsión de ayer (válida para el futuro solapado). |
| `INT-003` Excel | Datos de `clean_clients` existente en SQLite | Si el Excel no está disponible o falla, `clean_clients` de la ejecución anterior sigue disponible para el pipeline (el módulo Bronze simplemente no actualiza). |

**Implementación del fallback para OWM (roadmap):**

```python
# silver_transform_weather.py — usar datos de la ejecución anterior si OWM falla
def get_weather_with_fallback(client_id: str, db_path: str) -> pd.DataFrame:
    """
    Intenta leer los datos meteorológicos frescos del manifest Bronze.
    Si no hay datos nuevos, usa los últimos datos disponibles en clean_weather.
    """
    # 1. Intentar datos frescos del manifest
    fresh_data = transform_openweather_for_client(client_id)

    if not fresh_data.empty:
        return fresh_data

    # 2. Fallback: usar datos históricos de clean_weather (ya en SQLite)
    logger.warning(
        "[FALLBACK] No hay datos OWM frescos para %s — usando previsión anterior",
        client_id
    )
    with sqlite3.connect(db_path) as conn:
        return pd.read_sql(
            "SELECT * FROM clean_weather WHERE client_id = ? AND unix_time >= ?",
            conn, params=(client_id, int(time.time()))
        )
```

---

### 3.4 Health Checks de Conectores

**Health check recomendado** — ejecutar antes del pipeline o como monitorización periódica:

```python
# utils/health_check.py
import requests
import os
import sqlite3
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

def check_ree_api() -> dict:
    """Verifica que la API de REE responde correctamente."""
    try:
        response = requests.get(
            "https://apidatos.ree.es/es/datos/mercados/precios-mercados-tiempo-real"
            "?start_date=2026-01-01T00:00&end_date=2026-01-01T01:00"
            "&time_trunc=hour&geo_trunc=electric_system&geo_limit=peninsular&geo_ids=8741",
            headers={"Accept": "application/json"},
            timeout=10,
        )
        return {
            "api":    "REE PVPC",
            "status": "OK" if response.status_code == 200 else "ERROR",
            "code":   response.status_code,
            "ms":     response.elapsed.total_seconds() * 1000,
        }
    except Exception as exc:
        return {"api": "REE PVPC", "status": "ERROR", "error": str(exc)}


def check_owm_api() -> dict:
    """Verifica que la API de OWM responde con la API key configurada."""
    api_key = os.getenv("WEATHER_API_KEY")
    if not api_key:
        return {"api": "OWM", "status": "ERROR", "error": "WEATHER_API_KEY not set"}
    try:
        response = requests.get(
            "https://api.openweathermap.org/data/2.5/forecast",
            params={"lat": 40.0, "lon": -3.7, "appid": api_key, "cnt": 1},
            timeout=10,
        )
        return {
            "api":    "OpenWeatherMap",
            "status": "OK" if response.status_code == 200 else "ERROR",
            "code":   response.status_code,
            "ms":     response.elapsed.total_seconds() * 1000,
        }
    except Exception as exc:
        return {"api": "OpenWeatherMap", "status": "ERROR", "error": str(exc)}


def check_excel_source() -> dict:
    """Verifica que el fichero Excel de clientes existe y es legible."""
    from config_paths import get_client_path
    path = get_client_path()
    exists = path.exists()
    return {
        "api":    "Excel clientes",
        "status": "OK" if exists else "ERROR",
        "path":   str(path),
        "error":  None if exists else "Fichero no encontrado",
    }


def run_health_checks() -> bool:
    """Ejecuta todos los health checks y devuelve True si todos pasan."""
    results = [check_ree_api(), check_owm_api(), check_excel_source()]
    all_ok  = True
    print("\n── Health Checks de Conectores ────────────────────")
    for r in results:
        icon = "✅" if r["status"] == "OK" else "❌"
        ms   = f" ({r['ms']:.0f}ms)" if "ms" in r else ""
        err  = f" — {r['error']}" if r.get("error") else ""
        print(f"  {icon}  {r['api']}{ms}{err}")
        if r["status"] != "OK":
            all_ok = False
    print("────────────────────────────────────────────────────\n")
    return all_ok


if __name__ == "__main__":
    import sys
    sys.exit(0 if run_health_checks() else 1)
```

**Ejecución:**

```bash
# Antes de lanzar el pipeline:
python src/utils/health_check.py && python src/pipeline_runner.py

# Como cron independiente de monitorización (cada hora):
0 * * * * python /path/to/sunsaver/src/utils/health_check.py >> /var/log/sunsaver_health.log 2>&1
```

---

## 4. Configuración y Secretos

### 4.1 Variables de Entorno Requeridas por Integración

| Variable | Integración | Obligatoria | Descripción | Ejemplo (no real) |
|----------|-------------|------------|-------------|------------------|
| `WEATHER_API_KEY` | `INT-002` OWM | ✅ **SÍ** | API Key de OpenWeatherMap. Sin ella el módulo retorna `{}` para todos los clientes. | `a1b2c3d4e5f6789012345678901234ab` |
| `DB_PATH` | Todos | ❌ NO | Ruta absoluta a la base de datos SQLite. Default: `{PROJECT_ROOT}/data/sunsaver.db` | `/data/sunsaver/sunsaver.db` |
| `BRONZE_PATH` | Todos | ❌ NO | Ruta absoluta al directorio Bronze. Default: `{PROJECT_ROOT}/data/bronze` | `/data/sunsaver/bronze/` |

**Dónde se usa cada variable:**

```python
# config_paths.py — punto único de resolución de rutas
def get_db_path() -> Path:
    load_dotenv()
    _db_path_env = os.getenv("DB_PATH")
    return Path(_db_path_env) if _db_path_env else BASE_DIR / "data" / "sunsaver.db"

def get_bronze_path() -> Path:
    load_dotenv()
    _bronze_path_env = os.getenv("BRONZE_PATH")
    return Path(_bronze_path_env) if _bronze_path_env else BASE_DIR / "data" / "bronze"

# bronze_ingest_weather_owm.py — acceso a API key
API_KEY = os.getenv("WEATHER_API_KEY")
```

**Verificación de configuración antes de ejecutar:**

```bash
# Verificar que todas las variables obligatorias están configuradas
python -c "
import os
from dotenv import load_dotenv
load_dotenv()
required = ['WEATHER_API_KEY']
missing  = [v for v in required if not os.getenv(v)]
if missing:
    print('❌ Variables faltantes:', missing)
    exit(1)
print('✅ Configuración correcta')
"
```

---

### 4.2 Rotación de Credenciales

| Credencial | Frecuencia recomendada | Proceso | Impacto en pipeline |
|------------|----------------------|---------|-------------------|
| `WEATHER_API_KEY` (OWM) | Cada 90 días o ante sospecha de compromiso | 1. Crear nueva key en portal OWM. 2. Actualizar `.env`. 3. Verificar con health check. 4. Revocar key anterior en portal OWM. | 0 downtime si se hace fuera del horario de ejecución del pipeline |
| Credenciales del servidor (SSH, etc.) | Política del equipo de DevOps | Separada de este documento | Sin impacto en las APIs |

**Proceso de rotación de `WEATHER_API_KEY`:**

```bash
# 1. Crear nueva key en https://home.openweathermap.org/api_keys

# 2. Probar la nueva key ANTES de revocar la anterior
curl "https://api.openweathermap.org/data/2.5/weather\
?lat=40&lon=-3&appid=NUEVA_KEY" | python -m json.tool | head -5

# 3. Actualizar .env con la nueva key
sed -i 's/WEATHER_API_KEY=.*/WEATHER_API_KEY=NUEVA_KEY/' .env

# 4. Verificar con health check
python src/utils/health_check.py

# 5. Revocar la key anterior en el portal OWM
```

---

### 4.3 Gestión de Secretos

**DEV — Fichero `.env` local:**

```
Mecanismo:    python-dotenv (.env en raíz del proyecto)
Seguridad:    .env incluido en .gitignore — nunca versionado
Distribución: Manual — compartir por canal seguro (1Password, Signal, etc.)
Backup:       Responsabilidad del desarrollador
```

**Producción — Opciones recomendadas por orden de preferencia:**

| Opción | Complejidad | Seguridad | Caso de uso |
|--------|------------|----------|------------|
| **HashiCorp Vault** | Alta | ⭐⭐⭐⭐⭐ | Entorno empresarial con múltiples servicios y rotación automática |
| **AWS Secrets Manager** | Media | ⭐⭐⭐⭐⭐ | Despliegue en AWS — integración nativa con IAM |
| **Google Secret Manager** | Media | ⭐⭐⭐⭐⭐ | Despliegue en GCP |
| **Azure Key Vault** | Media | ⭐⭐⭐⭐⭐ | Despliegue en Azure |
| **Variables de entorno del sistema** | Baja | ⭐⭐⭐ | Servidor dedicado simple — sin `.env` en disco |
| **`.env` encriptado (git-crypt)** | Baja | ⭐⭐⭐ | Equipo pequeño con repositorio privado |

**Integración con AWS Secrets Manager (ejemplo de migración):**

```python
# utils/secrets.py — abstracción de gestión de secretos
import os
import json

def get_secret(secret_name: str) -> str:
    """
    Obtiene un secreto. En DEV usa .env; en producción usa AWS Secrets Manager.
    La variable ENV determina el comportamiento.
    """
    env = os.getenv("SUNSAVER_ENV", "dev")

    if env == "dev":
        # DEV: usar .env via python-dotenv
        from dotenv import load_dotenv
        load_dotenv()
        return os.getenv(secret_name, "")

    elif env == "production":
        # PRODUCCIÓN: usar AWS Secrets Manager
        import boto3
        client = boto3.client("secretsmanager", region_name="eu-west-1")
        response = client.get_secret_value(SecretId=f"sunsaver/{secret_name}")
        return json.loads(response["SecretString"])[secret_name]

    raise ValueError(f"Entorno desconocido: {env}")

# Uso en módulos de ingesta:
API_KEY = get_secret("WEATHER_API_KEY")
```

---

## 5. Testing de Integraciones

### 5.1 Sandbox / Entornos de Prueba Disponibles

| Integración | Sandbox disponible | Detalles |
|-------------|-------------------|---------|
| `INT-001` REE | ❌ No existe sandbox oficial | Usar datos históricos del endpoint real (la API no cobra por lectura de histórico) o fixtures JSON guardados de ejecuciones reales |
| `INT-002` OWM | ✅ Sí — Free tier actúa como sandbox | La misma API key del Free tier sirve para desarrollo. Usar coordenadas de prueba (ej. Madrid: lat=40.4, lon=-3.7) |
| `INT-003` Excel | ✅ Usar fichero de prueba | `tests/fixtures/clients_test.xlsx` con 2-3 instalaciones ficticias |

**Fichero de fixture para tests de Excel:**

```python
# tests/conftest.py
import pytest
import pandas as pd
from pathlib import Path

@pytest.fixture
def sample_clients_excel(tmp_path):
    """Genera un Excel de clientes de prueba en un directorio temporal."""
    data = [
        {
            "client_id": "TEST001", "name": "Test Plant A",
            "latitude": 40.4168, "longitude": -3.7038,
            "pv_peak_power_kw": 10.0, "angle": 30.0, "aspect": 180.0,
            "loss_pct": 14.0, "efficiency": 0.20, "nominal_load_kw": 15.0,
            "panel_area_m2": 50.0, "panel_type": "monoSi", "mounting": "rooftop",
            "battery_capacity_kwh": 10.0, "soc_min_pct": 20.0,
            "installation_cost_eur": 12000.0, "timezone": "Europe/Madrid",
            "description": "Instalación de prueba A",
        },
        {
            "client_id": "TEST002", "name": "Test Plant B",
            "latitude": 41.3851, "longitude": 2.1734,
            "pv_peak_power_kw": 25.0, "angle": 25.0, "aspect": 175.0,
            "loss_pct": 12.0, "efficiency": 0.22, "nominal_load_kw": 30.0,
            "panel_area_m2": 114.0, "panel_type": "bifacial", "mounting": "ground",
            "battery_capacity_kwh": 0.0, "soc_min_pct": 20.0,
            "installation_cost_eur": 28000.0, "timezone": "Europe/Madrid",
            "description": "Instalación de prueba B (sin batería)",
        },
    ]
    excel_path = tmp_path / "clients_test.xlsx"
    pd.DataFrame(data).to_excel(excel_path, index=False)
    return excel_path
```

---

### 5.2 Mock Responses para Tests Unitarios

**Mock de respuesta REE (fixture completo):**

```python
# tests/fixtures/mock_ree_response.py

REE_RESPONSE_SUCCESS = {
    "data": {
        "type": "Precios mercados de tiempo real",
        "id": "pmh",
        "attributes": {"title": "Precios", "last-update": "2026-05-10T20:35:00.000+02:00"}
    },
    "included": [
        {
            "type": "Precio mercados de tiempo real",
            "id": "1001",
            "groupId": "11",
            "attributes": {
                "title": "PVPC (Tarifa VPSC)",
                "last-update": "2026-05-10T20:35:00.000+02:00",
                "magnitude": "€/MWh",
                "values": [
                    {"value": 142.80, "percentage": 65.3, "datetime": "2026-05-11T00:00:00.000+02:00"},
                    {"value": 135.20, "percentage": 62.1, "datetime": "2026-05-11T01:00:00.000+02:00"},
                    {"value": 128.90, "percentage": 59.3, "datetime": "2026-05-11T02:00:00.000+02:00"},
                    # ... añadir los 24 valores para tests completos
                ]
            }
        }
    ]
}

REE_RESPONSE_EMPTY = {
    "data": {"type": "Precios mercados de tiempo real"},
    "included": [
        {
            "id": "1001",
            "attributes": {"values": []}  # ← precios no publicados aún
        }
    ]
}

# tests/fixtures/mock_owm_response.py
OWM_RESPONSE_SUCCESS = {
    "cod": "200",
    "message": 0,
    "cnt": 3,   # reducido para tests (normalmente 40)
    "list": [
        {
            "dt": 1746874800,
            "dt_txt": "2026-05-10 15:00:00",
            "main": {"temp": 20.29, "humidity": 65, "pressure": 1018,
                     "feels_like": 19.85, "temp_min": 18.5, "temp_max": 20.29, "temp_kf": 0},
            "weather": [{"id": 803, "main": "Clouds", "description": "broken clouds", "icon": "04d"}],
            "clouds": {"all": 82},
            "wind": {"speed": 5.54, "deg": 215, "gust": 8.20},
            "visibility": 10000,
            "pop": 0.15,
            "sys": {"pod": "d"},
        },
        {
            "dt": 1746885600,
            "dt_txt": "2026-05-10 18:00:00",
            "main": {"temp": 18.10, "humidity": 72, "pressure": 1019,
                     "feels_like": 17.50, "temp_min": 17.0, "temp_max": 18.1, "temp_kf": 0},
            "weather": [{"id": 801, "main": "Clouds", "description": "few clouds", "icon": "02n"}],
            "clouds": {"all": 20},
            "wind": {"speed": 3.20, "deg": 200, "gust": 5.10},
            "visibility": 10000,
            "pop": 0.05,
            "sys": {"pod": "n"},
        },
    ],
    "city": {
        "id": 3114992, "name": "Pamplona",
        "coord": {"lat": 42.8038, "lon": -1.7020},
        "country": "ES", "timezone": 7200,
    }
}

OWM_RESPONSE_UNAUTHORIZED = {
    "cod": 401,
    "message": "Invalid API key. Please see https://openweathermap.org/faq#error401 for more info."
}
```

**Uso de mocks en tests:**

```python
# tests/unit/test_bronze_ingest_prices_ree.py
from unittest.mock import patch, MagicMock
from tests.fixtures.mock_ree_response import REE_RESPONSE_SUCCESS, REE_RESPONSE_EMPTY
from bronze_ingest_prices_ree import extract_raw_json_from_ree

def test_extract_returns_data_when_available():
    """Cuando REE devuelve precios, el extractor debe retornar el payload filtrado."""
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = REE_RESPONSE_SUCCESS

    with patch("bronze_ingest_prices_ree.requests.get", return_value=mock_response):
        result = extract_raw_json_from_ree()

    assert result is not False
    assert len(result["included"]) == 1
    assert result["included"][0]["id"] == "1001"
    assert len(result["included"][0]["attributes"]["values"]) > 0


def test_extract_returns_false_when_no_prices():
    """Cuando REE devuelve lista vacía, debe retornar False (PARTIAL SUCCESS)."""
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = REE_RESPONSE_EMPTY

    with patch("bronze_ingest_prices_ree.requests.get", return_value=mock_response):
        result = extract_raw_json_from_ree()

    assert result is False


def test_extract_returns_false_on_server_error():
    """HTTP 503 debe retornar False sin lanzar excepción."""
    mock_response = MagicMock()
    mock_response.status_code = 503
    mock_response.raise_for_status.side_effect = Exception("503 Server Error")

    with patch("bronze_ingest_prices_ree.requests.get", return_value=mock_response):
        result = extract_raw_json_from_ree()

    assert result is False


def test_extract_returns_false_on_timeout():
    """Timeout de red debe retornar False sin propagar la excepción."""
    import requests as req
    with patch("bronze_ingest_prices_ree.requests.get",
               side_effect=req.exceptions.Timeout("timeout")):
        result = extract_raw_json_from_ree()

    assert result is False
```

---

### 5.3 Contract Tests Implementados

Los contract tests verifican que las respuestas de las APIs externas siguen cumpliendo el contrato de datos que el sistema espera. A diferencia de los unit tests (que usan mocks), los contract tests **llaman a las APIs reales** y validan la estructura de la respuesta.

> **Estado actual:** especificados como roadmap. Ejecutar en CI/CD periódicamente (diariamente), no en cada commit.

```python
# tests/contracts/test_api_contracts.py
import os
import pytest
import requests
from datetime import datetime, timedelta
from dotenv import load_dotenv

load_dotenv()

# Marcar como tests de integración (requieren conectividad real)
pytestmark = pytest.mark.integration


class TestREEContract:

    BASE_URL = (
        "https://apidatos.ree.es/es/datos/mercados/precios-mercados-tiempo-real"
        "?start_date=2026-01-01T00:00&end_date=2026-01-01T23:59"
        "&time_trunc=hour&geo_trunc=electric_system&geo_limit=peninsular&geo_ids=8741"
    )
    HEADERS = {"Accept": "application/json", "Origin": "https://www.ree.es"}

    def test_ree_api_reachable(self):
        """La API de REE debe responder en menos de 10 segundos."""
        response = requests.get(self.BASE_URL, headers=self.HEADERS, timeout=10)
        assert response.status_code == 200

    def test_ree_response_contains_included(self):
        """La respuesta debe contener la clave 'included'."""
        response = requests.get(self.BASE_URL, headers=self.HEADERS, timeout=10)
        data = response.json()
        assert "included" in data, "Estructura raíz sin 'included'"

    def test_ree_pvpc_series_present(self):
        """La serie con id='1001' (PVPC) debe estar presente en 'included'."""
        response = requests.get(self.BASE_URL, headers=self.HEADERS, timeout=10)
        data = response.json()
        ids = [item.get("id") for item in data.get("included", [])]
        assert "1001" in ids, f"Serie PVPC (id=1001) no encontrada. IDs presentes: {ids}"

    def test_ree_values_have_required_fields(self):
        """Cada valor debe tener los campos 'datetime' y 'value'."""
        response = requests.get(self.BASE_URL, headers=self.HEADERS, timeout=10)
        data = response.json()
        pvpc = next(i for i in data["included"] if i.get("id") == "1001")
        values = pvpc["attributes"]["values"]
        for v in values:
            assert "datetime" in v, f"Campo 'datetime' ausente en: {v}"
            assert "value" in v,    f"Campo 'value' ausente en: {v}"
            assert isinstance(v["value"], (int, float)), f"'value' no es numérico: {v['value']}"


class TestOWMContract:

    API_KEY = os.getenv("WEATHER_API_KEY")
    URL     = "https://api.openweathermap.org/data/2.5/forecast"
    PARAMS  = {"lat": 40.4168, "lon": -3.7038, "units": "metric", "cnt": 2}

    @pytest.fixture(autouse=True)
    def skip_if_no_key(self):
        if not self.API_KEY:
            pytest.skip("WEATHER_API_KEY no configurada — omitiendo contract test OWM")

    def test_owm_api_reachable(self):
        """La API de OWM debe responder en menos de 10 segundos."""
        r = requests.get(self.URL, params={**self.PARAMS, "appid": self.API_KEY}, timeout=10)
        assert r.status_code == 200, f"HTTP {r.status_code}: {r.text[:200]}"

    def test_owm_response_has_list(self):
        """La respuesta debe contener la clave 'list'."""
        r = requests.get(self.URL, params={**self.PARAMS, "appid": self.API_KEY}, timeout=10)
        data = r.json()
        assert "list" in data

    def test_owm_list_items_have_required_fields(self):
        """Cada tramo debe tener los campos críticos para el motor PV."""
        r    = requests.get(self.URL, params={**self.PARAMS, "appid": self.API_KEY}, timeout=10)
        data = r.json()
        for item in data["list"]:
            assert "dt_txt"           in item,               "Falta dt_txt"
            assert "temp"             in item["main"],        "Falta main.temp"
            assert "humidity"         in item["main"],        "Falta main.humidity"
            assert "all"              in item["clouds"],      "Falta clouds.all"
            assert "speed"            in item["wind"],        "Falta wind.speed"
            assert len(item["weather"]) > 0,                 "weather[] vacío"
            assert "id"               in item["weather"][0], "Falta weather[0].id"
            assert "pop"              in item,               "Falta pop"
```

---

### 5.4 Checklist de Validación de Nueva Integración

Usar este checklist al incorporar una nueva API o fuente de datos al pipeline:

```markdown
## Checklist: Nueva Integración — [NOMBRE DE LA API]

**Fecha:** YYYY-MM-DD
**Responsable:** [Nombre]
**ID asignado:** INT-00X

### 1. Análisis previo
- [ ] Documentación oficial revisada completamente
- [ ] Términos de uso y política de datos aceptados
- [ ] Plan de autenticación definido (API Key / OAuth2 / Bearer / pública)
- [ ] Rate limits documentados y compatibles con el volumen de SunSaver
- [ ] Estructura de respuesta analizada — campos críticos identificados
- [ ] Campos garantizados vs opcionales documentados
- [ ] Política de breaking changes del proveedor conocida
- [ ] Sandbox o entorno de prueba disponible verificado

### 2. Implementación
- [ ] Módulo `bronze_ingest_{fuente}.py` creado con estructura estándar
- [ ] Función `extract_{nombre}()` implementada con manejo de errores
- [ ] Función `ingest_{nombre}_to_bronze()` implementada con `chmod 444`
- [ ] Manifest `_process_manifest_{fuente}.json` implementado
- [ ] Variables de entorno requeridas añadidas a `.env.example`
- [ ] Módulo Silver `silver_transform_{entidad}.py` implementado
- [ ] Reglas de validación en Silver documentadas en `04_DATA_QUALITY_FRAMEWORK.md`
- [ ] Stage asignado en `PIPELINE` de `pipeline_runner.py`
- [ ] Timeout configurado (máximo 15s por request)

### 3. Documentación
- [ ] Ficha de integración añadida a este documento (`06_API_INTEGRATION_SPECS.md`)
- [ ] Schema Bronze documentado en `02_DATA_CATALOG.md`
- [ ] Mapeo Bronze → Silver documentado en `02_DATA_CATALOG.md`
- [ ] Variables de entorno añadidas a la sección 4.1 de este documento
- [ ] Reglas de calidad DQ-{CAPA}{NNN} creadas en `04_DATA_QUALITY_FRAMEWORK.md`

### 4. Testing
- [ ] Mock response fixture creado en `tests/fixtures/mock_{fuente}_response.py`
- [ ] Unit tests del extractor implementados (casos: éxito, vacío, timeout, error auth)
- [ ] Unit tests del transformer Silver implementados
- [ ] Contract test implementado y ejecutado contra API real
- [ ] Health check añadido a `utils/health_check.py`
- [ ] Test de integración end-to-end con entorno temporal ejecutado

### 5. Operaciones
- [ ] Health check verificado en entorno DEV
- [ ] Ejecución completa del pipeline con la nueva fuente verificada
- [ ] Reconciliación Bronze ↔ Silver ↔ Gold verificada
- [ ] Quality Score de la nueva tabla Silver dentro del umbral
- [ ] Alerta de fallo de fuente configurada (Slack / Email)
- [ ] Runbook de remediación documentado en `04_DATA_QUALITY_FRAMEWORK.md`

### 6. Sign-off
- [ ] Code review aprobado por ≥ 1 miembro del equipo
- [ ] Merge a `main` realizado
- [ ] Despliegue en DEV verificado post-merge
```

---

*SunSaver ETL · Especificación de Integraciones API v1.0.0 · Mayo 2026*  
*Clasificación: INTERNA · No distribuir fuera del equipo sin autorización*