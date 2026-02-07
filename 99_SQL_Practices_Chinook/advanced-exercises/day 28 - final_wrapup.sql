/*******************************************************************************
  DATA ENGINEERING - DÍA 28: OPTIMIZACIÓN Y COMPLEJIDAD TEMPORAL
  Proyecto: Global Sales Master Report
  Objetivo: Analizar la eficiencia de las agregaciones en entornos escalables.
*******************************************************************************/

-- =============================================================================
-- ENUNCIADO:
-- Crear una infraestructura de reporte (VIEW) que clasifique los países según 
-- su volumen de ventas, calculando el ticket medio y el estatus de mercado.
-- Además, documentar la estrategia de escalabilidad para Big Data.
-- =============================================================================

DROP VIEW IF EXISTS View_Global_Sales_Report;

CREATE VIEW View_Global_Sales_Report AS
SELECT 
    i.BillingCountry AS Country,
    COUNT(i.InvoiceId) AS Total_Orders,
    ROUND(SUM(i.Total), 2) AS Gross_Revenue,
    ROUND(AVG(i.Total), 2) AS Average_Ticket,
    CASE 
        WHEN SUM(i.Total) > 100 THEN 'Prioritario'
        ELSE 'Estrategia de Crecimiento'
    END AS Market_Status
FROM Invoice i
WHERE i.BillingCountry IS NOT NULL
GROUP BY i.BillingCountry
ORDER BY Gross_Revenue DESC;

/* =============================================================================
ANÁLISIS DE COMPLEJIDAD TEMPORAL (ENGINEERING NOTES)
=============================================================================

1. ESCENARIO CHINOOK (Pequeña Escala):
   - Filas: ~400 facturas.
   - Rendimiento: O(N log N) debido al ORDER BY y GROUP BY.
   - Comportamiento: El motor de SQLite carga toda la tabla en una fracción 
     mínima de tu RAM (apenas unos KB). La eficiencia es máxima porque los 
     datos caben en la caché de la CPU.

2. ESCENARIO REAL  (Millones de filas):
   - Si la tabla 'Invoice' tuviera 50 millones de filas, un GROUP BY simple 
     provocaría un "Full Table Scan" (lectura completa de disco), lo cual es 
     inaceptable en ingeniería.
   
   - ESTRATEGIA DE OPTIMIZACIÓN (Índices):
     Para que este reporte sea instantáneo en mi laptop con 32GB de RAM, 
     deberíamos crear un índice B-Tree en la columna de agrupación:
     
     CREATE INDEX idx_billing_country ON Invoice(BillingCountry);
     
     

   - ¿POR QUÉ FUNCIONA?: 
     El índice pre-ordena los países. En lugar de buscar en 50 millones de 
     filas desordenadas, el motor "salta" directamente a los grupos de cada 
     país. La complejidad pasaría de ser lineal a logarítmica O(log N).

=============================================================================
*/

-- Verificación de la Vista
SELECT * FROM View_Global_Sales_Report;