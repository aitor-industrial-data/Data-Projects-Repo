
> # 🏁 FINAL REPORT: Industrial Energy Analytics
---
---

>## Índice

1. [Resumen Ejecutivo](#1-resumen-ejecutivo)
2. [Arquitectura de Datos (Diseño Estructural)](#2-arquitectura-de-datos-diseño-estructural)
3. [ETL y Transformación de Datos](#3-etl-y-transformación-de-datos)
4. [Benchmarking de Rendimiento y Escalabilidad](#4-benchmarking-de-rendimiento-y-escalabilidad)
5. [Validación de Hipótesis (Resultados de Negocio)](#5-validación-de-hipótesis-resultados-de-negocio)
6. [Conclusiones Globales: Auditoría Energética de Alta Precisión](#6-conclusiones-globales-auditoría-energética-de-alta-precisión)
7. [Entregables Técnicos y Configuración](#7-entregables-técnicos-y-configuración)


---
---

>## 1. Resumen Ejecutivo 

El presente informe técnico documenta el desarrollo y los resultados de un ecosistema de procesamiento masivo de datos diseñado para el análisis del consumo eléctrico residencial. El proyecto se basa en la explotación de un dataset histórico que comprende **2.075.259 registros** capturados con una frecuencia de muestreo de un minuto entre los años 2006 y 2010.

### Objetivos Estratégicos
La finalidad primordial de esta implementación es la construcción de un pipeline de datos robusto y escalable, capaz de transformar información bruta en conocimiento operativo. El análisis se articula en torno a la **validación de 4 hipótesis críticas** que definen el perfil de carga y la eficiencia energética de la instalación:
* **Optimización de la Curva de Carga y Simultaneidad:** Identificación de ventanas críticas de demanda (>8 kW) para proponer un escalonamiento de cargas y optimizar la potencia contratada.
* **Detección de Anomalías y Outliers Estadísticos:** Localización de eventos disruptivos en el circuito de cocina mediante el cálculo de desviaciones típicas (3sigma) y funciones de ventana en Spark SQL.
* **Análisis del Consumo Residual (Cargas Fantasma):** Cuantificación del impacto económico del standby y la eficiencia pasiva durante periodos de inactividad
* **Diagnóstico de Calidad de Suministro:** Correlación entre picos de demanda y caídas de tensión por impedancia (<210V) para evaluar el estrés en la electrónica de control.

### Enfoque de Ingeniería de Datos
Bajo la metodología de un Ingeniero Técnico Industrial, el proyecto trasciende el análisis estadístico simple para centrarse en la integridad del sistema. Utilizando **Apache Spark** como motor de computación distribuida, se garantiza una arquitectura que permite el procesamiento de millones de filas con latencia mínima. Este enfoque asegura que el sistema sea capaz de escalar desde una unidad habitacional hasta el entorno de una red eléctrica inteligente (Smart Grid), manteniendo la precisión técnica y la paridad con entornos de producción mediante el uso de entornos **Linux nativos sobre WSL2 y VS Code Remote.**

---
---

>## 2. Arquitectura de Datos (Diseño Estructural)

La arquitectura del sistema ha sido diseñada para maximizar el rendimiento del hardware Intel Core i5-1334U, garantizando un entorno de procesamiento de baja latencia mediante la integración de tecnologías Linux en entorno Windows.

### 2.1. Ecosistema de Ejecución (Environment)
El pipeline opera en un entorno de desarrollo de alto nivel que asegura la paridad con sistemas de producción:
* **Infraestructura:** Uso de VS Code Remote conectado a una instancia nativa de Ubuntu sobre WSL2. Esta configuración permite ejecutar Apache Spark v4.1.1 con rendimiento de kernel Linux.
* **Gestión Crítica de Memoria:** A diferencia de configuraciones estándar, se ha optimizado la sesión de Spark para aprovechar los 32 GB de RAM del sistema Medion, asignando 16 GB al Driver y 8 GB al Executor. Esta asignación es clave para procesar los 2.07 millones de registros íntegramente en memoria sin recurrir a intercambio en disco (spilling).

### 2.2. Capas del Pipeline de Datos
El flujo de datos se ha estructurado siguiendo el patrón de arquitectura de medallas (Bronze/Silver), optimizando cada etapa para el hardware Intel i5-1334U.

#### A. Source Layer (Capa de Origen)
El punto de entrada es el dataset 'household_power_consumption.txt', ubicado en la ruta compartida de WSL2 (/mnt/c/Users/...).
* **Formato y Volumen:** Estructura de archivo plano con delimitador ; y un volumen superior a los 2 millones de registros.
* **Desafío Técnico:** La lectura convencional línea a línea resultaría ineficiente. Se aprovecha la capacidad de I/O paralelo de Spark para segmentar la carga del archivo, permitiendo que los 12 hilos lógicos del procesador trabajen simultáneamente en la ingesta.

#### B. Ingestion & Processing (Capa de Computación)
Esta es la unidad central donde el dato bruto se convierte en información estructurada y tipada:
* **PySpark Distributed Engine:** Se utiliza el framework de Apache Spark v4.1.1 para distribuir la carga de trabajo. La configuración de memoria asignada (16GB Driver / 8GB Executor) garantiza que el procesamiento se realice In-Memory, evitando latencias de escritura en disco temporal.
+ **Inferencia de Esquema:** Se ha habilitado inferSchema='True' para asegurar que las 7 métricas eléctricas se reconozcan automáticamente como tipos numéricos computables, permitiendo la validación inmediata de las hipótesis mediante Spark SQL.

#### C. Storage Layer (Capa de Persistencia)
Tras el procesamiento y la limpieza, los datos se preparan para el análisis de hipótesis y el consumo por herramientas de visualización:
* **Destino:** Los resultados y las tablas maestras se persisten en la ruta local data_storage/work.
* **Optimización Columnar (Parquet):** Se utiliza el formato Apache Parquet para el almacenamiento de los resultados finales.
* **Ventaja Técnica:** A diferencia del CSV original, Parquet implementa almacenamiento columnar y compresión Snappy. Esto no solo reduce drásticamente el espacio ocupado en el disco duro, sino que optimiza el rendimiento de las consultas posteriores al leer únicamente las columnas necesarias (ej. solo Voltage o Sub_metering_3) para validar cada hipótesis.

### 2.3. Paradigma de Modelado: Desnormalización (Flat Table)
A diferencia de los sistemas transaccionales (OLTP) que utilizan un Modelo Relacional o esquemas en Estrella/Copo de Nieve, en este proyecto de Big Data se ha optado por una Estrategia de Desnormalización.
* **Eficiencia en Spark:** En computación distribuida, los JOINs entre tablas son operaciones "costosas" (generan Shuffle de datos entre nodos). Al aplanar toda la información en una única tabla maestra (Flat Table), eliminamos la necesidad de cruces de datos en tiempo de ejecución.
* **Latencia Mínima:** Al tener el Full_Timestamp, las dimensiones temporales y las métricas eléctricas en una misma fila, Spark puede realizar agregaciones y cálculos de ventana de forma lineal y extremadamente rápida.

---
---

>## 3. ETL y Transformación de Datos

En esta fase se transforma el dataset bruto en un activo de información de alta calidad. La ingeniería aplicada se centra en eliminar el ruido industrial y enriquecer los datos para permitir análisis temporales complejos.

### 3.1. Data Cleaning: Saneamiento del "Ruido" Eléctrico
El dataset original presenta valores nulos representados por el carácter ?, los cuales invalidan cualquier cálculo estadístico si no se tratan adecuadamente.

* **Estrategia de Identificación:** Durante la ingesta, se utilizó el parámetro naStrings='?' para convertir estos caracteres en nulos nativos de Spark. Posteriormente, se aplicó una limpieza explícita mediante df_clean.replace('?', None) seguida de un na.drop() para eliminar las filas incompletas.
* **Justificación de Borrado:** Se optó por la eliminación de registros incompletos en lugar de la imputación (como la media o interpolación). En un contexto de Ingeniería Eléctrica, imputar valores en picos de consumo podría generar falsos positivos en las hipótesis de sobrecarga o subestimar eventos críticos de caída de tensión. Al contar con más de 2 millones de registros, la pérdida de una pequeña fracción de datos no compromete la significancia estadística del análisis.

### 3.2. Type Casting: Normalización de Métricas
Por defecto, los datos eléctricos son detectados como cadenas de texto (Strings). Para que las funciones matemáticas y de agregación operen correctamente, se realizó una conversión forzada a Número Real (Double).
* **Métricas Transformadas:** Se aplicó .cast("double") a columnas críticas como Global_active_power, Voltage y los tres circuitos de sub-medición (Sub_metering_1, 2 y 3).
* **Impacto Técnico:** Esta transformación es la que permite realizar cálculos de desviaciones estándar (3sigma) para la detección de anomalías y promedios horarios de potencia.

### 3.3. Feature Engineering: Inteligencia Temporal
Para validar hipótesis basadas en hábitos (como la diferencia entre días laborables y fines de semana), el dataset fue enriquecido con nuevas dimensiones temporales:
* **Unificación de Eje Temporal (Full_Timestamp):** Se creó una columna de tiempo unificada combinando Date y Time.
* **Dimensiones Derivadas:** A partir del timestamp unificado, se extrajeron componentes clave para el análisis:
    * Hour: Para identificar ventanas críticas de demanda horaria.
    * Day_Number: Utilizando dayofweek() para indexar los días.
    * Is_Weekend: Una columna booleana creada con una lógica condicional.

Tras este proceso de ETL, el volumen de registros listos para el análisis se mantiene sólido (Registros listos para análisis: 2,049,280), garantizando que la base de datos para el Proyecto Capstone es íntegra, está correctamente tipada y enriquecida para el análisis de negocio.

### 3.4. Data Transformation Workflow

<table style="width: 100%; border-collapse: collapse; border: none;">
  <tr>
    <td style="width: 45%; vertical-align: top; border: none;">
      <strong>Input Schema (Raw)</strong>
      <hr>
      <table>
        <thead><tr><th>Column Name</th><th>Data Type</th><th>Nullable</th></tr></thead>
        <tbody>
          <tr><td>Date</td><td>string</td><td>true</td></tr>
          <tr><td>Time</td><td>timestamp</td><td>true</td></tr>
          <tr><td>Global_active_power</td><td>string</td><td>true</td></tr>
          <tr><td>Global_reactive_power</td><td>string</td><td>true</td></tr>
          <tr><td>Voltage</td><td>string</td><td>true</td></tr>
          <tr><td>Global_intensity</td><td>string</td><td>true</td></tr>
          <tr><td>Sub_metering_1</td><td>string</td><td>true</td></tr>
          <tr><td>Sub_metering_2</td><td>string</td><td>true</td></tr>
          <tr><td>Sub_metering_3</td><td>double</td><td>true</td></tr>
        </tbody>
      </table>
    </td>
    <td style="width: 10%; text-align: center; vertical-align: middle; border: none; font-size: 24px;">
      ➜
    </td>
    <td style="width: 45%; vertical-align: top; border: none;">
      <strong>Output Schema (Transformed)</strong>
      <hr>
      <table>
        <thead><tr><th>Column Name</th><th>Data Type</th><th>Nullable</th></tr></thead>
        <tbody>
          <tr><td><strong>Full_Timestamp</strong></td><td>timestamp</td><td>true</td></tr>
          <tr><td><strong>Hour</strong></td><td>integer</td><td>true</td></tr>
          <tr><td><strong>Day_Number</strong></td><td>integer</td><td>true</td></tr>
          <tr><td><strong>Is_Weekend</strong></td><td>boolean</td><td>true</td></tr>
          <tr><td><strong>Global_active_power</strong></td><td>double</td><td>true</td></tr>
          <tr><td><strong>Global_reactive_power</strong></td><td>double</td><td>true</td></tr>
          <tr><td><strong>Voltage</strong></td><td>double</td><td>true</td></tr>
          <tr><td><strong>Global_intensity</strong></td><td>double</td><td>true</td></tr>
          <tr><td><strong>Sub_metering_1</strong></td><td>double</td><td>true</td></tr>
          <tr><td><strong>Sub_metering_2</strong></td><td>double</td><td>true</td></tr>
          <tr><td><strong>Sub_metering_3</strong></td><td>double</td><td>true</td></tr>
        </tbody>
      </table>
    </td>
  </tr>
</table>

---
---

>## 4. Benchmarking de Rendimiento y Escalabilidad

Este apartado documenta la eficiencia del pipeline y su capacidad para operar bajo condiciones de alta carga, aprovechando las especificaciones técnicas del hardware MEDION E15433.

### 4.1. Optimización de Recursos (Hardware Awareness)
A diferencia de un análisis de datos convencional, el pipeline se ha configurado para extraer el máximo rendimiento de la arquitectura Intel Core i5-1334U (13th Gen):
* **Paralelismo Masivo:** Mediante la configuración local[*], Spark ha distribuido las tareas de limpieza y transformación entre los 12 hilos lógicos del procesador. Esto permite que el procesamiento de los 2.07 millones de registros se realice mediante multihilo real.
* **Gestión de Memoria "In-Memory":** Aprovechando los 32 GB de RAM instalados, se ha asignado una configuración de alto rendimiento a la SparkSession:
* **Driver Memory:** 16g (Permite manejar grandes volúmenes de metadatos y recolección de resultados).
* **Executor Memory:** 8g (Garantiza que las transformaciones complejas y el shuffling se mantengan en RAM, evitando el intercambio en disco o spilling).

### 4.2. Performance Metrics
* **Volumen Procesado:** 2,075,259 registros.
* **Tiempo de Ejecución (ETL Completo):** 6,1 segundos.
* **Eficiencia de Ingesta:** Gracias al uso de naStrings='?' y la desnormalización (tabla aplanada), el acceso a cualquier métrica para las hipótesis (H1-H4) tiene una latencia mínima tras la primera carga.

### 4.3. Scalability Note (Hacia el entorno Cloud)
Este proyecto ha sido desarrollado bajo el principio de escalabilidad horizontal. Aunque se ejecuta en una instancia local de Ubuntu (WSL2), el código es "Cloud-Ready" por las siguientes razones:
* **Independencia de Datos:** El uso de PySpark permite que este mismo script pueda procesar 100 GB o 1 TB de datos en un entorno distribuido (como AWS EMR o Databricks) sin modificar la lógica de transformación. Solo sería necesario escalar el número de nodos trabajadores (worker nodes).
* **Portabilidad de Entorno:** Al estar desarrollado sobre Linux, el pipeline garantiza la paridad total con servidores de producción en la nube.
* **Eficiencia de Almacenamiento:** El uso del formato Parquet asegura que, al subir el volumen de datos, el costo de almacenamiento y el tiempo de lectura se mantengan optimizados mediante la compresión Snappy y la lectura de columnas específicas.

---
---

>## 5. Validación de Hipótesis (Resultados de Negocio)

### Hipótesis 1: Optimización de la Curva de Carga y Simultaneidad
* **Objetivo:** Identificar si los picos máximos de demanda (eventos críticos > 8 kW) responden a una necesidad real de potencia instalada o si son fruto de una elevada tasa de simultaneidad de cargas desplazables. El objetivo de negocio es validar si es técnicamente seguro reducir la potencia contratada a 6.9 kW.

* **Técnica:** Para validar esta hipótesis, se utilizó el motor de Spark SQL y funciones de agregación sobre el dataset de 2.07 millones de registros:
    * **Filtrado de Eventos Críticos:** Localización de registros donde Global_active_power > 8.0.
    * **Perfilado de Carga por Circuito:** Uso de groupBy("Hour") y promedios de Sub_metering_1, 2 y 3 para identificar el "Trigger" o disparador del consumo.
    * **Análisis de Frecuencia:** Cálculo del porcentaje de tiempo que la instalación supera el umbral propuesto de 6.9 kW mediante una función de conteo condicional.

* **Resultado: ✅ VALIDADA**
El análisis masivo confirma que la instalación está sobredimensionada. Los picos de demanda máxima no son estructurales, sino operativos:
    * **Identificación del "Trigger":** El circuito de Lavandería (S2) es el responsable de la saturación, aportando picos de ~4.0 kW que, al sumarse a la demanda base, disparan el consumo.
    * **Exoneración de Sistemas:** La climatización (S3) se mantiene estable (~1.0 kW), descartándose como causa raíz de los picos de arranque.
    * **Ventana Crítica:** Los eventos se concentran entre las 18:00 y 22:00, coincidiendo con el uso inamovible de la Cocina (S1).

* **Visual Evidence:** <br>
<p align="center">
  <img src="./H1_Frequency_LoadShift_Plot.png" alt="Industrial Energy Analysis" width="1100">
</p>

* **Conclusión e Impacto en el Negocio:**

    * **Recomendación:** Reducción de potencia contratada a 6.9 kW.
    * **Estrategia de Gestión:** Implementación de Load Shifting (desplazamiento de carga). La Lavandería se clasifica como "Carga Flexible" asincrónica, cuya programación en horas valle elimina el 100% de los eventos críticos detectados.
    * **Impacto Económico:** Ahorro directo en el término fijo de la factura anual. El riesgo de interrupción por el ICP es nulo debido a que el escenario de sobrecarga solo ocurre en el 0.005% del año y la curva de disparo térmica de los contadores inteligentes permite excesos puntuales.

---

### Hipótesis 2: Análisis de Outliers Estadísticos (3sigma)
* **Objetivo:** Identificar anomalías de consumo en el circuito de Cocina (S1) que se desvíen significativamente de la media histórica. El objetivo técnico es detectar eventos superiores a 2500W que ocurran fuera de las franjas horarias de uso estándar (madrugada), utilizando funciones de ventana para diferenciar entre demanda legítima y fallos operativos o descuidos.

* **Técnica:** La detección se realizó mediante un enfoque estadístico robusto implementado en Spark:
    * **Cálculo de Umbrales:** Se utilizaron funciones de agregación para determinar la media y la desviación estándar del consumo en cocina.
    * **Filtro de Outliers:** Aplicación de la regla de Tres Sigma para catalogar registros anómalos.
    * **Análisis de Firma Eléctrica (NIALM):** Aislamiento de la serie temporal del 05/06/2010 para analizar la ciclicidad y el balance de potencias, permitiendo identificar el activo específico (horno) sin sensores intrusivos.

* **Resultado: ✅ VALIDADA**
El análisis identifica un incidente por factor humano (olvido operativo) de alto impacto. El estudio confirma que el horno eléctrico permaneció encendido por error durante la madrugada del domingo.
    * **Evidencia Técnica:** El consumo registró una ciclicidad perfecta de mantenimiento de temperatura a 4.8 kW, operando al 83% de la capacidad nominal del circuito C3 (21A de 25A).
    * **Descarte de Fallo Mecánico:** La desconexión manual a las 01:27h invalida cualquier teoría de avería en el termostato, coincidiendo con el fin de una jornada social.
    * **Impacto Energético:** La fase de "mantenimiento inútil" (vacío) representó el 72% del gasto energético total del evento.

* **Visual Evidence:** <br>
<p align="center">
  <img src="./H2_Oven_Incident_Power_Analysis.png" alt="Industrial Energy Analysis" width="1100">
</p>

* **Conclusión e Impacto en el Negocio:**

    * **Seguridad Energética:** El algoritmo desarrollado permite diferenciar entre uso legítimo y situaciones de riesgo, sirviendo de base para sistemas de Smart Home y alertas de seguridad.
    * **Optimización de Activos:** Se valida que la instalación soporta el estrés térmico, pero se recomienda la implementación de sistemas de auto-apagado para evitar el desperdicio del 250% de la energía necesaria para la tarea original.
    * **Valor de Ingeniería:** Capacidad de realizar Auditoría de Comportamiento y cuantificar ahorros reales (kWh no consumidos) mediante la educación del usuario o automatización.

---

### Hipótesis 3: Análisis del Consumo Residual y Eficiencia Pasiva

* **Objetivo:** Determinar si el consumo base (Standby) durante periodos de inactividad (madrugadas y días no laborables) supera el 15% del consumo nominal. El objetivo es identificar ineficiencias estructurales ("cargas fantasma") y proponer protocolos de ahorro pasivo mediante la segmentación de datos temporales.

* **Técnica:**
Para esta validación se ejecutó una lógica de agregación avanzada en Spark:
    * **Segmentación Temporal:** Filtrado de la franja de madrugada (01:00 - 05:59) y distinción entre Is_Weekend (True/False).
    * **Algoritmo de Desagregación (NILM):** Análisis de la variabilidad del consumo en el circuito general ("Otros") para identificar patrones cíclicos de compresores.
    * **Cálculo de Ratios:** Comparativa del consumo base frente al promedio diario para obtener el porcentaje de ineficiencia estructural.

* **Resultado: ✅ VALIDADA**
La hipótesis se valida con un resultado de 37.66%, duplicando con creces el umbral de ineficiencia previsto (15%).
    * **Consumo Base Detectado:** La vivienda mantiene un "suelo" constante de 0.472 kW durante la noche.
    * **Identificación de Carga Oculta:** El 68.59% de este residuo proviene del circuito general. Se ha detectado una carga de refrigeración secundaria (arcón o vinoteca) con un Duty Cycle del 19.78% y picos de 0.44 kW, evidenciando obsolescencia tecnológica.
    * **Evaluación de Aislamiento:** Se descarta la climatización (S3) como culpable (solo aporta el 25.58%), confirmando que el problema es electrónico/electromecánico y no térmico.

* **Visual Evidence:** <br>
<p align="center">
  <img src="./H3_NILM_Fridge_Signature.png" alt="Industrial Energy Analysis" width="1100">
</p>


* **Conclusión e Impacto en el Negocio:**
    * **Sustitución Tecnológica:** El reemplazo del equipo de refrigeración ineficiente por tecnología Inverter proyecta un ahorro de 1,068 kWh anuales con un ROI de 1.9 años.
    * **Automatización (Smart Kill-Switch):** Se propone la instalación de relés inteligentes para eliminar el consumo residual de 0.20 kW en valles de inactividad, con el fin de reducir el ratio de standby al 12%.
    * **Impacto Financiero Total:** La corrección integral del consumo base (de 0.472 kW a 0.15 kW) generaría un ahorro anual aproximado de 2,800 kWh, maximizando la rentabilidad de la instalación.

---

### Hipótesis 4: Diagnóstico de Calidad de Suministro y Estabilidad de Tensión

* **Objetivo:** Evaluar la relación entre el consumo de potencia y la estabilidad del voltaje nominal para identificar riesgos de fatiga en componentes electrónicos. El objetivo es determinar si las caídas de tensión son de origen interno (mala instalación) o externo (saturación de la red de distribución), cuantificando el tiempo de exposición a la "Zona de Estrés" (<228V).

* **Técnica:** Se aplicó un análisis de correlación y series temporales masivas en Spark:
    * **Correlación de Pearson:** Cálculo del coeficiente entre Global_active_power y Voltage para medir la impedancia del bucle interno.
    * **Análisis por Franjas:** Segmentación horaria para comparar la tensión en horas de carga mínima interna vs. carga máxima del vecindario.
    * **Cuantificación de Exposición:** Uso de funciones de agregación para sumar los minutos totales donde el voltaje cae por debajo del umbral de fatiga de fuentes conmutadas (SMPS).

* **Resultado: ⚠️ PARCIALMENTE VALIDADA / REFUTADA INTERNAMENTE** La hipótesis de fallo interno queda refutada, pero se valida un riesgo crítico por factores externos. La vivienda es una "isla de robustez" en una red pública debilitada.
    * **Resiliencia Interna:** La instalación soporta picos de 11.1 kW manteniendo 229.7V, lo que descarta bornes flojos o secciones de cable insuficientes.
    * **Debilidad Externa (La Red):** Se detecta la tensión más baja (226.6V) por la mañana con cargas mínimas (1.7 kW), lo que confirma que el transformador de zona llega saturado por la actividad comercial/industrial del entorno.
    * **Tiempo de Exposición:** Se contabilizan 1,477 minutos en la "Zona de Estrés". Debido al muestreo de 1 min, se infiere la existencia de micro-caídas transitorias no registradas que golpean la electrónica sensible.

* **Visual Evidence:** <br>
<p align="center">
  <img src="./H4_correlation_stress.png" alt="Industrial Energy Analysis" width="1100">
  <img src="./H4_root_cause_analysis.png" alt="Industrial Energy Analysis" width="1100">
</p>

* **Conclusión e Impacto en el Negocio:**

    * **Evidencia Pericial:** Los datos de Spark proporcionan una base técnica sólida para reclamaciones a la distribuidora, demostrando que aunque se cumple la legalidad (>207V), existe una degradación silenciosa de los activos.
    * **Protección de Activos:** Se justifica la inversión en SAIs de Doble Conversión para electrónica crítica y una reprogramación horaria para evitar sumar carga interna entre las 09:00 y las 12:00.
    * **Optimización de Capex:** Se evita una inversión innecesaria en el re-cableado de la vivienda, ya que el análisis de datos demuestra que la infraestructura interna es sobresaliente.

---
---

>## 6. Conclusiones globales: Auditoría Energética de Alta Precisión

Tras el procesamiento distribuido de más de **2 millones de registros** mediante el motor de cómputo **Apache Spark**, se presenta la síntesis final del comportamiento eléctrico de la unidad bajo estudio. Este análisis trasciende el monitoreo convencional para convertirse en una **auditoría forense de alta precisión**, permitiendo segmentar el gasto, mitigar riesgos técnicos y maximizar el ahorro económico.


### 6.1 Comparativa de Impacto y Validación de Hipótesis
A continuación, se tabula el impacto de cada vector de análisis sobre la operatividad y la eficiencia de la instalación:

| Hipótesis | Estado | Factor Crítico Identificado | Impacto en Negocio / Ahorro | Relevancia Técnica |
| :--- | :---: | :--- | :--- | :--- |
| **H1: Simultaneidad** | ✅ Validada | Sobredimensionamiento estructural (Pico >10kW). | **Alto:** Reducción de término fijo al bajar a 6.9 kW. | Optimización de potencia contratada. |
| **H2: Outliers (Horno)** | ✅ Validada | Factor Humano (Olvido operativo el 05/06/2010). | **Medio:** Prevención de desperdicio energético (72% de ahorro). | NIALM (Firma de carga del activo). |
| **H3: Consumo Base** | ✅ **CRÍTICA** | Standby del **37.66%** (Ineficiencia masiva). | **Muy Alto:** Ahorro proyectado de **1,068 kWh/año**. | NILM: Desagregación de carga y perfilado de activos. |
| **H4: Estabilidad** | ⚠️ Parcial | Deficiencia en Red Externa (Distribuidora). | **Bajo (Económico) / Alto (Activos):** Vida útil. | Diagnóstico de calidad de suministro. |


### 6.2 Conclusiones Transversales de Ingeniería

### 1. Arquitectura de Carga y Eficiencia Operativa
El análisis revela una instalación con una excelente salud de infraestructura interna (**H4**), pero con una gestión operativa deficiente (**H1, H2, H3**). La vivienda sufre de un "goteo" energético constante que representa más de un tercio de su consumo total. 

> **Hallazgo Clave (H3):** El consumo residual de 0.472 kW en circuitos generales. Mediante analítica NILM, se ha desglosado este valor en un standby ~0.35 kW y una carga cíclica de refrigeración secundaria (presumiblemente un arcón o minibar fuera de la cocina) con un Duty Cycle del 19.78%. Aunque este ciclo de trabajo indica una salud mecánica óptima (inferior al umbral crítico del 25%), la elevada potencia de pico (0.44 kW) revela un equipo tecnológicamente obsoleto. Se descarta el mantenimiento preventivo en favor de una sustitución estratégica por tecnología Inverter, lo que reduciría el standby total a 0.35 kW y generaría un ahorro de 1,068 kWh/año, garantizando un ROI de 1.9 años."

### 2. Mitigación de Riesgos y Seguridad de Activos
La identificación forense del evento del horno (**H2**) demuestra que el riesgo no es técnico (averías), sino de comportamiento. Integrar algoritmos de detección de anomalías basados en las firmas eléctricas obtenidas permitiría implementar sistemas de **Smart Home** que corten el suministro ante patrones de olvido, protegiendo la instalación de estreses térmicos innecesarios como el detectado (83% de capacidad nominal durante 4 horas).

## 6.3 Optimización Financiera (Cost-Benefit Analysis)
La estrategia propuesta se divide en dos ejes:

* **Ahorro Pasivo:** La reducción de potencia contratada a 6.9 kW (H1) se define como una medida de CapEx 0 (inversión cero). Al demostrar mediante el análisis de simultaneidad que el umbral de 10 kW es innecesario, se genera un ahorro neto en el término fijo de la factura de forma inmediata y recurrente.
* **Ahorro Activo:** La analítica NILM proyecta un ahorro de 1,068 kWh/año con un ROI de 1.9 años. Este plan de eficiencia se desglosa en dos fases estratégicas:
    * **Sustitución por Obsolescencia:** Reemplazo del frigorífico secundario en el circuito de "Otros" (Salto ~0.44 kW). Su ineficiencia tecnológica exige tecnología Inverter.
    * **Gestión de Standby Residual:** Instalación de Smart Kill-Switches para eliminar el suelo de 0.20 kW en circuitos generales. Esta medida es la única vía para alcanzar el objetivo técnico de 0.15 kW de consumo basal.


## 6.4 Roadmap de Implementación Recomendado
Basado en la evidencia de los datos, el plan de acción post-notebook es:

**Inmediato (Gestión de Suministro y Carga):**
* Solicitar bajada de **potencia contratada a 6.9 kW (H1)**. Generará un ahorro mensual recurrente e inmediato sin inversión de capital (**CapEx 0**).
* **Desplazar el uso de lavandería** fuera del horario crítico de cena (18:00-22:00).

**Corto Plazo (Infraestructura y Auditoría de Activos):**
* **Sustituir el equipo frigorífico** instalado en la linea de Otros por tecnología Inverter
* **Protección de Hardware:** Instalar un SAI de doble conversión para aislar equipos críticos del estrés eléctrico identificado en la H4.

**Medio Plazo (Eficiencia Estructural y Reclamación):**
* **Eliminación de "Cargas Fantasma":** Implementar Smart Kill-Switches para erradicar el suelo de standby de 0.20 kW, bajando el ratio del 37% al <10%.
* **Acción Legal Basada en estudio de datos (H4):** Generación de un informe técnico pericial fundamentado en el procesamiento de 2.075.259 registros mediante Big Data Spark. La evidencia central es la exposición recurrente a la "Zona de Estrés" (<228V), detectada especialmente en franjas de baja carga interna. Se alega que, aunque los promedios minutales son legales, suponen la "punta del iceberg" de fluctuaciones instantáneas mucho más graves (sospecha de caídas a <215V) que la granularidad actual oculta. Este informe técnico servirá para exigir a la distribuidora una auditoría con instrumental de Clase A y el reajuste del transformador, basándose en la degradación por fatiga térmica acumulada en los equipos de la vivienda.

## 6.5 Roadmap y Escalabilidad del Proyecto
Para escalar este proyecto al siguiente nivel de Data Engineering, se proponen las siguientes fases:
* **Automatización (Data Pipeline):** Migrar este análisis local a un orquestador como Apache Airflow (objetivo del Mes 6) para procesar nuevos logs de telemetría de forma diaria y automática.
 * **Dashboarding en Tiempo Real:** Integrar el "Golden Dataset" generado en Spark con una herramienta de visualización (Grafana o Power BI) para monitorizar el consumo en tiempo real y emitir alertas de "Zona de Estrés" (H4).
* **Acción Pericial:** Utilizar el informe técnico generado por Spark para exigir a la distribuidora una auditoría con instrumental de Clase A, basándose en la exposición recurrente a la fatiga térmica detectada en los 2 millones de registros.

---
---

>## 7. Entregables Técnicos y Configuración

* **Notebook Principal:** [`notebooks/project_notebook.ipynb`](../notebooks/01_EDA_Electric_Data.ipynb)
* **Datos de Salida:** `data_storage/work/` (Contiene los archivos Parquet/CSV procesados por Spark).
* **Documentación:** [`docs/`](./) (Esquemas, evidencias visuales e informe final).

### 7.1 Cómo Ejecutar (Guía de Inicio Rápido):**
Para reproducir este análisis de Big Data en tu entorno de VS Code con WSL2, sigue estos pasos:
* 1. Preparación del Entorno en WSL2
Abre tu terminal de Ubuntu (o la terminal integrada en VS Code) y asegúrate de estar en el directorio del proyecto:

        ```bash
        cd ~/Documents/Data-Projects-Repo/03_SQL_Big_Data_Spark/03.01_CAPSTONE_Industrial_Energy_Analytics
        ```
* 2. Requisitos Previos
Asegúrate de tener instalado PySpark en tu entorno de Ubuntu:

        ```Bash
        pip install pyspark
        ```
* 3. Ejecución en VS Code
    * Abrir la carpeta del proyecto en VS Code (asegúrate de que el indicador azul abajo a la izquierda diga WSL: Ubuntu).
    * Abrir el archivo `notebooks/project_notebook.ipynb`.
    * Seleccionar el Kernel de Python de tu entorno de Ubuntu.
    * Ejecutar todas las celdas para procesar los registros y generar los resultados.