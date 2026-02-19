--------------------------------------------------------------------------------
-- 03_unique_client_markets.sql
-- AUTOR: Aitor | Ingeniero Técnico Industrial | Data Engineer
-- PROYECTO: Chinook Database (Singular Schema)
--------------------------------------------------------------------------------

/* ENUNCIADO:
   Listar de forma única los países de Europa (específicamente: Norway, 
   Belgium, Sweden, France, Spain) donde tenemos clientes, 
   excluyendo a 'Germany' y ordenados de la Z a la A.
*/

SELECT 
	DISTINCT Country
FROM Customer
WHERE Country IN ('Norway', 'Belgium', 'Sweden', 'France', 'Spain')
  AND Country != 'Germany'
ORDER BY Country DESC;

--------------------------------------------------------------------------------
-- ANOTACIONES TÉCNICAS Y FUNDAMENTOS:
-- 1. Filtrado de Conjuntos: Uso de 'IN' para manejar múltiples condiciones 
--    en una sola línea, evitando repetir 'OR' constantemente (Código Limpio).
-- 2. Operadores de Exclusión: Uso de '!=' (no igual) para filtrar ruido 
--    específico en los datos de salida.
-- 3. Prioridad de Operaciones: El motor SQL primero filtra las filas (WHERE), 
--    luego identifica los valores únicos (DISTINCT) y al final ordena (ORDER BY).
-- 4. Sentido de Negocio: Este tipo de "Data Wrangling" manual es el que se
--    automatizará con Python y el Robot ETL.
--------------------------------------------------------------------------------