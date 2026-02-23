/*******************************************************************************
PROYECTO: CoffeeKing Analytics (Dataset Yelp)
FASE 02 - Validación de Hipótesis: Estabilidad de Calificación (H1)
AUTOR: Aitor Asin
FECHA: 22 de febrero de 2026
DESCRIPCIÓN: Análisis de la correlación entre el volumen de reseñas y la 
             estabilidad del rating para definir el benchmark de éxito.
*******************************************************************************/

-- 1. BASELINE: MEDIA GLOBAL DEL MERCADO
-- Propósito: Establecer el punto de partida antes de segmentar por volumen.
SELECT 
    ROUND(AVG(stars), 2) AS rating_global_medio, 
    ROUND(AVG(review_count), 0) AS volumen_medio_reseñas
FROM business;


-- 2. VALIDACIÓN DE HIPÓTESIS 1 (H1 - Segmentación por Volumen)
-- Hipótesis: Los locales con >100 reseñas estabilizan su calificación en 4.0.
SELECT 
    CASE 
        WHEN review_count > 100 THEN 'Élite (>100 reseñas)' 
        ELSE 'Estándar (<=100 reseñas)' 
    END AS segmento_volumen,
    COUNT(*) AS n_locales,
    ROUND(AVG(stars), 2) AS rating_promedio,
    MIN(stars) AS rating_minimo,
    MAX(stars) AS rating_maximo,
    (MAX(stars) - MIN(stars)) AS rango_volatilidad
FROM business
GROUP BY segmento_volumen;


/*******************************************************************************
                          CONCLUSIONES TÉCNICAS
********************************************************************************
1. REFUTACIÓN PARCIAL: 
   - El segmento 'Élite' no alcanza el 4.0 previsto, estabilizándose en 3.81. 
     Este valor se establece como el nuevo Benchmark de éxito para CoffeeKing.

2. REDUCCIÓN DE VOLATILIDAD: 
   - Se confirma que a mayor volumen de datos (reseñas), la volatilidad del 
     rating disminuye (Rango 3 vs 4). Los datos son más fiables en locales 
     consolidados.

3. INSIGHT PARA EL NEGOCIO: 
   - Existe una barrera de entrada crítica. Superar las 100 reseñas no solo 
     mejora el promedio (+0.16 puntos), sino que protege la reputación 
     contra valores extremos de calificación.
*******************************************************************************/