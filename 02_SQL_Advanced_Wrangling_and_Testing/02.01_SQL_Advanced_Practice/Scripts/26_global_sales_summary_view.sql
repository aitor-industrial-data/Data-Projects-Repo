--------------------------------------------------------------------------------
-- 26_global_sales_summary_view.sql
-- AUTOR: Aitor | Ingeniero Técnico Industrial | Data Engineer
-- PROYECTO: Chinook Database (Singular Schema)
--------------------------------------------------------------------------------

/* ENUNCIADO:
   Crear una vista persistente llamada 'v_global_sales_summary' que resuma 
   el rendimiento comercial de la empresa. La vista debe mostrar:
   1. El país de facturación (BillingCountry).
   2. El año de la factura (extraído de InvoiceDate).
   3. El ingreso total generado (Total_Revenue).
   4. El número total de pedidos realizados.
   5. El ticket promedio por país y año (Avg_Ticket).
   
   Condiciones de la vista:
   - Los países deben clasificarse en 'Domestic' (USA) o 'Foreign'.
   - Solo incluir años donde el ingreso total sea superior a 100.
   - Si el país es NULL (limpieza de datos), mostrar 'Unknown'.
   - Ordenar el resultado final por año descendente y ventas de mayor a menor.
*/

-- Eliminamos la vista si ya existe para permitir re-ejecución (Idempotencia)
DROP VIEW IF EXISTS v_global_sales_summary;

CREATE VIEW v_global_sales_summary AS
SELECT 
    COALESCE(BillingCountry, 'Unknown') AS Country,
    -- STRFTIME se usa en SQLite para extraer el año. En otros SQL sería YEAR()
    STRFTIME('%Y', InvoiceDate) AS Sales_Year,
    CASE 
        WHEN BillingCountry = 'USA' THEN 'Domestic'
        ELSE 'Foreign'
    END AS Market_Type,
    SUM(Total) AS Total_Revenue,
    COUNT(InvoiceId) AS Order_Count,
    ROUND(AVG(Total), 2) AS Avg_Ticket
FROM Invoice
GROUP BY Country, Sales_Year
HAVING Total_Revenue > 100
ORDER BY Sales_Year DESC, Total_Revenue DESC;

-- EJECUCIÓN DE PRUEBA:
-- SELECT * FROM v_global_sales_summary WHERE Market_Type = 'Foreign';

--------------------------------------------------------------------------------
-- ANOTACIONES TÉCNICAS Y FUNDAMENTOS:
-- 1. Abstracción de Datos: Las vistas permiten ocultar la complejidad de los 
--    JOINs y cálculos a los analistas de BI, entregando datos ya procesados.
-- 2. Manipulación de Fechas (STRFTIME): Extraer componentes de tiempo es vital 
--    para el análisis de series temporales en ingeniería de datos.
-- 3. Agregación Multidimensional: El uso de GROUP BY con múltiples columnas 
--    prepara el terreno para la creación de "Cubos de Datos" o Data Marts.
-- 4. Lógica de Negocio Embebida: El uso de CASE y COALESCE dentro de la vista 
--    asegura que las reglas de negocio sean consistentes para todos.
-- 5. Data Quality: Al filtrar mediante HAVING, estamos garantizando que la 
--    capa de reporte solo contenga datos significativos (limpieza de ruido).
--------------------------------------------------------------------------------