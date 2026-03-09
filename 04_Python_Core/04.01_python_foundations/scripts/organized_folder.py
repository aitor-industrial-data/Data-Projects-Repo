#Escribe un código que genere un diccionario llamado organized_folder donde:
#   1. Las claves sean los nombres de las carpetas (Documents, Database_Scripts, Python_Codes).
#   2.Los valores sean listas con los nombres de los archivos, pero sin la fecha inicial (solo el nombre y la extensión).

backup_files = [
    "20260101_report.pdf",
    "20260102_database.sql",
    "20260103_script.py",
    "20260104_schema.sql",
    "20260105_manual.pdf",
    "20260106_process.py"
]

rules = {
    "pdf": "Documents",
    "sql": "Database_Scripts",
    "py": "Python_Codes"
}

# 1. Inicializamos el diccionario con listas vacías usando las reglas
organized_folder = {}
for folder_name in rules.values():
    organized_folder[folder_name] = []

# 2. Procesamos los archivos
for line in backup_files:
    # Separamos la fecha del resto
    _, file_name = line.split('_', 1) 
    
    # Extraemos la extensión (usando split es más seguro que find)
    extension = file_name.split('.')[-1].lower()
    
    # Buscamos qué carpeta le toca según el diccionario 'rules'
    target_folder = rules.get(extension)
    
    # Si la extensión está en nuestras reglas, añadimos el archivo a la lista
    if target_folder:
        organized_folder[target_folder].append(file_name)

print(organized_folder)
