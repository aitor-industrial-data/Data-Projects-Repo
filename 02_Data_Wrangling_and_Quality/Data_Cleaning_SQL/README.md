# 📂 Módulo de Prácticas: Data Cleaning & SQL Wrangling

Este directorio contiene la progresión de scripts técnicos desarrollados durante el Mes 2. Cada archivo aborda un desafío específico de limpieza, transformación y auditoría de datos utilizando la base de datos Chinook.

## 🛠️ Índice de Scripts y Objetivos Técnicos

### 01. Preparación para Producción (`01_production_prep_intro.sql`)
- **Objetivo:** Configuración de entornos y buenas prácticas iniciales.
- **Técnicas:** Estructuración de scripts e idempotencia (`DROP/CREATE`).

### 02. Desduplicación Avanzada (`02_advanced_deduplication.sql`)
- **Objetivo:** Identificación y eliminación de registros repetidos.
- **Técnicas:** Uso de `GROUP BY`, `HAVING` y subconsultas para detectar duplicados.

### 03. Parsing de Strings y Fechas (`03_string_and_date_parsing.sql`)
- **Objetivo:** Estandarización de formatos de texto y tiempo.
- **Técnicas:** Funciones `SUBSTR`, `INSTR`, `REPLACE` y formateo de fechas ISO.

### 04. Transformación con Lógica Condicional (`04_data_transformation_case.sql`)
- **Objetivo:** Reestructuración de datos basada en reglas de negocio.
- **Técnicas:** Dominio de la sentencia `CASE` para crear nuevas dimensiones.

### 05. Pipeline de Limpieza Automatizada (`05_automated_cleaning_pipeline.sql`)
- **Objetivo:** Ejecución secuencial de reglas de limpieza.
- **Técnicas:** Encadenamiento de operaciones de transformación.

### 06. Auditoría y Perfilado (`06_data_profiling_audit.sql`)
- **Objetivo:** Análisis de la salud de los datos.
- **Técnicas:** Detección de nulos, valores atípicos (outliers) e integridad referencial.

### 07. Integración de Tablas Maestras (`07_data_integration_master_table.sql`)
- **Objetivo:** Consolidación de fuentes de datos heterogéneas.
- **Técnicas:** `JOINs` complejos y uniones de tablas para crear una "Single Source of Truth".

### 08. Automatización mediante Vistas (`08_automation_staging_and_views.sql`)
- **Objetivo:** Abstracción de la lógica de limpieza para el usuario final.
- **Técnicas:** Creación de `VIEWS` y tablas de staging para optimizar el rendimiento.

## 🧠 Conceptos Clave Aplicados
* **Manejo de Nulos:** Implementación de `COALESCE` para robustez de datos.
* **Window Functions:** Aplicación de `PARTITION BY` para análisis granular.
* **Documentación:** Explicación técnica de la lógica aplicada en cada transformación.

---
*Estos ejercicios sirven como base técnica para el proyecto final: **"El Gran Limpiador"**.*