################################################################################
# 23_sqlite_chinook_check.py
# AUTOR: Aitor | Ingeniero Técnico Industrial | Data Engineer
# PROYECTO: Integración SQL - Verificación de Conectividad (El Puente)
#
# ENUNCIADO:
# 1. Validar la conexión entre Python y el motor SQLite usando la DB "Chinook".
# 2. Ejecutar una consulta relacional (JOIN) para consolidar ventas por territorio.
# 3. Transformar el set de datos (tuplas) en un reporte de texto legible (.txt).
# 4. Implementar gestión de excepciones para asegurar la integridad de la conexión.
# 5. Foco Técnico: Librería sqlite3, Context Managers, SQL Aggregations y File I/O.
################################################################################

import sqlite3

def generar_reporte_ventas():
    # 1. Conexión segura al 'Puente'
    # Asegurarse de que la db se encuentra en la misma carpeta que este archivo
    try:
        with sqlite3.connect('Chinook_Sqlite.sqlite') as conn:
            cursor = conn.cursor()
            
            # 2. La Query: Sumamos el total de facturas agrupado por país del cliente
            query = """
                SELECT c.Country, SUM(i.Total) as TotalSales
                FROM Customer c
                JOIN Invoice i ON c.CustomerId = i.CustomerId
                GROUP BY c.Country
                ORDER BY TotalSales DESC;
            """
            
            print("Ejecutando consulta en la base de datos...")
            cursor.execute(query)
            datos = cursor.fetchall()
            # datos es una lista de tuplas: [(country, TotalSales),(...

            # 3. Procesamiento en Python y Escritura de Archivo
            # Creamos un archivo de texto para persistir el reporte
            with open('sales_report_by_country.txt', 'w', encoding='utf-8') as f:
                f.write("REPORTE ESTRATÉGICO DE VENTAS - CHINOOK\n")
                f.write("="*40 + "\n\n")
                f.write(f"{'PAÍS':<20} | {'TOTAL FACTURADO':<15}\n")
                f.write("-" * 40 + "\n")
                
                for pais, total in datos:
                    linea = f"{pais:<20} | ${total:>14.2f}\n"
                    f.write(linea)
            
            print("¡Éxito! El archivo 'sales_report_by_country.txt' ha sido generado.")

    except sqlite3.Error as e:
        print(f"Error en la conexión a la base de datos: {e}")
    except Exception as e:
        print(f"Ocurrió un error inesperado: {e}")

if __name__ == "__main__":
    generar_reporte_ventas()