--------------------------------------------------------------------------------
-- 23_ranking_top_sales_employees.sql
-- AUTOR: Aitor | Ingeniero Técnico Industrial | Data Engineer
-- PROYECTO: Chinook Database (Singular Schema)
--------------------------------------------------------------------------------

/* ENUNCIADO:
   Crear un ranking de los 3 mejores empleados de ventas basado en el total
   de ingresos generados por las facturas (Invoice) asociadas a sus clientes.
   
   Condiciones del reporte:
   1. Incluir el nombre completo del empleado (FirstName + LastName) en mayúsculas.
   2. Calcular el ingreso total acumulado por cada empleado.
   3. Si el estado del empleado es NULL, mostrar 'No State'.
   4. Clasificar el rendimiento: Si las ventas superan los 800, marcar como 'Elite', 
      si no, 'Standard'.
   5. Usar RANK() para asignar la posición, permitiendo empates si los hay.
   6. Filtrar para mostrar solo el TOP 3 del ranking.
*/

WITH EmployeePerformance AS (
    SELECT 
        UPPER(e.FirstName || ' ' || e.LastName) AS Employee_Name,
        COALESCE(e.State, 'No State') AS Region,
        SUM(i.Total) AS Total_Sales,
        CASE 
            WHEN SUM(i.Total) > 800 THEN 'Elite'
            ELSE 'Standard'
        END AS Performance_Tier,
        -- Función de Ventana: Genera el ranking basado en las ventas totales
        RANK() OVER(ORDER BY SUM(i.Total) DESC) AS Sales_Rank
    FROM Employee e
    JOIN Customer c ON e.EmployeeId = c.SupportRepId
    JOIN Invoice i ON c.CustomerId = i.CustomerId
    GROUP BY e.EmployeeId
)
SELECT 
    Sales_Rank,
    Employee_Name,
    Region,
    Total_Sales,
    Performance_Tier
FROM EmployeePerformance
WHERE Sales_Rank <= 3
ORDER BY Sales_Rank ASC;

--------------------------------------------------------------------------------
-- ANOTACIONES TÉCNICAS Y FUNDAMENTOS:
-- 1. RANK() vs ROW_NUMBER(): A diferencia del ejercicio 21, RANK() permite que 
--    dos empleados con la misma venta compartan posición, esencial en incentivos.
-- 2. Integración de CASE y COALESCE: Se aplica limpieza de datos (Wrangling) 
--    en el mismo reporte para asegurar que no haya valores NULL en la salida.
-- 3. Triple JOIN: Conectamos Empleado -> Cliente -> Factura. Es la base para 
--    entender la trazabilidad del dinero en un modelo relacional.
-- 4. Agregación en Ventana: El uso de SUM() dentro de la lógica del ranking 
--    demuestra un nivel avanzado de manejo de SQL para Data Engineering.
-- 5. Preparación para Dashboarding: Este tipo de consultas son las que 
--    alimentan herramientas como PowerBI o Tableau en entornos remotos.
--------------------------------------------------------------------------------