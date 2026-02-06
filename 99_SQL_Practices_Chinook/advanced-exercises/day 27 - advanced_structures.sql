/*******************************************************************************
  DATA ENGINEERING - DÍA 26: ESTRUCTURAS AVANZADAS Y ANÁLISIS DE RETENCIÓN
  Foco: Acoplamiento de Temp Tables y Views para análisis histórico.
  Base de Datos: Chinook (SQLite)
*******************************************************************************/

-- =============================================================================
-- PROBLEMA: INFORME DE REACTIVACIÓN Y RIESGO DE FUGA (CHURN)
-- Enunciado: Identificar clientes que gastaron >30$ en 2009-2010 pero han 
-- disminuido su gasto en el periodo reciente (2012-2013).
-- =============================================================================

/* ANOTACIÓN TÉCNICA (CAPA DE STAGING):
   Usamos una Tabla Temporal para "congelar" la métrica histórica. 
   Esto evita que el motor de la base de datos tenga que recalcular el 
   pasado cada vez que consultamos la vista de riesgo. 
*/

DROP TABLE IF EXISTS Temp_Historical_Top_Customers;

CREATE TEMP TABLE Temp_Historical_Top_Customers AS
SELECT 
    c.CustomerId,
    SUM(i.Total) AS Total_2009_2010
FROM Customer c
INNER JOIN Invoice i ON c.CustomerId = i.CustomerId
WHERE i.InvoiceDate BETWEEN '2009-01-01' AND '2010-12-31'
GROUP BY c.CustomerId
HAVING Total_2009_2010 > 30;


/* ANOTACIÓN TÉCNICA (CAPA DE PRESENTACIÓN):
   1. Usamos LEFT JOIN: Es vital para no perder a los clientes que gastaron 0$ 
      en el periodo reciente. Un INNER JOIN los borraría del informe.
   2. CASE WHEN: Filtramos las fechas dentro del SUM para mantener la 
      integridad del JOIN y evitar que el WHERE elimine los registros NULL.
   3. COALESCE/CASE: Aseguramos que si no hay ventas, el valor sea 0 y no NULL 
      para poder realizar la resta aritmética (Diff).
*/



DROP VIEW IF EXISTS View_Customer_Retention_Risk;

CREATE VIEW View_Customer_Retention_Risk AS
SELECT  
    c.FirstName || ' ' || c.LastName AS Customer_Name,
    thtc.Total_2009_2010 AS Historic_Revenue,
    
    -- Gasto en el periodo reciente (2012-2013)
    ROUND(SUM(CASE 
        WHEN i.InvoiceDate BETWEEN '2012-01-01' AND '2013-12-31' 
        THEN i.Total ELSE 0 
    END), 2) AS Recent_Revenue,
    
    -- Cálculo de la caída de ingresos (Diferencia)
    ROUND(thtc.Total_2009_2010 - SUM(CASE 
        WHEN i.InvoiceDate BETWEEN '2012-01-01' AND '2013-12-31' 
        THEN i.Total ELSE 0 
    END), 2) AS Revenue_Drop
    
FROM Customer c 
INNER JOIN Temp_Historical_Top_Customers thtc ON c.CustomerId = thtc.CustomerId
LEFT JOIN Invoice i ON c.CustomerId = i.CustomerId
GROUP BY c.CustomerId, Customer_Name;

-- Ejecución del análisis para detección de alertas
SELECT * FROM View_Customer_Retention_Risk 
ORDER BY Revenue_Drop DESC;


-- =============================================================================
-- REGLAS DE ORO APLICADAS EN ESTE SCRIPT:
-- =============================================================================
/* 1. INDEPENDENCIA TEMPORAL: Se ajustaron las fechas al contexto real de la 
      DB (2009-2013) evitando errores de "dataset vacío".
   2. TRATAMIENTO DE NULOS: El uso de lógica condicional en el SUM garantiza 
      que los cálculos matemáticos no devuelvan NULL.
   3. ARQUITECTURA: La View depende de la Temp Table para cumplir con un 
      flujo de trabajo de sesión única (Ad-hoc reporting).
*/