/*
================================================================================
PROYECTO FINAL: Data Scientist en el USDA (Departamento de Agricultura de EE. UU.)
FASE 3: Análisis de Datos y Business Insights
================================================================================
ESCENARIO:
Análisis de producción agrícola para decisiones estratégicas del USDA.
DATASETS: milk_production, cheese_production, coffee_production, honey_production,
egg_production, yogurt_production y state_lookup.
================================================================================
*/

-- -----------------------------------------------------------------------------
-- PREGUNTA 1
-- ENUNCIADO: ¿Puede averiguar la producción total de leche para 2023? 
-- -----------------------------------------------------------------------------
-- Usamos SUM() para agregar todos los valores del año fiscal solicitado.
SELECT SUM(mp.Value) AS Total_Milk_2023
FROM milk_production mp 
WHERE mp.Year = 2023;

-- PREGUNTA: ¿Cuál es la producción total de leche para 2023?
-- RESPUESTA: 91812000000


-- -----------------------------------------------------------------------------
-- PREGUNTA 2
-- ENUNCIADO: ¿Qué estados tuvieron una producción de queso superior a 100 millones 
-- en abril de 2023?
-- -----------------------------------------------------------------------------
-- El INNER JOIN asegura que solo mostramos estados que existen en la tabla maestra.
-- HAVING es clave aquí para filtrar DESPUÉS de realizar la suma (agregación).
SELECT 
    sl.State, 
    SUM(cp.Value) AS Total_Production
FROM cheese_production cp
INNER JOIN state_lookup sl ON cp.State_ANSI = sl.State_ANSI
WHERE cp.Year = 2023 
  AND cp.Period = 'APR'
GROUP BY sl.State
HAVING Total_Production > 100000000;

-- PREGUNTA: ¿Cuántos estados hay?
-- RESPUESTA: 2


-- -----------------------------------------------------------------------------
-- PREGUNTA 3
-- ENUNCIADO: ¿Cómo ha cambiado la producción de café a lo largo de los años? 
-- -----------------------------------------------------------------------------
SELECT SUM(cp.Value) AS Total_Coffee_2011
FROM coffee_production cp 
WHERE cp.Year = 2011;

-- PREGUNTA: ¿Cuál es el valor total de la producción de café en 2011?
-- RESPUESTA: 7600000


-- -----------------------------------------------------------------------------
-- PREGUNTA 4
-- ENUNCIADO: Producción media de miel para 2022.
-- -----------------------------------------------------------------------------
-- AVG() calcula la media aritmética de los reportes estatales de ese año.
SELECT AVG(hp.Value) AS Avg_Honey_2022
FROM honey_production hp 
WHERE hp.Year = 2022;

-- PREGUNTA: ¿Cuál es la producción media de miel para 2022?
-- RESPUESTA: 3133275


-- -----------------------------------------------------------------------------
-- PREGUNTA 5
-- ENUNCIADO: Nombres de estados con sus correspondientes códigos ANSI.
-- -----------------------------------------------------------------------------
SELECT State, State_ANSI
FROM state_lookup
WHERE State = 'FLORIDA';

-- PREGUNTA: ¿Cuál es el código State_ANSI de Florida?
-- RESPUESTA: 12


-- -----------------------------------------------------------------------------
-- PREGUNTA 6
-- ENUNCIADO: Lista de todos los estados con su producción de queso, aunque sea 0.
-- -----------------------------------------------------------------------------
-- El LEFT JOIN mantiene todos los estados de la tabla 'sl' aunque no tengan datos.
-- COALESCE cambia los valores NULL resultantes por un '0' para un informe limpio.
SELECT 
    sl.State, 
    COALESCE(SUM(cp.Value), 0) AS Cheese_Value
FROM state_lookup sl
LEFT JOIN cheese_production cp ON sl.State_ANSI = cp.State_ANSI 
    AND cp.Year = 2023 
    AND cp.Period = 'APR'
WHERE sl.State = 'NEW JERSEY'
GROUP BY sl.State;

-- PREGUNTA: ¿Cuál es el total para NUEVA JERSEY?
-- RESPUESTA: 4889000


-- -----------------------------------------------------------------------------
-- PREGUNTA 7
-- ENUNCIADO: Producción total de yogur (2022) en estados activos en queso (2023).
-- -----------------------------------------------------------------------------
-- Usamos una SUBQUERY para identificar estados con infraestructura láctea activa.
SELECT SUM(yp.Value) AS Total_Yogurt_2022
FROM yogurt_production yp
WHERE yp.Year = 2022
  AND yp.State_ANSI IN (
    SELECT DISTINCT State_ANSI 
    FROM cheese_production 
    WHERE Year = 2023
  );

-- PREGUNTA: ¿Cuál es la producción total de yogur bajo estos criterios?
-- RESPUESTA: 1154233000


-- -----------------------------------------------------------------------------
-- PREGUNTA 8
-- ENUNCIADO: Estados que faltan en milk_production en 2023.
-- -----------------------------------------------------------------------------
-- NOT IN identifica brechas (gaps) en los reportes anuales.
SELECT COUNT(DISTINCT sl.State_ANSI) AS Missing_States
FROM state_lookup sl 
WHERE sl.State_ANSI NOT IN (
    SELECT mp.State_ANSI 
    FROM milk_production mp 
    WHERE mp.Year = 2023
);

-- PREGUNTA: ¿Cuántos estados hay?
-- RESPUESTA: 26


-- -----------------------------------------------------------------------------
-- PREGUNTA 9
-- ENUNCIADO: Producción de queso por estado (abril 2023), incluyendo los de valor 0.
-- -----------------------------------------------------------------------------
SELECT sl.State, cp.Value 
FROM state_lookup sl
LEFT JOIN cheese_production cp ON sl.State_ANSI = cp.State_ANSI 
    AND cp.Year = 2023 
    AND cp.Period = 'APR'
WHERE sl.State = 'DELAWARE';

-- PREGUNTA: ¿Produjo Delaware algún queso en abril de 2023?
-- RESPUESTA: No


-- -----------------------------------------------------------------------------
-- PREGUNTA 10
-- ENUNCIADO: Producción media de café en años con alta producción de miel (>1M).
-- -----------------------------------------------------------------------------
-- Combinación de agregación y subconsulta para correlacionar dos commodities.
SELECT AVG(cp.Value) AS Avg_Coffee_Production
FROM coffee_production cp 
WHERE cp.Year IN (
    SELECT hp.Year 
    FROM honey_production hp 
    GROUP BY hp.Year
    HAVING SUM(hp.Value) > 1000000
);

-- PREGUNTA: ¿Cuál es el valor medio resultante?
-- RESPUESTA: 6426666.666666667