/*******************************************************************************
  DATA ENGINEER TECHNICAL INTERVIEW - DÍA 25: SIMULACRO Y OPTIMIZACIÓN
  Candidato: Aitor (Ingeniero Técnico Industrial)
  Objetivo: Filtrado avanzado, Agregación y Rendimiento (SARGability).
*******************************************************************************/

-- =============================================================================
-- RETO: Análisis de fidelidad de clientes (Ventas > 10$ en el año 2022)
-- =============================================================================

/* LOGICA DE INGENIERÍA:
   1. JOIN: Conectamos Clientes con Facturas (1:N).
   2. FILTRO (WHERE): Acotamos el año ANTES de agrupar para procesar menos datos.
   3. AGRUPACIÓN (GROUP BY): Colapsamos las facturas por cada cliente único.
   4. FILTRO DE GRUPO (HAVING): Aplicamos la regla de negocio (> 10$).
   5. ORDEN (ORDER BY): Presentamos los datos de mayor a menor importancia.
*/

-- VERSIÓN 1: Funcional (Uso de funciones en el filtro)
-- Nota: strftime es útil pero puede penalizar el rendimiento en tablas masivas.
SELECT 
    c.FirstName,
    c.LastName,
    SUM(i.Total) AS Total_Customer
FROM Customer c 
INNER JOIN Invoice i ON c.CustomerId = i.CustomerId 
WHERE strftime('%Y', i.InvoiceDate) = '2022'
GROUP BY c.CustomerId, c.FirstName, c.LastName
HAVING SUM(i.Total) > 10
ORDER BY Total_Customer DESC;


-- VERSIÓN 2: OPTIMIZADA (SARGable - Search Argumentable)
-- Nota: Usamos BETWEEN para que el motor SQL pueda usar los Índices de la columna InvoiceDate.
-- Esta es la respuesta que un Senior espera de un Ingeniero.



SELECT 
    c.FirstName,
    c.LastName,
    SUM(i.Total) AS Total_Customer
FROM Customer c 
INNER JOIN Invoice i ON c.CustomerId = i.CustomerId 
WHERE i.InvoiceDate BETWEEN '2022-01-01' AND '2022-12-31'
GROUP BY c.CustomerId, c.FirstName, c.LastName
HAVING SUM(i.Total) > 10
ORDER BY Total_Customer DESC;


-- =============================================================================
-- ANÁLISIS TÉCNICO DE ERRORES COMUNES (Self-Review)
-- =============================================================================

/*
   1. ¿POR QUÉ HAVING Y NO WHERE PARA EL TOTAL?
      - El WHERE actúa sobre filas individuales antes de agrupar.
      - El HAVING actúa sobre el resultado de la función SUM() después de agrupar.
      - Intentar poner 'WHERE SUM(i.Total) > 40' daría error de sintaxis.

   2. ¿POR QUÉ INCLUIR FIRSTNAME Y LASTNAME EN EL GROUP BY?
      - Estándar SQL: Todas las columnas del SELECT que no tengan una función 
        agregada (SUM, AVG, etc.) deben estar en el GROUP BY para evitar 
        resultados ambiguos o errores en motores como PostgreSQL/SQL Server.

   3. DIFERENCIA DE RENDIMIENTO:
      - strftime('%Y', fecha) -> Ejecuta la función en CADA fila (Full Table Scan).
      - BETWEEN 'fecha1' AND 'fecha2' -> Salta directamente al rango (Index Seek).
*/



-- =============================================================================
-- FIN DEL DÍA 25 - HITOS: 
-- 1. Código optimizado para producción.
-- 2. Comprensión de SARGability.
-- 3. Dominio de la lógica de filtrado por grupos.
-- =============================================================================