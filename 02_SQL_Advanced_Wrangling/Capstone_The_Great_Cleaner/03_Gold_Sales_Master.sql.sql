/*******************************************************************************
PROYECTO: "The Great Cleaner"
FASE 3: 03_Gold_Sales_Master.sql (Gold Layer / Capa de Producción)
OBJETIVO: Unir las dimensiones limpias (Clientes y Catálogo) con las ventas 
          reales para entregar un "Data Mart" listo para herramientas de BI.
AUTOR: AITOR / Ingeniero Técnico Industrial / Data Engineer
*******************************************************************************/

-- 1. Limpieza previa por si la vista ya existe
DROP VIEW IF EXISTS V_Gold_Sales_Analytics;

-- 2. Creación de la vista de producción (Business Intelligence Ready)
CREATE VIEW V_Gold_Sales_Analytics AS
SELECT 
    -- Datos Transaccionales Base
    i.InvoiceId,
    DATE(i.InvoiceDate) AS Invoice_Date,
    
    -- Dimensión Cliente (Usando tu vista limpia de la FASE 1)
    c.Full_Name AS Customer_Name,
    c.Company AS Customer_Segment, -- Aquí veremos 'B2C Customer' o 'B2B Customer'
    c.Country AS Customer_Country,
    
    -- Dimensión Producto (Usando tu vista auditada de la FASE 2)
    t.Track_Name,
    t.Album_Title,
    t.Artist_Name,
    t.Duration_Status AS Track_Quality_Flag, -- Útil para ver si vendemos tracks "corruptos"
    
    -- Métricas Financieras (KPIs)
    il.UnitPrice,
    il.Quantity,
    ROUND(il.UnitPrice * il.Quantity, 2) AS Line_Revenue

FROM Invoice i
-- Unimos con la tabla de detalle de factura
JOIN InvoiceLine il ON i.InvoiceId = il.InvoiceId
-- Unimos con la Capa Silver de Clientes
JOIN V_Silver_Clean_Customer_Roster c ON i.CustomerId = c.CustomerId
-- Unimos con la Capa Silver del Catálogo
JOIN V_Silver_Track_Inventory_Audit t ON il.TrackId = t.TrackId;

/*******************************************************************************
NOTAS PARA EL RECLUTADOR:
- Esta vista consolida la limpieza de datos (Wrangling) de las Fases 1 y 2.
- Evita que los analistas de negocio tengan que lidiar con nulos, strings 
  sucios o errores de integridad referencial.
- Optimizada para ser conectada directamente a Power BI o Tableau.
*******************************************************************************/