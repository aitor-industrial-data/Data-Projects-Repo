--------------------------------------------------------------------------------
-- 04_sales_q1_2024.sql
-- AUTOR: Aitor | Ingeniero Técnico Industrial | Data Engineer
-- PROYECTO: Chinook Database (Singular Schema)
--------------------------------------------------------------------------------

/* ENUNCIADO:
   Identificar las facturas emitidas en el primer trimestre de 2024.
   Mostrar el ID, la fecha y el total, ordenando los resultados 
   desde la factura más reciente a la más antigua.
*/

SELECT DISTINCT
    InvoiceId,
    InvoiceDate,
    Total
FROM Invoice
WHERE InvoiceDate >= '2024-01-01' 
  AND InvoiceDate <= '2024-03-31'
ORDER BY InvoiceDate DESC;

--------------------------------------------------------------------------------
-- ANOTACIONES TÉCNICAS Y FUNDAMENTOS:
-- 1. Filtrado de Fechas: Uso de operadores de comparación (>=, <=). Este es 
--    el fundamento previo al uso de BETWEEN, permitiendo un control total.
-- 2. Formato de Tiempo: Las fechas se tratan como cadenas bajo el estándar 
--    ISO (Año-Mes-Día), lo que garantiza compatibilidad en SQLite y DBeaver.
-- 3. Unicidad de Datos: Aplicación de 'DISTINCT' para asegurar que cada 
--    registro de factura sea tratado como una entidad única en el reporte.
-- 4. Ordenación Cronológica: El uso de 'DESC' en fechas es una técnica de 
--    Ingeniería de Datos para priorizar la ingesta de los datos más recientes.
--------------------------------------------------------------------------------