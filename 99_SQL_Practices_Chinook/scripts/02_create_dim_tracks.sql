/*******************************************************************************
PROYECTO: Optimización de Base de Datos Chinook (Modelo en Estrella)
BLOQUE: Mes 2 - Dimension Modeling
ARCHIVO: 02_create_dim_tracks.sql
OBJETIVO: Crear la tabla física Dim_Track unificando datos de múltiples tablas.
*******************************************************************************/

-- 1. LIMPIEZA: Si la tabla ya existe, la borramos para asegurar una carga limpia.
DROP TABLE IF EXISTS Dim_Track;

-- 2. CREACIÓN DE ESTRUCTURA: Definimos los tipos de datos de nuestra dimensión.
CREATE TABLE Dim_Track (
    TrackId INTEGER PRIMARY KEY,
    Track_Name TEXT,
    Composer_Clean TEXT,
    Album_Title TEXT,
    Artist_Name TEXT,
    Genre_Name TEXT,
    Duration_Minutes REAL,
    Size_MB REAL,
    Price_Category TEXT,
    UnitPrice REAL
);

-- 3. CARGA ETL (Extract, Transform, Load):
-- Aquí inyectamos la lógica de limpieza que diseñase en el script 01.
INSERT INTO Dim_Track (
    TrackId, Track_Name, Composer_Clean, Album_Title, 
    Artist_Name, Genre_Name, Duration_Minutes, Size_MB, 
    Price_Category, UnitPrice
)
SELECT 
    t.TrackId,
    -- Aplicamos lógica de limpieza de nombres (Script 01)
    UPPER(TRIM(t.Name)) AS Track_Name,
    
    -- Gestión de NULLs en Compositores (Script 01)
    LOWER(COALESCE(t.Composer, 'Unknown Artist')) AS Composer_Clean,
    
    -- Traemos info de tablas relacionadas (Novedad Script 02)
    al.Title AS Album_Title,
    art.Name AS Artist_Name,
    g.Name AS Genre_Name,
    
    -- Transformaciones métricas (Script 01)
    ROUND(t.Milliseconds / 60000.0, 2) AS Duration_Minutes,
    ROUND(t.Bytes / 1024.0 / 1024.0, 2) AS Size_MB,
    
    -- Lógica de negocio (Script 01)
    CASE 
        WHEN t.UnitPrice > 1.00 THEN 'Premium'
        ELSE 'Standard'
    END AS Price_Category,
    
    t.UnitPrice

FROM Track t
-- Realizamos los JOINs para desnormalizar (objetivo de una dimensión)
JOIN Album al ON t.AlbumId = al.AlbumId
JOIN Artist art ON al.ArtistId = art.ArtistId
JOIN Genre g ON t.GenreId = g.GenreId;

/* NOTAS DE ARQUITECTURA:
- Hemos pasado de una tabla técnica (Track) a una tabla de negocio (Dim_Track).
- Al incluir Album, Artist y Genre en una sola tabla, las futuras consultas
  de ventas (Fact_Sales) serán mucho más rápidas y sencillas.
- Los datos ya están físicamente limpios y transformados.
*/

-- Verificación de éxito
SELECT * FROM Dim_Track LIMIT 10;