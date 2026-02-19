--------------------------------------------------------------------------------
-- 01_customer_contact_brazil.sql
-- AUTOR: Aitor | Ingeniero Técnico Industrial | Data Engineer
-- PROYECTO: Análisis de Base de Datos Chinook (Esquema Singular)
--------------------------------------------------------------------------------

/* ENUNCIADO:
   Extraer el nombre, apellido y correo electrónico de todos los 
   clientes que residen en Brasil.*/

SELECT 
    FirstName, 
    LastName, 
    Email
FROM Customer
WHERE Country = 'Brazil';

--------------------------------------------------------------------------------
-- ANOTACIONES TÉCNICAS:
-- 1. Lógica de Filtrado: Se utiliza la cláusula WHERE sobre la columna 'Country' 
--    para segmentar geográficamente la base de datos de clientes.
-- 2. Esquema Singular: El script cumple con la restricción de nombres de tablas 
--    y columnas en singular (Customer), compatible con tu versión de Chinook.
-- 3. Entorno: Código testeado en DB Browser (SQLite) y DBeaver, asegurando 
--    portabilidad entre herramientas locales y Docker.
--------------------------------------------------------------------------------