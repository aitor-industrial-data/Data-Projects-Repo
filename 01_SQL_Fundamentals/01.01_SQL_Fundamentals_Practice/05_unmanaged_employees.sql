--------------------------------------------------------------------------------
-- 05_unmanaged_employees.sql
-- AUTOR: Aitor | Ingeniero Técnico Industrial | Data Engineer
-- PROYECTO: Chinook Database (Singular Schema)
--------------------------------------------------------------------------------

/* ENUNCIADO:
   Listar de forma única los cargos (Title) y nombres de los empleados que:
   1. Son líderes de la organización (No tienen jefe / ReportsTo IS NULL).
   2. Fueron contratados después del año 2000.
   3. Tienen una ciudad de residencia asignada (City IS NOT NULL).
   
   Ordenar por fecha de contratación (HireDate) de forma descendente.
*/

SELECT DISTINCT
    FirstName,
    LastName,
    Title,
    HireDate,
    City
FROM Employee
WHERE ReportsTo IS NULL
  AND HireDate > '2000-01-01'
  AND City IS NOT NULL
ORDER BY HireDate DESC;

--------------------------------------------------------------------------------
-- ANOTACIONES TÉCNICAS Y FUNDAMENTOS:
-- 1. Gestión de Nulos (IS NULL / IS NOT NULL): Se aplican ambos fundamentos 
--    para identificar la jerarquía superior y garantizar la calidad del dato.
-- 2. Filtrado de Fechas: Uso del estándar ISO para asegurar que solo se 
--    muestren contrataciones del nuevo milenio.
-- 3. Unicidad con DISTINCT: Aunque los nombres suelen ser únicos, se aplica 
--    para asegurar que el set de resultados no contenga filas redundantes.
-- 4. Ordenamiento Temporal: Se prioriza la visualización de los líderes con 
--    incorporación más reciente (Fundamento ORDER BY DESC).
-- 5. Perfil de Datos: Como ingeniero, este reporte te permite auditar quiénes 
--    toman las decisiones en la empresa y desde cuándo.
--------------------------------------------------------------------------------