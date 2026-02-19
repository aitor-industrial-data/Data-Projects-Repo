# 📑 Master SQL Script Guide: Pipeline Chinook Star Schema

### 🎯 Overview
Este repositorio contiene el flujo de transformación de datos (**ETL**) para convertir la base de datos transaccional **Chinook (OLTP)** en un modelo analítico bajo un **Esquema en Estrella (OLAP)**. 

El objetivo principal es optimizar la base de datos para responder preguntas de negocio de forma rápida, eliminando valores nulos, normalizando textos y pre-calculando métricas clave de rendimiento.

---

### 🛠️ Execution Sequence (Orden de Ejecución)
Para reconstruir el modelo analítico correctamente y mantener la integridad referencial, los scripts deben ejecutarse siguiendo estrictamente este orden numérico:

| Orden | Archivo | Descripción del Proceso |
| :--- | :--- | :--- |
| **00** | `00_inventory_sanity_checks.sql` | **Auditoría y Control de Calidad**: Verificación del esquema (sqlite_master), validación de integridad de datos (Expected vs Actual) y chequeo de salud inicial del entorno. |
| **01** | `01_data_wrangling_tracks.sql` | **Limpieza y Estandarización**: Eliminación de espacios, normalización a mayúsculas, gestión de nulos (`COALESCE`) y conversión de unidades (ms a min, Bytes a MB). |
| **02** | `02_create_dim_tracks.sql` | **Modelado de Dimensión**: Creación de la tabla `Dim_Track`. Desnormalización de géneros y tipos de medio para minimizar `JOINs` en consultas finales. |
| **03** | `03_create_fact_sales.sql` | **Diseño de Tabla de Hechos**: Definición de `Fact_Sales`. Implementación de **Surrogate Keys** (Claves Subrogadas) y métricas de venta agregadas. |
| **04** | `04_load_star_schema.sql` | **Carga Masiva (ETL Load)**: Script final de carga desde el área de *Staging* hacia el modelo definitivo, asegurando consistencia en las relaciones FK/PK. |



---

### 🧠 Ingeniería de Datos Aplicada
* **Staging Isolation**: Uso de tablas temporales (`stg_`) para proteger la "Fuente de Verdad" (Source of Truth) original.
* **Data Casting & Nesting**: Aplicación de funciones anidadas para una limpieza profunda y eficiente.
* **Business Logic**: Clasificación automática de productos (Categorías Premium/Standard) mediante lógica condicional `CASE`.
* **Performance Tuning**: Filtrado estratégico de registros pesados y ordenación lógica para optimizar el acceso a disco.

---


> **Nota:** Este proyecto utiliza la versión "Singular" de la base de datos Chinook (ej., la tabla "Customer" en lugar de "Customers"). Si utiliza la versión plural, ajuste los nombres de las tablas según corresponda."

