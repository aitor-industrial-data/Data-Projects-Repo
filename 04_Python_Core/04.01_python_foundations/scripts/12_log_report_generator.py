################################################################################
# 12_log_report_generator.py
# AUTOR: Aitor | Ingeniero Técnico Industrial | Data Engineer
# PROYECTO: Generador de Reportes de Actividad (Python Core)
#
# ENUNCIADO:
# 1. El script debe procesar una lista de eventos (tuplas) con el formato:
#    (timestamp, event_type, description)
# 2. El objetivo es persistir estos datos en un archivo llamado 'daily_log.txt'.
# 3. La función 'generate_log_report' debe:
#    - Abrir el archivo en modo 'write' (sobreescribir) o 'append' (añadir).
#    - Escribir una cabecera profesional al inicio del archivo.
#    - Recorrer la lista de eventos y escribir cada uno en una línea nueva
#      con un formato limpio: "[TIMESTAMP] TYPE: Description"
#    - Asegurarse de cerrar el archivo correctamente (uso de 'with open').
# 4. Al finalizar, el script debe imprimir un mensaje indicando el éxito 
#    de la operación y la ruta del archivo.
# 5. FOCO TÉCNICO: Manejo de Context Managers (with), escritura de strings
#    y persistencia de datos en disco.
################################################################################

from pathlib import Path

# Datos de prueba
events_list = [
    ("2026-03-16 08:00:12", "INFO", "System Boot Up"),
    ("2026-03-16 08:05:45", "DATA", "Connected to Chinook Database"),
    ("2026-03-16 09:15:00", "WARNING", "High Memory Usage Detected"),
    ("2026-03-16 10:30:22", "ERROR", "Failed to sync Docker Container")
]

def generate_log_report(filename: str, events: list):
    print(f'Iniciando el proceso de persistencia en: {filename}')
    
    try:
        with open(filename, "w", encoding="utf-8") as file:
            # Cabecera profesional
            file.write("="*60 + "\n")
            file.write("DAILY SERVER EVENT REPORT (12_log_report_generator.py)\n")
            file.write("="*60 + "\n\n")
            
            # Desempaquetado directamente en el bucle for (Más limpio)
            for timestamp, event_type, description in events:
                file.write(f'[{timestamp}] {event_type:7}: {description}\n')
        
        # Obtener ruta absoluta para el log
        file_path = Path(filename).absolute()
        
        print(f'Datos guardados con éxito.')
        print(f'Ruta del archivo: {file_path}')
        return True

    except Exception as e:
        print(f"Error al escribir el archivo: {e}")
        return False

# Ejecución
generate_log_report('daily_log.txt', events_list)