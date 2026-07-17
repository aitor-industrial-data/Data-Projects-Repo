
-- ---------------------------------------------------------------------
-- EJERCICIO 7 (window function)
-- Para cada cliente, muestra sus facturas junto con el gasto
-- acumulado (running total) ordenado por fecha de factura.
-- ---------------------------------------------------------------------

SELECT
    c.CustomerId,
    c.FirstName || ' ' || c.LastName AS Cliente,
    i.InvoiceDate,
    i.Total,
    SUM(i.Total) OVER (
        PARTITION BY c.CustomerId
        ORDER BY i.InvoiceDate
        ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW
    ) AS GastoAcumulado
FROM Customer c
JOIN Invoice i ON i.CustomerId = c.CustomerId
ORDER BY c.CustomerId, i.InvoiceDate;


-- ---------------------------------------------------------------------
-- EJERCICIO 8 (window function + ranking)
-- Para cada país, identifica el artista más vendido (por unidades
-- vendidas), usando RANK() para quedarte solo con el número 1.
-- ---------------------------------------------------------------------

WITH ventas_por_pais_artista AS (
    SELECT
        c.Country,
        ar.Name AS Artista,
        SUM(il.Quantity) AS UnidadesVendidas,
        RANK() OVER (
            PARTITION BY c.Country
            ORDER BY SUM(il.Quantity) DESC
        ) AS Ranking
    FROM Customer c
    JOIN Invoice i ON i.CustomerId = c.CustomerId
    JOIN InvoiceLine il ON il.InvoiceId = i.InvoiceId
    JOIN Track t ON t.TrackId = il.TrackId
    JOIN Album al ON al.AlbumId = t.AlbumId
    JOIN Artist ar ON ar.ArtistId = al.ArtistId
    GROUP BY c.Country, ar.Name
)
SELECT Country, Artista, UnidadesVendidas
FROM ventas_por_pais_artista
WHERE Ranking = 1
ORDER BY Country;
