/*
===============================================================================
PROYECTO FINAL: UC Davis - SQL for Data Science
FASE 2: Limpieza y Transformación de Datos (Data Wrangling)
===============================================================================
ENUNCIADO:
Tras la ingesta de los archivos CSV, la columna 'Value' se importa como TEXT 
debido a la presencia de comas como separadores de miles (ej. "1,250").

OBJETIVO:
1. Eliminar las comas de la columna 'Value' en todas las tablas de producción.
2. Formatear los datos para permitir operaciones aritméticas y agregaciones 
   (SUM, AVG, etc.) en las fases de análisis.

NOTA: La tabla 'state_lookup' se excluye de este proceso al no contener 
datos numéricos de producción.
===============================================================================
*/

-- Limpieza de caracteres no numéricos (comas) en las tablas de hechos:

-- 1. Producción de Queso
UPDATE cheese_production SET Value = REPLACE(Value, ',', '');

-- 2. Producción de Café
UPDATE coffee_production SET Value = REPLACE(Value, ',', '');

-- 3. Producción de Huevos
UPDATE egg_production   SET Value = REPLACE(Value, ',', '');

-- 4. Producción de Miel
UPDATE honey_production  SET Value = REPLACE(Value, ',', '');

-- 5. Producción de Leche
UPDATE milk_production   SET Value = REPLACE(Value, ',', '');

-- 6. Producción de Yogurt
UPDATE yogurt_production SET Value = REPLACE(Value, ',', '');

/*
VERIFICACIÓN:
Se recomienda ejecutar 'SELECT Value FROM [table] LIMIT 5' para asegurar 
que el formato es ahora puramente numérico antes de proceder al análisis.
===============================================================================
*/
