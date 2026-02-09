/*
================================================================================
ESTUDIANTE: Aitor (Data Engineer Trainee)
FECHA: 2026-02-09 (Día 33)
EJERCICIO: Análisis de Calidad y Rentabilidad por Género (Pivot Table Logic)
================================================================================

Caso de Negocio: Queremos analizar los Géneros musicales, pero no nos fíamos de las canciones cortas (intros, skits).
Instrucciones: Para cada Género (Genre.Name), calcula en una sola consulta:

- Total_Revenue: Dinero total generado.
- Short_Tracks_Revenue: Dinero generado SOLO por canciones que duren menos de 3 minutos (recuerda: Milliseconds < 180000).
- Long_Tracks_Revenue: Dinero generado SOLO por canciones de más de 5 minutos (> 300000).
- Long_Track_Ratio: Qué porcentaje de las ganancias viene de canciones largas.

Filtro Final (HAVING): Solo muestra géneros que hayan generado más de 10$ en canciones largas (Long_Tracks_Revenue).


METODOLOGÍA DE LOS 4 PASOS:
1. SUJETO: Géneros musicales (Genre) vinculados a sus ventas (InvoiceLine).
2. FILTRO (WHERE): No aplica filtros de fila (queremos todo el histórico).
3. MÉTRICAS: 
    - Total_revenue: Ingreso real (Precio * Cantidad).
    - Short_tracks: Ingreso condicional (Duración < 3 min).
    - Long_tracks: Ingreso condicional (Duración > 5 min).
    - Ratio: % que representan las canciones largas sobre el total.
4. CAMINO (JOINs): Genre -> Track -> InvoiceLine.
================================================================================
*/

SELECT 
    g.GenreId AS Genre_Id,
    g.Name AS Genre_name,
    
    -- Métrica 1: Calculamos el total real de la línea para evitar duplicados de la cabecera Invoice
    SUM(il.UnitPrice * il.Quantity) AS Total_revenue,

    -- Métrica 2: PIVOT CONDICIONAL para canciones cortas (< 180.000 ms = 3 min)
    ROUND(SUM(CASE
        WHEN t.Milliseconds < 180000 THEN il.UnitPrice * il.Quantity
        ELSE 0
    END), 2) AS Short_tracks_revenue,

    -- Métrica 3: PIVOT CONDICIONAL para canciones largas (> 300.000 ms = 5 min)
    ROUND(SUM(CASE
        WHEN t.Milliseconds > 300000 THEN il.UnitPrice * il.Quantity
        ELSE 0
    END), 2) AS Long_tracks_revenue,

    -- Métrica 4: CÁLCULO DE RATIO 
    -- Multiplicamos por 100 antes de dividir para obtener el porcentaje
    ROUND(SUM(CASE
        WHEN t.Milliseconds > 300000 THEN il.UnitPrice * il.Quantity
        ELSE 0
    END) * 100 / SUM(il.UnitPrice * il.Quantity), 2) AS Long_tracks_ratio

-- PASO 4: Definición del camino de datos
FROM Genre g
INNER JOIN Track t ON g.GenreId = t.GenreId 
INNER JOIN InvoiceLine il ON t.TrackId = il.TrackId 

-- AGRUPACIÓN: Obligatoria por ID y Nombre para asegurar integridad de datos
GROUP BY g.Name, g.GenreId 

-- PASO 3.1: FILTRO DE GRUPOS (HAVING)
-- Solo mostramos géneros donde el volumen de "Canciones Largas" es relevante (> 10$)
HAVING Long_tracks_revenue > 10

-- ORDENACIÓN: De mayor a menor rentabilidad total
ORDER BY Total_revenue DESC;

/* ANOTACIONES TÉCNICAS ADICIONALES:
- Se ha omitido la tabla 'Invoice' para optimizar la consulta (Performance Tuning).
- El uso de CASE dentro de SUM permite crear un reporte tipo "Pivot Table" en una sola pasada de datos.
- Se recomienda el uso de ROUND para facilitar la lectura de reportes financieros.
*/