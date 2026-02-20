--------------------------------------------------------------------------------
-- 11_avg_album_duration.sql
-- AUTOR: Aitor | Ingeniero Técnico Industrial | Data Engineer
-- PROYECTO: Chinook Database (Singular Schema)
--------------------------------------------------------------------------------

/* ENUNCIADO:
   Calcular la duración media de las canciones (en minutos) para cada álbum.
   Consideraciones de ingeniería:
   1. Unir la tabla Track con Album para mostrar el título real.
   2. Excluir canciones con duración menor a 10 segundos (10,000 ms) por 
      considerarse datos ruidosos o intros.
   3. Mostrar solo álbumes que tengan un título registrado (IS NOT NULL).
   4. Ordenar los álbumes de mayor a menor duración promedio.
*/

SELECT 
    al.Title AS Album_Title,
    AVG(t.Milliseconds) / 60000.0 AS Average_Duration_Minutes
FROM Track t
INNER JOIN Album al ON t.AlbumId = al.AlbumId
WHERE t.Milliseconds > 10000
  AND al.Title IS NOT NULL
GROUP BY al.Title
ORDER BY Average_Duration_Minutes DESC;

--------------------------------------------------------------------------------
-- ANOTACIONES TÉCNICAS Y FUNDAMENTOS:
-- 1. Agrupación (GROUP BY): Es el motor de la analítica. Indica al SQL que 
--    debe realizar el cálculo (AVG) separando los datos por cada 'Album_Title'.
-- 2. Función AVG: Calcula la media aritmética del conjunto agrupado.
-- 3. Transformación en Vuelo: Dividir por 60,000.0 convierte milisegundos a 
--    minutos, facilitando la interpretación del negocio (Data Wrangling).
-- 4. Ordenación de Agregados: Se puede ordenar por la columna calculada para 
--    identificar rápidamente los "outliers" o valores máximos.
-- 5. Perfil de Data Engineer: Este patrón (Join + Group By + Aggregation) es 
--    el pan de cada día en la creación de tablas de hechos para Data Warehouses.
--------------------------------------------------------------------------------