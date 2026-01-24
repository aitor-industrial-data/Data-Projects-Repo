--DIA 11 -   Ejercicios de repaso: Casos reales de negocio.

/*Caso 1: Análisis de Clientes VIP (Marketing)
Objetivo: El departamento de marketing quiere lanzar una campaña para los clientes que más han gastado.

Reto: Encuentra el nombre, apellido y el total gastado de los 5 clientes que más ingresos han generado.
Tablas: Customer e Invoice.
Tu meta: Usar JOIN y GROUP BY con SUM.*/

SELECT c.FirstName, c.LastName, sum(i.Total) as Total_gastado
FROM Customer c
join Invoice i on i.CustomerId = c.CustomerId
GROUP by c.CustomerId, c.FirstName, c.LastName
order BY Total_gastado DESC
limit 5
;


/*Caso 2: Reporte de Ventas por Género Musical (Contenido)
Objetivo: La plataforma quiere saber qué tipo de música es la que realmente se vende para decidir qué licencias renovar.

Reto: Lista todos los géneros (Genre.Name) y cuántas pistas (Track) se han vendido de cada uno.
Tablas: Genre, Track, InvoiceLine.
Tu meta: Unir 3 tablas y usar COUNT para ver el volumen de ventas.*/

select g.name, SUM (i.Quantity) AS Total_Sales
from Genre g
JOIN track t on t.GenreId = g.GenreId
join InvoiceLine i on i.TrackId = t.TrackId
group by g.GenreId, g.name
order by Total_Sales desc
;



/*Caso 3: Rendimiento de Empleados (Recursos Humanos)
Objetivo: Ver quién es el mejor gestor de ventas.

Reto: Muestra el nombre del empleado y el total de ventas (en dólares) realizadas a los clientes que tienen asignados.
Tablas: Employee, Customer, Invoice.
Tu meta: Lógica relacional: Employee -> Customer -> Invoice.*/

SELECT 
    e.FirstName, e.LastName AS Employee_Name, 
    SUM(i.Total) AS Total_Revenue
FROM Employee e
JOIN Customer c ON e.EmployeeId = c.SupportRepId -- Aquí está el truco
JOIN Invoice i  ON c.CustomerId = i.CustomerId
GROUP BY e.EmployeeId, e.FirstName, e.LastName
ORDER BY Total_Revenue DESC;