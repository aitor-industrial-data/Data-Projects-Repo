# 📊 SQL_Fundamentals_Practice

## 📂 Descripción del Proyecto
Este directorio contiene una colección de scripts SQL desarrollados durante el modulo **01_SQL_Fundamentals** de mi plan de especialización en Ingeniería de Datos. El objetivo de esta etapa fue dominar los **Fundamentos de SQL**, utilizando la base de datos **Chinook** (esquema en singular) para resolver problemas de lógica de negocio reales.

Estos ejercicios demuestran mi capacidad para extraer, limpiar y agregar datos de manera eficiente y estructurada.

---

## 🛠️ Stack Técnico
* **Base de Datos:** SQLite (Esquema Chinook)
* **Herramientas:** DB Browser (SQLite), DBeaver, VS Code
* **Conceptos Clave:** Joins, Agregaciones, Filtrado de Fechas, Búsqueda de Patrones e Integridad de Datos.

---

## 📜 Inventario de Scripts

| # | Nombre del Archivo | Enunciado / Problema Real | Foco Técnico |
| :--- | :--- | :--- | :--- |
| 01 | `01_customer_contact_brazil.sql` | Obtener nombres y correos de clientes de Brasil. | `SELECT` / `WHERE` |
| 02 | `02_rock_tracks_by_duration.sql` | Listar canciones de Rock por duración (mayor a menor). | `ORDER BY` |
| 03 | `03_unique_client_markets.sql` | Listar países únicos con clientes. | `DISTINCT` |
| 04 | `04_sales_q1_2024.sql` | Identificar facturas emitidas en el Q1 de 2024. | `Date Filtering` |
| 05 | `05_unmanaged_employees.sql` | Listar empleados sin jefe asignado (Nivel Directivo). | `IS NULL` |
| 06 | `06_customer_name_search.sql` | Buscar clientes con patrones específicos ("J...n"). | `LIKE` / `Wildcards` |
| 07 | `07_album_artist_mapping.sql` | Relacionar títulos de álbumes con sus artistas. | `INNER JOIN` |
| 08 | `08_invoice_customer_details.sql` | Listar facturas con el nombre completo del cliente. | `JOIN` / `Aliases` |
| 09 | `09_track_media_inventory.sql` | Listar canciones con su género y tipo de formato. | `Multiple JOINs` |
| 10 | `10_total_historical_revenue.sql` | Calcular el ingreso total histórico de la tienda. | `SUM` |
| 11 | `11_avg_album_duration.sql` | Calcular la duración media por cada álbum. | `AVG` / `GROUP BY` |
| 12 | `12_jazz_price_range.sql` | Encontrar el rango de precios (Mín/Máx) en Jazz. | `MIN` / `MAX` |
| 13 | `13_playlist_track_count.sql` | Contar canciones por cada lista de reproducción. | `COUNT` / `JOIN` |
| 14 | `14_popular_genres_report.sql` | Filtrar géneros con más de 100 canciones. | `HAVING` |

---

## 📈 Hitos de Aprendizaje
1.  **Lógica Relacional:** Implementación exitosa de uniones de múltiples tablas para consolidar información.
2.  **Calidad de Datos:** Uso de filtros `IS NULL` y `IS NOT NULL` para asegurar la integridad de los reportes.
3.  **Analítica:** Desarrollo de consultas complejas utilizando agrupaciones y funciones de agregado para extraer KPIs.
4.  **Estándares Profesionales:** Todos los archivos siguen convenciones de nomenclatura en inglés y un formato de código limpio.
