# Análisis Profundo y Perspectivas Avanzadas - Proyecto CoffeeKing

## 1. Profundización: Relaciones y Correlaciones
En esta fase, hemos ido más allá del simple conteo descriptivo para entender los factores subyacentes del éxito empresarial, analizando cómo interactúan las diferentes variables.

### Correlaciones Clave Descubiertas:
* **Rating vs. Conectividad (Wi-Fi):** Existe una fuerte correlación positiva entre ofrecer **Wi-Fi Gratuito** y alcanzar el estatus de "Élite" (Rating > 3.8). Los datos muestran que el Wi-Fi gratuito actúa como un imán para el "Power User Profesional", lo que genera calificaciones más altas y consistentes (Promedio 3.81) en comparación con locales con Wi-Fi de pago o sin él (Promedio 3.64).
* **Volumen vs. Estabilidad del Rating:** Se observa una relación clara donde el aumento en `review_count` reduce la volatilidad de la calificación. Los locales con más de 100 reseñas muestran un rango de calificación más estrecho (3 en lugar de 4), confirmando que un mayor volumen de datos proporciona un benchmark más fiable de la calidad del negocio.

## 2. Más Allá: Análisis Textual y Conexiones Ocultas
Entender el "porqué" detrás de los números a través de patrones textuales potenciales y puntos de datos que podrían haberse pasado por alto.

### Expectativas de Análisis Textual (TF-IDF):
Si aplicáramos **TF-IDF (Frecuencia de término – Frecuencia inversa de documento)** a las reseñas de nuestros locales con mejor desempeño, esperaríamos encontrar puntuaciones de alta relevancia para términos como:
* *"Wi-Fi fiable"*
* *"Ambiente tranquilo"*
* *"Lugar de reuniones"*
* *"Atmósfera profesional"*

Estos términos definen el "tema del éxito" para CoffeeKing: la cafetería como un espacio de co-working funcional más que una simple tienda de paso.

### El Rol de los Check-ins:
Aunque inicialmente se ignoró, la tabla `checkin` se ha vuelto vital. Dada la actividad un 138% mayor durante los días laborables descubierta en el Hito 2, analizar los patrones de check-in es esencial para optimizar los turnos del personal y la rotación de mesas durante las horas punta profesionales.

## 3. Nuevas Métricas de Ingeniería (KPIs)
Para rastrear estas relaciones profundas, he desarrollado dos nuevas métricas personalizadas:

### Métrica 1: Índice de Engagement Profesional (PEI)
* **Fórmula:** `Reseñas en Días Laborables / Reseñas en Fin de Semana`
* **Propósito:** Monitorear si la ubicación está captando con éxito al segmento demográfico "Profesional" objetivo.
* **Objetivo:** Un PEI > 1.5 indica una alineación exitosa con el segmento de clientes profesionales.

### Métrica 2: Prima de Conectividad (CP)
* **Fórmula:** `Rating Promedio (Wi-Fi Gratis) - Rating Promedio Global`
* **Propósito:** Cuantificar exactamente cuánto valor (en estrellas de calificación) añade al negocio la inversión en conectividad de alta velocidad.
* **Valor Actual:** Basado en los datos actuales, la Prima de Conectividad es de **+0.16 estrellas**.

## 4. Implementación Técnica (SQL)
A continuación, se presentan las consultas desarrolladas para extraer las métricas de la Fase 03:

### Cálculo de KPIs (PEI y CP)
```sql
-- 1. Professional Engagement Index (PEI)
-- Ratio de actividad laborable vs fin de semana
SELECT 
    ROUND(
        (SELECT COUNT(*) FROM review WHERE strftime('%w', date) NOT IN ('0', '6')) * 1.0 / 
        (SELECT COUNT(*) FROM review WHERE strftime('%w', date) IN ('0', '6')), 
    2) AS professional_engagement_index;

-- 2. Connectivity Premium (CP)
-- Impacto del Wi-Fi gratuito frente a la media global
WITH GlobalAvg AS (
    SELECT AVG(stars) AS global_mean FROM business
),
WiFiAvg AS (
    SELECT AVG(stars) AS wifi_mean FROM business WHERE "attributes.WiFi" LIKE '%free%'
)
SELECT 
    ROUND(wifi_mean - global_mean, 2) AS connectivity_premium
FROM WiFiAvg, GlobalAvg;

-- 3. EXPLORACIÓN PARA TF-IDF (Frecuencia de términos)
-- Como SQLite no tiene una función nativa de TF-IDF, preparamos la extracción
-- de las reviews de los locales de "Élite" para un futuro procesamiento en Python/Spark.
SELECT 
    b.name,
    r.text
FROM business b
JOIN review r ON b.business_id = r.business_id
WHERE b.stars >= 3.8 AND "attributes.WiFi" LIKE '%free%'
LIMIT 10;
```

