# Diccionario de Datos: Individual Household Power Consumption

Este documento define las especificaciones técnicas, unidades de medida y rangos de operación de las variables del dataset utilizado para el proyecto SparkGrid-Insights


## 1. Información General
* **Frecuencia de muestreo:** 1 minuto.
* **Periodo temporal:** Diciembre 2006 – Noviembre 2010.
* **Ubicación del sensor:** Sceaux, Francia (vivienda residencial).

## 2. Definición de Variables

| Columna | Unidad | Descripción Técnica | Observaciones de Ingeniería |
| :--- | :--- | :--- | :--- |
| **Date** | dd/mm/yyyy | Fecha de la lectura. | Formato original: Día/Mes/Año. |
| **Time** | hh:mm:ss | Hora de la lectura. | Precisión de minuto. |
| **Global_active_power** | kW | Potencia activa total consumida por el hogar. | Potencia "útil" que realiza trabajo. |
| **Global_reactive_power**| kW | Potencia reactiva total consumida. | Relacionada con cargas inductivas/capacitivas. |
| **Voltage** | V | Tensión media por minuto. | **Rango nominal:** 230V. Crítico para detectar caídas de tensión. |
| **Global_intensity** | A | Intensidad de corriente media. | Suma de corrientes de todos los circuitos. |
| **Sub_metering_1** | Wh | Energía activa (Cocina). | Incluye principalmente lavavajillas, horno y microondas. |
| **Sub_metering_2** | Wh | Energía activa (Lavandería). | Incluye lavadora, secadora y luces exteriores. |
| **Sub_metering_3** | Wh | Energía activa (Climatización). | Calentador de agua eléctrico y aire acondicionado. |

## 3. Lógica de Negocio y Reglas de Calidad
Como parte del proceso de Ingeniería de Datos, se aplican las siguientes reglas basadas en principios eléctricos:

1.  **Consumo Remanente:** Existe una potencia no medida por los sub-medidores que corresponde a luces y pequeños electrodomésticos.
    Se calcula como: `Resto = (Global_active_power * 1000 / 60) - (Sub_metering_1 + Sub_metering_2 + Sub_metering_3)`
2.  **Detección de Nulos (Gaps):** Los valores nulos representados por `?` en el dataset original indican fallos en la transmisión del sensor o pérdida de alimentación en el equipo de medida.
3.  **Anomalías de Tensión:** Valores de `Voltage` fuera del rango +/- 10% del nominal (230V) deben ser etiquetados para auditoría de calidad de red.

## 4. Transformación Técnica (Target Schema)
En la fase de procesamiento con **Spark SQL**, los datos serán convertidos de tipo `String` a los siguientes tipos de datos nativos:
* `Timestamp`: Combinación de Date + Time.
* `Double/Float`: Para todas las medidas eléctricas.
* `Integer`: Para identificadores si fuera necesario.