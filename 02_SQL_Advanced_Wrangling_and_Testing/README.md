# 02_ Data Quality, Wrangling & Testing

Este módulo marca la transición de un usuario de SQL básico a un **Ingeniero de Datos** capaz de auditar, limpiar y estructurar información bajo estándares de producción. Durante este apartado, el foco ha sido la transformación de datos crudos (Bronze) en activos digitales fiables (Silver/Gold).

## 📂 Estructura del Módulo

El repositorio está organizado de forma modular para reflejar un flujo de trabajo profesional, priorizando la práctica técnica antes de la ejecución de proyectos complejos:

* **[02.01_SQL_Advanced_Practice](./02.01_SQL_Advanced_Practice/)**: Batería de ejercicios avanzados que cubren desde Window Functions hasta auditorías de integridad. Es la base técnica del módulo.
* **[02.02_Data_Cleaning_SQL](./02.02_Data_Cleaning_SQL/)**: Scripts y metodologías enfocadas en la resolución de problemas específicos de limpieza y transformación de tipos de datos.
* **[02.03_CAPSTONE_The_Great_Cleaner](./02.03_CAPSTONE_The_Great_Cleaner/)**: Mi proyecto estrella de consolidación. Un pipeline de limpieza en 3 fases que aplica una arquitectura de capas sobre la base de datos Chinook.
* **[02.04_AB_Testing_SQL](./02.04_AB_Testing_SQL/)**: Implementación de un flujo experimental completo sobre la capa Gold. Incluye la segmentación determinista de usuarios y el análisis de métricas de negocio (ARPU y conversión).

## 🚀 Habilidades Técnicas Consolidadas

### 1. Manipulación Avanzada de Datos (Wrangling)
- **Normalización de Strings:** Uso de funciones anidadas para estandarizar formatos telefónicos y de contacto.
- **Lógica Condicional Compleja:** Segmentación de negocio (B2B/B2C) mediante `CASE` y gestión de nulos con `COALESCE` y `NULLIF`.
- **Arquitectura de Vistas:** Creación de capas de abstracción para proteger la integridad de los datos originales.

### 2. Auditoría y Calidad (Data Quality)
- **Data Profiling:** Identificación de registros corruptos u outliers mediante análisis de distribución y duración.
- **Integridad Referencial:** Detección de registros "huérfanos" y estandarización de metadatos mediante Joins avanzados.

### 3. SQL de Alto Rendimiento
- **Window Functions:** Implementación de `RANK`, `LEAD`, `LAG` y particionamiento de datos para analítica avanzada sin colapsar registros.
- **CTEs (Common Table Expressions):** Estructuración de consultas legibles, modulares y fáciles de mantener.

### 4. Experimentación y Análisis de Negocio (A/B Testing)
- **Segmentación Determinista:** Creación de grupos de control (A) y variante (B) mediante operadores matemáticos (`MOD`) para asegurar una distribución equilibrada y reproducible.
- **Cálculo de KPIs de Performance:** Desarrollo de consultas para medir el **ARPU** (Average Revenue Per User) e ingresos totales.
- **Análisis de Conversión:** Uso de `LEFT JOIN` avanzado para evitar el "sesgo de supervivencia", incluyendo en las métricas a usuarios sin transacciones.

## 🛠️ Herramientas Utilizadas
- **DB Browser for SQLite & DBeaver:** Gestión y visualización de bases de datos.
- **Visual Studio Code:** Desarrollo de scripts SQL y documentación.
- **Git Bash:** Control de versiones y despliegue a GitHub.

---
*Este módulo forma parte de mi programa de especialización intensiva en Data Engineering, enfocado en ganar eficiencia técnica y capacidad analítica para entornos de trabajo remoto.*