/*******************************************************************************
RUTA DE INGENIERÍA DE DATOS - MES 2: SQL Avanzado y Wrangling
DÍA 47: Limpieza - Scripts Avanzados para Detectar y Borrar Duplicados
*******************************************************************************
Objetivo: 
    Implementar una estrategia de deduplicación profesional para asegurar
    que cada cliente sea único basado en su Email.

Hito: Datos únicos y fiables para producción.
Base de Datos: Chinook (Columnas en singular).
*******************************************************************************/

-- =============================================================================
-- PASO 1: DETECCIÓN (Profiling de Duplicados)
-- Antes de limpiar, necesitamos saber la magnitud del problema.
-- =============================================================================

-- Buscamos emails que se repiten. 
-- Si el conteo es > 1, tenemos un problema de integridad.
SELECT 
    Email, 
    COUNT(*) as Repeticiones
FROM customer
GROUP BY Email
HAVING COUNT(*) > 1
ORDER BY Repeticiones DESC;


-- =============================================================================
-- PASO 2: ESTRATEGIA DE NUMERACIÓN (Window Functions)
-- Usamos ROW_NUMBER() para "etiquetar" los registros.
-- El registro 1 será el "Original" (el CustomerId más antiguo).
-- El registro 2 o superior será considerado "Duplicado".
-- =============================================================================

SELECT 
    CustomerId, 
    FirstName, 
    LastName, 
    Email,
    ROW_NUMBER() OVER (
        PARTITION BY Email           -- Agrupamos por lo que debería ser único
        ORDER BY CustomerId ASC      -- Criterio: nos quedamos con el ID más bajo
    ) as row_num
FROM customer;


-- =============================================================================
-- PASO 3: CREACIÓN DE CAPA DE PRODUCCIÓN (Deduplicación Lógica)
-- En ingeniería de datos profesional, NO borramos la tabla 'customer'.
-- Creamos una Vista que filtra los duplicados automáticamente.
-- =============================================================================

-- 3.1. Idempotencia: Limpieza del entorno
DROP VIEW IF EXISTS V_Customer_Unique;

-- 3.2. Creación de la Vista con CTE (Common Table Expression)
CREATE VIEW V_Customer_Unique AS
WITH Duplicate_CTE AS (
    SELECT 
        *,
        ROW_NUMBER() OVER (
            PARTITION BY Email 
            ORDER BY CustomerId ASC
        ) as rn
    FROM customer
)
SELECT 
    CustomerId,
    FirstName,
    LastName,
    Company,
    Address,
    City,
    State,
    Country,
    PostalCode,
    Phone,
    Fax,
    Email,
    SupportRepId
FROM Duplicate_CTE
WHERE rn = 1; -- Filtro: Solo el primer registro de cada grupo de email


-- =============================================================================
-- PASO 4: CONTROL DE CALIDAD (QA)
-- Verificamos que el producto final (la Vista) sea correcto.
-- =============================================================================

-- Comprobamos si la Vista aún tiene duplicados (Debería devolver 0 filas)
SELECT 
    Email, 
    COUNT(*) 
FROM V_Customer_Unique
GROUP BY Email
HAVING COUNT(*) > 1;

-- Visualizamos los datos listos para el negocio
SELECT * FROM V_Customer_Unique LIMIT 10;

/*******************************************************************************
NOTAS TÉCNICAS PARA EL PORTFOLIO:
- Se utilizó la técnica de 'Logical Deletion' mediante Vistas.
- La Window Function ROW_NUMBER() permite una deduplicación escalable.
- Este proceso es IDEMPOTENTE y seguro para pipelines de producción.
*******************************************************************************/