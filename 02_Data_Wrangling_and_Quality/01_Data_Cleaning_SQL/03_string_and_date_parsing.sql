/*******************************************************************************
RUTA DE INGENIERÍA DE DATOS - MES 2: SQL Avanzado y Wrangling
DÍA 48: Parsing - Limpieza de Strings y Fechas
*******************************************************************************
Objetivo: 
    Normalizar columnas de texto desordenadas (Teléfonos) y extraer información
    útil de columnas compuestas (Emails y Fechas).

Lógica Aplicada:
    1. Phone: REPLACE anidado para eliminar caracteres basura '() -'.
    2. Email: SUBSTR + INSTR para cortar el dominio.
    3. Date: STRFTIME para extraer componentes temporales.
*******************************************************************************/

-- =============================================================================
-- 1. LIMPIEZA DE TELÉFONOS (Standardization)
-- =============================================================================
/* PROBLEMA: Los teléfonos tienen formatos mixtos: (123) 456-7890 vs 123.456.7890
   SOLUCIÓN: Eliminar todo lo que no sea número o '+'.
   NOTA: SQLite no tiene REGEXP_REPLACE nativo fácil, usamos REPLACE anidado.
*/

SELECT 
    Phone as Raw_Phone,
    -- Pseudocódigo: Reemplaza '(', ')', '-' y ' ' por vacío.
    REPLACE(REPLACE(REPLACE(REPLACE(Phone, '(', ''), ')', ''), '-', ''), ' ', '') as Normalized_Phone
FROM customer
WHERE Phone IS NOT NULL
LIMIT 10;

-- =============================================================================
-- 2. PARSING DE EMAILS (Domain Extraction)
-- =============================================================================
/*
   PROBLEMA: Queremos analizar clientes por "Empresa" (Dominio del email).
   LÓGICA: 
     1. Encontrar la posición del '@' --> INSTR(Email, '@')
     2. Cortar desde esa posición + 1 hasta el final --> SUBSTR(...)
*/

SELECT 
    Email,
    SUBSTR(Email, INSTR(Email, '@') + 1) as Email_Domain
FROM customer
LIMIT 10;

-- =============================================================================
-- 3. CREACIÓN DE VISTA DE PRODUCCIÓN (Staging Layer)
-- Juntamos todo lo aprendido en una vista limpia para el analista.
-- =============================================================================

DROP VIEW IF EXISTS V_Customer_Enriched;

CREATE VIEW V_Customer_Enriched AS
SELECT 
    CustomerId,
    -- Limpieza de Nombre
    FirstName || ' ' || LastName as Full_Name,
    
    -- Limpieza de Teléfono
    REPLACE(REPLACE(REPLACE(REPLACE(Phone, '(', ''), ')', ''), '-', ''), ' ', '') as Clean_Phone,
    
    -- Extracción de Dominio
    SUBSTR(Email, INSTR(Email, '@') + 1) as Email_Domain,
    
    -- Estandarización de País (Ejemplo simple: Mayúsculas)
    UPPER(Country) as Country_Code
FROM customer;

-- Verificación final
SELECT * FROM V_Customer_Enriched LIMIT 5;

-- =============================================================================
-- 4. ANÁLISIS DE FECHAS (Temporal Parsing)
-- Usamos la tabla 'invoice' para ver ventas por año.
-- =============================================================================

SELECT 
    STRFTIME('%Y', InvoiceDate) as Sales_Year,
    STRFTIME('%m', InvoiceDate) as Sales_Month,
    SUM(Total) as Total_Revenue
FROM invoice
GROUP BY 1, 2 -- Agrupar por Año y Mes
ORDER BY 1 DESC, 2 DESC;