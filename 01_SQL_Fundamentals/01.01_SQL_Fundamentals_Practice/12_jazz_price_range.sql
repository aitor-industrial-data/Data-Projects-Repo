--------------------------------------------------------------------------------
-- 12_jazz_price_range.sql
-- AUTOR: Aitor | Ingeniero Técnico Industrial | Data Engineer
-- PROYECTO: Chinook Database (Singular Schema)
--------------------------------------------------------------------------------

/* ENUNCIADO:
   Determinar el rango de precios de las canciones de Jazz.
   Se requiere:
   1. El precio más bajo (Min_Price).
   2. El precio más alto (Max_Price).
   3. Solo considerar canciones del género 'Jazz'.
   4. Asegurar que los precios sean superiores a 0 para evitar errores de catálogo.
*/

SELECT 
    MIN(t.UnitPrice) AS Min_Price,
    MAX(t.UnitPrice) AS Max_Price
FROM Track t
INNER JOIN Genre g ON t.GenreId = g.GenreId
WHERE g.Name = 'Jazz'
  AND t.UnitPrice > 0;

--------------------------------------------------------------------------------
-- ANOTACIONES TÉCNICAS Y FUNDAMENTOS:
-- 1. Funciones de Extremos (MIN/MAX): Identifican los valores límites dentro 
--    de un conjunto de datos. Útiles para detectar valores atípicos (outliers).
-- 2. Filtrado Relacional: Se usa 'INNER JOIN' para filtrar por el nombre del 
--    género ('Jazz') en lugar de usar un ID a ciegas.
-- 3. Integridad Numérica: El filtro 'UnitPrice > 0' es una regla de validación 
--    de datos (Data Validation) para asegurar que el MIN sea un valor comercial.
-- 4. Escalabilidad: Aunque aquí el resultado es una sola fila, este patrón 
--    se usa con 'GROUP BY' para comparar rangos de precios entre géneros.
--------------------------------------------------------------------------------