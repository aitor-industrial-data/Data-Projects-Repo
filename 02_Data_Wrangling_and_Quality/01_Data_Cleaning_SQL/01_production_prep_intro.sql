/*******************************************************************************
RUTA DE INGENIERÍA DE DATOS - MES 2: SQL Avanzado y Wrangling
DÍA 46: Wrangling Intro - Preparación de Datos para Producción
*******************************************************************************
Objetivo: 
    Auditar la integridad de la tabla 'customer' y crear una vista robusta 
    y limpia para sistemas de producción.

Herramientas: SQLite (DB Browser / DBeaver)
Base de Datos: Chinook (Nombres de tablas en singular)
*******************************************************************************/

-- =============================================================================
-- PASO 1: PERFILADO DE DATOS (Diagnóstico) 
-- Antes de limpiar, debemos entender qué tan "sucios" están los datos crudos.
-- =============================================================================

-- 1.1. Verificación de NULOS en columnas críticas (Integridad/Completitud)
-- Necesitamos saber cuántos clientes no tienen información en el campo 'State'.
SELECT 
    COUNT(*) as Total_Customers,
    COUNT(State) as Customers_With_State,
    COUNT(*) - COUNT(State) as Missing_State_Count
FROM customer;

-- 1.2. Verificación de estandarización en nombres de países (Consistencia)
-- Identifica si el mismo país está escrito de formas distintas (ej. USA vs U.S.A.).
SELECT 
    Country, 
    COUNT(*) as Frequency
FROM customer
GROUP BY Country
ORDER BY Country;

-- 1.3. Verificación de correos electrónicos potencialmente inválidos (Validez)
-- Validación básica para asegurar que el string del email sigue un patrón estándar.
SELECT 
    Email 
FROM customer 
WHERE Email NOT LIKE '%@%' OR Email NOT LIKE '%.%';


-- =============================================================================
-- PASO 2: TRANSFORMACIÓN DE DATOS (Wrangling) 
-- Creamos una "Capa Dorada" (Vista Limpia) para los usuarios finales o sistemas.
-- =============================================================================

/* REGLA DE IDEMPOTENCIA: 
   Eliminamos la vista si ya existe para asegurar que cada vez que ejecutemos 
   este script, se aplique la versión más reciente de nuestra lógica de limpieza.
*/
DROP VIEW IF EXISTS V_Customers_Clean;

-- Creación de la vista preparada para producción
CREATE VIEW V_Customers_Clean AS
SELECT 
    CustomerId,
    -- Requisito 1: Crear una columna de nombre completo para reportes directos
    FirstName || ' ' || LastName as Full_Name,
    
    -- Requisito 2: Asegurar que los emails estén en minúsculas para evitar duplicados visuales
    LOWER(Email) as Normalized_Email,
    
    -- Requisito 3: Gestión de Nulos. En producción, 'Unknown' es mejor que NULL para filtros. 
    COALESCE(State, 'Unknown') as State_Clean,
    
    Country
FROM customer;


-- =============================================================================
-- PASO 3: CONTROL DE CALIDAD (Verificación de Resultados)
-- =============================================================================

-- Consultamos la nueva vista para asegurar que las transformaciones funcionen.
SELECT * FROM V_Customers_Clean 
LIMIT 10;
