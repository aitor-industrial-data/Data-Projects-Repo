/*******************************************************************************
HITO DÍA 50: SCRIPT DE LIMPIEZA AUTOMÁTICA (PIPELINE SQL)
Autor: Aitor - Ingeniero Técnico Industrial & Data Engineer Pro
Descripción: Pipeline de dos capas para la normalización total de clientes.
*******************************************************************************/

-- =============================================================================
-- CAPA 1: STAGING (Limpieza de "Materia Prima")
-- Responsabilidad: Formatos, Nulos y Tipos.
-- =============================================================================

DROP VIEW IF EXISTS V_Staging_Customer;

CREATE VIEW V_Staging_Customer AS
SELECT 
    CustomerId,
    -- Parsing: Nombres limpios y en mayúsculas para consistencia
    UPPER(FirstName) as FirstName,
    UPPER(LastName) as LastName,
    
    -- Parsing: Normalización de Emails (siempre minúsculas)
    LOWER(Email) as Email,
    
    -- Wrangling: Gestión de Nulos
    COALESCE(Company, 'Individual') as Company,
    COALESCE(State, 'N/A') as State,
    
    -- Parsing: Teléfonos sin caracteres especiales
    REPLACE(REPLACE(REPLACE(REPLACE(Phone, '(', ''), ')', ''), '-', ''), ' ', '') as Clean_Phone,
    
    Country
FROM customer;

-- =============================================================================
-- CAPA 2: PRODUCTION (Lógica de Negocio y Unicidad)
-- Responsabilidad: Deduplicación y Transformación CASE.
-- =============================================================================

DROP VIEW IF EXISTS V_Final_Customer_Clean;

CREATE VIEW V_Final_Customer_Clean AS
WITH Deduplicated AS (
    SELECT 
        *,
        -- Transformación: Regiones por continente (Lógica CASE)
        CASE 
            WHEN Country IN ('USA', 'Canada') THEN 'North America'
            WHEN Country IN ('Brazil', 'Argentina', 'Chile') THEN 'LATAM'
            WHEN Country IN ('India', 'Australia') THEN 'APAC'
            ELSE 'EMEA'
        END as Territory,
        
        -- Deduplicación Pro: Solo un registro por Email
        ROW_NUMBER() OVER (
            PARTITION BY Email 
            ORDER BY CustomerId ASC
        ) as row_num
    FROM V_Staging_Customer
)
SELECT 
    CustomerId,
    FirstName,
    LastName,
    Email,
    Company,
    Clean_Phone,
    Territory,
    Country,
    State
FROM Deduplicated
WHERE row_num = 1; -- Solo datos únicos y fiables

-- =============================================================================
-- VERIFICACIÓN TÉCNICA (QA)
-- =============================================================================

-- 1. ¿Hay duplicados? (Debe dar 0)
SELECT Email, COUNT(*) FROM V_Final_Customer_Clean GROUP BY 1 HAVING COUNT(*) > 1;

-- 2. ¿Hay nulos en Company? (Debe dar 0)
SELECT COUNT(*) FROM V_Final_Customer_Clean WHERE Company IS NULL;

-- 3. Muestra final
SELECT * FROM V_Final_Customer_Clean LIMIT 10;