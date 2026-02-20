--------------------------------------------------------------------------------
-- 10_total_historical_revenue.sql
-- AUTOR: Aitor | Ingeniero Técnico Industrial | Data Engineer
-- PROYECTO: Chinook Database (Singular Schema)
--------------------------------------------------------------------------------

/* ENUNCIADO:
   Calcular el ingreso total histórico de la tienda (suma de la columna Total).
   Consideraciones de integridad:
   1. Solo sumar facturas que tengan una fecha válida (IS NOT NULL).
   2. Excluir facturas de prueba o erróneas (por ejemplo, Total = 0).
   3. Mostrar el resultado con un alias descriptivo 'Total_Historical_Revenue'.
*/

SELECT 
    SUM(i.Total) AS Total_Historical_Revenue
FROM Invoice i
WHERE i.Total > 0
  AND i.InvoiceDate IS NOT NULL;

--------------------------------------------------------------------------------
-- ANOTACIONES TÉCNICAS Y FUNDAMENTOS:
-- 1. Función de Agregación (SUM): Colapsa todos los registros del conjunto 
--    en un único valor numérico. Es el pilar de los reportes de BI.
-- 2. Limpieza de Datos (Data Cleansing): Se filtran valores cero o negativos 
--    que podrían sesgar el cálculo real de ingresos.
-- 3. Alias de Agregación: Es obligatorio usar 'AS' para nombrar la columna 
--    resultante, ya que las funciones de agregación no heredan el nombre original.
-- 4. Fundamento Acumulado: Se integra 'IS NOT NULL' para asegurar que solo 
--    se sumen registros con trazabilidad temporal.
-- 5. Visión de Data Engineer: Este dato es un "KPI" (Key Performance Indicator). 
--    En el modulo de Spark, se calculan estos totales sobre 
--    volúmenes de datos que no caben en una base de datos tradicional.
--------------------------------------------------------------------------------