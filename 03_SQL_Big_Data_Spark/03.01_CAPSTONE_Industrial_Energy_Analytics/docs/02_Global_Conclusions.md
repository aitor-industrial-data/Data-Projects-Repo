># Conclusiones globales: Auditoría Energética de Alta Precisión

Tras el procesamiento distribuido de más de **2 millones de registros** mediante el motor de cómputo **Apache Spark**, se presenta la síntesis final del comportamiento eléctrico de la unidad bajo estudio. Este análisis trasciende el monitoreo convencional para convertirse en una **auditoría forense de alta precisión**, permitiendo segmentar el gasto, mitigar riesgos técnicos y maximizar el ahorro económico.


## Comparativa de Impacto y Validación de Hipótesis
A continuación, se tabula el impacto de cada vector de análisis sobre la operatividad y la eficiencia de la instalación:

| Hipótesis | Estado | Factor Crítico Identificado | Impacto en Negocio / Ahorro | Relevancia Técnica |
| :--- | :---: | :--- | :--- | :--- |
| **H1: Simultaneidad** | ✅ Validada | Sobredimensionamiento estructural (Pico >10kW). | **Alto:** Reducción de término fijo al bajar a 6.9 kW. | Optimización de potencia contratada. |
| **H2: Outliers (Horno)** | ✅ Validada | Factor Humano (Olvido operativo el 05/06/2010). | **Medio:** Prevención de desperdicio energético (72% de ahorro). | NIALM (Firma de carga del activo). |
| **H3: Consumo Base** | ✅ **CRÍTICA** | Standby del **37.66%** (Ineficiencia masiva). | **Muy Alto:** Ahorro proyectado de **1,068 kWh/año**. | NILM: Desagregación de carga y perfilado de activos. |
| **H4: Estabilidad** | ⚠️ Parcial | Deficiencia en Red Externa (Distribuidora). | **Bajo (Económico) / Alto (Activos):** Vida útil. | Diagnóstico de calidad de suministro. |


## Conclusiones Transversales de Ingeniería

### 1. Arquitectura de Carga y Eficiencia Operativa
El análisis revela una instalación con una excelente salud de infraestructura interna (**H4**), pero con una gestión operativa deficiente (**H1, H2, H3**). La vivienda sufre de un "goteo" energético constante que representa más de un tercio de su consumo total. 

> **Hallazgo Clave (H3):** El consumo residual de 0.472 kW en circuitos generales. Mediante analítica NILM, se ha desglosado este valor en un standby ~0.35 kW y una carga cíclica de refrigeración secundaria (presumiblemente un arcón o minibar fuera de la cocina) con un Duty Cycle del 19.78%. Aunque este ciclo de trabajo indica una salud mecánica óptima (inferior al umbral crítico del 25%), la elevada potencia de pico (0.44 kW) revela un equipo tecnológicamente obsoleto. Se descarta el mantenimiento preventivo en favor de una sustitución estratégica por tecnología Inverter, lo que reduciría el standby total a 0.35 kW y generaría un ahorro de 1,068 kWh/año, garantizando un ROI de 1.9 años."

### 2. Mitigación de Riesgos y Seguridad de Activos
La identificación forense del evento del horno (**H2**) demuestra que el riesgo no es técnico (averías), sino de comportamiento. Integrar algoritmos de detección de anomalías basados en las firmas eléctricas obtenidas permitiría implementar sistemas de **Smart Home** que corten el suministro ante patrones de olvido, protegiendo la instalación de estreses térmicos innecesarios como el detectado (83% de capacidad nominal durante 4 horas).

##  Optimización Financiera (Cost-Benefit Analysis)
La estrategia propuesta se divide en dos ejes:

* **Ahorro Pasivo:** La reducción de potencia contratada a 6.9 kW (H1) se define como una medida de CapEx 0 (inversión cero). Al demostrar mediante el análisis de simultaneidad que el umbral de 10 kW es innecesario, se genera un ahorro neto en el término fijo de la factura de forma inmediata y recurrente.
* **Ahorro Activo:** La analítica NILM proyecta un ahorro de 1,068 kWh/año con un ROI de 1.9 años. Este plan de eficiencia se desglosa en dos fases estratégicas:
    * **Sustitución por Obsolescencia:** Reemplazo del frigorífico secundario en el circuito de "Otros" (Salto ~0.44 kW). Su ineficiencia tecnológica exige tecnología Inverter.
    * **Gestión de Standby Residual:** Instalación de Smart Kill-Switches para eliminar el suelo de 0.20 kW en circuitos generales. Esta medida es la única vía para alcanzar el objetivo técnico de 0.15 kW de consumo basal.


## Roadmap de Implementación Recomendado
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