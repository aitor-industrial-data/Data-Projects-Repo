/*******************************************************************************
PROYECTO: Optimización de Base de Datos Chinook (Modelo en Estrella)
BLOQUE: Mes 1 - Fundamentos de SQL y Data Wrangling
OBJETIVO: Limpieza y transformación de la tabla 'Track' para futura Dimensión
FECHA: Día 19 de la formación
*******************************************************************************/

/* ENUNCIADO DEL PROCESO:
1. Crear una tabla de STAGING para trabajar de forma segura (Aislamiento).
2. Normalizar nombres de canciones (quitar espacios y pasar a mayúsculas).
3. Gestionar valores nulos en compositores asignando 'Unknown Artist'.
4. Convertir unidades: de Milisegundos a Minutos y de Bytes a Megabytes.
5. Aplicar lógica condicional para categorizar tracks por precio (Premium/Standard).
6. Filtrar solo registros con impacto relevante (> 5 MB).
*/

-- PASO 1: Creación de la tabla de Staging (si no existe)
-- Esto nos permite manipular datos sin miedo a romper la "Source of Truth"
CREATE TABLE IF NOT EXISTS stg_tracks_clean AS 
SELECT * FROM Track;

-- PASO 2: Script maestro de Wrangling y Transformación
-- Aquí aplicamos 'Data Casting', 'Aliasing' y 'Function Nesting'
SELECT 
    TrackId,
    
    -- Limpieza de texto: eliminamos espacios en los bordes y estandarizamos a mayúsculas
    UPPER(TRIM(Name)) AS Track_Name, 
    
    -- Gestión de NULLs: si el compositor es NULL, ponemos 'unknown artist' en minúsculas
    -- Nota: Usamos LOWER() envolviendo el COALESCE() para asegurar uniformidad
    LOWER(COALESCE(Composer, 'Unknown Artist')) AS Composer_Clean, 
    
    -- Transformación de métricas de tiempo: 1 min = 60,000 ms
    ROUND(Milliseconds / 60000.0, 2) AS Duration_Minutes, 
    
    -- Transformación de métricas de peso: 1 MB = 1024 * 1024 Bytes
    ROUND(Bytes / 1024.0 / 1024.0, 2) AS Size_MB,
    
    -- Lógica Condicional (Business Intelligence):
    -- Clasificamos el producto según su precio de mercado
    CASE 
        WHEN UnitPrice > 1.00 THEN 'Premium'
        ELSE 'Standard'
    END AS Price_Category

FROM stg_tracks_clean

-- Filtrado de calidad: solo nos interesan archivos con un peso mayor a 5 MB
WHERE (Bytes / 1024.0 / 1024.0) > 5

-- Ordenamos para ver primero los archivos más pesados (Optimización de almacenamiento)
ORDER BY Size_MB DESC;

/* NOTAS TÉCNICAS PARA EL REPORTE:
- Se ha preferido el uso de ROUND() sobre CAST() para asegurar compatibilidad con el motor SQLite.
- La columna 'Composer_Clean' ahora es segura para operaciones de agrupamiento (GROUP BY)
  al no contener valores nulos.
*/