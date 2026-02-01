-- Ejecuta esto para eliminar las comas de los valores para formatear los datos correctamente.
-- Todas MENOS para state_lookup.

UPDATE cheese_production SET Value = REPLACE(Value, ',', '');
UPDATE coffee_production SET Value = REPLACE(Value, ',', '');
UPDATE egg_production   SET Value = REPLACE(Value, ',', '');
UPDATE honey_production  SET Value = REPLACE(Value, ',', '');
UPDATE milk_production   SET Value = REPLACE(Value, ',', '');
UPDATE yogurt_production SET Value = REPLACE(Value, ',', '');

