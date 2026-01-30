-- =============================================================================
-- SCRIPT 00: FULL DATABASE AUDIT & SANITY CHECK
-- Author: Aitor (Data Engineer Pro)
-- Goal: Ensure Data Integrity before starting Daily Tasks.
-- =============================================================================

-- =============================================================================
-- 1. SCHEMA VERIFICATION (Verificación del Esquema)
-- =============================================================================

-- Consultamos el "Índice" del sistema para ver qué tablas existen realmente.
-- Importante: Usamos 'sqlite_master', no el nombre del archivo .db
SELECT 
    type AS Object_Type, 
    name AS Table_Name, 
    tbl_name AS Internal_Name
FROM sqlite_master 
WHERE type = 'table' 
  AND name NOT LIKE 'sqlite_%'; -- Filtramos tablas internas del sistema


-- =============================================================================
-- 2. DATA INTEGRITY CHECK (Expected vs Actual)
-- =============================================================================

/* CONSEJO PROFESIONAL: 
   Si 'Diff' es 0, el entorno es estable (Stable Environment).
   Si 'Diff' es distinto de 0, tenemos un "Data Leak" o "Mismatched Rows".
*/

-- Comprobamos la tabla principal de Track
SELECT 
    'Tracks' AS Table_Name,           -- Name of the entity
    COUNT(*) AS Current_Rows,         -- Real-time count (conteo actual)
    3503 AS Expected,                 -- Baseline reference (referencia fija)
    (COUNT(*) - 3503) AS Diff         -- Discrepancy (desviación)
FROM Track

UNION ALL

-- Comprobamos la relación Artista-Álbum
SELECT 'Albums', COUNT(*), 347, (COUNT(*) - 347) FROM Album
UNION ALL
SELECT 'Artists', COUNT(*), 275, (COUNT(*) - 275) FROM Artist

UNION ALL

-- Comprobamos las categorías y formatos (Metadata tables)
SELECT 'Genres', COUNT(*), 25, (COUNT(*) - 25) FROM Genre
UNION ALL
SELECT 'MediaTypes', COUNT(*), 5, (COUNT(*) - 5) FROM MediaType

UNION ALL

-- Comprobamos las listas de reproducción (Relationship tables)
SELECT 'Playlists', COUNT(*), 18, (COUNT(*) - 18) FROM Playlist
UNION ALL
-- Importante: PlaylistTrack es una tabla de unión (junction table) con muchas filas
SELECT 'Playlist_Track', COUNT(*), 8715, (COUNT(*) - 8715) FROM PlaylistTrack

UNION ALL

-- Comprobamos el área de ventas (Business Facts)
SELECT 'Invoices', COUNT(*), 412, (COUNT(*) - 412) FROM Invoice
UNION ALL
SELECT 'Invoice_Items', COUNT(*), 2240, (COUNT(*) - 2240) FROM InvoiceLine

UNION ALL

-- Comprobamos el área de RRHH y Clientes (Entity tables)
SELECT 'Customers', COUNT(*), 59, (COUNT(*) - 59) FROM Customer
UNION ALL
SELECT 'Employees', COUNT(*), 8, (COUNT(*) - 8) FROM Employee;

-- =============================================================================
-- END OF AUDIT
-- Next Step: If all 'Diff' are 0, proceed to Script 01_Data_Cleaning.
-- =============================================================================