--------------------------------------------------------------------------------
-- 08_invoice_customer_details.sql
-- AUTOR: Aitor | Ingeniero Técnico Industrial | Data Engineer
-- PROYECTO: Chinook Database (Singular Schema)
--------------------------------------------------------------------------------

/* ENUNCIADO:
   Generar un listado de facturas que incluya el ID de factura, la fecha, 
   el total y el nombre completo del cliente (nombre + apellido) que realizó 
   el pago. Solo incluir clientes que tengan una dirección de facturación 
   registrada y cuyas facturas superen los 5€, ordenadas de mayor a menor importe.
*/

SELECT 
    i.InvoiceId,
    i.InvoiceDate,
    i.Total,
    c.FirstName || ' ' || c.LastName AS Full_Name, -- Fundamento: Concatenación
    c.Country
FROM Invoice i
INNER JOIN Customer c ON i.CustomerId = c.CustomerId
WHERE c.Address IS NOT NULL
  AND i.Total > 5
  AND i.InvoiceDate IS NOT NULL
ORDER BY i.Total DESC;

--------------------------------------------------------------------------------
-- ANOTACIONES TÉCNICAS Y FUNDAMENTOS:
-- 1. Unión Relacional (INNER JOIN): Conexión de la tabla de hechos (Invoice) 
--    con la tabla de dimensiones (Customer) mediante 'CustomerId'.
-- 2. Concatenación de Strings: Se utiliza '||' para unir el nombre y apellido 
--    en una sola columna 'Full_Name' (Data Formatting).
-- 3. Uso de Alias Estratégicos (i, c): Permite referenciar tablas de forma 
--    limpia, esencial cuando se escalan consultas a múltiples JOINs.
-- 4. Validación de Calidad (IS NOT NULL): Aplicado tanto al cliente (Address) 
--    como a la factura (InvoiceDate) para evitar registros incompletos.
-- 5. Lógica de Negocio: Se filtra por importe (> 5) y se ordena por valor, 
--    identificando a los clientes con mayor impacto económico (High Value).
--------------------------------------------------------------------------------