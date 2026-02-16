/*******************************************************************************
RUTA DE INGENIERÍA DE DATOS - MES 2: SQL Avanzado y Wrangling
DÍA 49: Transformación - Lógica CASE y Adaptación de Esquemas
*******************************************************************************
Objetivo: 
    Enriquecer los datos crudos creando nuevas dimensiones de análisis 
    (Categorías y Regiones) sin alterar los datos originales.

Lógica de Negocio Aplicada:
    1. Segmentación de Clientes (VIP vs Regular).
    2. Agrupación Geográfica (Regiones).
    3. Categorización de Transacciones (Bucketing de precios).
*******************************************************************************/

-- =============================================================================
-- 1. TRANSFORMACIÓN DE CLIENTES (Enriquecimiento)
-- Creamos una vista intermedia con regiones y segmentos.
-- =============================================================================

DROP VIEW IF EXISTS V_Customer_Segmented;

CREATE VIEW V_Customer_Segmented AS
SELECT 
    CustomerId,
    FirstName || ' ' || LastName as Full_Name,
    Country,
    -- Lógica de Regiones (Mapping)
    CASE 
        WHEN Country IN ('USA', 'Canada') THEN 'North America'
        WHEN Country IN ('Brazil', 'Argentina', 'Chile') THEN 'Latin America'
        WHEN Country IN ('India', 'Australia') THEN 'Asia-Pacific'
        ELSE 'Europe/EMEA' 
    END as World_Region
FROM customer;

-- =============================================================================
-- 2. TRANSFORMACIÓN DE VENTAS (Bucketing)
-- Clasificamos las facturas por su valor monetario.
-- =============================================================================

DROP VIEW IF EXISTS V_Invoice_Categorized;

CREATE VIEW V_Invoice_Categorized AS
SELECT 
    InvoiceId,
    CustomerId,
    InvoiceDate,
    Total,
    -- Lógica de Precios (Bucketing)
    CASE 
        WHEN Total < 5.00 THEN 'Low Value'
        WHEN Total BETWEEN 5.00 AND 15.00 THEN 'Mid Value'
        ELSE 'High Value'
    END as Sales_Category,
    
    -- Lógica de Temporada (Parsing de Fecha + CASE)
    -- Extraemos el mes y decimos qué trimestre (Q) es.
    CASE 
        WHEN STRFTIME('%m', InvoiceDate) IN ('01','02','03') THEN 'Q1'
        WHEN STRFTIME('%m', InvoiceDate) IN ('04','05','06') THEN 'Q2'
        WHEN STRFTIME('%m', InvoiceDate) IN ('07','08','09') THEN 'Q3'
        ELSE 'Q4'
    END as Quarter
FROM invoice;

-- =============================================================================
-- 3. CAPA FINAL: ANALÍTICA DE NEGOCIO (Join de Transformaciones)
-- Unimos las dos vistas transformadas para responder preguntas complejas.
-- =============================================================================

SELECT 
    c.World_Region,
    i.Sales_Category,
    COUNT(i.InvoiceId) as Total_Invoices,
    SUM(i.Total) as Total_Revenue
FROM V_Invoice_Categorized i
JOIN V_Customer_Segmented c ON i.CustomerId = c.CustomerId
GROUP BY 1, 2
ORDER BY 1, 4 DESC;

/*******************************************************************************
RESUMEN DE INGENIERÍA:
Hemos transformado datos crudos (números y nombres de países) en 
información estratégica (Regiones y Categorías de Venta) usando CASE.
*******************************************************************************/