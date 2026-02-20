--------------------------------------------------------------------------------
-- 09_track_media_inventory.sql
-- AUTOR: Aitor | Ingeniero Técnico Industrial | Data Engineer
-- PROYECTO: Chinook Database (Singular Schema)
--------------------------------------------------------------------------------

/* ENUNCIADO:
   Crear un inventario completo de canciones que muestre:
   1. El nombre de la canción.
   2. El nombre del género (Genre).
   3. El nombre del tipo de formato (MediaType).
   
   Condiciones del reporte:
   - Solo incluir canciones cuyos géneros NO sean 'MPEG audio file' (filtrado de tipo).
   - Asegurarse de que el nombre de la canción contenga al menos una letra 'a'.
   - El género y el tipo de medio deben estar informados (IS NOT NULL).
   - Ordenar por Género (Ascendente) y luego por nombre de canción.
*/

SELECT 
    t.Name AS Track_Name,
    g.Name AS Genre_Name,
    m.Name AS Format_Type
FROM Track t
INNER JOIN Genre g ON t.GenreId = g.GenreId
INNER JOIN MediaType m ON t.MediaTypeId = m.MediaTypeId
WHERE m.Name != 'MPEG audio file'
  AND t.Name LIKE '%a%'
  AND g.Name IS NOT NULL
  AND m.Name IS NOT NULL
ORDER BY g.Name ASC, t.Name ASC;

--------------------------------------------------------------------------------
-- ANOTACIONES TÉCNICAS Y FUNDAMENTOS:
-- 1. Unión Múltiple (Multiple JOINs): Se conectan tres entidades (Track, Genre, 
--    MediaType). Este es el fundamento de la normalización de bases de datos.
-- 2. Filtrado de Exclusión (!=): Se utiliza para limpiar el inventario de 
--    formatos no deseados, un paso crítico en el Data Wrangling.
-- 3. Búsqueda de Patrones (LIKE): Se asegura que el nombre cumpla con un 
--    criterio de texto específico (contener 'a').
-- 4. Gestión de Alias: Se usan 't', 'g' y 'm' para mantener la consulta 
--    compacta y profesional, facilitando el mantenimiento del código.
-- 5. Preparación para Ingeniería de Datos: En Spark, estas uniones 
--    múltiples requieren entender bien las claves primarias y foráneas para 
--    evitar cuellos de botella en el procesamiento.
--------------------------------------------------------------------------------