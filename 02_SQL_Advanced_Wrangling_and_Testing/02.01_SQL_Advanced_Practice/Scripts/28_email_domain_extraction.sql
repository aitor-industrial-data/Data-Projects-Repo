--------------------------------------------------------------------------------
-- 28_email_domain_extraction.sql
-- AUTOR: Aitor | Ingeniero Técnico Industrial | Data Engineer
-- PROYECTO: Chinook Database (Singular Schema)
--------------------------------------------------------------------------------

/* ENUNCIADO:
   Crear un informe detallado de clientes extranjeros que incluya:
   1. Nombre completo, País y Email original.
   2. Extracción del dominio del email. [String Parsing]
   3. Clasificación del dominio (Public vs Corporate).
   4. Total de clientes que comparten ese mismo dominio.
   5. Diferencia (DIFF) entre los clientes de ese dominio y la media global.
   
   Condiciones:
   - Mantener el detalle de cada cliente (no agrupar filas).
   - Excluir mercado USA.
   - Ordenar por dominio y luego por nombre.
*/

WITH CustomerData AS (
    -- 1 y 2. Extraemos el detalle básico y el dominio aislando la lógica
    SELECT 
        TRIM(FirstName) || ' ' || TRIM(LastName) AS FullName,
        Country,
        Email,
        LOWER(SUBSTR(Email, INSTR(Email, '@') + 1)) AS DomainName,
        -- 3. Clasificación del dominio
        CASE 
            WHEN Email LIKE '%@gmail.%' OR Email LIKE '%@yahoo.%' 
                 OR Email LIKE '%@hotmail.%' OR Email LIKE '%@outlook.%' THEN 'Public'
            ELSE 'Corporate'
        END AS DomainType
    FROM Customer
    WHERE Country != 'USA' -- Condición: Excluir USA
),

DomainCounts AS (
    -- 4. Calculamos el total exacto por dominio
    SELECT 
        DomainName, 
        COUNT(*) AS Total_Customers
    FROM CustomerData
    GROUP BY DomainName
),

GlobalAvg AS (
    -- 5. Calculamos la media global (de los totales por dominio)
    SELECT AVG(Total_Customers) AS Avg_Global
    FROM DomainCounts
)

-- SELECT Final manteniendo el detalle fila a fila
SELECT 
    c.FullName,
    c.Country,
    c.Email,
    c.DomainName,
    c.DomainType,
    d.Total_Customers,
    ROUND(d.Total_Customers - g.Avg_Global, 2) AS DIFF
FROM CustomerData c
JOIN DomainCounts d ON c.DomainName = d.DomainName
CROSS JOIN GlobalAvg g
-- Condición: Ordenar por dominio y luego por nombre
ORDER BY c.DomainName ASC, c.FullName ASC;

--------------------------------------------------------------------------------
-- ANOTACIONES TÉCNICAS:
-- 1. Cumplimiento estricto de requisitos: Se muestran las 7 columnas pedidas.
-- 2. Integridad de los datos: El CROSS JOIN con la media global (1 sola fila) 
--    y el JOIN con los conteos aseguran que el cálculo matemático es exacto 
--    y no altera el número de clientes ni su detalle individual.
--------------------------------------------------------------------------------