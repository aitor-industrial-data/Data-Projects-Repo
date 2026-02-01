/*
===============================================================================
PROYECTO FINAL: UC Davis - SQL for Data Science
FASE 1: Definición del Esquema (DDL) e Ingesta de Datos
===============================================================================
ENUNCIADO:
1. Crear la estructura de tablas (Schema) en SQLite para los datos agrícolas.
2. INGESTA: Cargar los archivos .csv correspondientes a cada tabla utilizando 
   el asistente "Import Data" de DBeaver.
   
Nota: Es vital asegurar que el mapeo de columnas en DBeaver coincida con los 
nombres definidos en este script.
===============================================================================
*/


-- 1. milk_production: Producción de leche. Incluye 'Domain' para segmentación de mercado.
CREATE TABLE milk_production (
    Year INTEGER,
    Period TEXT,
    Geo_Level TEXT,
    State_ANSI INTEGER,
    Commodity_ID INTEGER,
    Domain TEXT,
    Value INTEGER
);

-- 2. cheese_production: Producción de queso. Estructura idéntica a milk_production.
CREATE TABLE cheese_production (
    Year INTEGER,
    Period TEXT,
    Geo_Level TEXT,
    State_ANSI INTEGER,
    Commodity_ID INTEGER,
    Domain TEXT,
    Value INTEGER
);

-- 3. coffee_production: Producción de café.
CREATE TABLE coffee_production (
    Year INTEGER,
    Period TEXT,
    Geo_Level TEXT,
    State_ANSI INTEGER,
    Commodity_ID INTEGER,
    Value INTEGER
);

-- 4. egg_production: Producción de huevos.
CREATE TABLE egg_production (
    Year INTEGER,
    Period TEXT,
    Geo_Level TEXT,
    State_ANSI INTEGER,
    Commodity_ID INTEGER,
    Value INTEGER
);

-- 5. honey_production: Producción de miel (datos con granularidad anual).
CREATE TABLE honey_production (
    Year INTEGER,
    Geo_Level TEXT,
    State_ANSI INTEGER,
    Commodity_ID INTEGER,
    Value INTEGER
);

-- 6. state_lookup: Tabla de referencia para mapear códigos ANSI con nombres de estados.
CREATE TABLE state_lookup (
    State TEXT,
    State_ANSI INTEGER
);

-- 7. yogurt_production: Datos de producción de yogurt.
CREATE TABLE yogurt_production (
    Year INTEGER,
    Period TEXT,
    Geo_Level TEXT,
    State_ANSI INTEGER,
    Commodity_ID INTEGER,
    Value INTEGER
);