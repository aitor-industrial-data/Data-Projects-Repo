# ⚡ Industrial Energy Analytics — Big Data Spark Capstone
 
> **Transformando 2 millones de registros de telemetría eléctrica en decisiones financieras concretas mediante Apache Spark.**
 
---
 
## 🧠 El problema que resuelve este proyecto
 
La mayoría de hogares e instalaciones **pagan de más en electricidad** sin saberlo — no por consumir demasiado, sino por tres ineficiencias invisibles:
 
- **Potencia contratada sobredimensionada:** Se paga un término fijo mensual por un pico de demanda que casi nunca ocurre.
- **Cargas fantasma y standby:** Aparatos consumiendo silenciosamente las 24 horas, sin que nadie lo detecte.
- **Estrés de red que deteriora los equipos:** Caídas de tensión que degradan la electrónica con el tiempo, imperceptibles hasta que algo falla.
Las herramientas convencionales (Excel, bases de datos relacionales) colapsan ante el volumen de datos eléctricos de alta frecuencia. Este proyecto demuestra cómo **Apache Spark + conocimiento de dominio de ingeniería** permite identificar estos problemas a escala y traducirlos en recomendaciones de ahorro concretas y cuantificadas.
 
---
 
## 📊 El proyecto de un vistazo
 
| Métrica | Valor |
|---|---|
| 📁 Volumen del dataset | 2.075.259 registros (4 años, muestreo cada minuto) |
| ⚙️ Motor de procesamiento | Apache Spark v4.1.1 (PySpark) |
| ⏱️ Tiempo de ejecución (ETL completo) | 17,3 segundos |
| 💾 Optimización de almacenamiento | CSV → Parquet (compresión Snappy) |
| 🖥️ Entorno | Ubuntu WSL2 · VS Code Remote · 32 GB RAM |
| 💡 Hipótesis validadas | 4 de 4 (3 confirmadas ✅ · 1 parcial ⚠️) |
 
---
 
## 🔍 Qué se encontró — Las 4 hipótesis
 
### H1 · Optimización de la Curva de Carga ✅ VALIDADA
 
**Pregunta:** ¿Los picos de demanda (>8 kW) son estructuralmente necesarios o simplemente una mala gestión de cargas?
 
**Hallazgo:** La instalación está **sobredimensionada por hábito operativo**. El circuito de lavandería (Sub_metering_2) genera picos de ~4 kW que, sumados a la demanda de cocina, superan el umbral contratado — pero solo el **0,005% del año**. El análisis forense de la composición de carga (H1.2) exonera a la climatización: S3 aporta un ~10% constante en todos los picos. El trigger es la lavandería (S2, ~40%) coincidiendo con la carga base.
 
**Impacto en negocio:** Reducir la potencia contratada de 10 kW → **6,9 kW** genera ahorro inmediato y recurrente en el término fijo de la factura. Sin inversión de capital (**CapEx 0**).
 
<details>
<summary><b>📈 Ver evidencia: Frecuencia de Picos Críticos vs. Umbral 6,9 kW</b></summary>
<br>
<img src="./docs/H1_Frequency_LoadShift_Plot.png" alt="H1 Load Shift Plot" width="800">
> **Cómo leer el gráfico:** Cada punto rojo es un evento crítico por encima de 6,9 kW, etiquetado con su frecuencia de ocurrencia. El área azul es la demanda media (muy por debajo del umbral). Desplazar el uso de lavandería fuera de la franja 18:00–22:00 elimina el 100% de los eventos críticos detectados.
</details>
---
 
### H2 · Detección de Anomalías Estadísticas (3σ) ✅ VALIDADA
 
**Pregunta:** ¿Puede Spark identificar eventos de consumo anómalos en el circuito de cocina que no responden a patrones de uso habitual?
 
**Hallazgo:** El análisis forense del evento del 05/06/2010 confirmó que el **horno eléctrico quedó encendido por error durante la madrugada** — funcionando al 83% de la capacidad nominal del circuito (21A de 25A) durante ~3 horas con el horno vacío.
 
**Impacto en negocio:** La fase de "mantenimiento inútil" representó el **72% del gasto energético total** del evento. Este algoritmo es la base para sistemas de Smart Home con apagado automático por firma eléctrica.
 
<details>
<summary><b>📈 Ver evidencia: Seguimiento Forense de Carga del Horno</b></summary>
<br>
<img src="./docs/H2_Oven_Incident_Power_Analysis.png" alt="H2 Oven Incident Analysis" width="800">
> **Cómo leer el gráfico:** La línea roja (potencia cocina) muestra un patrón de ciclado perfecto de termostato desde las 22:30 hasta las 01:27 — firma característica de un elemento resistivo manteniendo temperatura. La desconexión manual a las 01:27 descarta cualquier avería mecánica.
</details>
---
 
### H3 · Consumo Residual y Eficiencia Pasiva ✅ VALIDADA — CRÍTICA
 
**Pregunta:** ¿El consumo base durante periodos de inactividad (madrugadas, fines de semana) supera el umbral de eficiencia del 15%?
 
**Hallazgo:** Ratio de standby medido en **37,66%** — más del doble del umbral previsto. Mediante análisis NILM (*Non-Intrusive Load Monitoring*) sobre el circuito "Otros", se identificó una unidad de refrigeración secundaria (probable arcón o vinoteca) con un **Duty Cycle del 19,78%** y picos de 0,44 kW, firma característica de un compresor tecnológicamente obsoleto.
 
**Impacto en negocio:** Sustitución por tecnología Inverter → **ahorro proyectado de 1.068 kWh/año · ROI: 1,9 años.**
 
<details>
<summary><b>📈 Ver evidencia: Firma NILM — Circuito "Otros" vs. Perfil Histórico</b></summary>
<br>
<img src="./docs/H3_NILM_Fridge_Signature.png" alt="H3 NILM Fridge Signature" width="800">
> **Cómo leer el gráfico:** La línea azul muestra el consumo real entre la 01:00 y las 05:30 (sin ocupantes activos). La oscilación regular (subida → bajada → subida) es la firma de ciclado del compresor. El delta entre picos y valles (~0,24 kW) es consistente con una unidad de refrigeración pre-Inverter.
</details>
---
 
### H4 · Calidad de Suministro y Estabilidad de Tensión ⚠️ PARCIALMENTE VALIDADA
 
**Pregunta:** ¿Las caídas de tensión correlacionan con la alta demanda interna o tienen origen en la red de distribución externa?
 
**Hallazgo:** La infraestructura interna es excelente — la instalación aguanta picos de 11,1 kW manteniendo 229,7V, descartando bornes flojos o secciones de cable insuficientes. Sin embargo, el **72,5% de los 1.477 "minutos de estrés"** (tensión <228V) se producen en franjas de baja carga interna, apuntando a **saturación externa del transformador de zona**.
 
**Impacto en negocio:** Se evita una inversión innecesaria en re-cableado. La evidencia respalda una solicitud técnica formal a la distribuidora para auditoría con instrumental de Clase A. Si ésta confirma caídas por debajo de los límites del RD 1955/2000, se abre la vía de reclamación por degradación de activos.
 
<details>
<summary><b>📈 Ver evidencia: Distribución del Estrés de Red vs. Curva de Carga Propia</b></summary>
<br>
<img src="./docs/H4_correlation_stress.png" alt="H4 Correlation Stress" width="800">
> **Cómo leer el gráfico:** Los eventos de estrés (barras rosas) se concentran a las 10:00, cuando el consumo propio de la vivienda (línea azul) ya está bajando. Esto es lo contrario de lo que produciría una impedancia interna elevada — evidencia clave del origen externo.
</details>
<details>
<summary><b>📈 Ver evidencia: Análisis de Causa Raíz — Eventos en Zona de Estrés</b></summary>
<br>
<img src="./docs/H4_root_cause_analysis.png" alt="H4 Root Cause Analysis" width="800">
> **Cómo leer el gráfico:** El 72,5% de los minutos de estrés se clasifican como "External/Grid Weakness". Solo el 2,2% corresponde a estrés por picos críticos internos. La red interna no es el problema.
</details>

---

## 💰 Impacto económico real
 
> Cálculos aplicados al mercado eléctrico español (tarifa PVPC 2025): **~60 €/kW·año** en término de potencia · **0,137 €/kWh** de energía (fuente: Red Eléctrica de España / CNMC). El dataset procede de una vivienda en Francia; los hallazgos se presentan extrapolados al contexto tarifario español, mercado de aplicación profesional de este análisis.
 
| # | Acción | Inversión estimada | Ahorro energético | Ahorro en € / año | ROI |
|---|---|---|---|---|---|
| H1 | ↓ Potencia contratada: 10 kW → 6,9 kW | **€0** *(gestión tarifaria)* | — | **~186 €** *(3,1 kW × 60 €/kW)* | **Inmediato** |
| H3a | Sustituir arcón/vinoteca por tecnología Inverter | **~300 €** *(gama media, MediaMarkt/El Corte Inglés)* | 1.068 kWh/año | **~146 €** *(× 0,137 €/kWh)* | **~2 años** |
| H3b | Instalar Smart Kill-Switches (4× Tapo P110, ~15 €/ud) | **~60 €** *(enchufes inteligentes con monitoreo)* | ~700 kWh/año | **~96 €** | **< 1 año** |
| | | | | | |
| | **TOTAL** | **~360 €** | **~1.768 kWh/año** | **🟢 ~428 €/año** | **< 1 año** *(global)* |
 
> 💡 **La lectura clave:** con una inversión única de ~360 €, el sistema se amortiza en menos de 12 meses y genera ~428 €/año de ahorro recurrente de forma indefinida. La acción de mayor retorno es el ajuste de potencia: **186 €anuales sin gastar un euro**, simplemente reorganizando el uso de la lavandería.
 
---

## 🛠️ Stack tecnológico
 
```
Apache Spark v4.1.1 (PySpark)    — Motor de computación distribuida
Spark SQL + Window Functions      — Análisis estadístico y validación de hipótesis
Apache Parquet + Snappy           — Almacenamiento columnar y compresión
Ubuntu WSL2 + VS Code Remote      — Ejecución nativa en Linux
Python                            — Lógica ETL e ingeniería de características
```
 
**Patrón de arquitectura:** Medallón Bronze/Silver · Flat Table desnormalizada para latencia mínima en shuffle · Procesamiento In-Memory (16 GB Driver / 8 GB Executor)
 
---
 
## 🗂️ Estructura del proyecto
 
```
├── notebooks/
│   └── 01_EDA_Electric_Data.ipynb           # Pipeline ETL completo + validación de hipótesis
├── docs/
│   ├── 01_Project_Proposal.md               # Objetivos y metodología de ingeniería
│   ├── 02_Global_Conclusions.md             # Impacto en negocio y análisis financiero
│   ├── 03_FINAL_REPORT_[...].md             # Informe técnico pericial completo
│   └── [H1–H4]_*.png                        # Evidencia visual por hipótesis
├── data_storage/work/                       # Dataset procesado en formato Parquet
└── README.md
```
 
---
 
## ▶️ Guía de ejecución rápida
 
```bash
# 1. Instalar dependencias (Ubuntu / WSL2)
pip install pyspark
 
# 2. Navegar al directorio del proyecto
cd ~/Documents/Data-Projects-Repo/03_SQL_Big_Data_Spark/03.01_CAPSTONE_Industrial_Energy_Analytics
 
# 3. Abrir en VS Code (verificar que el indicador inferior izquierdo diga "WSL: Ubuntu")
# Abrir: notebooks/01_EDA_Electric_Data.ipynb → Ejecutar todas las celdas
```
 
> ℹ️ Probado en Intel Core i5-1334U (13ª Gen) · 32 GB RAM · Ubuntu 22.04 sobre WSL2
 
---
 
## 👤 Sobre el autor
 
Aitor — Ingeniero Técnico Industrial Eléctrico con 10 años en automatización industrial, diseño eléctrico y sistemas de control. Aplico ese dominio técnico a proyectos de Data Engineering donde el contexto de negocio marca la diferencia entre un análisis correcto y uno útil.
 
---
 
*Dataset: UCI Individual Household Electric Power Consumption · Sceaux, Francia · 2006–2010*