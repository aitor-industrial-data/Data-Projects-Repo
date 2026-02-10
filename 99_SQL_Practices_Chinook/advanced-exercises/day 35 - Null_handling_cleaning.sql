/*
================================================================================
ESTUDIANTE: Aitor (Data Engineer Trainee)
FECHA: 2026-02-11 (Día 35)
EJERCICIO: Limpieza de Datos y Manejo de Nulos (Data Quality)
================================================================================

ENUNCIADO DE NEGOCIO:
El equipo de Logística quiere enviar regalos de fidelización a los clientes, pero la base de datos es un desastre:
-Muchos clientes no tienen empresa (Company es NULL), por lo que son particulares.
-Muchos no tienen State (Estado/Provincia).
-Algunos no tienen Fax ni Phone.

Genera un listado limpio para la empresa de mensajería con:
1. Customer_Name: Nombre completo.
2. Client_Type: Si el campo Company está vacío, debe decir 'End User'. Si tiene datos, debe mostrar el nombre de la empresa.
3. Region: Si el campo State está vacío, debe decir 'Unknown State'.
4. Priority_Contact: Necesitamos un número. Si tiene Phone, usa el Phone. Si no, usa el Fax. Si no tiene ninguno, debe decir 'No Phone on File'.
5. Clean_Address: Una dirección completa formateada así: "Address, City (Region) - Country". Cuidado: Si Region es nulo aquí, al concatenar podrías romper la cadena.
6. Postal_Code_Status:Si el PostalCode es nulo, marca 'Check Manually', si no 'Valid'.

CONCEPTO TÉCNICO (COALESCE vs CASE):
- Usamos COALESCE() para reemplazos directos de NULL (más limpio y performante).
- Usamos CASE para lógica de negocio condicional compleja (ej. estatus del código postal).
================================================================================
*/

SELECT 
    -- Concatenación simple
    c.FirstName || ' ' || c.LastName AS Customer_Name,
    
    -- Si no tiene empresa, es un usuario final
    COALESCE(c.Company, 'End User') AS Client_Type,
    
    -- Normalización de regiones geográficas
    COALESCE(c.State, 'Unknown State') AS Region,
    
    -- Lógica de prioridad de contacto (Phone -> Fax -> Fallback)
    COALESCE(c.Phone, c.Fax, 'No Phone on File') AS Priority_Contact,
    
    -- Construcción de cadena de texto "Blindada"
    -- Al usar COALESCE dentro de la concatenación, evitamos que un NULL rompa toda la cadena
    c.Address || ', ' || c.City || ' (' || COALESCE(c.State, 'Unknown State') || ') - ' || c.Country AS Clean_Address,
    
    -- Validación de Calidad de Datos (Data Quality Check)
    -- COALESCE no sirve porque si c.PostalCode no es nulo daria c.PostalCode y no 'Valid'.
    CASE 
        WHEN c.PostalCode IS NULL THEN 'Check Manually' -- Flag para revisión manual
        ELSE 'Valid'
    END AS Postal_Code_Status

FROM Customer c
ORDER BY Client_Type, Region;