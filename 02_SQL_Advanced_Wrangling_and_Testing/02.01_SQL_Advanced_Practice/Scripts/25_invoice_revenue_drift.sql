--------------------------------------------------------------------------------
-- 25_invoice_revenue_drift.sql
-- AUTOR: Aitor | Ingeniero Técnico Industrial | Data Engineer
-- PROYECTO: Chinook Database (Singular Schema)
--------------------------------------------------------------------------------

/* ENUNCIADO:
   Calcular la diferencia de ingresos (Drift) entre la factura más reciente 
   y la factura anterior para cada cliente, mostrando:
   1. El nombre completo del cliente en mayúsculas (FullName).
   2. El total de la última factura (Last_Invoice_Total).
   3. El total de la factura inmediatamente anterior (Previous_Invoice_Total).
   4. La diferencia neta entre ambas (Revenue_Difference).
   
   Condiciones del reporte:
   - Utilizar funciones de ventana para evitar auto-uniones (Self-Joins).
   - Solo mostrar el registro más reciente de cada cliente.
   - Ordenar los resultados por la mayor diferencia positiva de ingresos.
*/

WITH InvoiceHistory AS (
    SELECT 
        c.CustomerId,
        UPPER(c.FirstName || ' ' || c.LastName) AS FullName,
        i.Total AS Current_Total,
        -- Obtenemos el total anterior mediante LAG
        LAG(i.Total, 1, 0) OVER(PARTITION BY c.CustomerId ORDER BY i.InvoiceDate ASC) AS Prev_Total,
        -- Identificamos la última factura con un ranking inverso
        ROW_NUMBER() OVER(PARTITION BY c.CustomerId ORDER BY i.InvoiceDate DESC) AS Latest_Record_Flag
    FROM Customer c
    JOIN Invoice i ON c.CustomerId = i.CustomerId
)
SELECT 
    CustomerId,
    FullName,
    Current_Total AS Last_Invoice_Total,
    Prev_Total AS Previous_Invoice_Total,
    (Current_Total - Prev_Total) AS Revenue_Difference
FROM InvoiceHistory
WHERE Latest_Record_Flag = 1
ORDER BY Revenue_Difference DESC;

--------------------------------------------------------------------------------
-- ANOTACIONES TÉCNICAS Y FUNDAMENTOS:
-- 1. Funciones de Ventana (LAG): Se utiliza para acceder a datos de filas 
--    anteriores sin necesidad de JOINs complejos, optimizando el rendimiento.
-- 2. Análisis de Tendencias (Drift): Técnica esencial en Data Engineering para 
--    detectar cambios en el comportamiento de los datos a lo largo del tiempo.
-- 3. CTE (Common Table Expression): Mejora la legibilidad del código al separar 
--    la lógica de preparación de la lógica de filtrado final.
-- 4. Deduplicación con ROW_NUMBER: Método estándar para extraer únicamente el 
--    estado más reciente de una entidad (Latest-state-only).
-- 5. Preparación para ETL: Este tipo de transformaciones son la base para 
--    alimentar tablas de "Hechos" (Fact Tables) en un Data Warehouse.
--------------------------------------------------------------------------------