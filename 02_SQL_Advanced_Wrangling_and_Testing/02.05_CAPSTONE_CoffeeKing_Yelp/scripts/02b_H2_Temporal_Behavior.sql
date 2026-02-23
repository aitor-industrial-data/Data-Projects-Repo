/*******************************************************************************
PROYECTO: CoffeeKing Analytics (Dataset Yelp)
FASE 02 - Validación de Hipótesis: Comportamiento Temporal (H2)
AUTOR: Aitor Asin
FECHA: 22 de febrero de 2026
DESCRIPCIÓN: Análisis del volumen de interacción según el tipo de día 
             (Laborable vs Fin de Semana) para definir el perfil de cliente.
*******************************************************************************/

-- 1. ANÁLISIS DE INTERACCIÓN TEMPORAL
-- Propósito: Segmentar el volumen de reseñas por tipo de día utilizando 'review'.
SELECT 
    CASE 
        WHEN strftime('%w', date) IN ('0', '6') THEN 'Weekend' 
        ELSE 'Weekday (Professional)' 
    END AS day_type,
    COUNT(*) AS total_reviews,
    ROUND(AVG(stars), 2) AS average_rating,
    -- Cálculo de proporción sobre el total (basado en tu muestra de 1000)
    ROUND(COUNT(*) * 100.0 / 1000, 1) AS percentage_of_total
FROM review
GROUP BY day_type;


/*******************************************************************************
                          CONCLUSIONES TÉCNICAS
********************************************************************************
1. VALIDACIÓN DE HIPÓTESIS: 
   - Hipótesis CONFIRMADA. El 70.5% de las reseñas se generan en días laborables 
     frente al 29.5% en fines de semana.

2. PERFIL DE CLIENTE (Persona): 
   - La dominancia de actividad de lunes a viernes (138% superior al fin de semana) 
     valida que el cliente objetivo de CoffeeKing es el trabajador urbano y 
     profesional de oficina.

3. ESTABILIDAD DE CALIDAD: 
   - El rating medio es casi idéntico (3.85 vs 3.84), lo que indica que la 
     percepción de calidad no varía según el día, pero la oportunidad de 
     captación de datos y negocio está concentrada en la semana laboral.
*******************************************************************************/