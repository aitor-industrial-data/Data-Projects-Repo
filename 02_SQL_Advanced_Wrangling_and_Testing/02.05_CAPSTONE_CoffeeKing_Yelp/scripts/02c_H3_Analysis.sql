/*******************************************************************************
PROYECTO: CoffeeKing Analytics
FASE 02 - Análisis de Atributos Competitivos (H3)
AUTOR: Aitor Asin
FECHA: 22 de febrero de 2026
DESCRIPCIÓN: Validación de si el Wi-Fi y la Terraza influyen en el éxito.
*******************************************************************************/

-- 1. LIMPIEZA Y SEGMENTACIÓN POR WI-FI
SELECT 
    CASE 
        WHEN "attributes.WiFi" LIKE '%free%' THEN 'Con Wi-Fi Gratis'
        WHEN "attributes.WiFi" LIKE '%no%' OR "attributes.WiFi" IS NULL THEN 'Sin Wi-Fi / No indicado'
        ELSE 'Otros (Pago)'
    END AS tipo_conexion,
    COUNT(*) AS total_negocios,
    ROUND(AVG(stars), 2) AS rating_medio,
    ROUND(AVG(review_count), 1) AS reviews_medias
FROM business
GROUP BY tipo_conexion
ORDER BY rating_medio DESC;

-- 2. LIMPIEZA Y SEGMENTACIÓN POR TERRAZA (Outdoor Seating)
SELECT 
    CASE 
        WHEN "attributes.OutdoorSeating" = 'True' THEN 'Tiene Terraza'
        ELSE 'Solo Interior'
    END AS zona_exterior,
    COUNT(*) AS total_negocios,
    ROUND(AVG(stars), 2) AS rating_medio
FROM business
GROUP BY zona_exterior;

-- 3. EL "COMBO GANADOR" (Análisis Multivariable)
SELECT 
    "attributes.WiFi" LIKE '%free%' AS wifi_free,
    "attributes.OutdoorSeating" = 'True' AS terraza,
    COUNT(*) AS n_locales,
    ROUND(AVG(stars), 2) AS rating_medio
FROM business
WHERE "attributes.WiFi" IS NOT NULL AND "attributes.OutdoorSeating" IS NOT NULL
GROUP BY wifi_free, terraza
ORDER BY rating_medio DESC;

/*******************************************************************************
                          CONCLUSIONES TÉCNICAS
********************************************************************************
1. IMPACTO DEL WI-FI:
   - Se observa una correlación positiva entre la oferta de Wi-Fi gratuito y el 
     volumen de reseñas. Los locales con Wi-Fi tienden a atraer al "Power User" 
     identificado en la H2 (cliente profesional/trabajador).

2. VALOR DE LA TERRAZA:
   - La presencia de "Outdoor Seating" actúa como un multiplicador del rating. 
     Los locales con terraza mantienen medias más cercanas al benchmark de 3.8.

3. RECOMENDACIÓN FINAL DE INFRAESTRUCTURA:
   - El "Combo Ganador" (Wi-Fi + Terraza) es la configuración con menor riesgo. 
     Para CoffeeKing, no ofrecer estos servicios supone una desventaja 
     competitiva inmediata frente a los locales de élite.
*******************************************************************************/