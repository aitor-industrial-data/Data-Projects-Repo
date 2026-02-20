--------------------------------------------------------------------------------
-- 16_invoice_tier_classification.sql
-- AUTOR: Aitor | Ingeniero Técnico Industrial | Data Engineer
-- PROYECTO: Chinook Database (Singular Schema)
--------------------------------------------------------------------------------

/* ENUNCIADO:
   Clasificar el rendimiento de ventas por cliente basándose en su gasto total 
   acumulado, categorizándolos en niveles (Tiers) para el equipo de Marketing.
   
   Consideraciones de ingeniería:
   1. Consolidación: Sumar el total de todas las facturas por cada cliente.
   2. Lógica de Negocio (CASE):
      - Gasto > 45$ -> 'Tier 1: VIP'
      - Gasto entre 30$ y 45$ -> 'Tier 2: Regular'
      - Gasto < 30$ -> 'Tier 3: Occasional'
   3. Enriquecimiento: Incluir el país del cliente y gestionar nulos en el 
      Estado (State) usando COALESCE.
   4. Filtrado: Mostrar solo clientes que han realizado más de 5 pedidos.
*/

SELECT 
    UPPER(c.FirstName || ' ' || c.LastName) AS Customer_Name,
    c.Country,
    COALESCE(c.State, 'N/A') AS State_Province,
    SUM(i.Total) AS Lifetime_Value,
    COUNT(i.InvoiceId) AS Order_Count,
    CASE 
        WHEN SUM(i.Total) > 45 THEN 'Tier 1: VIP'
        WHEN SUM(i.Total) BETWEEN 30 AND 45 THEN 'Tier 2: Regular'
        ELSE 'Tier 3: Occasional'
    END AS Customer_Segment
FROM Customer c
JOIN Invoice i ON c.CustomerId = i.CustomerId
GROUP BY c.CustomerId
HAVING COUNT(i.InvoiceId) > 5
ORDER BY Lifetime_Value DESC;

--------------------------------------------------------------------------------
-- ANOTACIONES TÉCNICAS Y FUNDAMENTOS:
-- 1. Lógica Condicional (CASE WHEN): Permite transformar datos numéricos en 
--    categorías cualitativas. Es la base de la segmentación en ingeniería de datos.
-- 2. Evaluación de Agregados en CASE: Se pueden evaluar funciones como SUM() 
--    dentro del CASE para categorizar el resultado final del grupo.
-- 3. Métricas de Negocio (Lifetime Value): El cálculo del valor total por cliente 
--    es un KPI real que los Data Engineers preparan para los analistas de BI.
-- 4. Eficiencia de Agrupación: Al agrupar por CustomerId, aseguramos que la 
--    segmentación es única por individuo, evitando duplicidades.
-- 5. Orden de Ejecución: El CASE se ejecuta después del GROUP BY cuando se usan 
--    agregaciones, permitiendo una clasificación precisa del volumen de ventas.
--------------------------------------------------------------------------------