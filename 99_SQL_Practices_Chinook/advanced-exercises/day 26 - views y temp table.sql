/*******************************************************************************
  DATA ENGINEERING - DÍA 26: ESTRUCTURAS DE REUTILIZACIÓN Y STAGING
  Foco: Vistas (Views) y Tablas Temporales (Temp Tables)
  Base de Datos: Chinook (SQLite)
*******************************************************************************/

-- =============================================================================
-- PROBLEMA 1: CREACIÓN DE VISTA (BUSINESS INTELLIGENCE)
-- Enunciado: Crear una vista que reporte el rendimiento financiero por género.
-- =============================================================================

/* ANOTACIÓN TÉCNICA:
   Las Vistas son "consultas virtuales". No duplican los datos, solo guardan 
   la lógica. Son ideales para que otros departamentos (como Marketing) 
   consulten datos complejos sin conocer los JOINs. */

DROP VIEW IF EXISTS View_Genre_Revenue;

CREATE VIEW View_Genre_Revenue AS
SELECT 
    g.Name AS Genre_Name,
    ROUND(SUM(il.UnitPrice * il.Quantity), 2) AS Revenue,
    SUM(il.Quantity) AS Units_Sold
FROM Genre g
JOIN Track t ON g.GenreId = t.GenreId
JOIN InvoiceLine il ON t.TrackId = il.TrackId
GROUP BY g.Name
ORDER BY Revenue DESC;

-- Prueba de la vista:
SELECT * FROM View_Genre_Revenue WHERE Units_Sold > 100;


-- =============================================================================
-- PROBLEMA 2: TABLA TEMPORAL PARA LIMPIEZA (ETL / STAGING)
-- Enunciado: Identificar clientes inactivos durante el año 2013.
-- =============================================================================

/* ANOTACIÓN TÉCNICA:
   Para buscar "Inactividad", el uso de subconsultas con NOT IN es más 
   robusto que un JOIN. Usamos una TEMP TABLE para aislar estos IDs 
   sin afectar a la base de datos permanente. */

DROP TABLE IF EXISTS Temp_Inactive_2013;

CREATE TEMP TABLE Temp_Inactive_2013 AS
SELECT 
    CustomerId, 
    FirstName, 
    Email
FROM Customer
WHERE CustomerId NOT IN (
    -- Subconsulta: Clientes que SÍ compraron en 2013
    SELECT DISTINCT CustomerId 
    FROM Invoice 
    WHERE strftime('%Y', InvoiceDate) = '2013'
);

-- Consulta de verificación:
SELECT * FROM Temp_Inactive_2013;


-- =============================================================================
-- PROBLEMA 3: ANÁLISIS DE PASOS INTERMEDIOS (TOP 3 MENSUAL)
-- Enunciado: Calcular el promedio de ventas de los 3 meses más exitosos.
-- =============================================================================

/* ANOTACIÓN TÉCNICA:
   Este es un proceso de "Agregación sobre Agregación". 
   Paso 1: Agrupar por mes en una tabla temporal.
   Paso 2: Calcular el promedio sobre los mejores resultados de esa tabla. */

DROP TABLE IF EXISTS Temp_Monthly_Sales;

CREATE TEMP TABLE Temp_Monthly_Sales AS
SELECT 
    strftime('%Y-%m', InvoiceDate) AS Periodo,
    SUM(Total) AS Monthly_Total
FROM Invoice
GROUP BY Periodo;

-- Consulta final usando la tabla temporal como fuente:
SELECT 
    ROUND(AVG(Monthly_Total), 2) AS Avg_Top_3_Months
FROM (
    SELECT Monthly_Total 
    FROM Temp_Monthly_Sales 
    ORDER BY Monthly_Total DESC 
    LIMIT 3
);



-- =============================================================================
-- RESUMEN DE APRENDIZAJE - DÍA 26
-- =============================================================================
/* 1. VIEW: Uso para simplificar reportes recurrentes. Ocupa 0 bytes.
   2. TEMP TABLE: Uso para staging, limpieza y cálculos intermedios. 
      Desaparece al cerrar la sesión de DBeaver.
   3. NOT IN vs JOIN: En ingeniería de datos, preferimos NOT IN o NOT EXISTS 
      para lógica de exclusión por claridad y, a veces, rendimiento.
*/