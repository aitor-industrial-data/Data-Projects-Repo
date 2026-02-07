/*******************************************************************************
  DÍA 32: CONSOLIDACIÓN DE ESTRATEGIA Y MENTALIDAD DE CONSULTOR
  Ingeniero: Aitor | Herramientas: CASE, CTE, Subqueries y Joins.
*******************************************************************************/

/*******************************************************************************
   ESTRATEGIA DE DISEÑO SQL (THE 4-STEP FRAMEWORK)
********************************************************************************

 1. EL SUJETO (¿De quién hablamos?)
    - Objetivo: Definir la unidad de análisis y nivel de detalle.
    - SQL: Determina el GROUP BY (País, Cliente, Empleado...).

 2. EL FILTRO (¿A quién quitamos antes de calcular?)
    - Objetivo: Limpiar el ruido y procesar solo filas relevantes.
    - SQL: Define la cláusula WHERE (Filtra FILAS individuales).

 3. LA MÉTRICA (¿Qué medimos?)
    - Objetivo: Definir los cálculos, KPIs y segmentaciones.
    - SQL: Funciones SUM, COUNT, AVG + Lógica CASE WHEN.

    --> 3.1 EL FILTRO DE MÉTRICA (HAVING)
        - Objetivo: Filtrar grupos basados en el resultado del cálculo.
        - SQL: Define la cláusula HAVING (Filtra GRUPOS agregados).

 4. EL CAMINO (¿Cómo llegamos?)
    - Objetivo: Trazar el mapa de relaciones y conexiones.
    - SQL: Definir los JOINs necesarios entre el Sujeto y la Métrica.

*******************************************************************************/

/* =============================================================================
   EJERCICIO 1: IMPACTO DEL SEGMENTO VIP EN USA
   
   ENUNCIADO: El Director de Ventas de USA quiere saber qué porcentaje del total
   de ingresos del país proviene de los "Clientes VIP" (aquellos que han gastado
   más de 40$ en total). Necesita comparar Ventas Totales vs Ventas VIP.
   
   METODOLOGÍA DE 4 PASOS:
   1. PASO 1 (SUJETO): Clientes de USA.
   2. PASO 2 (FILTRO): Solo país 'USA'.
   3. PASO 3 (MÉTRICA): % del total de ventas que viene de clientes "VIP".
   4. PASO 4 (CAMINO): Customer -> Invoice.
   =============================================================================
*/

SELECT 
    c.Country,
    
    -- Métrica 1: Total ventas en el país
    ROUND(SUM(i.Total), 2) AS Ventas_Totales_Pais,
    
    -- Métrica 2: Ventas solo de clientes VIP (>40$)
    ROUND(SUM(CASE WHEN c.CustomerId IN (
        SELECT CustomerId FROM Invoice GROUP BY CustomerId HAVING SUM(Total) > 40
    ) THEN i.Total ELSE 0 END), 2) AS Ventas_VIP,

    -- Métrica 3: El KPI de peso del segmento VIP
    ROUND(
        (SUM(CASE WHEN c.CustomerId IN (
            SELECT CustomerId FROM Invoice GROUP BY CustomerId HAVING SUM(Total) > 40
        ) THEN i.Total ELSE 0 END) * 100.0) 
        / SUM(i.Total), 
    2) AS Porcentaje_Impacto_VIP

FROM Customer c
JOIN Invoice i ON c.CustomerId = i.CustomerId
WHERE c.Country = 'USA'
GROUP BY c.Country;



/* =============================================================================
   EJERCICIO 2: SEGMENTACIÓN DE FACTURAS (SMALL VS BIG TICKETS)
   
   ENUNCIADO: Marketing quiere saber qué países tienen una cultura de "compra 
   hormiga" (facturas de menos de 10$) frente a países con compras grandes. 
   Se requiere el total de dinero de cada grupo y cuántas facturas grandes hay.
   
   METODOLOGÍA DE 4 PASOS:
   1. PASO 1 (SUJETO): Países (BillingCountry).
   2. PASO 2 (FILTRO): Ninguno (Análisis global).
   3. PASO 3 (MÉTRICA): Sumas condicionales por importe de factura.
   4. PASO 4 (CAMINO): Tabla Invoice (Directo).
   =============================================================================
*/

SELECT 
    BillingCountry AS Pais,

    -- MÉTRICA 1: Suma de facturas menores a 10$
    ROUND(SUM(CASE WHEN Total < 10 THEN Total ELSE 0 END), 2) AS Dinero_Facturas_Pequeñas,

    -- MÉTRICA 2: Suma de facturas de 10$ o más
    ROUND(SUM(CASE WHEN Total >= 10 THEN Total ELSE 0 END), 2) AS Dinero_Facturas_Grandes,

    -- MÉTRICA 3: Conteo de volumen de facturas "Grandes"
    SUM(CASE WHEN Total >= 10 THEN 1 ELSE 0 END) AS Cantidad_Facturas_Grandes

FROM Invoice
GROUP BY BillingCountry
ORDER BY Cantidad_Facturas_Grandes DESC;



/* =============================================================================
   EJERCICIO 3: ANÁLISIS DE CHURN (CLIENTES DORMIDOS VS ACTIVOS)
   
   ENUNCIADO: Identificar por país cuántos clientes han dejado de comprar. 
   Un cliente es "Dormido" si su ÚLTIMA factura es de 2011 o antes. Si es de 
   2012 en adelante, está "Activo". Calcular también el dinero que aportan.
   
   METODOLOGÍA DE 4 PASOS:
   1. PASO 1 (SUJETO): Países.
   2. PASO 2 (FILTRO): Ninguno (Segmentación por fecha).
   3. PASO 3 (MÉTRICA): Conteo de clientes únicos y suma de sus facturas.
   4. PASO 4 (CAMINO): CTE (Última compra por cliente) -> Invoice.
   =============================================================================
*/

WITH Ultima_factura AS (
    -- Pre-calculamos la fecha de la última actividad de cada cliente
    SELECT 
        c.CustomerId,
        c.Country, 
        MAX(i.InvoiceDate) AS Ultima_fecha
    FROM Customer c 
    INNER JOIN Invoice i ON c.CustomerId = i.CustomerId 
    GROUP BY c.CustomerId
)

SELECT 
    uf.Country,
    -- Conteo condicional: ¿Es su última compra antigua o reciente?
    SUM(CASE WHEN strftime('%Y', uf.Ultima_fecha) <= '2011' THEN 1 ELSE 0 END) AS Clientes_dormidos,
    SUM(CASE WHEN strftime('%Y', uf.Ultima_fecha) >= '2012' THEN 1 ELSE 0 END) AS Clientes_activos,
    
    -- Dinero generado por los clientes que siguen activos hoy
    ROUND(SUM(CASE WHEN strftime('%Y', uf.Ultima_fecha) >= '2012' THEN i.Total ELSE 0 END), 2) AS total_activos

FROM Ultima_factura uf
INNER JOIN Invoice i ON uf.CustomerId = i.CustomerId 
GROUP BY uf.Country;



/* -----------------------------------------------------------------------------
   ANOTACIONES TÉCNICAS (SOPORTE MEDION I5):
   - Ejercicio 1: Evita el error de filtrar con WHERE, permitiendo sacar %.
   - Ejercicio 2: Optimización de recursos al no requerir JOINs.
   - Ejercicio 3: Uso de CTE para aislar la lógica de "Estado del Cliente".
   -----------------------------------------------------------------------------
*/