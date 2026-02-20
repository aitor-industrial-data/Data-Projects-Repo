--------------------------------------------------------------------------------
-- 21_mpeg_format_consumers.sql
-- AUTOR: Aitor | Ingeniero Técnico Industrial | Data Engineer
-- PROYECTO: Chinook Database (Singular Schema)
--------------------------------------------------------------------------------

/* ENUNCIADO:
   Identificar a los clientes que han consumido contenido en formato 'MPEG audio file', 
   navegando por la jerarquía de la base de datos mediante subconsultas anidadas.
   
   Consideraciones de ingeniería:
   1. Navegación Jerárquica: Customer > Invoice > InvoiceLine > Track > MediaType.
   2. Desacoplamiento: Uso de subconsultas para filtrar niveles de datos sin 
      necesidad de múltiples JOINs en la consulta principal.
   3. Calidad: Uso de COALESCE para normalizar el campo Country.
   4. Estilo: Formateo de nombres en mayúsculas para reportes estandarizados.
*/

SELECT
    c.CustomerId,
    UPPER(c.FirstName || ' ' || c.LastName) AS Full_Name,
    COALESCE(c.Country, 'Global') AS Country	
FROM Customer c 
WHERE c.CustomerId IN (
    SELECT i.CustomerId 
    FROM Invoice i 
    WHERE i.InvoiceId IN (
        SELECT il.InvoiceId
        FROM InvoiceLine il
        WHERE il.TrackId IN (
            SELECT t.TrackId
            FROM Track t
            WHERE t.MediaTypeId IN (
                SELECT m.MediaTypeId
                FROM MediaType m
                WHERE m.Name = 'MPEG audio file'
            )
        )
    )
)
ORDER BY c.CustomerId ASC;

--------------------------------------------------------------------------------
-- ANOTACIONES TÉCNICAS Y FUNDAMENTOS:
-- 1. Nested Subqueries (Inception): Esta estructura permite filtrar la tabla 
--    principal basándose en propiedades de tablas muy alejadas en el esquema.
-- 2. Operador IN: A diferencia del JOIN, el IN gestiona automáticamente los 
--    duplicados; si un cliente compró 10 canciones MPEG, solo aparecerá una vez.
-- 3. Rendimiento en SQL Tradicional: Las subconsultas anidadas son muy legibles 
--    pero pueden ser lentas en tablas masivas. Es el "Trade-off" entre 
--    mantenibilidad y performance.
--------------------------------------------------------------------------------