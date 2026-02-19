
# 🌾 Análisis de Producción Agrícola (Proyecto SQL de UC Davis)
## Descripción del Proyecto
Este repositorio contiene el proyecto final (Capstone) del curso **"SQL for Data Science"** impartido por la **University of California, Davis (UC Davis)**.

Se centra en los aspectos fundamentales de la Ingeniería de Datos: **Definición de Esquemas (Schema Definition)** e **Ingesta de Datos (Data Ingestion)**. Utilizando conjuntos de datos agrícolas (leche, huevos, queso, miel, etc.), he construido una estructura relacional para almacenar y consultar datos de producción.

## 🛠️ Stack Tecnológico
- **Motor de Base de Datos:** SQLite
- **Stack de Software:** DBeaver / DB Browser (SQLite)
- **Lenguajes:** SQL (DDL y DML)

## 🗺️ Esquema de Datos (ERD)

<details>
  <summary><b>Ver Diagrama de Entidad-Relación (ERD) 🗺️</b></summary>
  <br>
  <img src="./images/Diagram_UC_Davis_Agriculture_Project.png" alt="Database Schema" width="800">
</details>

## 📂 Estructura del Proyecto
- `/source`: Archivos CSV originales (Raw Data).
- `/scripts`: Scripts de SQL organizados por orden de ejecución.
    - [`01_create_tables.sql`](./scripts/01_create_agriculture_tables.sql): Script DDL para definir el esquema de la base de datos.
    - [`02_data_cleaning.sql`](./scripts/02_data_cleaning.sql): Limpieza y normalización de datos (DML). Este script elimina caracteres especiales (como comas en los campos numéricos) para permitir el análisis matemático y asegurar la integridad de los datos.
    - [`03_UC_Davis_Agriculture_Project.sql`](./scripts/03_UC_Davis_Agriculture_Project.sql): Proyecto Final (Capstone). Análisis exhaustivo mediante JOINS, subconsultas y funciones de agregación.
- `/image`: Diagrama de la Base de Datos.
## 🚀 Objetivos de Aprendizaje
1. **Organización de Datos:** Implementación de una estructura de carpetas profesional para tuberías de datos (Data Pipelines).
2. **Diseño de Esquemas:** Definición de tipos de datos adecuados (INTEGER, TEXT) para métricas agrícolas.
3. **Ingesta de Datos:** Gestión del proceso de importación de CSV a una base de datos relacional.
4. **Análisis de Datos:** Extracción de insights mediante lógica SQL avanzada aprendida en el curso de UC Davis.

---
*Proyecto de certificación integrado en mi programa de especialización intensiva en Data Engineering*