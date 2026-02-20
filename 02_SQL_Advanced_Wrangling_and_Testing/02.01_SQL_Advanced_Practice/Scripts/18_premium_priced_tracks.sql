--------------------------------------------------------------------------------
-- 18_premium_priced_tracks.sql
-- AUTOR: Aitor | Ingeniero Técnico Industrial | Data Engineer
-- PROYECTO: Chinook Database (Singular Schema)
--------------------------------------------------------------------------------

/* ENUNCIADO:
   Identificar activos "Premium" cuyo precio unitario supera la media global de 
   la tienda, excluyendo formatos de archivo específicos (MPEG).
   
   Consideraciones de ingeniería:
   1. Dinamismo: Uso de Subquery para calcular la media en tiempo real.
   2. Integración: Unir tablas de Track, Album y MediaType para un reporte completo.
   3. Filtrado de Calidad: Excluir formatos 'MPEG audio file' por requisitos de negocio.
   4. Precisión: El cálculo de la media debe considerar el universo total de canciones.
*/

SELECT 
    t.Name AS Track_Name,
    al.Title AS Album_Name,
    t.UnitPrice AS Pricing_Audit,
    m.Name AS MediaType
FROM Track t
JOIN Album al ON t.AlbumId = al.AlbumId 
JOIN MediaType m ON t.MediaTypeId = m.MediaTypeId 
WHERE t.UnitPrice > (
    SELECT AVG(t2.UnitPrice) 
    FROM Track t2
)
    AND m.Name != 'MPEG audio file'
ORDER BY Pricing_Audit DESC, Track_Name ASC;

--------------------------------------------------------------------------------
-- ANOTACIONES TÉCNICAS Y FUNDAMENTOS:
-- 1. Subquery Escalar: La consulta interna devuelve un único valor (la media), 
--    que actúa como una constante dinámica para el filtro WHERE de la externa.
-- 2. Desacoplamiento: Esta técnica evita "hardcodear" valores (como 0.99). Si 
--    los precios suben, el reporte se ajusta automáticamente sin cambiar el código.
-- 3. Optimización de Joins: Se utiliza INNER JOIN ya que solo nos interesan 
--    canciones que tengan un álbum y un formato de medio asignado.
-- 4. Relevancia en Big Data: En entornos distribuidos (Spark), las subqueries 
--    pueden ser costosas. Se suelen optimizar mediante "Broadcast Joins" o 
--    reemplazándolas por Window Functions si es posible.
-- 5. Perfil DE: Este tipo de lógica se usa para detectar anomalías o realizar 
--    análisis de outliers (valores fuera de la norma) en pipelines de datos.
--------------------------------------------------------------------------------