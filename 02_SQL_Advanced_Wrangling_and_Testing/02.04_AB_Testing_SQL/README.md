# A/B Testing & Business Intelligence 📈

Este submódulo representa la culminación analítica del modulo de formación, centrado en la transición de la limpieza de datos (Wrangling) hacia la generación de valor estratégico para el negocio. Utilizando la arquitectura de capas, aplicamos lógica experimental sobre los datos normalizados en la capa **Silver**.

## 📂 Contenido de la Carpeta

Siguiendo un flujo de trabajo profesional, la carpeta se organiza en dos scripts fundamentales:

1.  **[01_AB_Testing_Segmentation.sql](./01_AB_Testing_Segmentation.sql)**: Infraestructura para la creación de grupos experimentales deterministas.
2.  **[02_AB_Testing_Performance.sql](./02_AB_Testing_Performance.sql)**: Motor de cálculo de métricas de rendimiento y KPIs.

## 🛠️ Fases del Proyecto

### Fase I: Segmentación Determinista (Capa Gold)
El objetivo es garantizar una división de audiencia equilibrada y consistente, siguiendo las mejores prácticas de ingeniería:
* **Técnica**: Uso del operador módulo (`%`) sobre el `CustomerId` para asegurar que un usuario pertenezca siempre al mismo grupo de forma determinista.
* **Distribución**: Segmentación 50/50 (Grupo A: Control / Grupo B: Variante).
* **Validación**: Implementación de *Data Profiling* para verificar la salud y el equilibrio de los grupos antes del análisis.

### Fase II: Medición de KPIs y ARPU
Transformamos los registros de ventas en indicadores clave para la toma de decisiones:
* **Métrica Principal (ARPU)**: Cálculo del *Average Revenue Per User* para determinar la rentabilidad real por usuario asignado.
* **Prevención de Sesgos**: Uso estratégico de `LEFT JOIN` para incluir a todos los usuarios del experimento, incluso aquellos que no realizaron compras, evitando el "sesgo de supervivencia" en las métricas de conversión.
* **Métricas Agregadas**: Análisis de volumen de pedidos e ingresos totales comparativos entre segmentos.



## 🚀 Impacto en el Pipeline
Este proyecto cierra la etapa de **SQL Problem Solving** de UC Davis. Al consolidar la lógica de negocio en la capa **Gold**, el sistema queda preparado para la siguiente fase de especializacion: **Procesamiento Distribuido con Spark** , donde estos mismos análisis se escalarán a millones de filas.

---
*Este módulo es parte de mi especialización intensiva en Data Engineering, enfocada en la creación de activos de datos fiables y listos para producción.*