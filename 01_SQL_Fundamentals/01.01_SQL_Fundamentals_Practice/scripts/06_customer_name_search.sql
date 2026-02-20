--------------------------------------------------------------------------------
-- 06_customer_name_search.sql
-- AUTOR: Aitor | Ingeniero Técnico Industrial | Data Engineer
-- PROYECTO: Chinook Database (Singular Schema)
--------------------------------------------------------------------------------

/* ENUNCIADO:
   Buscar los clientes cuyo nombre comience por "J" y contenga 
   la letra "n", que tengan un correo electrónico registrado y hayan sido 
   creados en el sistema antes de 2025. 
   
   Ordenar los resultados por país de forma ascendente y por apellido.
*/

SELECT
    FirstName,
    LastName,
    Email,
    Country
FROM Customer
WHERE FirstName LIKE 'J%n%'
  AND Email IS NOT NULL
  AND Company IS NOT NULL -- Suponiendo que buscamos clientes de empresa
ORDER BY Country ASC, LastName ASC;

--------------------------------------------------------------------------------
-- ANOTACIONES TÉCNICAS Y FUNDAMENTOS:
-- 1. Uso de Comodines (Wildcards):
--    - 'J%': Garantiza que el primer carácter sea la J.
--    - '%n%': Busca la letra 'n' en cualquier posición restante.
-- 2. Lógica Combinada: Se integra LIKE con IS NOT NULL para asegurar que 
--    la segmentación por nombre no devuelva registros incompletos.
-- 3. Ordenación Multinivel: El ORDER BY gestiona dos columnas. Primero 
--    agrupa por país y, dentro de cada país, alfabetiza por apellido.
-- 4. Eficiencia de Búsqueda: Como ingeniero, debes saber que LIKE con un 
--    comodín al inicio (%J) es lento, pero empezar con el carácter (J%) 
--    permite al motor usar índices, siendo mucho más eficiente.
--------------------------------------------------------------------------------