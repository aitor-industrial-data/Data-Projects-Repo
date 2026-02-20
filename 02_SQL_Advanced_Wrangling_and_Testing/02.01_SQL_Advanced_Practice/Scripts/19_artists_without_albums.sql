--------------------------------------------------------------------------------
-- 19_artists_without_albums.sql
-- AUTOR: Aitor | Ingeniero Técnico Industrial | Data Engineer
-- PROYECTO: Chinook Database (Singular Schema)
--------------------------------------------------------------------------------

/* ENUNCIADO:
   Identificar artistas registrados en la base de datos que no cuentan con ningún 
   álbum asociado, facilitando la limpieza de registros huérfanos.
   
   Consideraciones de ingeniería:
   1. Integridad: Uso de NOT EXISTS para verificar la ausencia de relaciones.
   2. Eficiencia: Evitar JOINs innecesarios que filtren los datos antes de tiempo.
   3. Robustez: Uso de COALESCE para asegurar que el nombre del artista sea legible.
*/

SELECT
    a.ArtistId AS Artist_Id,
    COALESCE(a.Name, 'Unknown Artist') AS Artist_Name	
FROM Artist a
WHERE NOT EXISTS (
    SELECT 1
    FROM Album al
    WHERE al.ArtistId = a.ArtistId
)
ORDER BY Artist_Name ASC;

--------------------------------------------------------------------------------
-- ANOTACIONES TÉCNICAS Y FUNDAMENTOS:
-- 1. Subconsulta Correlacionada: Se ejecuta "fila por fila", comparando el 
--    ArtistId de la tabla externa con la tabla interna Album.
-- 2. Operador NOT EXISTS: Es altamente eficiente. El motor SQL se detiene en 
--    cuanto encuentra la primera coincidencia (o falta de ella), sin necesidad 
--    de cargar todos los datos de la tabla relacionada en memoria.
-- 3. SELECT 1: En un EXISTS/NOT EXISTS, el contenido del SELECT interno es 
--    irrelevante; solo importa si la subquery devuelve "algo" o "nada". Usar '1' 
--    es un estándar de legibilidad y rendimiento.
-- 4. Diferencia con LEFT JOIN: Un LEFT JOIN traería columnas de la tabla Album 
--    (aunque fueran NULL). NOT EXISTS es más limpio cuando solo necesitamos 
--    validar la existencia lógica.
-- 5. Casos de Uso en Data Engineering: Esencial para procesos de borrado en 
--    cascada o para generar reportes de "Missing Data" en auditorías de calidad.
--------------------------------------------------------------------------------