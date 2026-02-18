# 🧹 The Great Cleaner: Pipeline de Limpieza y Auditoría de Datos en SQL

![SQL](https://img.shields.io/badge/SQL-SQLite-blue)
![Data Engineering](https://img.shields.io/badge/Data_Engineering-Wrangling-orange)
![Arquitectura](https://img.shields.io/badge/Arquitectura-Medallion-success)

## 📌 Descripción del Proyecto
Este proyecto es un **pipeline integral de Limpieza de Datos (Wrangling) y Perfilado** construido sobre la base de datos relacional Chinook. Simula un escenario real de Ingeniería de Datos donde los datos brutos e inconsistentes (Capa Bronze) se transforman en datos estandarizados (Capa Silver) y, finalmente, en vistas listas para negocio (Capa Gold).



## 🎯 El Problema de Negocio
La base de datos original de Chinook presenta varios problemas de calidad:
- Formatos de texto inconsistentes en datos de CRM (teléfonos con paréntesis, guiones y espacios).
- Valores nulos en campos categóricos críticos.
- Registros anómalos o corruptos en el inventario (pistas con duraciones imposibles).
- Falta de segmentación clara entre clientes particulares (B2C) y empresas (B2B).

**El objetivo es establecer un marco de Calidad de Datos y entregar un Data Mart limpio.**

## 🏗️ Arquitectura y Flujo de Trabajo

El proyecto se estructura en tres fases secuenciales, aplicando los principios de la **Arquitectura Medallón**:

### Fase 1: Estandarización de Clientes (`01_Silver_Customer_Cleansing.sql`)
**Capa:** Silver 🥈
- **Limpieza de Datos:** Manipulación profunda de strings mediante funciones `REPLACE` anidadas para normalizar teléfonos para integraciones de API.
- **Gestión de Nulos:** Uso estratégico de `COALESCE` para evitar que la falta de valores rompa sistemas posteriores.
- **Lógica de Negocio:** Segmentación de usuarios en `B2C Customer` o `B2B Customer` basada en metadatos de empresa.

### Fase 2: Auditoría de Inventario y Calidad (`02_Silver_Track_Audit.sql`)
**Capa:** Silver 🥈
- **Perfilado de Datos (Profiling):** Auditoría de duraciones (milisegundos) para identificar valores atípicos (< 10s o > 1h) marcándolos como `Corrupted`.
- **Funciones de Ventana (Window Functions):** Uso de `COUNT() OVER(PARTITION BY ...)` para categorizar álbumes en 'EP' o 'LP' dinámicamente.
- **Integridad Referencial:** Uso de `LEFT JOIN` para identificar pistas "huérfanas" sin perder datos, asignando valores por defecto.

### Fase 3: Capa de Producción (`03_Gold_Sales_Master.sql`)
**Capa:** Gold 🥇
- **Creación del Data Mart:** Unión de las dimensiones limpias (`V_Silver_Clean_Customer_Roster` & `V_Silver_Track_Inventory_Audit`) con las tablas de hechos transaccionales (`Invoice` e `InvoiceLine`).
- **Generación de KPIs:** Cálculo de ingresos por línea (`Line_Revenue`) y exposición de banderas de calidad para el equipo de BI.



## 🛠️ Stack Tecnológico
- **Motor de Base de Datos:** SQLite (Versión Chinook con columnas en singular).
- **Herramientas:** DB Browser for SQLite / DBeaver / Visual Studio Code.
- **Técnicas:** CTEs, Window Functions, String Parsing, Data Profiling, Vistas SQL.

## 🚀 Cómo Ejecutarlo
1. Conéctate a la base de datos Chinook usando tu IDE preferido.
2. Ejecuta los scripts en orden secuencial:
   - [`01_Silver_Customer_Cleansing.sql`](./Capstone_The_Great_Cleaner/01_Silver_Customer_Cleansing.sql)
   - [`02_Silver_Track_Audit.sql`](./Capstone_The_Great_Cleaner/02_Silver_Track_Audit.sql)
   - [`03_Gold_Sales_Master.sql`](./Capstone_The_Great_Cleaner/03_Gold_Sales_Master.sql)
3. Consulta la vista final para ver los resultados:
   ```sql
   SELECT * FROM V_Gold_Sales_Analytics LIMIT 100;