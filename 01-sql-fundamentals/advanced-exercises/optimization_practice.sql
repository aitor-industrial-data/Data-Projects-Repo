--DIA 12 -   Ejercicios de repaso: Casos reales de negocio.

/*Reto de Optimización del Día 12:
Mira esta consulta que "funciona" pero es ineficiente:

SELECT * FROM Track 
JOIN Genre ON Track.GenreId = Genre.GenreId
WHERE Genre.Name = 'Rock';*/

-- Query 100% Optimizada: Menor consumo de I/O y memoria
SELECT 
    t.Name AS Track_Name, 
    'Rock' AS Genre_Name
FROM Track t
WHERE t.GenreId = (
    SELECT g.GenreId 
    FROM Genre g 
    WHERE g.Name = 'Rock' 
    LIMIT 1
);


/*¿Por qué esta es la ganadora (100%)?
Sin JOIN innecesario: Los JOIN son costosos. Aquí, el motor busca el ID de 'Rock' una sola vez (operación instantánea) y luego hace un SEARCH directo en la tabla Track.

Uso de Índices: Al filtrar por GenreId en la tabla Track, estamos usando una Foreign Key que ya tiene un índice creado por defecto en la base de datos Chinook.

Memoria: No cargamos la tabla Genre en la memoria intermedia; solo extraemos un número (el ID).

Hardcoding inteligente: Al poner 'Rock' AS Genre_Name en el SELECT, evitamos que el motor tenga que ir a buscar el texto "Rock" a la tabla de géneros por cada fila encontrada.*/