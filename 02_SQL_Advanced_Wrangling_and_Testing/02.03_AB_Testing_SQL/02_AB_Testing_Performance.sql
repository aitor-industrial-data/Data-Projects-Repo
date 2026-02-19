/*******************************************************************************
  RUTA DE INGENIERÍA DE DATOS - 02_SQL_Advanced_Wrangling_and_Testing
  A/B Testing II - Medición de KPIs (Capa GOLD)
  Objetivo: Determinar mediante KPIs qué grupo genera mayor rentabilidad y conversión.
*******************************************************************************/

/* ENUNCIADO:
  Evaluar el rendimiento del experimento A/B comparando el comportamiento de compra
  entre el Grupo A (Control) y el Grupo B (Variante). 
  
  REQUERIMIENTOS TÉCNICOS:
  1. Cruzar la segmentación de la capa GOLD con la tabla de ventas (invoice).
  2. Calcular el Volumen de Usuarios, Pedidos e Ingresos Totales por grupo.
  3. Calcular el ARPU (Average Revenue Per User) para determinar la rentabilidad.
*/

-- 1. ANÁLISIS DE RENDIMIENTO Y KPIs
-- Usamos LEFT JOIN para incluir a todos los usuarios del test, incluso si no compraron.
-- Esto es vital para que el cálculo del ARPU sea estadísticamente honesto.

SELECT 
    seg.test_group,
    COUNT(DISTINCT seg.CustomerId) AS total_usuarios,
    COUNT(i.InvoiceId) AS numero_pedidos,
    ROUND(SUM(i.Total), 2) AS ingresos_totales,
    -- KPI Crítico: Gasto Promedio por Usuario (ARPU)
    -- Nos indica cuánto valor aporta cada individuo asignado al grupo.
    ROUND(SUM(i.Total) / COUNT(DISTINCT seg.CustomerId), 2) AS arpu
FROM V_Gold_AB_Test_Segmentation seg
LEFT JOIN invoice i ON seg.CustomerId = i.CustomerId
GROUP BY seg.test_group;

/*
  ANOTACIONES TÉCNICAS:
  - Integración: Se utiliza la vista 'V_Gold_AB_Test_Segmentation' como base. 
  - Lógica de Negocio: El uso de LEFT JOIN asegura que el denominador del ARPU 
    incluya a toda la muestra, evitando el sesgo de supervivencia. 
  - Hito: Este análisis cierra la etapa de SQL Problem Solving de 
    UC Davis, preparando el terreno para la escalabilidad en Spark. 
*/