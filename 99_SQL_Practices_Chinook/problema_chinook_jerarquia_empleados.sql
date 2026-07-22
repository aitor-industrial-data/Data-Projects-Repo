/* ============================================================
   PROBLEMA - Base de datos Chinook
   ============================================================

   ENUNCIADO:

   La tabla Employee tiene una jerarquía interna a través de la columna
   ReportsTo (cada empleado reporta a otro empleado, o a NULL si es el
   máximo responsable). Cada empleado puede tener clientes asignados
   como SupportRepId en la tabla Customer, y esos clientes generan
   ventas a través de Invoice / InvoiceLine.

   Para cada empleado que sea MANAGER (es decir, que tenga al menos un
   subordinado, directo o indirecto, en cualquier nivel de profundidad),
   calcula:

     - Nombre completo y cargo (Title)
     - Número total de subordinados a su cargo (en toda la jerarquía,
       no solo los directos)
     - Profundidad máxima de su jerarquía (cuántos niveles por debajo
       de él existen)
     - Ventas totales generadas por él mismo y por TODOS sus
       subordinados en conjunto (suma de todas las facturas de los
       clientes que atienden, en cualquier nivel)

   Mostrar solo a los managers (con al menos 1 subordinado), ordenados
   por ventas totales del equipo de forma descendente.

   ------------------------------------------------------------
   Dificultad: requiere una CTE RECURSIVA para "aplanar" la jerarquía
   de empleados a cualquier profundidad, combinada con agregación de
   ventas y CTEs adicionales.
   ------------------------------------------------------------ */


-- ============================================================
-- RESOLUCIÓN
-- ============================================================

WITH RECURSIVE jerarquia AS (
    -- Caso base: cada empleado es su propio "subordinado" en nivel 0
    -- (esto permite que las ventas propias del manager también cuenten)
    SELECT
        EmployeeId AS ManagerId,
        EmployeeId AS SubordinadoId,
        0 AS Nivel
    FROM Employee

    UNION ALL

    -- Caso recursivo: bajamos un nivel más buscando quién reporta
    -- a los subordinados ya encontrados
    SELECT
        j.ManagerId,
        e.EmployeeId AS SubordinadoId,
        j.Nivel + 1 AS Nivel
    FROM jerarquia j
    JOIN Employee e ON e.ReportsTo = j.SubordinadoId
),

ventas_por_empleado AS (
    -- Ventas generadas por los clientes que atiende cada empleado
    SELECT
        c.SupportRepId AS EmployeeId,
        SUM(il.UnitPrice * il.Quantity) AS Ventas
    FROM Customer c
    JOIN Invoice i      ON i.CustomerId = c.CustomerId
    JOIN InvoiceLine il ON il.InvoiceId = i.InvoiceId
    GROUP BY c.SupportRepId
),

resumen_equipo AS (
    -- Para cada manager, sumamos las ventas de todo su equipo
    -- (él mismo + subordinados en cualquier nivel)
    SELECT
        j.ManagerId,
        COUNT(DISTINCT CASE
                  WHEN j.SubordinadoId <> j.ManagerId THEN j.SubordinadoId
              END) AS NumSubordinados,
        MAX(j.Nivel) AS ProfundidadMax,
        SUM(COALESCE(v.Ventas, 0)) AS VentasTotalesEquipo
    FROM jerarquia j
    LEFT JOIN ventas_por_empleado v ON v.EmployeeId = j.SubordinadoId
    GROUP BY j.ManagerId
)

SELECT
    e.FirstName || ' ' || e.LastName AS Manager,
    e.Title,
    re.NumSubordinados,
    re.ProfundidadMax,
    ROUND(re.VentasTotalesEquipo, 2) AS VentasTotalesEquipo
FROM resumen_equipo re
JOIN Employee e ON e.EmployeeId = re.ManagerId
WHERE re.NumSubordinados > 0
ORDER BY VentasTotalesEquipo DESC;
