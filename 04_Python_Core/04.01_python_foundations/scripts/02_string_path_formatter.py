################################################################################
# 02_string_path_formatter.py
# AUTOR: Aitor | Ingeniero Técnico Industrial | Data Engineer
# PROYECTO: Automatización de Rutas WSL2 (Python Core)
#
# ENUNCIADO:
# 1. Definir una ruta de Windows como string.
# 2. Manipular el string para convertirlo al formato de archivos de Linux/WSL.
# 3. Reemplazar separadores y ajustar el prefijo de la unidad de disco.
# 4. Usar métodos de string: .lower(), .replace(), .lstrip().
################################################################################

# 1. Ruta original de Windows
# Usamos 'r' (raw string) para que Python no interprete las \ como caracteres especiales
win_path = r"C:\Users\Aitor\Documents\Data-Projects-Repo"

# 2. Convertir a minúsculas (Estándar en Data Engineering para evitar errores)
path_lower = win_path.lower()

# 3. Reemplazar barras invertidas \ por barras /
linux_style_path = path_lower.replace("\\", "/")

# 4. Ajustar el prefijo de la unidad (de "c:/" a "/mnt/c/")
# Quitamos el "c:" del principio y añadimos el prefijo de montaje de WSL
final_wsl_path = "/mnt/" + linux_style_path.replace(":", "", 1)

# 5. Salida de resultados
print("=== FORMATEADOR DE RUTAS WINDOWS -> WSL ===")
print(f"Original Windows: {win_path}")
print(f"Formateada WSL2:  {final_wsl_path}")

print("-" * 45)
# Verificación de tipo para asegurar que sigue siendo un string
print(f"Tipo de objeto: {type(final_wsl_path)}")