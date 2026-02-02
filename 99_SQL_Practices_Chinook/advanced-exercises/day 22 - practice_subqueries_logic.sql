/*
  PROYECTO: Chinook Data Analysis
  SESIÓN: Día 22 - Laboratorio de Rapidez Mental
  OBJETIVO: Dominar Subconsultas, Lógica Condicional (CASE) y Agregaciones Dinámicas.
  INGENIERO: Aitor
*/

-- =================================================================================
-- EJERCICIO 1: El Filtro Inteligente (Subquery Simple)
-- Enunciado: Encontrar todas las pistas (Track) que pertenecen al género 'Rock' 
-- sin usar un JOIN directo en el filtrado principal.
-- =================================================================================

SELECT 
    t.Name AS Track_Name,
    t.GenreId
FROM Track t 
WHERE t.GenreId IN (
    -- Esta subconsulta busca el ID dinámicamente, evitando "hardcoding"
    SELECT g.GenreId 
    FROM Genre g 
    WHERE g.Name = 'Rock'
)
LIMIT 10;


-- =================================================================================
-- EJERCICIO 2: Categorización de Mercados (CASE Statement)
-- Enunciado: Clasificar a los clientes en tres mercados geográficos (North America, 
-- South America, Rest of the World) basándose en su país.
-- =================================================================================

SELECT 
    c.FirstName, 
    c.LastName,
    c.Country,
    CASE 
        WHEN c.Country IN ('USA', 'Canada') THEN 'North_America'
        WHEN c.Country IN ('Brazil', 'Argentina', 'Chile') THEN 'South_America'
        ELSE 'Rest of the World'
    END AS Market_Type
FROM Customer c;


-- =================================================================================
-- EJERCICIO 3: Ventas Premium (Subquery + Agregación Escalar)
-- Enunciado: Listar todas las facturas cuyo importe total sea superior a la 
-- media global de todas las ventas de la empresa.
-- =================================================================================

SELECT 
    i.InvoiceId,
    i.CustomerId,
    i.InvoiceDate,
    i.Total
FROM Invoice i 
WHERE i.Total > (
    -- Subconsulta escalar: devuelve un único valor (el promedio)
    SELECT AVG(i1.Total) 
    FROM Invoice i1
)
ORDER BY i.Total DESC;