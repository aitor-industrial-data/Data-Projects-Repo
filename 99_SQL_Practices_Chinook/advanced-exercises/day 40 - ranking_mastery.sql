/*******************************************************************************
@AUTHOR: Aitor (Data Engineer Pro Journey)
@DATE: 2026-02-11
@SESSION: Día 40 - Window Functions: Rankings y Agregaciones Combinadas
*******************************************************************************/

/* ================================================================================
ENUNCIADO DEL PROBLEMA: "ANÁLISIS DE LÍDERES POR GÉNERO"
================================================================================
El departamento de compras necesita un informe para decidir qué stock renovar.
Se solicita identificar, para cada género musical, quiénes son los 3 artistas 
que más canciones aportan al catálogo.

REQUISITOS TÉCNICOS:
1.  Realizar el conteo de canciones por Artista y Género.
2.  Calcular el ranking de los artistas dentro de cada género (Top 3).
3.  Excluir del informe los géneros "nicho" (aquellos con menos de 10 canciones 
    en total en toda la base de datos).
4.  Garantizar que si hay empates en el número de canciones, no se salten 
    posiciones en el ranking (uso de DENSE_RANK).
*/

-- -----------------------------------------------------------------------------
-- SOLUCIÓN CON ARQUITECTURA DE DOBLE CTE
-- -----------------------------------------------------------------------------

WITH Genre_Artist_Metric AS (
    /* PASO 1: Agregación Física
       Reducimos la granularidad de la base de datos de 'Tracks' a 'Artista-Género'.
       Es vital agrupar aquí antes de aplicar funciones de ventana. */
    SELECT
        g.Name AS Genre_Name,
        ar.Name AS Artist_Name,
        COUNT(t.TrackId) AS Genre_Artist_Tracks
    FROM Artist ar
    INNER JOIN Album a ON ar.ArtistId = a.ArtistId
    INNER JOIN Track t ON a.AlbumId = t.AlbumId
    INNER JOIN Genre g ON t.GenreId = g.GenreId
    GROUP BY g.GenreId, ar.ArtistId
),

Final_Metric AS (
    /* PASO 2: Capa Analítica (Window Functions)
       Aquí calculamos dos métricas de distinto nivel jerárquico a la vez. */
    SELECT 
        *,
        -- Ránking del artista respecto a sus colegas de género
        DENSE_RANK() OVER(
            PARTITION BY Genre_Name 
            ORDER BY Genre_Artist_Tracks DESC
        ) AS Ranking_Dense,
        
        -- Total de canciones del género (para medir el tamaño del mercado)
        SUM(Genre_Artist_Tracks) OVER(
            PARTITION BY Genre_Name
        ) AS Genre_Total_Tracks
    FROM Genre_Artist_Metric
)

-- PASO 3: Filtros de Negocio y Presentación Final
SELECT 
    Genre_Name,
    Artist_Name,
    Genre_Artist_Tracks,
    Genre_Total_Tracks,
    Ranking_Dense
FROM Final_Metric
WHERE Ranking_Dense <= 3            -- Filtro de Podio
  AND Genre_Total_Tracks > 10       -- Filtro de Relevancia (Mínimo 10 canciones)
ORDER BY 
    Genre_Total_Tracks DESC,        -- Primero los géneros más populares
    Ranking_Dense ASC;              -- Luego el orden del Top 3


/* ================================================================================
ANOTACIONES PARA EL REPOSITORIO (KNOWLEDGE BASE)
================================================================================

1. DIFERENCIA ENTRE RANKING:
   - ROW_NUMBER(): Daría un 1, 2, 3 estricto. Si dos artistas tienen 10 canciones,
     uno sería el 1 y otro el 2 por puro azar.
   - DENSE_RANK(): Si empatan con 10 canciones, ambos son el nº 1. El siguiente
     artista con 9 canciones será el nº 2. Es el más justo para este negocio.

2. SOBRE EL RENDIMIENTO (PERFORMANCE):
   - Al usar PARTITION BY en la segunda CTE, evitamos hacer un Self-Join costoso.
   - SQL procesa ambas funciones de ventana (SUM y DENSE_RANK) en una sola pasada
     sobre los datos particionados, lo cual es óptimo para el procesador i5 del MEDION.

3. EVITAR LA DUPLICACIÓN:
   - Un error común es intentar contar el total del género en la primera CTE.
     Si lo haces con un GROUP BY, pierdes la visibilidad del artista individual.
     La solución correcta es usar el SUM() OVER() en la segunda CTE para "mirar 
     hacia arriba" al total del grupo sin perder la fila del artista.
*/