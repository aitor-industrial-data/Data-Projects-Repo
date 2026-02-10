/*
================================================================================
ESTUDIANTE: Aitor (Data Engineer Trainee)
FECHA: 2026-02-11 (Día 35)
BLOQUE: Limpieza y Transformación de Datos (Data Cleaning)
EJERCICIO: Normalización de Catálogo y GDPR Masking para Marketing
================================================================================

ENUNCIADO DE NEGOCIO:
El departamento de Marketing requiere una lista de clientes y sus compras para una 
campaña personalizada. Para ello, los datos deben cumplir con:
1. Username: Genera un nombre de usuario combinando la primera letra del nombre en minúscula
   y el apellido completo en minúscula. Y limitalo a 10 caracteres.
2. Domain_Check: Marketing sospecha que hay correos mal escritos. Extrae solo el dominio del email
   (lo que va después del @).
3. Clean_Track: En la tabla Track, hay canciones que contienen la palabra "Instrumental" o "Remix"
   entre paréntesis. Elimina esas palabras y los paréntesis usando REPLACE.
4. Hidden_Email: Por seguridad (GDPR), muestra el email pero reemplaza todo lo que esté antes
   del @ por asteriscos ****.

HERRAMIENTAS:
UPPER() / LOWER(): Normaliza a mayúsculas o minúsculas. (Fundamental para comparar correos).
LENGTH(): Mide cuántos caracteres hay. Útil para detectar errores en códigos postales o DNIs.
REPLACE(columna, 'viejo', 'nuevo'): Cambia partes de un texto.
SUBSTR(columna, inicio, longitud): Extrae una "rebanada" del texto.
INSTR(columna, 'carácter'): Te dice en qué posición está un símbolo (como el @ en un email).
================================================================================
*/

SELECT 
    -- 1. GENERACIÓN DE USERNAME (Primera inicial + Apellido)
    -- Lógica: Convertimos todo a minúsculas, concatenamos y limitamos a 10 chars.
    SUBSTR(
        LOWER(SUBSTR(c.FirstName, 1, 1)) || LOWER(c.LastName), 
        1, 10
    ) AS Username,

    -- 2. DOMAIN_CHECK (Extracción de dominio)
    -- Lógica: Buscamos la posición del '@' y cortamos desde esa posición + 1.
    SUBSTR(c.Email, INSTR(c.Email, '@') + 1) AS Domain_Check,

    -- 3. CLEAN_TRACK (Cirugía de Strings en el Catálogo)
    -- Lógica: Usamos REPLACE anidados para eliminar etiquetas redundantes.
    -- Se recomienda limpiar también los paréntesis si existen.
    REPLACE(
        REPLACE(t.Name, 'Instrumental', ''), 
        'Remix', ''
    ) AS Clean_Track,

    -- 4. HIDDEN_EMAIL (Data Masking - Privacidad)
    -- Lógica: Concatenamos una máscara fija con el resto del email desde el '@'.
    '****' || SUBSTR(c.Email, INSTR(c.Email, '@')) AS Hidden_Email,

    -- Columnas de referencia para verificar la limpieza
    c.Email AS Original_Email,
    t.Name AS Original_Track_Name

FROM Customer c
INNER JOIN Invoice i ON c.CustomerId = i.CustomerId 
INNER JOIN InvoiceLine il ON i.InvoiceId = il.InvoiceId 
INNER JOIN Track t ON t.TrackId = il.TrackId

-- Ordenamos por el nombre limpio para facilitar la auditoría de Marketing
ORDER BY Clean_Track ASC;

/*
================================================================================
ANOTACIONES TEÓRICAS PARA EL PORTFOLIO:

1. ¿POR QUÉ ANIDAR FUNCIONES? 
   En procesos ETL, anidar funciones (como el SUBSTR del LOWER) reduce la necesidad 
   de crear columnas temporales, ahorrando memoria y tiempo de ejecución.

2. INSTR + SUBSTR: 
   Es la combinación ganadora para parsear textos dinámicos (como emails o URLs) 
   donde no sabemos en qué posición exacta termina cada parte.

3. REEMPLAZOS MÚLTIPLES: 
   En SQLite, al no existir REGEX_REPLACE por defecto, la anidación de REPLACE() 
   es el estándar para limpiezas de múltiples patrones.
================================================================================
*/