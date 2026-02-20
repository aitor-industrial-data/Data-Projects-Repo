--------------------------------------------------------------------------------
-- 20_top_5_spending_clients.sql
-- AUTOR: Aitor | Ingeniero Técnico Industrial | Data Engineer
-- PROYECTO: Chinook Database (Singular Schema)
--------------------------------------------------------------------------------

/* ENUNCIADO:
   Identificar a los 5 clientes con mayor gasto histórico (Lifetime Value) y 
   calcular su peso porcentual respecto a la facturación total de la compañía.
   
   Consideraciones de ingeniería:
   1. Consolidación: Agregación de ventas totales por cliente.
   2. Subquery Escalar: Cálculo dinámico del total global de ventas para el 
      denominador del porcentaje.
   3. Aritmética de Datos: Cálculo de cuota de mercado (Share) con redondeo a 
      2 decimales para facilitar la interpretación de negocio.
   4. Filtrado de Calidad: Exclusión de facturas con valor cero.
*/

SELECT
    UPPER(c.FirstName || ' ' || c.LastName) AS Full_Name,
    c.Country,
    SUM(i.Total) AS Total_Spent,
    ROUND(
        (SUM(i.Total) / (SELECT SUM(Total) FROM Invoice)) * 100.0, 
        2
    ) AS Percentage_Total_Sales 
FROM Customer c 
JOIN Invoice i ON c.CustomerId = i.CustomerId
WHERE i.Total > 0
GROUP BY c.CustomerId
ORDER BY Total_Spent DESC
LIMIT 5;

--------------------------------------------------------------------------------
-- ANOTACIONES TÉCNICAS Y FUNDAMENTOS:
-- 1. Subquery en SELECT: Muy útil para comparar una métrica individual contra 
--    un agregado global en la misma fila de salida.
-- 2. Análisis de Pareto: Este reporte permite visualizar rápidamente si el 
--    ingreso está concentrado en pocos clientes (riesgo de concentración).
-- 3. Optimización: Aunque la subquery escalar es cómoda, en tablas con miles 
--    de millones de filas se preferiría una Window Function (OVER) para evitar 
--    re-escanear la tabla Invoice.
-- 4. Escalabilidad: Este es el último paso antes de Spark, donde aprenderás a 
--    realizar estos cálculos de forma distribuida.
--------------------------------------------------------------------------------