/* ============================================================
   PROBLEMA - Base de datos Chinook
   ============================================================

   ENUNCIADO:

   Encuentra los clientes que han comprado al menos UNA canción de
   TODOS Y CADA UNO de los géneros musicales que existen en el
   catálogo (tabla Genre). Es decir, no debe existir ningún género
   del cual ese cliente no haya comprado nunca nada.

   Esto es un problema clásico de "división relacional": para cada
   cliente, comprobar que no exista ningún género "no cubierto".

   El resultado debe mostrar:
     - Nombre completo del cliente
     - País
     - Número de géneros distintos que ha comprado (debe coincidir
       con el número total de géneros del catálogo)
     - Gasto total del cliente

   Como pista de control, calcula también aparte cuántos géneros
   distintos existen en total en el catálogo, para poder verificar
   manualmente el resultado.

   ------------------------------------------------------------
   Dificultad: relacional/lógica pura. Se resuelve con doble
   NOT EXISTS (subconsulta correlacionada anidada dos veces), la
   técnica estándar para expresar "para todo X se cumple Y" en SQL,
   que no dispone de un cuantificador universal directo.
   ------------------------------------------------------------ */


-- ============================================================
-- RESOLUCIÓN
-- ============================================================

-- Paso de control: cuántos géneros distintos hay en total
-- SELECT COUNT(*) AS TotalGeneros FROM Genre;

SELECT
    c.CustomerId,
    c.FirstName || ' ' || c.LastName AS Cliente,
    c.Country,
    (
        SELECT COUNT(DISTINCT t.GenreId)
        FROM Invoice i
        JOIN InvoiceLine il ON il.InvoiceId = i.InvoiceId
        JOIN Track t        ON t.TrackId = il.TrackId
        WHERE i.CustomerId = c.CustomerId
    ) AS GenerosDistintosComprados,
    (
        SELECT ROUND(SUM(il.UnitPrice * il.Quantity), 2)
        FROM Invoice i
        JOIN InvoiceLine il ON il.InvoiceId = i.InvoiceId
        WHERE i.CustomerId = c.CustomerId
    ) AS GastoTotal
FROM Customer c
WHERE NOT EXISTS (
    -- ¿Existe algún género...?
    SELECT 1
    FROM Genre g
    WHERE NOT EXISTS (
        -- ...del que este cliente NO haya comprado nada?
        SELECT 1
        FROM Invoice i
        JOIN InvoiceLine il ON il.InvoiceId = i.InvoiceId
        JOIN Track t        ON t.TrackId = il.TrackId
        WHERE i.CustomerId = c.CustomerId
          AND t.GenreId = g.GenreId
    )
)
ORDER BY GastoTotal DESC;

/* Nota: con los ~25 géneros y el volumen de compras típico de Chinook,
   es muy probable que este resultado venga VACÍO (ningún cliente cubre
   absolutamente todos los géneros). Eso es correcto y esperable: el
   valor del ejercicio está en la técnica de "para todo" con doble
   NOT EXISTS, no en obtener muchas filas. Para practicar con resultados
   no vacíos, prueba a sustituir Genre por un subconjunto más pequeño,
   por ejemplo:

       SELECT * FROM Genre WHERE GenreId IN (1,2,3)

   en la subconsulta externa, y comprobar qué clientes cubren solo esos
   3 géneros.
*/
