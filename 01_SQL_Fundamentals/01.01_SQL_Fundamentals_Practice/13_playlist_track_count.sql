--------------------------------------------------------------------------------
-- 13_playlist_track_count.sql
-- AUTOR: Aitor | Ingeniero Técnico Industrial | Data Engineer
-- PROYECTO: Chinook Database (Singular Schema)
--------------------------------------------------------------------------------

/* ENUNCIADO:
   Realizar un inventario de las listas de reproducción (Playlists) que 
   contenga el nombre de la lista y el número total de canciones en cada una.
   
   Requerimientos técnicos:
   1. Unir las tablas Playlist, PlaylistTrack y Track.
   2. Solo incluir listas que tengan al menos una canción (COUNT > 0).
   3. Asegurarse de que el nombre de la Playlist no sea nulo.
   4. Ordenar los resultados de mayor a menor cantidad de canciones.
*/

SELECT 
    p.Name AS Playlist_Name,
    COUNT(pt.TrackId) AS Total_Tracks
FROM Playlist p
INNER JOIN PlaylistTrack pt ON p.PlaylistId = pt.PlaylistId
WHERE p.Name IS NOT NULL
GROUP BY p.Name
ORDER BY Total_Tracks DESC;

--------------------------------------------------------------------------------
-- ANOTACIONES TÉCNICAS Y FUNDAMENTOS:
-- 1. Función de Conteo (COUNT): Contabiliza las ocurrencias de IDs de canciones 
--    asociadas a cada grupo. Es la base de las métricas de volumen.
-- 2. Unión de Tabla Intermedia: Se conecta 'Playlist' con 'PlaylistTrack'. En 
--    ingeniería, estas tablas "puente" gestionan relaciones complejas N:M.
-- 3. Agrupación por Texto (GROUP BY): Se segmentan los totales por el nombre 
--    de la lista, permitiendo una visión clara del inventario.
-- 4. Ordenación por Agregado: Se usa el alias o la función en el 'ORDER BY' 
--    para priorizar las listas con mayor densidad de datos.
-- 5. Este patrón de 'JOIN' + 'GROUP BY' + 'COUNT' es el 
--    cimiento sobre el que construirán los Pipelines de datos.
--------------------------------------------------------------------------------