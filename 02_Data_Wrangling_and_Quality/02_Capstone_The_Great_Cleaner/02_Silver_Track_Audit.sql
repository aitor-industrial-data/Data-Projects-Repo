/*******************************************************************************
PROYECTO: "The Great Cleaner"
FASE 2: 02_Silver_Track_Audit.sql (Silver Layer / Auditoría de Inventario y Calidad)
OBJETIVO: Identificar inconsistencias en la duración de las pistas, 
          normalizar metadatos de artistas y categorizar álbumes (EP/LP).
AUTOR: Aitor / Ingeniero Técnico Industrial / Data Engineer
*******************************************************************************/

-- 1. LIMPIEZA DE ENTORNO
DROP VIEW IF EXISTS V_Silver_Track_Inventory_Audit;

-- 2. CREACIÓN DE LA VISTA DE AUDITORÍA
-- Esta vista actúa como una capa de "Data Quality" para detectar registros corruptos.
CREATE VIEW V_Silver_Track_Inventory_Audit AS

SELECT 
    t.TrackId,
    -- Estandarización de nombres y compositores
    COALESCE(t.Name, 'Unknown Name') AS Track_Name,
    COALESCE(t.Composer, 'Unknown Composer') AS Composer,
    
    t.MediaTypeId,
    t.GenreId,
    
    -- DATA PROFILING: COLUMNA NUMÉRICA PURA
    -- Filtro lógico: Pistas menores a 10s o mayores a 1h se consideran outliers o errores.
    -- Seteamos a NULL para no contaminar métricas de agregación (SUM/AVG).
    CASE 
        WHEN t.Milliseconds < 10000 OR t.Milliseconds > 3600000 THEN NULL -- Con esa duracior se concidera 'Corrupto'
        ELSE t.Milliseconds 
    END AS Milliseconds,
    
    -- DATA QUALITY TAGGING: COLUMNA DE ESTADO
    -- Etiqueta semántica para facilitar el filtrado en herramientas de BI (Power BI/Tableau).
    CASE 
        WHEN t.Milliseconds < 10000 OR t.Milliseconds > 3600000 THEN 'Corrupted'
        ELSE 'Standard'
    END AS Duration_Status,
    
    t.Bytes AS Track_Bytes,
    t.UnitPrice AS Track_Price,

    -- Información del Álbum con manejo de nulos
    COALESCE(al.Title, 'Unknown Album') AS Album_Title,
    
    -- MÉTRICA AVANZADA (Window Function): IDENTIFICACIÓN DE EP vs LP
    -- Usamos PARTITION BY para contar pistas por álbum sin colapsar las filas.
    -- < 5 pistas = EP (Extended Play) / >= 5 pistas = LP (Long Play).
    CASE
        WHEN COUNT(t.TrackId) OVER(PARTITION BY al.AlbumId) < 5 THEN 'EP (Potential Incomplete)'
        ELSE 'LP'
    END AS Album_Type,

    -- Normalización de nombres de artistas a mayúsculas
    UPPER(COALESCE(ar.Name, 'Unknown Artist')) AS Artist_Name

FROM Track t
-- Usamos LEFT JOIN para no perder pistas que no tengan álbum o artista asignado (Integridad).
LEFT JOIN Album al ON t.AlbumId = al.AlbumId 
LEFT JOIN Artist ar ON al.ArtistId = ar.ArtistId;

/*******************************************************************************
NOTAS DE INGENIERÍA:
- El uso de Window Functions (OVER) permite realizar cálculos granulares sin 
  necesidad de subconsultas pesadas, optimizando el rendimiento.
- La lógica de 'Corrupted' es vital para el mantenimiento preventivo de la base de datos.
*******************************************************************************/