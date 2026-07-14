################################################################################
# 20_text_data_cleaner.py
# AUTOR: Aitor | Ingeniero Técnico Industrial | Data Engineer
# PROYECTO: Normalización de Inventario de Activos Industriales (Python Core)
#
# ENUNCIADO:
# 1. Leer un archivo de texto llamado 'raw_assets.txt' con datos "sucios".
# 2. Implementar una función de limpieza que:
#    - Elimine caracteres especiales innecesarios ($, #, %, etc.).
#    - Normalice los nombres (Todo en MAYÚSCULAS o Capitalizado).
#    - Elimine espacios en blanco extra al principio y al final (strip).
# 3. Filtrar líneas vacías o registros que no cumplan un formato mínimo.
# 4. Exportar el resultado limpio a un nuevo archivo 'clean_assets.txt'.
# 5. Foco Técnico: String Manipulation, I/O de archivos y Data Cleaning.
################################################################################

# 1. Preparación del entorno (Input)
raw_file = "raw_assets.txt"
clean_file = "clean_assets.txt"

content = """m01_motor_vfd##
    pump_station_02    
$$$valve_control_unit

sensor_temp_01%
#backup_generator_alpha"""

with open(raw_file, "w", encoding="utf-8") as f:
    f.write(content)

# 2. Función de limpieza (Separada para ser reutilizable)
def clean_record(text):
    # Definimos los caracteres prohibidos en una lista o string
    chars_to_remove = "#$%&/()"
    
    # Limpiamos espacios y aplicamos normalización
    clean_text = text.strip()
    for char in chars_to_remove:
        clean_text = clean_text.replace(char, "")
    
    return clean_text.capitalize()

# 3. Procesamiento Eficiente (I/O Profesional)
print(f"\n{'='*50}\nSTARTING DATA CLEANING PROCESS\n{'='*50}")

counter_in = 0
counter_out = 0

# Abrimos el de lectura (r) y el de escritura (w) al mismo tiempo
with open(raw_file, "r", encoding="utf-8") as f_in, \
     open(clean_file, "w", encoding="utf-8") as f_out:
    
    for line in f_in:
        counter_in += 1
        cleaned = clean_record(line)
        
        # Solo guardamos si la línea resultante no está vacía
        if cleaned:
            f_out.write(f"{cleaned}\n")
            print(f"DEBUG: '{line.strip():<25}' -> '{cleaned}'")
            counter_out += 1

print(f"{'='*50}")
print(f"📊 SUMMARY:")
print(f"Lines processed: {counter_in}")
print(f"Cleaned records: {counter_out}")
print(f"File '{clean_file}' is ready for SQL injection.")
print(f"{'='*50}")