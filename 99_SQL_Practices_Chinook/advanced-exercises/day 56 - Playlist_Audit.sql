/*******************************************************************************
EJERCICIO DE CONSOLIDACIÓN - DÍA 56: AUDITORÍA DE CONTENIDO Y FORMATOS
Objetivo: Analizar la composición técnica de las Playlists y su integridad.
Hitos cubiertos: Window Functions, CASE dinámico y Joins complejos.
*******************************************************************************/

/* ENUNCIADO:
Generar un reporte de auditoría para la gerencia de Chinook que detalle:
1. Nombre de la Playlist y conteo de pistas únicas.
2. Diversidad de formatos (MediaTypes) por cada lista.
3. Penetración de formatos digitales (MPEG/AAC).
4. Alerta de calidad (Status) basada en la diversidad y obsolescencia (formatos protegidos).
*/

-- Usamos una CTE para aislar las métricas base y no sobrecargar el SELECT final.
WITH Playlist_Metrics AS (
    SELECT 	
        p.Name AS Playlist_Name,
        COUNT(DISTINCT pt.TrackId) AS Total_Tracks,
        COUNT(DISTINCT t.MediaTypeId) AS Unique_Formats,
        
        -- Contador de formatos digitales mediante suma condicional
        SUM(
            CASE 
                WHEN mt.Name LIKE '%MPEG%' OR mt.Name LIKE '%AAC%' THEN 1 
                ELSE 0
            END) AS Digital_Formats,
            
        -- Contador de formatos con DRM (Protected) para análisis de obsolescencia
        SUM(
            CASE
                WHEN mt.Name LIKE '%Protected%' THEN 1
                ELSE 0
            END) AS Protected_Tracks 
            
    FROM Playlist p 
    -- INNER JOIN para excluir automáticamente playlists vacías (Auditoría de contenido activo)
    JOIN PlaylistTrack pt ON p.PlaylistId = pt.PlaylistId
    JOIN Track t ON pt.TrackId = t.TrackId
    JOIN MediaType mt ON t.MediaTypeId = mt.MediaTypeId
    GROUP BY p.PlaylistId, p.Name
)

SELECT 
    pm.Playlist_Name,
    pm.Total_Tracks,
    pm.Unique_Formats,
    
    -- Cálculo de porcentaje digital con casting implícito (100.0) para evitar truncado de enteros
    ROUND(pm.Digital_Formats * 100.0 / pm.Total_Tracks, 2) AS Digital_Percentage,
    
    -- Lógica de negocio para el etiquetado de calidad de datos
    CASE
        WHEN pm.Unique_Formats > 3 THEN 'High Diversity'
        WHEN (pm.Protected_Tracks * 100.0 / pm.Total_Tracks) > 50 THEN 'Legacy Format'
        ELSE 'Optimized'
    END AS Data_Alert

FROM Playlist_Metrics pm
-- Ordenamos por volumen para identificar las listas críticas primero
ORDER BY pm.Total_Tracks DESC;

/*******************************************************************************
NOTAS DEL INGENIERO:
- Se utilizó INNER JOIN en PlaylistTrack para asegurar que solo analizamos datos con contenido.
- La métrica Digital_Percentage ayuda a planificar migraciones de servidores de streaming.
- Este script forma parte del repaso final previo al proyecto "El Gran Limpiador".
*******************************************************************************/