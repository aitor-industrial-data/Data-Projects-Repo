/*******************************************************************************
  RUTA DE INGENIERÍA DE DATOS - 02_SQL_Advanced_Wrangling_and_Testing
  A/B Testing I - Creación de Grupos de Prueba
  Objetivo: Segmentación de usuarios en la base de datos Chinook.
*******************************************************************************/

/* ENUNCIADO:
  Utilizar la vista de datos limpios 'V_Silver_Clean_Customer_Roster' (generada
  en el hito del "Gran Limpiador") para crear una segmentación de clientes 
  para un experimento de marketing.
  
  REQUERIMIENTOS:
  1. Los datos de origen deben provenir de la capa SILVER (datos ya normalizados). 
  2. Dividir la audiencia en dos grupos equilibrados (A y B) mediante el ID del cliente.
  3. La asignación debe ser determinista para evitar que un usuario cambie de grupo.
*/

-- 1. ELIMINACIÓN DE VISTA PREVIA
-- Como buena práctica de ingeniería, aseguramos un entorno limpio antes de crear.
DROP VIEW IF EXISTS V_Gold_AB_Test_Segmentation;

-- 2. CREACIÓN DE LA VISTA EN CAPA GOLD
-- Esta capa representa los datos listos para el consumo de negocio y analítica. 
CREATE VIEW V_Gold_AB_Test_Segmentation AS
SELECT 
    CustomerId,
    Full_Name,
    Country,
    Email,
    -- Lógica de segmentación: Par (A) / Impar (B)
    CASE 
        WHEN CustomerId % 2 = 0 THEN 'A' 
        ELSE 'B' 
    END AS test_group
FROM V_Silver_Clean_Customer_Roster; 

-- 3. VALIDACIÓN TÉCNICA (Data Profiling)
-- Verificamos que el volumen de clientes en cada grupo sea estadísticamente similar.
SELECT 
    test_group, 
    COUNT(*) AS total_clientes,
    AVG(CustomerId) as id_promedio 
FROM V_Gold_AB_Test_Segmentation
GROUP BY test_group;

/*
  ANOTACIONES TÉCNICAS PARA GITHUB:
  - Origen de Datos: Capa Silver (V_Silver_Clean_Customer_Roster). 
  - Técnica de Particionado: Uso de operador módulo sobre Clave Primaria (PK).
  - Aplicación: Este modelo permite realizar análisis de conversión y gasto (ARPU) 
    comparando ambos grupos en la fase final del proyecto SQL. 
*/