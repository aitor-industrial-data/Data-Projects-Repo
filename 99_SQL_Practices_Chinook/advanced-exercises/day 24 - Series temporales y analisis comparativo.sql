/*******************************************************************************
  MASTER CLASS SQL - DÍA 24: SERIES TEMPORALES Y ANÁLISIS COMPARATIVO
  Autor: Aitor (Ingeniero Técnico Industrial / Data Engineer Trainee)
  Base de Datos: Chinook (SQLite)
  
  RESUMEN: Dominio de la función strftime() y subconsultas correlacionadas 
  aplicadas a la dimensión temporal.
*******************************************************************************/

-- =============================================================================
-- 1. LA CAJA DE HERRAMIENTAS: strftime()
-- =============================================================================
/* En SQLite, las fechas son textos. Usamos strftime para "trocearlas".
   %Y -> Año (2010)
   %m -> Mes (01, 02...)
   %d -> Día
   %Y-%m -> Formato de periodo (Ideal para agrupaciones)
*/

-- Ejemplo rápido de extracción:
SELECT 
    InvoiceId,
    InvoiceDate,
    strftime('%Y-%m', InvoiceDate) AS Periodo,
    strftime('%W', InvoiceDate) AS Semana_Del_Año
FROM Invoice;


-- =============================================================================
-- 2. ANÁLISIS MoM (Month over Month) - COMPARACIÓN ESTÁTICA
-- =============================================================================
/* OBJETIVO: ¿Superamos en Marzo de 2023 lo que se hizo en Febrero de 2023?
   LÓGICA: Usamos una subconsulta escalar para fijar el valor del mes anterior
   y compararlo fila por fila con el mes actual.
*/

SELECT 
    i.InvoiceId,
    i.InvoiceDate,
    i.Total, 
    -- Valor de referencia fijo (Media de Feb 2023)
    (SELECT ROUND(AVG(i1.Total), 2)
     FROM Invoice i1
     WHERE strftime('%Y-%m', i1.InvoiceDate) = '2023-02') AS Media_Feb_2010
FROM Invoice i
WHERE strftime('%Y-%m', i.InvoiceDate) = '2023-03'
  AND i.Total > (SELECT AVG(i1.Total) 
                 FROM Invoice i1 
                 WHERE strftime('%Y-%m', i1.InvoiceDate) = '2023-02');


-- =============================================================================
-- 3. ANÁLISIS DE ESTACIONALIDAD (Correlación por Mes)
-- =============================================================================
/* OBJETIVO: Buscar facturas que destacan sobre la media histórica de su mes.
   PUENTE: 'strftime('%m', i1.InvoiceDate) = strftime('%m', i.InvoiceDate)'
   EXPLICACIÓN: Si la factura es de Mayo, la subconsulta calcula la media de 
   TODOS los Mayos de la historia de la base de datos.
*/



SELECT 
    i.InvoiceId,
    i.InvoiceDate,
    i.Total,
    ROUND((SELECT AVG(i1.Total)
           FROM Invoice i1
           WHERE strftime('%m', i1.InvoiceDate) = strftime('%m', i.InvoiceDate)), 2) AS Media_Historica_Mes
FROM Invoice i
WHERE i.Total > (SELECT AVG(i1.Total)
                FROM Invoice i1
                WHERE strftime('%m', i1.InvoiceDate) = strftime('%m', i.InvoiceDate));


-- =============================================================================
-- 4. EL FILTRO DE PRECISIÓN (Mismo Mes y Mismo Año)
-- =============================================================================
/* OBJETIVO: Detectar "Outliers" o ventas excepcionales dentro de su propio mes.
   LÓGICA: Doble acoplamiento (Mes y Año). Es el nivel más alto de filtrado local.
   USO: Identificar qué facturas tiraron del carro en un mes específico.
*/

SELECT 
    i.InvoiceId,
    i.InvoiceDate,
    i.Total,
    ROUND((SELECT AVG(i1.Total)
           FROM Invoice i1
           WHERE strftime('%m', i1.InvoiceDate) = strftime('%m', i.InvoiceDate)
             AND strftime('%Y', i1.InvoiceDate) = strftime('%Y', i.InvoiceDate)
          ), 2) AS Promedio_Mes_Actual
FROM Invoice i
WHERE i.Total > (SELECT AVG(i1.Total)
                FROM Invoice i1
                WHERE strftime('%m', i1.InvoiceDate) = strftime('%m', i.InvoiceDate)
                  AND strftime('%Y', i1.InvoiceDate) = strftime('%Y', i.InvoiceDate)
);


/*******************************************************************************
  CONCLUSIONES TÉCNICAS (PARA EL PORTFOLIO):
  
  1. EFICIENCIA: Las subconsultas correlacionadas en el WHERE son potentes pero 
     costosas (se ejecutan N veces). Para tablas masivas, se recomienda usar 
     Window Functions (OVER / PARTITION BY) que veremos en el Mes 2.
     
  2. ESCALABILIDAD: Al usar strftime(), estamos preparados para agrupar datos 
     sin importar si la base de datos crece con años nuevos.
     
  3. APLICACIÓN REAL: Este tipo de consultas son la base para crear Dashboards 
     de rendimiento empresarial y detección de anomalías.
*******************************************************************************/