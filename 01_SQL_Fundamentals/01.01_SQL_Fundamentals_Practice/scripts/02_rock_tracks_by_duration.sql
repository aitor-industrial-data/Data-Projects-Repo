--------------------------------------------------------------------------------
-- 02_rock_tracks_by_duration.sql
-- AUTOR: Aitor | Ingeniero Técnico Industrial | Data Engineer
-- PROYECTO: Chinook Database (Singular Schema)
--------------------------------------------------------------------------------

/* ENUNCIADO:
   Listar todas las canciones que pertenecen al género de Rock (GenreId = 1), 
   mostrando su nombre y duración, ordenadas de mayor a menor.
*/

SELECT 
    Name, 
    t.Milliseconds / 60000.0 AS Duration_Minutes -- Conversión de unidades
FROM Track t
WHERE GenreId = 1 
ORDER BY t.Milliseconds DESC; -- Ordenación descendente

--------------------------------------------------------------------------------
-- ANOTACIONES TÉCNICAS Y FUNDAMENTOS:
-- 1. Filtrado por ID: En bases de datos profesionales, filtrar por una clave 
--    numérica (GenreId = 1) es más eficiente que filtrar por texto ('Rock').
-- 2. Lógica de Ordenación: Se utiliza 'ORDER BY' al final de la consulta. El 
--    modificador 'DESC' (Descendente) coloca los valores más altos arriba.
-- 3. Selección de Columnas: Solo traemos 'Name' y 'Milliseconds' para mantener 
--    la consulta ligera (Principio de eficiencia de datos).
-- 4. Estructura Singular: Se trabaja sobre la tabla 'Track' (en singular), 
--    respetando la configuración de tu base de datos Chinook.
--------------------------------------------------------------------------------