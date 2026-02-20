--------------------------------------------------------------------------------
-- 15_client_location_cleanup.sql
-- AUTOR: Aitor | Ingeniero Técnico Industrial | Data Engineer
-- PROYECTO: Chinook Database (Singular Schema)
--------------------------------------------------------------------------------

/* ENUNCIADO:
   Generar un reporte de auditoría de clientes que han realizado compras de alto 
   valor (>10$) en el periodo 2024-2025, estandarizando la información de contacto.
   
   Consideraciones de ingeniería:
   1. Normalización: Mostrar el nombre completo en mayúsculas (Client_Identity).
   2. Limpieza de Nulos: Si el Estado (State) es NULL, mostrar 'N/A'.
   3. Gestión de Datos Faltantes: Si el Fax es NULL, mostrar 'NO FAX'.
   4. Integridad Geográfica: Concatenar dirección, ciudad y país en 'Full_Location'.
   5. Filtrado de Negocio: Solo clientes con gasto acumulado superior a 10$ 
      en el rango de fechas 2024-2025.
*/

SELECT
    UPPER(c.FirstName || ' ' || c.LastName) AS Client_Identity,
    c.Address || ', ' || c.City || ', ' || c.Country AS Full_Location,
    COALESCE(c.State, 'N/A') AS Province_Status,
    COALESCE(c.Fax, 'NO FAX') AS Fax_Status,
    SUM(i.Total) AS Total_Spent
FROM Customer c
JOIN Invoice i ON c.CustomerId = i.CustomerId
WHERE i.InvoiceDate BETWEEN '2024-01-01' AND '2025-12-31'
GROUP BY c.CustomerId
HAVING SUM(i.Total) > 10
ORDER BY Total_Spent DESC;

--------------------------------------------------------------------------------
-- ANOTACIONES TÉCNICAS Y FUNDAMENTOS:
-- 1. Gestión de Nulos (COALESCE): Fundamental en Data Quality. Permite que las 
--    herramientas de reporte o BI no fallen al encontrar valores vacíos.
-- 2. Concatenación de Strings: El uso de '||' permite crear campos calculados 
--    más descriptivos para el usuario final (Data Transformation).
-- 3. Lógica de Filtrado Agregado (HAVING): A diferencia del WHERE, el HAVING 
--    actúa sobre el resultado del SUM, permitiendo filtrar segmentos de clientes.
-- 4. Rango de Fechas: El uso de BETWEEN con strings ISO ('YYYY-MM-DD') es el 
--    estándar para asegurar la compatibilidad entre diferentes motores SQL.
-- 5. Mentalidad Data Engineer: Este script simula un proceso de "Bronze to Silver", 
--    donde tomamos datos crudos con nulos y los transformamos en una tabla limpia.
--------------------------------------------------------------------------------