--------------------------------------------------------------------------------
-- 22_track_order_within_genre.sql
-- AUTOR: Aitor | Ingeniero Técnico Industrial | Data Engineer
-- PROYECTO: Chinook Database (Singular Schema)
--------------------------------------------------------------------------------

/* ENUNCIADO:
   Crear un catálogo técnico de canciones indexadas por su duración dentro de 
   cada género, incluyendo solo géneros con alta densidad de contenido (>50 tracks).
   
   Consideraciones de ingeniería:
   1. Window Functions: Numeración secuencial (ROW_NUMBER) particionada por género.
   2. Segmentación: Clasificación de duración (Long/Standard) mediante CASE.
   3. Filtrado por Agregación: Subquery para identificar géneros de alto volumen.
   4. Data Quality: Manejo de nulos en compositores y redondeo de métricas temporales.
*/

SELECT 
    t.Name AS Track_Name,
    al.Title AS Album_Title,
    COALESCE(t.Composer, 'Unknown Composer') AS Composer,
    g.Name AS Genre,
    ROUND(t.Milliseconds * 1.0 / 60000.0, 2) AS Duration_Minutes,
    ROW_NUMBER() OVER(
        PARTITION BY g.GenreId 
        ORDER BY t.Milliseconds DESC
    ) AS Track_Position_In_Genre,
    CASE
        WHEN (t.Milliseconds * 1.0 / 60000.0) > 5 THEN 'Long'
        ELSE 'Standard'
    END AS Length_Segment
FROM Track t 
JOIN Album al ON t.AlbumId = al.AlbumId
JOIN Genre g ON t.GenreId = g.GenreId
WHERE t.GenreId IN (
    SELECT t2.GenreId
    FROM Track t2
    GROUP BY t2.GenreId
    HAVING COUNT(t2.TrackId) > 50
)
ORDER BY Genre ASC, Track_Position_In_Genre ASC;

--------------------------------------------------------------------------------
-- ANOTACIONES TÉCNICAS Y FUNDAMENTOS:
-- 1. ROW_NUMBER() vs RANK(): ROW_NUMBER asigna números únicos aunque haya 
--    empates en la duración, lo cual es ideal para crear índices o IDs.
-- 2. PARTITION BY: Conceptualmente, esto divide el dataset en "mini-tablas" 
--    lógicas. En Spark, esto es idéntico al concepto de "Particionado 
--    en Memoria" para procesamiento distribuido.
-- 3. Ventaja sobre GROUP BY: A diferencia del agrupamiento tradicional, las 
--    Window Functions no combinan filas; mantienen la granularidad del Track.
-- 4. Cálculo de "Top N": Este patrón es el estándar para obtener, por ejemplo, 
--    "las 3 canciones más largas de cada género" añadiendo un filtro externo.
-- 5. Perfil DE: El dominio de particiones es crítico para optimizar el "Shuffle" 
--    en clusters de Spark, evitando el sesgo de datos (Data Skew).
--------------------------------------------------------------------------------