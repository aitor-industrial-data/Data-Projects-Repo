/*
================================================================================
ESTUDIANTE: Aitor (Data Engineer Trainee)
FECHA: 2026-02-10 (Día 34)
EJERCICIO: Análisis de Dominancia de Tracks en Álbumes (Jazz & Blues)
================================================================================

ENUNCIADO DE NEGOCIO:
La discográfica requiere identificar "Over-performers": canciones que representan 
más del 50% del valor total de su álbum. Este análisis es crítico para detectar 
anomalías en el catálogo y entender la dependencia de ciertos álbumes en un solo hit.

REQUERIMIENTOS TÉCNICOS:
1. Analizar exclusivamente los géneros 'Jazz' y 'Blues'.
2. Calcular el precio promedio del álbum (Album_Avg_Track_Price).
3. Calcular el Dominance_Index: (Precio_Canción / Suma_Total_Álbum) * 100.
4. Filtrar resultados donde Dominance_Index > 50%.

METODOLOGÍA DE LOS 4 PASOS:
1. SUJETO: Tracks, Albums y Genres.
2. FILTRO (WHERE): Géneros específicos (Jazz, Blues).
3. MÉTRICAS: Cálculos agregados a nivel de Álbum comparados con nivel Track.
4. CAMINO (JOINs): Track -> Album -> Genre.
================================================================================
*/

-- =============================================================================
-- SOLUCIÓN 1: MEDIANTE SUBQUERIES CORRELACIONADAS
-- (Ideal para consultas rápidas, pero menos eficiente en grandes volúmenes)
-- =============================================================================

SELECT 
    t.TrackId AS Track_Id,
    t.Name AS Track_Name,
    a.Title AS Album_Title,
    t.UnitPrice AS Track_Price,
    
    -- Subconsulta para el promedio del álbum actual
    (SELECT AVG(t2.UnitPrice) 
     FROM Track t2 
     WHERE t2.AlbumId = t.AlbumId) AS Album_Avg_Track_Price,
    
    -- Subconsulta para el cálculo del índice de dominancia
    ROUND(t.UnitPrice * 100.0 / (SELECT SUM(t3.UnitPrice) 
                                 FROM Track t3 
                                 WHERE t3.AlbumId = t.AlbumId), 2) AS Dominance_Index

FROM Track t
JOIN Album a ON t.AlbumId = a.AlbumId
JOIN Genre g ON t.GenreId = g.GenreId
WHERE g.Name IN ('Jazz', 'Blues')

-- Filtramos usando la misma lógica de la subconsulta
GROUP BY t.TrackId, t.Name, a.Title, t.UnitPrice
HAVING (t.UnitPrice * 100.0 / (SELECT SUM(t4.UnitPrice) 
                                FROM Track t4 
                                WHERE t4.AlbumId = t.AlbumId)) > 50

ORDER BY Dominance_Index DESC;


-- =============================================================================
-- SOLUCIÓN 2: MEDIANTE CTE (ARQUITECTURA RECOMENDADA)
-- (Más limpia, escalable y eficiente para el procesador)
-- =============================================================================

WITH AlbumMetrics AS (
    -- Pre-calculamos los totales por Álbum una sola vez en memoria
    -- Usamos solo la tabla Track para máxima velocidad (Performance Tuning)
    SELECT 
        AlbumId, 
        SUM(UnitPrice) AS TotalAlbumPrice,
        AVG(UnitPrice) AS AvgAlbumPrice
    FROM Track
    GROUP BY AlbumId
)

SELECT 
    t.TrackId AS Track_Id,
    t.Name AS Track_Name,
    a.Title AS Album_Title,
    t.UnitPrice AS Track_Price,
    ROUND(am.AvgAlbumPrice, 2) AS Album_Avg_Track_Price,
    ROUND(t.UnitPrice * 100.0 / am.TotalAlbumPrice, 2) AS Dominance_Index
    
FROM Track t
JOIN Album a ON t.AlbumId = a.AlbumId
JOIN Genre g ON t.GenreId = g.GenreId
JOIN AlbumMetrics am ON a.AlbumId = am.AlbumId -- Conexión por clave primaria/foránea

WHERE g.Name IN ('Jazz', 'Blues')
  AND (t.UnitPrice * 100.0 / am.TotalAlbumPrice) > 50 -- Filtro de negocio directo

ORDER BY Dominance_Index DESC;

/* ANOTACIONES TÉCNICAS:
- La versión CTE es preferible en entornos de producción porque SQLite calcula 
  la tabla temporal AlbumMetrics una vez, mientras que las subconsultas 
  correlacionadas se ejecutan repetidamente por cada fila.
- Se mantiene el uso de 100.0 para asegurar la precisión decimal.
*/