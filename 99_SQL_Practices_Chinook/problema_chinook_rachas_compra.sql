/* ============================================================
   PROBLEMA - Base de datos Chinook
   ============================================================

   ENUNCIADO:

   Para cada cliente, calcula la racha de MESES CONSECUTIVOS más larga en
   la que realizó al menos una compra (una factura). Es decir, queremos
   detectar periodos de actividad continua sin ningún mes en blanco.

   El resultado debe mostrar:
     - Nombre completo del cliente
     - Mes de inicio de su racha más larga
     - Mes de fin de su racha más larga
     - Longitud de la racha, en número de meses

   Solo interesan los clientes cuya racha más larga sea de 2 meses o más
   (descartamos a quienes solo compraron en meses sueltos y aislados).

   Ordenar el resultado por longitud de racha descendente y, en caso de
   empate, por nombre de cliente ascendente.

   ------------------------------------------------------------
   Dificultad: técnica clásica de "gaps and islands" combinando
   ROW_NUMBER(), aritmética de fechas y agregación por grupo generado.
   Sintaxis de fechas en SQLite (strftime/date), adaptable a otros
   motores cambiando esas funciones por sus equivalentes.
   ------------------------------------------------------------ */


-- ============================================================
-- RESOLUCIÓN
-- ============================================================

WITH meses_con_compra AS (
    -- Un registro por cliente y mes en que tuvo al menos una factura
    SELECT DISTINCT
        c.CustomerId,
        c.FirstName || ' ' || c.LastName AS Cliente,
        strftime('%Y-%m-01', i.InvoiceDate) AS Mes
    FROM Customer c
    JOIN Invoice i ON i.CustomerId = c.CustomerId
),

numerado AS (
    -- Numeramos los meses de cada cliente en orden cronológico
    SELECT
        CustomerId,
        Cliente,
        Mes,
        ROW_NUMBER() OVER (
            PARTITION BY CustomerId
            ORDER BY Mes
        ) AS rn
    FROM meses_con_compra
),

islas AS (
    -- Truco "gaps and islands": si a cada mes le restamos su número de
    -- orden (rn) en meses, todos los meses de una racha consecutiva caen
    -- en la MISMA fecha "ancla". Los saltos (gaps) rompen esa igualdad.
    SELECT
        CustomerId,
        Cliente,
        Mes,
        date(Mes, '-' || rn || ' months') AS grupo_isla
    FROM numerado
),

rachas AS (
    -- Agrupamos por la "isla": cada grupo es una racha consecutiva
    SELECT
        CustomerId,
        Cliente,
        grupo_isla,
        MIN(Mes) AS InicioRacha,
        MAX(Mes) AS FinRacha,
        COUNT(*) AS LongitudMeses
    FROM islas
    GROUP BY CustomerId, Cliente, grupo_isla
),

mejor_racha_por_cliente AS (
    -- Nos quedamos con la racha más larga de cada cliente
    SELECT
        *,
        ROW_NUMBER() OVER (
            PARTITION BY CustomerId
            ORDER BY LongitudMeses DESC, InicioRacha ASC
        ) AS posicion
    FROM rachas
)

SELECT
    Cliente,
    InicioRacha,
    FinRacha,
    LongitudMeses
FROM mejor_racha_por_cliente
WHERE posicion = 1
  AND LongitudMeses >= 2
ORDER BY LongitudMeses DESC, Cliente ASC;
