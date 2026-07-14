################################################################################
# 15_automated_folder_sorter.py
# AUTOR: Aitor | Ingeniero Técnico Industrial | Data Engineer
# PROYECTO: Automatización de Clasificación de Archivos (Python Core)
#
# ENUNCIADO:
# 1. Detectar el sistema operativo (Windows vs WSL2) para definir rutas.
# 2. Generar archivos de prueba en una carpeta origen 'scripts'.
# 3. Clasificar y mover archivos a carpetas (Datasets, Documents, Scripts) 
#    según su extensión utilizando un mapeo optimizado.
# 4. Foco Técnico: Pathlib, Shutil, Diccionarios y Gestión de Filesystem.
################################################################################

import os
import shutil
import platform
from pathlib import Path

# 1. CONFIGURACIÓN DE RUTAS AL ESCRITORIO (DESKTOP)
def get_desktop_path():
    if platform.system() == "Linux" and "microsoft" in platform.uname().release.lower():
        # Estamos en WSL2: Extraemos el usuario de Windows desde las variables de entorno de shell
        # Usualmente /mnt/c/Users/NombreUsuario
        win_user = os.popen("powershell.exe '$env:UserName'").read().strip()
        return Path(f"/mnt/c/Users/{win_user}/Desktop/15_automated_folder_sorter")
    else:
        # Estamos en Windows nativo
        return Path.home() / "Desktop" / "15_automated_folder_sorter"

base_path = get_desktop_path()

# Crear la carpeta si no existe para evitar errores de "File Not Found"
base_path.mkdir(parents=True, exist_ok=True)

print(f"\nTarget path: {base_path}")

# Definimos el origen dentro de esa carpeta del escritorio
source_path = base_path 

# 2. DICCIONARIO DE CLASIFICACIÓN (MAPPING)
extension_map = {
    '.csv': 'Datasets', '.json': 'Datasets', '.parquet': 'Datasets',
    '.pdf': 'Documents', '.docx': 'Documents', '.txt': 'Documents',
    '.sql': 'Scripts', '.sh': 'Scripts'
}

# 3. PREPARACIÓN DEL ENTORNO
# Creamos la carpeta principal y las subcarpetas de destino
base_path.mkdir(parents=True, exist_ok=True)
source_path.mkdir(parents=True, exist_ok=True)

for folder_name in set(extension_map.values()):
    (base_path / folder_name).mkdir(parents=True, exist_ok=True)

# 4. GENERACIÓN DE ARCHIVOS DE PRUEBA (TEST DATA)
test_files = [
    "sales_data.csv", "users_registry.json", "inventory_logs.parquet",
    "project_plan.pdf", "requirements_doc.docx", "dev_notes.txt",
    "chinook_queries.sql", "deploy_service.sh"
]

print(f"\n--- [STAGE 1] GENERANDO ARCHIVOS EN: {source_path} ---")
for file_name in test_files:
    full_file_path = source_path / file_name 
    full_file_path.touch()
    print(f"Creado: {file_name}")

# 5. LÓGICA DE ORGANIZACIÓN (CORE)
print("\n--- [STAGE 2] ORGANIZANDO ARCHIVOS ---")

for file in source_path.iterdir():
    if file.is_file():
        ext = file.suffix.lower()
        
        if ext in extension_map:
            dest_folder_name = extension_map[ext]
            target_dir = base_path / dest_folder_name
            
            # Movimiento: Origen -> Escritorio/15_automated_folder_sorter/...
            shutil.move(str(file), str(target_dir / file.name))
            
            print(f"✔ MOVED: {file.name:<25} ➔  {dest_folder_name}/")
        else:
            print(f"⚠ SKIPPED: {file.name} (Extensión no reconocida)")

print("\n################################################################################")
print(f"# PROCESO FINALIZADO. REVISA LA CARPETA EN TU ESCRITORIO.")
print("################################################################################")