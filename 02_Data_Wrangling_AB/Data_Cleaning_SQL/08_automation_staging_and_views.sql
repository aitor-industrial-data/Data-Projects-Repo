/*******************************************************************************
RUTA DE INGENIERÍA DE DATOS - MES 2 
DÍA 55: Automatización - Arquitectura Eficiente (Staging + Views)
*******************************************************************************
Objetivo: 
    Optimizar el rendimiento mediante una tabla de paso (Staging) y automatizar 
    la lógica de negocio mediante una Vista de Producción.

Lógica de Ingeniero:
    1. Pre-calculamos los totales en una tabla física para ahorrar CPU.
    2. Creamos una vista que "bebe" de esa tabla y de la vista limpia 'V_Final_Customer_Clean'.
*******************************************************************************/

-- =============================================================================
-- 1. CAPA DE PROCESAMIENTO (Staging Table)
-- Creamos una tabla real para que los datos sean persistentes y visibles.
-- =============================================================================

DROP TABLE IF EXISTS Staging_Customer_Sales_Summary;

CREATE TABLE Staging_Customer_Sales_Summary AS
SELECT 
    CustomerId,
    SUM(Total) as Total_Spent,
    COUNT(InvoiceId) as Transaction_Count
FROM invoice
GROUP BY CustomerId;

-- =============================================================================
-- 2. CAPA DE PRESENTACIÓN (Production View)
-- Unimos nuestra vista de clientes limpios con el resumen de ventas.
-- =============================================================================

DROP VIEW IF EXISTS V_Customer_Performance_Report;

CREATE VIEW V_Customer_Performance_Report AS
SELECT 
    c.CustomerId,
    c.FirstName || ' ' || c.LastName as Customer_Name,
    c.Territory,
    t.Total_Spent,
    t.Transaction_Count,
    -- Automatización de Lógica de Negocio: Clasificación de valor
    CASE 
        WHEN t.Total_Spent > 45 THEN 'Top Tier (Gold)'
        WHEN t.Total_Spent BETWEEN 35 AND 45 THEN 'Mid Tier (Silver)'
        ELSE 'Standard'
    END as Customer_Value_Rank
FROM V_Final_Customer_Clean c -- Vista maestra
JOIN Staging_Customer_Sales_Summary t ON c.CustomerId = t.CustomerId;

-- =============================================================================
-- 3. AUDITORÍA Y RESULTADOS
-- =============================================================================

-- Comprobamos que la automatización funciona y el reporte está listo
SELECT * FROM V_Customer_Performance_Report 
ORDER BY Total_Spent DESC;

/* Nota de Ingeniero: 
Al usar una tabla física (Staging), cualquier herramienta externa podrá 
ver las columnas de la vista sin errores de conexión.
*/