# Propuesta de Proyecto: Industrial Energy Analytics (Spark Capstone)
**Sector:** Infraestructura Eléctrica e Ingeniería de Datos  
**Responsable:** Aitor (Ingeniero Técnico Industrial)  
**Fecha:** Febrero 2026

## 1. Resumen Ejecutivo
Este proyecto utiliza el motor de computación distribuida **Apache Spark** para procesar y analizar un conjunto de datos masivo de más de 2 millones de registros eléctricos de alta resolución. El objetivo es transformar datos brutos de telemetría en inteligencia operativa, identificando anomalías técnicas y oportunidades críticas de ahorro en el mantenimiento y la facturación de una infraestructura residencial de gran escala. 

Las herramientas tradicionales (Excel, bases de datos relacionales simples) colapsan ante el volumen de datos de alta frecuencia. Este proyecto demuestra la capacidad de **Spark SQL** para escalar el análisis donde otras herramientas fallan.

A través de un **análisis exploratorio de datos (EDA) previo**, se ha determinado que, aunque el volumen de carga sugiere una actividad comercial, los parámetros eléctricos sitúan el estudio en el ámbito de una **vivienda unifamiliar de alta gama (tipo chalet)** con una gestión energética compleja.

## 2. Contexto y Justificación del Análisis
En instalaciones de gran capacidad, los costes energéticos y el deterioro de los equipos suelen verse afectados por tres factores críticos que este proyecto busca mitigar:
* **Ineficiencia por Simultaneidad:** Sobrecostes por términos de potencia mal dimensionados ante picos de demanda mal gestionados.
* **Degradación de Componentes:** Riesgo de fatiga en la electrónica de control debido a fluctuaciones de tensión durante eventos de alta carga.
* **Cargas Pasivas No Optimizadas:** Fugas energéticas persistentes en periodos de descanso que incrementan el coste operativo anual.

#### Nota Técnica: Validación del Entorno de Estudio
Durante la fase inicial de ingesta de datos, se realizó un proceso de validación para determinar la naturaleza de la fuente, llegando a las siguientes conclusiones:
1. **Detección de Anomalías de Carga:** El registro de picos de demanda recurrentes cercanos a los **10 kW** sugería inicialmente una actividad de pequeña industria o taller, ya que estos valores exceden con creces el perfil de un hogar estándar.
2. **Contraste de Infraestructura:** Sin embargo, el análisis de la tensión de red confirmó una **acometida monofásica estable de 230 VAC**. Al carecer de suministro trifásico (400 VAC), se descartó la presencia de maquinaria industrial pesada.
3. **Veredicto:** Cruzando estas evidencias con las especificaciones del dataset, se concluye que el estudio se centra en una **vivienda de grandes dimensiones** con un alto grado de electrificación (posible aerotermia, climatización avanzada o sistemas de bombeo), lo que justifica el uso de herramientas de Big Data para su optimización.


## 3. Objetivos Técnicos (Data Engineering)
* **Ingesta Masiva:** Carga y lectura eficiente de registros a gran escala sin comprometer la estabilidad del sistema.
* **Validación de Calidad:** Implementación de esquemas estrictos y limpieza de telemetría corrupta o ruidosa.
* **Optimización de Rendimiento:** Gestión avanzada de memoria y computación distribuida para consultas de baja latencia.
* **Arquitectura de Datos:** Transición de almacenamiento plano (CSV) a estructuras columnares optimizadas para analítica.

## 4. Stack Tecnológico (Herramientas)
* **Motor de Procesamiento:** Apache Spark (PySpark) para computación distribuida en memoria.
* **Lenguajes:** Python (Lógica de transformación) y SQL (Consultas analíticas).
* **Formato de Almacenamiento:** Apache Parquet (Compresión y alto rendimiento).
* **Infraestructura:** Docker Desktop para contenedorización del entorno Spark.
* **Entorno de Desarrollo:** JupyterLab y VS Code.
* **Control de Versiones:** Git / GitHub para documentación y versionado de código.

## 5. Hipótesis de Ingeniería (Marco Analítico)

Como Ingeniero Tecnico Industrial Electrico, el análisis se centrará en validar tres escenarios críticos:

* **H1 (Optimización de la Curva de Carga y Simultaneidad):** La instalación registra picos de demanda máxima vinculados a una elevada **tasa de simultaneidad** de equipos de gran potencia (climatización, bombeo de piscina y electrodomésticos térmicos). Utilizaremos la capacidad de procesamiento de Spark para identificar las **ventanas críticas de demanda** donde la coincidencia de uso dispara el término de potencia por encima de los 9 kW. El análisis busca determinar si estos picos son evitables mediante un **escalonamiento de cargas** (arranque secuencial) o una reprogramación de hábitos, permitiendo así una reducción de la potencia contratada sin sacrificar el confort."

* **H2 (Análisis del Consumo Residual y Eficiencia Pasiva):** "El ratio de **consumo base (Standby)** frente al consumo nominal es superior al 15% durante los periodos de inactividad o descanso (madrugadas y días no laborables). Esta hipótesis busca cuantificar el impacto económico de los **sistemas auxiliares y cargas fantasma** (sistemas de seguridad, recirculación de agua, climatización en modo espera y domótica) que no están optimizados para el ahorro energético pasivo. Utilizaremos la comparativa entre días laborables y fines de semana para determinar si el consumo base es constante o si existen ineficiencias por falta de protocolos de 'apagado inteligente' en la vivienda."

* **H3 (Diagnóstico de Calidad de Suministro y Estabilidad de Tensión):** "Existe una degradación en la calidad de la red interna donde las **caídas de tensión momentáneas (<210V)** correlacionan con periodos de alta demanda de potencia. Este fenómeno sugiere que el arranque de cargas de gran caballaje (como bombas de calor o sistemas de filtrado) está estresando la acometida monofásica, provocando 'caídas de tensión por impedancia'. Utilizaremos Spark para identificar estos eventos, ya que incrementan el riesgo de **fatiga prematura en la electrónica de control** de los electrodomésticos y reducen la eficiencia de los motores de inducción de la vivienda."


## 6. Hoja de Ruta de Implementación


1. **Fase 1: Ingesta y Profiling Inicial (Data Diagnosis)**
   * Carga masiva del dataset de 2M de registros en el motor Apache Spark.
   * Auditoría de calidad: Identificación de registros nulos, duplicados y desbordamientos de rango en sensores (Outliers).
   * Verificación de la integridad de los metadatos (Esquema de datos).

2. **Fase 2: Data Wrangling (Normalización y Tipado)**
   * **Casting:** Conversión de tipos de datos (de String a Double/Float/Timestamp).
   * **Data Cleansing:** Tratamiento de valores nulos y estandarización de magnitudes eléctricas (unidades SI).
   * Sincronización horaria y manejo de zonas temporales.


3. **Fase 3: Feature Engineering (Enriquecimiento de Datos)**
   * **Segmentación Temporal Avanzada:** Creación de indicadores para diferenciar periodos de **Fin de Semana (`Is_Weekend`)** y franjas horarias críticas.
   * **Ventanas de Maximímetro:** Cálculo de medias móviles para identificar la **ventana crítica de simultaneidad**, simulando el comportamiento de un contador inteligente profesional en la detección de picos.

4. **Fase 4: Analítica Spark SQL (Validación de Hipótesis)**
   * Identificación de eventos > 9 kW para proponer un **escalonamiento de cargas** y reducir la potencia contratada. (H1).
   * Cuantificación del **gasto en standby** durante madrugadas y fines de semana para optimización domótica (H2).
   * Detección de caídas de voltaje (< 210V) ante picos de demanda para prevenir **fatiga electrónica** en la vivienda (H3).

5. **Fase 5: Optimización de Almacenamiento (Persistence)**
   * Persistencia del dataset procesado en formato columnar **Parquet**.
   * Implementación de **Particionado** por fecha para optimizar las lecturas futuras y reducir costes de cómputo.

6. **Fase 6: Reporting y Business Intelligence (Entrega de Valor)**
   * Generación de visualizaciones clave (Curvas de carga, Histogramas de tensión).
   * Documentación final con conclusiones técnicas y recomendaciones de ahorro energético para el negocio.


## 7. KPIs de Éxito (Métricas de Desempeño)

Para evaluar la calidad técnica y el impacto del proyecto, se establecen los siguientes indicadores:

* **Eficiencia de Procesamiento Masivo:** Las consultas de agregación y filtros complejos sobre los 2 millones de registros deben ejecutarse en un tiempo inferior a 30 segundos, validando la correcta configuración del motor Spark.
* **Integridad y Salud del Dato (Data Health):** Resolución del 100% de las inconsistencias detectadas (nulos, outliers físicos y errores de lectura de sensores) en las columnas críticas de potencia y tensión antes de la fase de analítica.
* **Precisión de la Inferencia Industrial:** Validación o refutación empírica, basada al 100% en datos objetivos, de las 3 hipótesis industriales planteadas, proporcionando una base sólida para decisiones de inversión (CAPEX).
* **Escalabilidad del Pipeline:** La arquitectura diseñada debe demostrar capacidad para procesar un incremento de carga (hasta 10M de registros) manteniendo una degradación de rendimiento lineal, asegurando su viabilidad en entornos de producción real.
* **Optimización de Almacenamiento:** El paso de CSV a Parquet debe suponer una reducción de al menos el 80% en el peso del archivo y una mejora drástica en la velocidad de acceso por columna.