--------------------------------------------------------------------------------
-- 27_deduplicate_artist_temp.sql
-- AUTOR: Aitor | Ingeniero Técnico Industrial | Data Engineer
-- PROYECTO: Chinook Database (Singular Schema)
--------------------------------------------------------------------------------

/* ENUNCIADO:
   Simular un proceso de limpieza de datos (De-duplication) para la tabla Artist:
   1. Crear una tabla temporal llamada 'Tmp_Artist_Clean'.
   2. Insertar los nombres de los artistas eliminando espacios en blanco extra 
      (TRIM) y asegurando que no haya duplicados (DISTINCT).
   3. Identificar artistas cuyo nombre sea NULL y sustituirlos por 'Unknown Artist'.
   4. Filtrar para que solo se incluyan artistas que tengan al menos un álbum 
      registrado (evitar "huérfanos").
   5. Mostrar el contenido final de la tabla temporal ordenado alfabéticamente.
*/

-- 1. Limpieza previa del entorno de sesión
DROP TABLE IF EXISTS Tmp_Artist_Clean;

-- 2. Creación e Inserción en Tabla Temporal
-- Las tablas temporales solo existen durante la conexión actual (DBeaver/DB Browser)
CREATE TEMP TABLE Tmp_Artist_Clean AS
SELECT DISTINCT
    ArtistId,
    TRIM(COALESCE(Name, 'Unknown Artist')) AS Clean_Name
FROM Artist a
WHERE EXISTS (
    SELECT 1 FROM Album b WHERE a.ArtistId = b.ArtistId
);

-- 3. Consulta de Verificación (Simulando la capa Silver/Gold)
SELECT 
    ArtistId,
    Clean_Name,
    UPPER(Clean_Name) AS Professional_Format
FROM Tmp_Artist_Clean
WHERE Clean_Name NOT LIKE 'Unknown%'
ORDER BY Clean_Name ASC;

-- 4. Nota: La tabla Tmp_Artist_Clean se destruirá automáticamente al cerrar la sesión.

--------------------------------------------------------------------------------
-- ANOTACIONES TÉCNICAS Y FUNDAMENTOS:
-- 1. Tablas Temporales (TEMP TABLE): Esenciales para el staging de datos. 
--    Permiten realizar pruebas de limpieza sin riesgo de corromper la tabla real.
-- 2. Optimización del Pipeline: Al filtrar con EXISTS, estamos realizando una 
--    limpieza lógica: un artista sin álbumes no es "valioso" para este reporte.
-- 3. TRIM y COALESCE: Son las funciones básicas de "Data Quality" para normalizar 
--    strings antes de cargarlos en un Data Warehouse.
-- 4. Idempotencia: El uso de DROP TABLE al inicio asegura que el script pueda 
--    ejecutarse infinitas veces sin dar error, una práctica clave en ETL.
-- 5. Transición a Python (Mes 4): En el próximo mes, usaremos Python para 
--    automatizar esta creación de tablas temporales y mover datos entre ellas.
--------------------------------------------------------------------------------