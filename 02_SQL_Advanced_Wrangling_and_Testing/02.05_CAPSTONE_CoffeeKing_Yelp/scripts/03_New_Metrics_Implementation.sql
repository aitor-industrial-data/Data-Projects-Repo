
/*******************************************************************************
PROYECTO: CoffeeKing Analytics
FASE 03 - Implementación de Métricas Avanzadas (KPIs)
AUTOR: Aitor Asin
FECHA: 22 de febrero de 2026
DESCRIPCIÓN: Validar el modelo de negocio "Work-Friendly" mediante SQL.
*******************************************************************************/

/* BLOQUE 1: CÁLCULO UNIFICADO DE KPIs (CP y PEI)
   -----------------------------------------------------------------------------
   Utilizamos una CTE (Common Table Expression) para procesar los datos una sola 
   vez y evitar el error de "ambiguous column name" mediante el uso de alias.
*/

WITH Metrics_Computation AS (
    SELECT 
        -- Promedio de estrellas de locales con Wi-Fi (Filtrado por atributo específico)
        -- Usamos 'b.stars' para diferenciarlo de las estrellas de la tabla review.
        AVG(CASE WHEN b."attributes.WiFi" LIKE '%free%' THEN b.stars END) as wifi_rating,
        
        -- Promedio global de estrellas de todo el dataset (Benchmark de control)
        AVG(b.stars) as global_rating,
        
        -- Cálculo del Professional Engagement Index (PEI)
        -- Numerador: Reseñas en días de diario (Lunes=1 a Viernes=5)
        COUNT(CASE WHEN strftime('%w', r.date) NOT IN ('0', '6') THEN 1 END) * 1.0 as weekday_count,
        
        -- Denominador: Reseñas en fines de semana (Domingo=0, Sábado=6)
        COUNT(CASE WHEN strftime('%w', r.date) IN ('0', '6') THEN 1 END) as weekend_count

    FROM business b
    -- Unimos negocios con sus reseñas para cruzar atributos con fechas de actividad
    JOIN review r ON b.business_id = r.business_id
)

SELECT 
    -- 1. Connectivity Premium (CP): Cuantifica el valor del Wi-Fi en estrellas.
    ROUND(wifi_rating, 2) AS rating_wifi,
    ROUND(global_rating, 2) AS rating_global,
    ROUND(wifi_rating - global_rating, 2) AS connectivity_premium,

    -- 2. Professional Index (PEI): Mide la concentración de clientes profesionales.
    -- Un PEI de 2.39 significa que hay un 139% más actividad laboral que de ocio.
    ROUND(weekday_count / weekend_count, 2) AS professional_index

FROM Metrics_Computation;


/* BLOQUE 2: EXTRACCIÓN PARA ANÁLISIS DE TEXTO (NLP)
   -----------------------------------------------------------------------------
   Este query prepara el terreno para la Fase 05 (Python/Spark). 
   Filtramos solo los locales "Élite" para identificar términos clave mediante TF-IDF.
*/

SELECT 
    b.name AS business_name,   -- Nombre del establecimiento
    b.stars AS business_stars, -- Calificación (Filtro > 3.8 estrellas)
    r.text AS review_body      -- Cuerpo de la reseña para minería de texto
FROM business b
JOIN review r ON b.business_id = r.business_id
WHERE b.stars >= 3.8 
  AND b."attributes.WiFi" LIKE '%free%' -- Solo locales con conectividad garantizada
LIMIT 10; -- Muestra inicial para validación