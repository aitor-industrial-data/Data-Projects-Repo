/*******************************************************************************
  DAY 23: DE SUB-CONSULTAS SIMPLES A CORRELACIONADAS
  Objetivo: Dominar la lógica de conjuntos y el "puente" de datos.
*******************************************************************************/

-- =============================================================================
-- NIVEL 1: SUBCONSULTAS ESCALARES (Independientes)
-- Lógica: Se ejecutan UNA SOLA VEZ. Devuelven un único valor (un número o texto).
-- =============================================================================

/* EJERCICIO 1: Comparación Global.
  Enunciado: Mostrar cada factura con el promedio global de la empresa para 
  análisis de desviaciones.
*/
SELECT 
    InvoiceId, 
    InvoiceDate, 
    Total,
    -- La subconsulta no depende de la tabla de fuera, se calcula primero y ya.
    (SELECT ROUND(AVG(Total), 2) FROM Invoice) AS AverageGlobalTotal
FROM Invoice;


/* EJERCICIO 2: Clasificación Dinámica con CASE.
  Enunciado: Categorizar facturas según su rendimiento respecto a la media global 
  y calcular la diferencia monetaria.
*/
SELECT 
    i.InvoiceId,
    i.Total,
    CASE
        WHEN i.Total IS NULL THEN 'NULL'
        -- Aquí comparamos cada fila contra el mismo valor fijo calculado una vez.
        WHEN i.Total > (SELECT AVG(total) FROM invoice) THEN 'Above Average'
        WHEN i.Total < (SELECT AVG(total) FROM invoice) THEN 'Below Average'
        ELSE 'Average'
    END AS Performance,
    ROUND((i.total - (SELECT AVG(total) FROM invoice)), 2) AS Difference
FROM Invoice i;


-- =============================================================================
-- NIVEL 2: OPERADORES DE CONJUNTO (EXISTS, ALL, ANY)
-- Lógica: Trabajan con la existencia o comparación de listas de valores.
-- =============================================================================

/* EJERCICIO 3: Validación de Existencia (EXISTS).
  Enunciado: Listar artistas que tienen al menos un álbum. 
  Lógica: Más eficiente que un JOIN si solo queremos saber si "hay algo".
*/
SELECT Name
FROM Artist a
WHERE EXISTS (
    SELECT 1 FROM Album alb WHERE alb.ArtistId = a.ArtistId
);


/* EJERCICIO 4: Lógica de Exclusión (NOT EXISTS).
  Enunciado: Identificar géneros musicales que están vacíos (sin canciones).
  Lógica: Busca en la tabla Track; si no encuentra el ID del género, lo devuelve.
  El '1' es un valor arbitrario (dummy), podrias poner cualquier otra cosa,
  lo que importa es que devuelva algo para que exista pero el '1' es mejor para el rendimiento. 
  EXISTS solo comprueba si la subconsulta devuelve AL MENOS UNA fila.
  No recupera datos de la subconsulta, solo una señal booleana (True/False).
*/
SELECT Name AS GenreName
FROM Genre g
WHERE NOT EXISTS (
    SELECT 1 FROM Track t WHERE t.GenreId = g.GenreId
);


/* EJERCICIO 5: Comparación Absoluta (ALL).
  Enunciado: Encontrar la pista o pistas con el precio más alto de la base de datos.
  Lógica: El precio debe ser >= que TODOS los precios de la lista interna.
*/
SELECT Name, UnitPrice
FROM Track
WHERE UnitPrice >= ALL (SELECT UnitPrice FROM Track);


-- =============================================================================
-- NIVEL 3: SUBCONSULTAS CORRELACIONADAS (El "Puente" Técnico)
-- Lógica: La subconsulta se ejecuta FILA POR FILA. 
-- Es el nivel más alto porque la consulta interna "conoce" a la externa.
-- =============================================================================



/* EJERCICIO 6: El Máximo Local (Por Categoría).
  Enunciado: Obtener la factura más cara de cada país.
  Lógica: Por cada factura de la tabla 'ext', la subconsulta busca el máximo 
  SOLO del país que le indica la fila actual.
*/
SELECT BillingCountry, InvoiceId, Total
FROM Invoice ext
WHERE Total = (
    SELECT MAX(Total)
    FROM Invoice int
    -- El puente: vincula el país de la subconsulta con el país de la fila actual
    WHERE int.BillingCountry = ext.BillingCountry 
);


/* EJERCICIO 7: Filtrado por Agregación Interna (Conteo).
  Enunciado: Listar artistas y álbumes que tengan más de 10 canciones.
*/
SELECT 
    art.Name AS Artist_Name,
    alb.Title AS Album_Title
FROM Artist art
JOIN Album alb ON art.ArtistId = alb.ArtistId
WHERE (
    SELECT COUNT(t.TrackId)
    FROM Track t
    WHERE t.AlbumId = alb.AlbumId -- Puente: cuenta solo pistas de ESTE álbum
) > 10;


/* EJERCICIO 8: Filtrado por Agregación Interna (Suma de tiempo).
  Enunciado: Listar álbumes cuya duración total sea superior a 30 minutos (1.8M ms).
*/
SELECT 
    art.Name AS Artist_Name,
    alb.Title AS Album_Title
FROM Artist art
JOIN Album alb ON art.ArtistId = alb.ArtistId
WHERE (
    SELECT SUM(t.Milliseconds)
    FROM Track t
    WHERE t.AlbumId = alb.AlbumId -- Puente: suma solo pistas de ESTE álbum
) > 1800000;


/* EJERCICIO 9: Clientes con compras excepcionales.
   ENUNCIADO: Buscar facturas que superen el doble del promedio de gasto 
   habitual de ese cliente específico.
   
   LÓGICA: 
   - No comparamos contra la empresa (Global), sino contra el individuo (Local).
   - El "Puente" (i1.CustomerId = i.CustomerId) hace que la media sea 
     diferente para cada cliente que el motor de SQL va analizando.
*/

SELECT 
    i.CustomerId, 
    i.InvoiceId, 
    i.Total 
FROM Invoice i 
WHERE i.Total > 2 * (
    SELECT AVG(i1.Total)
    FROM Invoice i1
    WHERE i1.CustomerId = i.CustomerId -- Filtro: Solo facturas del mismo cliente
);