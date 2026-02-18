# 02_ Data Wrangling & Quality Assurance 🛠️

Este módulo marca la transición de un usuario de SQL básico a un **Ingeniero de Datos** capaz de auditar, limpiar y estructurar información bajo estándares de producción. Durante este apartado, el foco ha sido la transformación de datos crudos (Bronze) en activos digitales fiables (Silver/Gold).

## 📂 Estructura del Módulo

El repositorio está organizado de forma modular para reflejar un flujo de trabajo profesional:


* **[Data_Cleaning_SQL](./01_Data_Cleaning_SQL/)**: Colección de scripts y ejercicios diarios enfocados en la resolución de problemas específicos de limpieza y transformación.
* **[CAPSTONE: The Great Cleaner](./02_Capstone_The_Great_Cleaner/)**: Mi proyecto estrella de consolidación. Un pipeline de limpieza en 3 fases que aplica una arquitectura de capas sobre la base de datos Chinook.

## 🚀 Habilidades Técnicas Consolidadas

### 1. Manipulación Avanzada de Datos (Wrangling)
- **Normalización de Strings:** Uso de funciones anidadas para estandarizar formatos telefónicos y de contacto.
- **Lógica Condicional Compleja:** Segmentación de negocio (B2B/B2C) mediante `CASE` y gestión de nulos con `COALESCE` y `NULLIF`.
- **Arquitectura de Vistas:** Creación de capas de abstracción para proteger la integridad de los datos originales.

### 2. Auditoría y Calidad (Data Quality)
- **Data Profiling:** Identificación de registros corruptos u outliers mediante análisis de distribución y duración.
- **Integridad Referencial:** Detección de registros "huérfanos" y estandarización de metadatos mediante Joins avanzados.

### 3. SQL de Alto Rendimiento
- **Window Functions:** Implementación de `COUNT() OVER`, `SUM() OVER` y particionamiento de datos para analítica avanzada sin colapsar registros.
- **CTEs (Common Table Expressions):** Estructuración de consultas legibles, modulares y fáciles de mantener.

## 🛠️ Herramientas Utilizadas
- **DB Browser for SQLite & DBeaver:** Gestión y visualización de bases de datos.
- **Visual Studio Code:** Desarrollo de scripts SQL y documentación.
- **Git Bash:** Control de versiones y despliegue a GitHub.

---
*Este módulo forma parte de mi programa de especialización intensiva en Data Engineering, enfocado en ganar eficiencia técnica y capacidad analítica para entornos de trabajo remoto.*