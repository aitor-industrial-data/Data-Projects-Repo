--------------------------------------------------------------------------------
-- 14_popular_genres_report.sql
-- AUTOR: Aitor | Ingeniero Técnico Industrial | Data Engineer
-- PROYECTO: Chinook Database (Singular Schema)
--------------------------------------------------------------------------------

/* ENUNCIADO:
   Generar un reporte de "Géneros Populares" que identifique aquellos 
   géneros musicales con un catálogo superior a 100 canciones.
   
   Requerimientos de ingeniería:
   1. Unir 'Track' con 'Genre' para obtener los nombres descriptivos.
   2. Contar el número de canciones por género.
   3. Filtrar el resultado post-agregación para mostrar solo géneros > 100.
   4. Ordenar de forma descendente por popularidad.
*/

SELECT 
    g.Name AS Genre_Name,
    COUNT(t.TrackId) AS Track_Count
FROM Track t
INNER JOIN Genre g ON t.GenreId = g.GenreId
GROUP BY g.Name
HAVING COUNT(t.TrackId) > 100
ORDER BY Track_Count DESC;

--------------------------------------------------------------------------------
-- ANOTACIONES TÉCNICAS Y FUNDAMENTOS:
-- 1. Filtrado de Agregados (HAVING): A diferencia del WHERE (que filtra filas 
--    individuales), HAVING filtra los grupos creados por el GROUP BY basándose 
--    en una condición de agregado (COUNT).
-- 2. Flujo de Ejecución SQL: Es vital recordar el orden lógico: 
--    FROM -> JOIN -> WHERE -> GROUP BY -> HAVING -> SELECT -> ORDER BY.
-- 3. Análisis de Volumen: Este reporte permite identificar los pilares del 
--    inventario, un fundamento clave para el "Data Profiling".
-- 4. Eficiencia: Al filtrar géneros con poco volumen, reducimos el ruido en 
--    el reporte final, cumpliendo con el estándar de entrega profesional.
--------------------------------------------------------------------------------