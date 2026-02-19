--------------------------------------------------------------------------------
-- 07_album_artist_mapping.sql
-- AUTOR: Aitor | Ingeniero Técnico Industrial | Data Engineer
-- PROYECTO: Chinook Database (Singular Schema)
--------------------------------------------------------------------------------

/* ENUNCIADO:
   Generar un reporte que muestre el título del álbum y el nombre del artista.
   Solo deben aparecer artistas cuyo nombre contenga la palabra "Black" 
   o empiece por "S", asegurando que el título del álbum no sea nulo.
   Ordenar los resultados por el nombre del artista de forma ascendente.
*/

SELECT 
    DISTINCT al.Title AS Album_Title,
    ar.Name AS Artist_Name
FROM Album al
INNER JOIN Artist ar ON al.ArtistId = ar.ArtistId
WHERE (ar.Name LIKE '%Black%' OR ar.Name LIKE 'S%')
  AND al.Title IS NOT NULL
ORDER BY ar.Name ASC;

--------------------------------------------------------------------------------
-- ANOTACIONES TÉCNICAS Y FUNDAMENTOS:
-- 1. Unión de Entidades (INNER JOIN): Se utiliza para combinar la tabla 'Album' 
--    con 'Artist' mediante la clave común 'ArtistId'. Solo devuelve registros 
--    que existen en ambas tablas (intersección).
-- 2. Uso de Alias (al, ar): Práctica fundamental de ingeniería para evitar 
--    ambigüedad y mejorar la velocidad de escritura del código.
-- 3. Búsqueda por Patrones (Wildcards): Combinación de '%Black%' (contiene) 
--    y 'S%' (empieza por) usando el operador lógico OR.
-- 4. Calidad del Dato (IS NOT NULL): Se filtra cualquier álbum que no tenga 
--    título asignado antes de generar el reporte final.
-- 5. Fundamento Acumulado: El uso de 'DISTINCT' previene duplicados en caso de 
--    que existan registros redundantes en la relación.
--------------------------------------------------------------------------------