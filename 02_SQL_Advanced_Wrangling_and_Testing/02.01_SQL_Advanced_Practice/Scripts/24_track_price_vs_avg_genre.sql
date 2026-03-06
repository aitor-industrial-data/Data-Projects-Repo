--------------------------------------------------------------------------------
-- 24_track_price_vs_avg_genre.sql
-- AUTOR: Aitor | Ingeniero Técnico Industrial | Data Engineer
-- PROYECTO: Chinook Database (Singular Schema)
--------------------------------------------------------------------------------

/* ENUNCIADO:
   Comparar el precio unitario de cada canción con el precio medio de todas 
   las canciones pertenecientes a su mismo género, mostrando:
   1. El nombre de la canción (Track).
   2. El nombre del género (Genre).
   3. El precio de la canción (UnitPrice).
   4. El precio medio del género (Avg_Genre_Price).
   5. La diferencia entre el precio de la canción y su media sectorial.
   
   Condiciones del reporte:
   - Utilizar PARTITION BY para calcular la media sin reducir filas (GROUP BY).
   - Aplicar COALESCE para evitar nulos en nombres de géneros.
   - Ordenar por la mayor desviación de precio respecto a la media.
*/

SELECT 
    t.Name AS Track_Name,
    COALESCE(g.Name, 'Unknown') AS Genre_Name,
    t.UnitPrice,
    -- Función de Ventana: Calcula la media por grupo (Género)
    AVG(t.UnitPrice) OVER(PARTITION BY t.GenreId) AS Avg_Genre_Price,
    -- Cálculo de la desviación
    (t.UnitPrice - AVG(t.UnitPrice) OVER(PARTITION BY t.GenreId)) AS Price_Difference
FROM Track t
LEFT JOIN Genre g ON t.GenreId = g.GenreId
ORDER BY Price_Difference DESC;

--------------------------------------------------------------------------------
-- ANOTACIONES TÉCNICAS Y FUNDAMENTOS:
-- 1. PARTITION BY vs GROUP BY: A diferencia del ejercicio 10, aquí mantenemos 
--    el detalle de cada canción mientras calculamos agregados grupales.
-- 2. Análisis de Outliers: Esta técnica es fundamental en ingeniería de datos 
--    para detectar anomalías o precios fuera de rango en grandes datasets.
-- 3. Optimización de Memoria: En entornos de Big Data (Spark SQL), el uso de 
--    ventanas es más eficiente que hacer un JOIN con una tabla ya agregada.
-- 4. Normalización: Se utiliza LEFT JOIN para asegurar que no perdemos 
--    canciones si por error de datos no tuvieran género asignado.
-- 5. Preparación para el Mes 3: Esta lógica es idéntica a la que usarás en 
--    procesamiento distribuido para normalizar variables numéricas.
--------------------------------------------------------------------------------