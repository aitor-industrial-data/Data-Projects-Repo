/*******************************************************************************
RUTA DE INGENIERÍA DE DATOS - DÍA 53: Data Profiling & Auditoría
Objetivo: Generar un reporte de salud de la vista 'V_Final_Customer_Clean'.
*******************************************************************************/

-- =============================================================================
-- 1. ANÁLISIS DE VOLUMEN (Volume Analysis)
-- ¿Cuántos clientes "limpios" tenemos vs la tabla original?
-- =============================================================================

SELECT 
    (SELECT COUNT(*) FROM customer) as Total_Original_Rows,
    (SELECT COUNT(*) FROM V_Final_Customer_Clean) as Total_Clean_Rows,
    (SELECT COUNT(*) FROM customer) - (SELECT COUNT(*) FROM V_Final_Customer_Clean) as Filas_Eliminadas_Duplicados
;

-- =============================================================================
-- 2. COMPLETITUD (Completeness Check)
-- ¿Qué porcentaje de datos tenemos completos en columnas clave?
-- Un Ingeniero busca el 100% en claves primarias y >90% en datos de contacto.
-- =============================================================================

SELECT 
    COUNT(*) as Total_Records,
    
    -- Chequeo de Empresa   
    -- 1. Métrica "Mentirosa" (Técnicamente no es nulo)
    SUM(CASE WHEN Company IS NOT NULL THEN 1 ELSE 0 END) as Technical_Fill_Rate,
    -- 2. Métrica "Honesta" (La realidad de la fuente)
    -- Contamos solo si NO es el valor por defecto que inventamos nosotros
    SUM(CASE WHEN Company != 'Individual' THEN 1 ELSE 0 END) as True_Company_Count, -- Recuerda que en V_Final_Customer_Clean cambiamos nulor por 'Individual'
    -- Porcentaje Real
    ROUND(SUM(CASE WHEN Company != 'Individual' THEN 1 ELSE 0 END) * 100.0 / COUNT(*), 2) as Company_Fill_Rate_Pct,
    
    -- Chequeo de Estado/Provincia (Suele tener muchos nulos)
    SUM(CASE WHEN State != 'N/A' THEN 1 ELSE 0 END) as Real_State_Count, -- Recuerda que el día 50 pusimos 'N/A'
    ROUND(SUM(CASE WHEN State != 'N/A' THEN 1 ELSE 0 END) * 100.0 / COUNT(*), 2) as State_Fill_Rate_Pct,

      -- Chequeo de Telefonos (Suele tener muchos nulos)
    SUM(CASE WHEN Clean_Phone IS NOT NULL THEN 1 ELSE 0 END) as Clean_Phone_Count,
    ROUND(SUM(CASE WHEN Clean_Phone IS NOT NULL THEN 1 ELSE 0 END) * 100.0 / COUNT(*), 2) as Clean_Phone_Fill_Rate_Pct
FROM V_Final_Customer_Clean;

-- =============================================================================
-- 3. UNICIDAD (Uniqueness Check)
-- PRUEBA DE FUEGO: Si esto devuelve algo > 0, el script V_Final_Customer_Clean falló.
-- =============================================================================

SELECT 
    Email,
    COUNT(*) as Duplicate_Count
FROM V_Final_Customer_Clean
GROUP BY Email
HAVING COUNT(*) > 1;

-- =============================================================================
-- 4. CONSISTENCIA DE REGLAS (Validity Check)
-- ¿Se aplicó bien la regla CASE de los Territorios (North America, LATAM, etc)?
-- No debería aparecer ningún país suelto aquí, solo las categorías definidas.
-- =============================================================================

SELECT 
    Territory,
    COUNT(*) as Customers_In_Region,
    ROUND(COUNT(*) * 100.0 / (SELECT COUNT(*) FROM V_Final_Customer_Clean), 2) as Market_Share_Pct
FROM V_Final_Customer_Clean
GROUP BY Territory
ORDER BY Customers_In_Region DESC;


/* =============================================================================
DIAGNÓSTICO TÉCNICO DE CALIDAD DE DATOS (DATA QUALITY REPORT)
Estado Global: APROBADO CON OBSERVACIONES
=============================================================================

1. UNICIDAD: [ÉXITO] 
   - No se detectan correos duplicados en la vista final. 
   - La lógica de deduplicación mediante ROW_NUMBER() ha consolidado correctamente los registros.

2. COMPLETITUD TÉCNICA VS. REAL: [ADVERTENCIA]
   - La completitud técnica es del 100% gracias a la estandarización ('Individual', 'N/A').
   - Sin embargo, la calidad REAL de la columna 'Company' es del ~16%. 
   - El 84% de los datos son valores por defecto. Esto sugiere que la mayoría de los 
     clientes no están asociados a una empresa o el dato no se captura en el origen.

3. INTEGRIDAD DE FORMATO (PARSING): [ÉXITO]
   - Los teléfonos han sido normalizados y están libres de caracteres especiales.
   - Los dominios de email han sido extraídos correctamente para análisis de segmentación.

4. RECOMENDACIONES:
   - No utilizar la columna 'Company' para campañas B2B masivas sin antes enriquecer la fuente.
   - Utilizar la columna 'Territory' como dimensión principal para reportes geográficos, 
     ya que presenta un 100% de validez según las reglas de negocio aplicadas.
=============================================================================
*/