################################################################################
# 24_execution_timer.py
# AUTOR: Aitor | Ingeniero Técnico Industrial | Data Engineer
# PROYECTO: Optimización y Telemetría de Consultas Multi-Tabla (Pytho Core)
#
# ENUNCIADO:
# 1. Desarrollar un script de auditoría para medir el coste computacional de queries.
# 2. Implementar una consulta SQL de alta complejidad con 4 JOINs y filtros HAVING.
# 3. Analizar el rendimiento mediante la medición de latencia (Time) y memoria (Peak).
# 4. Automatizar la generación de un reporte de Business Intelligence en formato .txt.
# 5. Foco Técnico: Performance Profiling, SQL Relacional Complejo y File Persistence.
################################################################################

import sqlite3
import time
import tracemalloc

def auditoria_rendimiento_bi():
    # Iniciamos telemetría (Sensores)
    tracemalloc.start()
    inicio = time.time()

    try:
        # Conexión al puente de datos 
        with sqlite3.connect('Chinook_Sqlite.sqlite') as conn:
            cursor = conn.cursor()
            
            # Query Compleja: 5 tablas unidas (Artist -> Album -> Track -> InvoiceLine -> Invoice)
            query = """
                SELECT 
                    art.Name as ArtistName,
                    COUNT(il.TrackId) as TotalUnitsSold,
                    SUM(il.UnitPrice * il.Quantity) as TotalRevenue,
                    AVG(il.UnitPrice) as AveragePrice
                FROM Artist art
                JOIN Album alb ON art.ArtistId = alb.ArtistId
                JOIN Track t ON alb.AlbumId = t.AlbumId
                JOIN InvoiceLine il ON t.TrackId = il.TrackId
                GROUP BY art.Name
                HAVING TotalUnitsSold > 10
                ORDER BY TotalRevenue DESC
                LIMIT 10;
            """
            
            print(">>> Lanzando Query de Alta Complejidad...")
            cursor.execute(query)
            reporte_datos = cursor.fetchall()

            # Escritura de resultados en el sistema de archivos 
            with open('execution_timer_report.txt', 'w', encoding='utf-8') as f:
                f.write("REPORTE DE AUDITORÍA DE RENDIMIENTO (BI)\n")
                f.write("="*60 + "\n")
                f.write(f"{'ARTISTA':<30} | {'UDS':<5} | {'INGRESOS':<10} | {'AVG'}\n")
                f.write("-" * 60 + "\n")
                
                for nombre, unidades, ingresos, promedio in reporte_datos:
                    f.write(f"{nombre:<30} | {unidades:<5} | ${ingresos:>8.2f} | ${promedio:.2f}\n")

        # Captura de métricas finales (Día 114: Calidad Técnica) 
        fin = time.time()
        actual, pico = tracemalloc.get_traced_memory()
        tracemalloc.stop()

        print(f"\n[MÉTRICAS DE INGENIERÍA]")
        print(f"Latencia de Query: {fin - inicio:.5f} segundos")
        print(f"Consumo RAM Pico: {pico / 1024:.2f} KB")
        print(f"Estado: Éxito en la automatización de tarea de sistema.")

    except sqlite3.Error as e:
        print(f"Error en el motor SQL: {e}")
    except Exception as e:
        print(f"Error inesperado: {e}")

if __name__ == "__main__":
    auditoria_rendimiento_bi()