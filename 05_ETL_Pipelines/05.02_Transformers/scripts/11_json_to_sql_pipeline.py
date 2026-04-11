################################################################################
# 11_json_to_sql_pipeline.py
# AUTOR: Aitor | Ingeniero Técnico Industrial | Data Engineer
# PROYECTO: Normalización y Carga Optimizada en Bases de Datos (Python Core)
#
# ENUNCIADO:
# 1. Desarrollar un pipeline ETL que transforme datos de un archivo JSON plano 
#    en un modelo relacional normalizado de SQLite.
# 2. El objetivo es procesar un registro de membresías (Roster) estructurando 
#    la información en tres tablas: 'User', 'Course' y 'Member'.
# 3. El programa debe implementar las siguientes funcionalidades técnicas:
#    - Definición del esquema DDL mediante 'executescript' para asegurar 
#      la integridad de las tablas en cada ejecución.
#    - Gestión de relaciones N:M (muchos a muchos) mediante una tabla intermedia 
#      ('Member') que vincula usuarios y cursos con roles específicos.
#    - Uso de 'INSERT OR IGNORE' y 'INSERT OR REPLACE' para el manejo eficiente 
#      de claves únicas y resolución de conflictos de datos duplicados.
#    - Resolución dinámica de llaves foráneas (Foreign Keys) recuperando IDs 
#      generados automáticamente tras la inserción.
# 4. OPTIMIZACIÓN DE RENDIMIENTO:
#    - Implementar una estrategia de "Commit por Bloques" (Batch Processing).
#    - Agrupar las transacciones (ej. cada 50 registros) para reducir el 
#      overhead de E/S en el sistema de archivos y acelerar la carga.
# 5. FOCO TÉCNICO: Modelado de datos relacionales, persistencia con SQLite3, 
#    procesamiento de JSON y optimización de transacciones SQL.
################################################################################

import json
import sqlite3

# 1. Conexión a la base de datos
conn = sqlite3.connect('rosterdb.sqlite')
cur = conn.cursor()

# 2. Configuración del Esquema (DDL)
# Usamos executescript para ejecutar varias sentencias de una vez
cur.executescript('''
DROP TABLE IF EXISTS User;
DROP TABLE IF EXISTS Member;
DROP TABLE IF EXISTS Course;

CREATE TABLE User (
    id     INTEGER PRIMARY KEY,
    name   TEXT UNIQUE
);

CREATE TABLE Course (
    id     INTEGER PRIMARY KEY,
    title  TEXT UNIQUE
);

CREATE TABLE Member (
    user_id     INTEGER,
    course_id   INTEGER,
    role        INTEGER,
    PRIMARY KEY (user_id, course_id)
)
''')

# 3. Selección y carga del archivo de origen
fname = input('Enter file name: ')
if len(fname) < 1:
    fname = 'roster_data.json'

try:
    str_data = open(fname).read()
    json_data = json.loads(str_data)
except Exception as e:
    print(f"Error al leer el archivo: {e}")
    exit()

# --- CONFIGURACIÓN DE OPTIMIZACIÓN ---
count = 0
batch_size = 50  # Tamaño del bloque para el commit
# -------------------------------------

for entry in json_data:

    name = entry[0]
    title = entry[1]
    role = entry[2]

    print(name,title,role)

    # Inserción en User: 'IGNORE' evita errores si el nombre ya existe
    cur.execute('''INSERT OR IGNORE INTO User (name)
        VALUES ( ? )''', ( name, ) )
    cur.execute('SELECT id FROM User WHERE name = ? ', (name, ))
    user_id = cur.fetchone()[0]

    # Inserción en Course
    cur.execute('''INSERT OR IGNORE INTO Course (title)
        VALUES ( ? )''', ( title, ) )
    cur.execute('SELECT id FROM Course WHERE title = ? ', (title, ))
    course_id = cur.fetchone()[0]

    # Inserción en Member: 'REPLACE' actualiza el rol si la combinación ya existe
    cur.execute('''INSERT OR REPLACE INTO Member
        (user_id, course_id, role) VALUES ( ?, ?, ? )''',
        ( user_id, course_id, role) )

    # 4. Lógica de Commit por Bloques
    count += 1
    if count % batch_size == 0:
        conn.commit()
        print(f"Progreso: {count} registros procesados...")

# 5. Commit final y limpieza
# Fundamental para guardar los últimos registros que no completaron un bloque
conn.commit()
print(f"Carga finalizada. Total: {count} registros.")
cur.close()
conn.close()