/*
================================================================================
ESTUDIANTE: Aitor (Data Engineer Trainee)
FECHA: 2026-02-10 (Día 36)
BLOQUE: Consultas de métricas y lógica compleja
HITO: Resolución de caso real documentado - Auditoría de RRHH
================================================================================

ENUNCIADO:
El departamento de RRHH necesita un informe de "Relevo Generacional" para:
1. Identificar empleados próximos a la jubilación (estimada a los 65 años).
2. Categorizar la experiencia en la empresa (Seniority) según la fecha de contrato.
3. Asegurar que todos tengan un email de contacto. Si el empleado no tiene email, 
   se debe usar el de su responsable directo (ReportsTo).

REQUERIMIENTOS TÉCNICOS:
- Uso de PRINTF para normalización de IDs.
- Funciones de fecha (STRFTIME) para cálculos de edad y veteranía.
- Implementación de SELF-JOIN para resolver jerarquías de datos.
- Lógica condicional CASE para segmentación de talento.
================================================================================
*/

-- Inicio del Hito de Resolución
SELECT
    -- 1. NORMALIZACIÓN DE ID
    -- Aseguramos formato de 3 dígitos (ej: 001) para compatibilidad con sistemas antiguos.
    PRINTF('%03d', e.EmployeeId) AS Employee_ID,

    -- 2. FORMATO DE NOMBRE
    -- Combinación y limpieza de strings en mayúsculas.
    UPPER(e.FirstName || ' ' || e.LastName) AS Full_Name,

    -- 3. EXTRACCIÓN DE AÑO DE NACIMIENTO
    STRFTIME('%Y', e.BirthDate) AS Birth_Year,

    -- 4. CÁLCULO DE JUBILACIÓN (Lógica de Negocio)
    -- Sumamos 65 años al año de nacimiento para prever salidas.
    STRFTIME('%Y', e.BirthDate) + 65 AS Retirement_Year,

    -- 5. CATEGORIZACIÓN DE SENIORITY (Basado en HireDate, no BirthDate)
    -- Calculamos la diferencia entre el año actual y el de contratación.
    CASE
        WHEN STRFTIME('%Y', 'now') - STRFTIME('%Y', e.HireDate) > 20 THEN 'VETERAN'
        WHEN STRFTIME('%Y', 'now') - STRFTIME('%Y', e.HireDate) BETWEEN 10 AND 20 THEN 'SENIOR'
        ELSE 'JUNIOR'
    END AS Seniority_Status,

    -- 6. RESOLUCIÓN DE EMAIL JERÁRQUICO (Lógica de Self-Join)
    -- Prioridad: 1. Email Propio | 2. Email Jefe | 3. Email Soporte
    COALESCE(e.Email, m.Email, 'support_it@chinook.com') AS Contact_Email

FROM Employee e 
-- Aplicamos LEFT JOIN sobre la misma tabla para no perder al CEO (quien no tiene jefe)
LEFT JOIN Employee m ON e.ReportsTo = m.EmployeeId

ORDER BY Retirement_Year ASC;

/*
================================================================================
EXPLICACIÓN TÉCNICA: EL SELF-JOIN
================================================================================
Un Self-Join ocurre cuando unimos una tabla consigo misma. Es fundamental cuando
los datos tienen una estructura jerárquica (como un organigrama).

¿Cómo funciona aquí?
1. Usamos alias ('e' para empleado, 'm' para manager) para que SQL crea que son 
   dos tablas distintas.
2. Conectamos la columna 'ReportsTo' de la tabla 'e' con el 'EmployeeId' de la 
   tabla 'm'.
3. Esto nos permite "saltar" de la fila del empleado a la fila de su jefe para 
   extraer información que no está en la fila original (como su email).



NOTAS DE DATA QUALITY:
- Se utiliza 'LEFT JOIN' en lugar de 'INNER JOIN' para garantizar que los empleados
  que no reportan a nadie (NULL en ReportsTo) no sean eliminados del informe.
- El uso de STRFTIME('%Y', 'now') asegura que el reporte sea dinámico y funcione
  correctamente cada año que se ejecute.
================================================================================
*/