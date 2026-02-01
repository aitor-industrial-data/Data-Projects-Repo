/*
  PROYECTO: Análisis de Clientes VIP en Brasil
  OBJETIVO: Identificar clientes con gasto superior a la media global.
  FASE: 02 - SQL Avanzado
*/

SELECT 
    c.FirstName, 
    c.LastName, 
    c.Email, 
    SUM(i.Total) as Gasto_Total
FROM Customer c
JOIN Invoice i ON c.CustomerId = i.CustomerId
WHERE c.Country = 'Brazil'
GROUP BY c.CustomerId
HAVING Gasto_Total > (
    SELECT AVG(Total_Por_Cliente)
    FROM (
        SELECT SUM(Total) as Total_Por_Cliente
        FROM Invoice
        GROUP BY CustomerId
    )
);
