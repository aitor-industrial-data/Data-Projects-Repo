-- =============================================================================
-- SCRIPT 03: CREATE FACT SALES (Star Schema)
-- Author: Aitor (Data Engineer Pro)
-- Goal: Create the central Fact Table for Sales Analysis.
-- =============================================================================

-- 1. LIMPIEZA DE ENTORNO
-- Borramos la tabla si ya existe para asegurar una carga limpia desde cero.
DROP TABLE IF EXISTS Fact_Sales;

-- 2. CREACIÓN DE LA ESTRUCTURA DE LA TABLA DE HECHOS
-- Esta tabla almacena los "Hechos" (Ventas) y las claves para unir con Dimensiones.
CREATE TABLE Fact_Sales (
    SalesId INTEGER PRIMARY KEY AUTOINCREMENT, -- Surrogate Key para la tabla de hechos
    InvoiceId INTEGER,                         -- ID original de la factura
    InvoiceLineId INTEGER,                     -- ID original de la línea
    TrackId INTEGER,                           -- FK a Dim_Track (Creada en Script 02)
    CustomerId INTEGER,                        -- FK a Dim_Customer (Pendiente)
    
    -- Métricas (Medidas cuantitativas)
    Quantity INTEGER,
    UnitPrice REAL,
    LineTotal REAL,                            -- Métrica calculada (Quantity * UnitPrice)
    
    -- Atributos de tiempo (Denormalizados para facilitar reportes rápidos)
    InvoiceDate DATETIME,
    Sale_Year INTEGER,
    Sale_Month INTEGER,
    
    FOREIGN KEY (TrackId) REFERENCES Dim_Track(TrackId)
);

-- 3. CARGA DE DATOS (ETL - Fact Load)
-- Unimos Invoice (Cabecera) con InvoiceLine (Detalle) para aplanar la información.
INSERT INTO Fact_Sales (
    InvoiceId, 
    InvoiceLineId, 
    TrackId, 
    CustomerId, 
    Quantity, 
    UnitPrice, 
    LineTotal, 
    InvoiceDate, 
    Sale_Year, 
    Sale_Month
)
SELECT 
    i.InvoiceId,
    il.InvoiceLineId,
    il.TrackId,
    i.CustomerId,
    il.Quantity,
    il.UnitPrice,
    (il.Quantity * il.UnitPrice) AS LineTotal, -- Cálculo de la métrica de negocio
    i.InvoiceDate,
    STRFTIME('%Y', i.InvoiceDate) AS Sale_Year, -- Extracción de año para analítica
    STRFTIME('%m', i.InvoiceDate) AS Sale_Month  -- Extracción de mes para estacionalidad
FROM Invoice i
JOIN InvoiceLine il ON i.InvoiceId = il.InvoiceId;

-- 4. VALIDACIÓN DE CARGA
-- Verificamos que el total de registros coincida con nuestra auditoría del Script 00.
-- El Script 00 decía que InvoiceLine tiene 2240 filas.
SELECT 
    'Fact_Sales' AS Table_Name,
    COUNT(*) AS Total_Rows,
    SUM(LineTotal) AS Total_Revenue
FROM Fact_Sales;

-- Ver un ejemplo de los datos finales
SELECT * FROM Fact_Sales LIMIT 5;