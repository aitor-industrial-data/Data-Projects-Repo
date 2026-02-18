/*******************************************************************************
RUTA DE INGENIERÍA DE DATOS - DÍA 54: Integración de Fuentes
Objetivo: Crear una "Tabla Maestra de Consumo" uniendo clientes, facturas y música.
*******************************************************************************/

-- =============================================================================
-- 1. CREACIÓN DE LA VISTA INTEGRADA (Master Table)
-- =============================================================================

DROP VIEW IF EXISTS V_Master_Sales_Analysis;

CREATE VIEW V_Master_Sales_Analysis AS
SELECT 
    -- Datos del Cliente (Desde tu vista limpia 'V_Final_Customer_Clean')
    c.CustomerId,
    c.FirstName || ' ' || c.LastName as Customer_Name,
    c.Territory,
    c.Country,

    -- Datos de la Venta
    i.InvoiceId,
    i.InvoiceDate,
    il.UnitPrice * il.Quantity as Line_Total,

    -- Datos del Producto (Música)
    t.Name as Track_Name,
    g.Name as Genre_Name
FROM V_Final_Customer_Clean c                             -- Capa limpia de clientes
JOIN Invoice i ON c.CustomerId = i.CustomerId             -- Unión con facturas
JOIN InvoiceLine il ON i.InvoiceId = il.InvoiceId         -- Detalle de cada factura
JOIN Track t ON il.TrackId = t.TrackId                    -- Unión con canciones
JOIN Genre g ON t.GenreId = g.GenreId;                    -- Unión con géneros

-- =============================================================================
-- 2. ANÁLISIS DE INTEGRACIÓN (Business Intelligence)
-- Ahora que todo está unido, podemos responder preguntas de alto nivel.
-- =============================================================================

-- ¿Cuál es el género más vendido por cada Territorio ?
SELECT 
    Territory,
    Genre_Name,
    ROUND(SUM(Line_Total), 2) as Total_Revenue,
    COUNT(*) as Units_Sold
FROM V_Master_Sales_Analysis
GROUP BY 1, 2
ORDER BY 1, 3 DESC;