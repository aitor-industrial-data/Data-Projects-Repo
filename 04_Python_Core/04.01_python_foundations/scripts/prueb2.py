import os

# Get the current working directory
current_folder = os.getcwd() 

# List all files and folders
content = os.listdir(current_folder)


file_mapping = {}
for archivo in content:
    # Separación segura: 'name' se queda con el nombre y 'ext' con la extensión (ej: .txt)
    name, ext = os.path.splitext(archivo)
    
    # Filtro importante: ignorar carpetas (que no tienen extensión) y el propio script
    if ext == "" or archivo == "exercise_day102.py":
        continue
        
    # Tu lógica de diccionario (que está muy bien planteada)
    if ext not in file_mapping:
        file_mapping[ext] = [archivo]
    else:
        file_mapping[ext].append(archivo)

import shutil  # Necesaria para mover archivos

for ext, files in file_mapping.items():
    # Creamos un nombre de carpeta limpio (ej: de '.txt' a 'txt_files')
    folder_name = ext.strip('.').lower() + "_files"
    
    # 1. Crear la carpeta si no existe
    if not os.path.exists(folder_name):
        os.makedirs(folder_name)
        print(f"Created folder: {folder_name}")

    # 2. Mover los archivos (Paso Final)
    for file in files:
        # Definimos origen y destino
        source = os.path.join(current_folder, file)
        destination = os.path.join(current_folder, folder_name, file)
        
        # Movemos el archivo
        shutil.move(source, destination)
        print(f"Moved: {file} -> {folder_name}/")
        