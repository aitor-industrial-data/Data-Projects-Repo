--------------------------------------------------------------------------------
-- 17_market_segmentation.sql
-- AUTOR: Aitor | Ingeniero Técnico Industrial | Data Engineer
-- PROYECTO: Chinook Database (Singular Schema)
--------------------------------------------------------------------------------

/* ENUNCIADO:
   Analizar la penetración de mercado comparando clientes locales (USA) frente a 
   internacionales, evaluando su nivel de actividad y volumen de gasto.
   
   Consideraciones de ingeniería:
   1. Segmentación Geográfica: Clasificar como 'Domestic' (USA) o 'Foreign'.
   2. Categorización de Actividad: Clasificar por volumen de pedidos (High/Moderate/Low).
   3. Métricas Financieras: Calcular el Valor Total (SUM) y el Ticket Medio (AVG).
   4. Calidad de Datos: Filtrar registros sin email para asegurar contactabilidad.
   5. Robustez: Usar LEFT JOIN para incluir clientes incluso si no tienen ventas.
*/

SELECT 
    UPPER(c.LastName || ', ' || c.FirstName) AS Client_Profile,
    CASE 
        WHEN c.Country = 'USA' THEN 'Domestic'
        ELSE 'Foreign'
    END AS Market_Type,
    CASE 
        WHEN COUNT(i.InvoiceId) > 10 THEN 'High Activity'
        WHEN COUNT(i.InvoiceId) BETWEEN 5 AND 10 THEN 'Moderate Activity'
        WHEN COUNT(i.InvoiceId) BETWEEN 1 AND 4 THEN 'Low Activity'
        ELSE 'No Activity'
    END AS Activity_Level,
    COALESCE(SUM(i.Total), 0) AS Total_Sales,
    COALESCE(ROUND(AVG(i.Total), 2), 0) AS AVG_Sales
FROM Customer c
LEFT JOIN Invoice i ON c.CustomerId = i.CustomerId
WHERE c.Email IS NOT NULL
GROUP BY c.CustomerId
ORDER BY Market_Type ASC, Total_Sales DESC;

--------------------------------------------------------------------------------
-- ANOTACIONES TÉCNICAS Y FUNDAMENTOS:
-- 1. CASE Logic Multi-nivel: Permite crear taxonomías de negocio complejas en 
--    una sola pasada de datos, optimizando el procesamiento.
-- 2. LEFT JOIN vs INNER JOIN: En ingeniería de datos, el LEFT JOIN es preferible 
--    cuando auditamos actividad, ya que permite identificar clientes inactivos (Churn).
-- 3. COALESCE en Métricas: Evita que los clientes sin ventas muestren NULL en 
--    campos financieros, normalizando el output para herramientas de BI.
-- 4. ROUND para Presentación: Limitar a 2 decimales es una práctica estándar 
--    de Data Wrangling para facilitar la lectura de reportes financieros.
-- 5. Escalabilidad: Este patrón de segmentación es el que se utiliza para crear 
--    tablas de dimensiones en modelos de datos en estrella (Kimball).
--------------------------------------------------------------------------------