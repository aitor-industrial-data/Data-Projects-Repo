/*******************************************************************************
PROYECTO: "The Great Cleaner"
FASE 1: 01_Silver_Customer_Cleansing.sql  (Silver Layer / Perfilado y Estandarización)
OBJETIVO: Normalizar la tabla 'Customer' de Chinook para eliminar ruido en 
          datos de contacto y segmentar el tipo de cliente (B2B/B2C).
AUTOR: AITOR / Ingeniero Técnico Industrial / Data Engineer
*******************************************************************************/

-- 1. Eliminar la vista si ya existe para permitir re-ejecución del script (Idempotencia)
DROP VIEW IF EXISTS V_Silver_Clean_Customer_Roster;

-- 2. Creación de la vista de limpieza de datos
CREATE VIEW V_Silver_Clean_Customer_Roster AS
SELECT
    -- Mantener la PK original para facilitar JOINs posteriores
    c.CustomerId,

    -- Transformación: Nombre completo en mayúsculas para estandarización de reportes
    UPPER(c.FirstName || ' ' || c.LastName) AS Full_Name,

    -- Lógica de Negocio: Clasificación de clientes
    -- Si 'Company' es NULL, se asume cliente final (B2C), de lo contrario es empresa (B2B)
    CASE
        WHEN c.Company IS NULL THEN 'B2C Customer'
        ELSE 'B2B Customer'
    END AS Company,

    -- Manejo de Nulos: Uso de COALESCE para asegurar que no haya valores vacíos en el set de datos
    COALESCE(c.Address, 'Unknown') AS Address,
    COALESCE(c.City, 'Unknown') AS City,
    COALESCE(c.State, 'Unknown') AS State,
    COALESCE(c.Country, 'Unknown') AS Country,
    COALESCE(c.PostalCode, 'Unknown') AS PostalCode,

    -- Limpieza de Strings: Eliminación de '(', ')', '-', y espacios en el teléfono
    -- Esto es crucial para procesos de integración con APIs de SMS o CRM
    COALESCE(
        REPLACE(
            REPLACE(
                REPLACE(
                    REPLACE(c.Phone, '(', ''), 
                ')', ''), 
            '-', ''), 
        ' ', ''), 
    'Unknown') AS Phone,

    COALESCE(c.Fax, 'Unknown') AS Fax,
    COALESCE(c.Email, 'Unknown') AS Email,
    
    -- FK para relación con la tabla de empleados (Sales Support)
    c.SupportRepId	
FROM Customer c;

-- Notas adicionales para el Portfolio:
-- Esta vista actúa como una capa de "Silver Zone" o limpieza, 
-- asegurando que los analistas de datos consuman información pre-procesada.