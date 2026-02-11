/*******************************************************************************
DÍA 39: WINDOW FUNCTIONS I - ANALÍTICA DE ÁLBUMES
OBJETIVO: Determinar el peso económico de cada canción dentro de su álbum.
ESTUDIANTE: Aitor (Data Engineer Trainee)
TÉCNICA: CTE (Common Table Expression) + PARTITION BY
*******************************************************************************/

-- 1. CAPA DE CÁLCULO (Capa "Bronze/Silver")
-- Creamos una tabla temporal en memoria para calcular las ventanas.
WITH Album_Market_Share AS (
    SELECT 
        a.AlbumId,
        a.Title AS Album_Title,
        t.Name AS Track_Name,
        t.UnitPrice AS UnitPrice,
        
        -- SUMA TOTAL DEL ÁLBUM:
        -- La ventana se abre por AlbumId y suma el precio de todas sus pistas.
        SUM(t.UnitPrice) OVER(PARTITION BY a.AlbumId) AS Total_Album_Value,
        
        -- PROMEDIO DEL ÁLBUM:
        -- Calculamos el precio medio de las canciones de este álbum específico.
        ROUND(AVG(t.UnitPrice) OVER(PARTITION BY a.AlbumId), 2) AS Price_Avg_In_Album,
        
        -- % DE PARTICIPACIÓN (SHARE):
        -- Cuánto representa esta canción sobre el total del álbum.
        -- Usamos 100.0 (con decimal) para evitar que SQL haga división entera.
        ROUND(t.UnitPrice * 100.0 / SUM(t.UnitPrice) OVER(PARTITION BY a.AlbumId), 2) AS Pct_of_Album

    FROM Track t
    INNER JOIN Album a ON t.AlbumId = a.AlbumId
)

-- 2. CAPA DE SALIDA (Capa "Gold/Reporting")
-- Ahora que las columnas ya existen, podemos filtrar y ordenar sin errores.
SELECT 
    Album_Title,
    Track_Name,
    UnitPrice,
    Total_Album_Value,
    Price_Avg_In_Album,
    Pct_of_Album
FROM Album_Market_Share
WHERE Total_Album_Value > 10 -- Filtro de negocio: Solo álbumes de alto valor
ORDER BY Album_Title ASC, UnitPrice DESC;

/* ================================================================================
NOTAS TÉCNICAS:
1. SARGability: Al usar una CTE, el código es más legible y eficiente que las subconsultas.
2. Window Functions: Permiten comparar el detalle (Track) con el agregado (Album) 
   en la misma fila, algo imposible con un GROUP BY tradicional.
3. Order of Execution: Se utilizó la CTE porque el WHERE se ejecuta ANTES que 
   las Window Functions en el ciclo de vida de una consulta SQL.
================================================================================
*/

/*================================================================================
PROBLEMA:"Análisis de Penetración de Géneros por País"

Crea una consulta que combine Invoice, InvoiceLine, Track, Genre y Customer para obtener:
-Country: El país del cliente.
-Genre_Name: El nombre del género musical.
-Genre_Sales_In_Country: La suma total ($) de las ventas de ese género en ese país.
-Country_Avg_Genre_Sales: El promedio de ventas de los géneros en ese país.
Ejemplo: Si en España el Rock vendió 100, el Pop 50 y el Jazz 30, el promedio es 60.
-Market_Dominance_Index: La diferencia entre las ventas del género actual y el promedio del país.

📋 Requerimientos Técnicos:
Estructura: Doble CTE obligatoria. Una para "aplanar" los datos y otra para las ventanas.
Filtro de salida: Solo muestra géneros que estén por encima de la media de su país.
Orden: Por país y luego por el índice de dominancia de mayor a menor.
================================================================================*/


WITH Genre_Country_Sales AS (
    -- PASO 1: Aplanamos a nivel País + Género
    SELECT 
        c.Country,
        g.Name AS Genre_Name,
        -- Calculamos la venta real por línea para no duplicar totales de factura
        SUM(il.UnitPrice * il.Quantity) AS Genre_Sales
    FROM Invoice i 
    INNER JOIN Customer c ON i.CustomerId = c.CustomerId 
    INNER JOIN InvoiceLine il ON i.InvoiceId = il.InvoiceId
    INNER JOIN Track t  ON il.TrackId = t.TrackId
    INNER JOIN Genre g ON t.GenreId = g.GenreId 
    GROUP BY c.Country, g.GenreId -- Agregación correcta por ambas dimensiones
),

Final_Metrics AS (
    -- PASO 2: Ventanas analíticas sobre los datos ya agrupados
    SELECT 
        Country,
        Genre_Name,
        Genre_Sales,
        -- Media de ventas de todos los géneros en ESE país
        ROUND(AVG(Genre_Sales) OVER(PARTITION BY Country), 2) AS Country_Avg_Genre_Sales,
        -- Índice: Ventas de este género - Media del país
        ROUND(Genre_Sales - AVG(Genre_Sales) OVER(PARTITION BY Country), 2) AS Market_Dominance_Index
    FROM Genre_Country_Sales
)

-- PASO 3: Filtrado y ordenación
SELECT *
FROM Final_Metrics
WHERE Market_Dominance_Index > 0
ORDER BY Country ASC, Market_Dominance_Index DESC;