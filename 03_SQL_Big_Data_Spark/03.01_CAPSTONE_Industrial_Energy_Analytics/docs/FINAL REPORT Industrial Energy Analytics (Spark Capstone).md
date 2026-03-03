# FINAL REPORT: Industrial Energy Analytics (Spark Capstone)

---

## 1. Executive Summary

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

## 2. Data Architecture (The Blueprint)
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

## 3. ETL & Data Transformation
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

## 4. Performance & Scalability Benchmarking
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

## 5. Validación de hipótesis (Business Results)

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

* **Visual Evidence:**
![Visual Evidence](./docs/H1_Frequency_LoadShift_Plot.png)

* **Visual Evidence:** <br>
  ![Industrial Energy Analysis](./docs/H1_Frequency_LoadShift_Plot.png)