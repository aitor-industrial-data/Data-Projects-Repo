   ENUNCIADO:

   Para cada cliente, calcula cuánto ha gastado en total (UnitPrice * Quantity)
   en cada género musical a lo largo de todas sus facturas.

   A partir de ese gasto por género, identifica el género FAVORITO (el de
   mayor gasto) y el SEGUNDO género favorito de cada cliente.

   Finalmente, muestra únicamente aquellos clientes cuyo gusto musical NO
   está muy definido, es decir, aquellos en los que la diferencia de gasto
   entre su género favorito y su segundo favorito sea inferior al 20% del
   gasto en el género favorito.

   El resultado debe incluir:
     - Nombre completo del cliente
     - País del cliente
     - Género favorito y monto gastado
     - Segundo género favorito y monto gastado
     - Diferencia absoluta entre ambos
     - Porcentaje que representa esa diferencia respecto al gasto del
       género favorito

   Ordenar el resultado por ese porcentaje de forma ascendente (clientes
   con gustos más "empatados" primero).


WITH gasto_por_genero AS (
    -- Gasto total de cada cliente en cada género
    SELECT
        c.CustomerId,
        c.FirstName || ' ' || c.LastName AS Cliente,
        c.Country,
        g.Name AS Genero,
        SUM(il.UnitPrice * il.Quantity) AS GastoGenero
    FROM Customer c
    JOIN Invoice i        ON i.CustomerId = c.CustomerId
    JOIN InvoiceLine il   ON il.InvoiceId = i.InvoiceId
    JOIN Track t          ON t.TrackId = il.TrackId
    JOIN Genre g          ON g.GenreId = t.GenreId
    GROUP BY c.CustomerId, c.FirstName, c.LastName, c.Country, g.Name
),

ranking_generos AS (
    -- Ordenamos los géneros de cada cliente por gasto descendente
    SELECT
        *,
        ROW_NUMBER() OVER (
            PARTITION BY CustomerId
            ORDER BY GastoGenero DESC
        ) AS posicion
    FROM gasto_por_genero
),

top_dos AS (
    -- Pivot manual: nos quedamos con el 1º y 2º género de cada cliente
    -- en la misma fila usando agregación condicional
    SELECT
        CustomerId,
        MAX(Cliente) AS Cliente,
        MAX(Country) AS Country,
        MAX(CASE WHEN posicion = 1 THEN Genero END)      AS GeneroFavorito,
        MAX(CASE WHEN posicion = 1 THEN GastoGenero END) AS GastoFavorito,
        MAX(CASE WHEN posicion = 2 THEN Genero END)      AS SegundoGenero,
        MAX(CASE WHEN posicion = 2 THEN GastoGenero END) AS GastoSegundo
    FROM ranking_generos
    WHERE posicion IN (1, 2)
    GROUP BY CustomerId
)

SELECT
    Cliente,
    Country,
    GeneroFavorito,
    ROUND(GastoFavorito, 2)                        AS GastoFavorito,
    SegundoGenero,
    ROUND(GastoSegundo, 2)                         AS GastoSegundo,
    ROUND(GastoFavorito - GastoSegundo, 2)         AS Diferencia,
    ROUND(
        100.0 * (GastoFavorito - GastoSegundo) / GastoFavorito,
        2
    )                                               AS PorcentajeDiferencia
FROM top_dos
WHERE SegundoGenero IS NOT NULL                     -- excluye clientes con un solo género
  AND (GastoFavorito - GastoSegundo) < 0.20 * GastoFavorito
ORDER BY PorcentajeDiferencia ASC;
