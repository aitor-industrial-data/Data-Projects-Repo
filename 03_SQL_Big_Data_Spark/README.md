# SparkGrid-Insights: Auditoría de Redes Eléctricas con Procesamiento Distribuido

## 1. Introducción y Contexto
En el sector industrial y eléctrico, la digitalización de la red (Smart Grids) genera un volumen de datos que los sistemas relacionales tradicionales no pueden procesar de forma eficiente. Como **Ingeniero Técnico Industrial**, este proyecto representa el puente entre mi experiencia en electricidad y mi especialización en **Ingeniería de Datos**.

Este proyecto aborda el análisis de series temporales de alta frecuencia para auditar el comportamiento energético de una unidad de consumo durante 4 años.

## 2. El Problema de Negocio
El análisis de datos eléctricos minuto a minuto presenta tres desafíos críticos que este proyecto resuelve:
1.  **Escalabilidad:** Las bases de datos SQL convencionales sufren degradación de rendimiento al realizar cálculos agregados sobre millones de filas.
2.  **Calidad de Energía:** La detección de anomalías (caídas de tensión o picos de potencia) requiere procesar grandes volúmenes de datos sin perder la resolución temporal.
3.  **Eficiencia de Almacenamiento:** Los archivos de texto plano (.csv/.txt) son ineficientes para consultas repetitivas. Se necesita una transición a formatos columnares de Big Data.

## 3. El Dataset (Individual Household Power Consumption)
Se trabaja con una base de datos de **2,075,259 registros**, que incluye:
* **Métricas de Potencia:** Activa (kW) y Reactiva (kW).
* **Métricas Eléctricas:** Voltaje (V) e Intensidad (A).
* **Sub-mediciones:** Desglose por circuitos (Cocina, Lavandería, Climatización).
* **Temporalidad:** Datos registrados cada 60 segundos entre 2006 y 2010.

## 4. Metodología y Solución Técnica
El proyecto se ejecuta utilizando **Apache Spark**, aprovechando su motor de computación distribuida para procesar los datos de forma paralela.

### Fases del Proyecto:
1.  **Ingesta Masiva:** Carga de datos desde el Local Data Lake hacia Spark DataFrames, gestionando correctamente los tipos de datos técnicos.
2.  **Data Wrangling & Cleaning:** * Tratamiento de valores nulos producidos por fallos en los sensores.
    * Normalización de unidades de medida.
3.  **Procesamiento Spark SQL:**
    * Uso de **Window Functions** para calcular medias móviles y detectar picos de carga.
    * Agregación temporal para obtener perfiles de carga diarios y mensuales.
4.  **Capa de Persistencia (Work Zone):** Conversión de los datos procesados a formato **Parquet**, optimizando el espacio en disco y la velocidad de lectura para herramientas de BI.

## 5. Estructura del Repositorio
```text
/03_SQL_Big_Data_Spark
│
├── data_storage/           # Data Lake Local (Capas Source y Work)
├── notebooks/              # Prototipado y Análisis Exploratorio con Spark
├── scripts/                # Lógica de producción y ETL final
└── docs/                   # Diccionario de datos y especificaciones técnicas