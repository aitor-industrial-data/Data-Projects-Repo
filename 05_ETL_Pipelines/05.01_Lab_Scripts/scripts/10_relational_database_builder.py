################################################################################
# 10_relational_database_builder.py
# AUTOR: Aitor | Ingeniero Técnico Industrial | Data Engineer
# PROYECTO: Sistema de Normalización de Datos (ETL Pipeline)
#
# ENUNCIADO:
# 1. Desarrollar un script robusto para la carga y transformación de datos 
#    desde un archivo plano (CSV) a un motor de base de datos relacional SQLite3.
# 2. El objetivo es implementar un modelo de datos normalizado que elimine la 
#    redundancia mediante la gestión de claves foráneas (Foreign Keys).
# 3. El programa debe realizar los siguientes pasos técnicos:
#    - Inicializar el esquema de la base de datos eliminando tablas previas y 
#      definiendo Artist, Genre, Album y Track con restricciones UNIQUE.
#    - Procesar el archivo 'tracks.csv' utilizando el módulo csv de Python 
#      para garantizar la integridad de los campos con delimitadores complejos.
#    - Ejecutar una lógica de inserción "Relacional Selectiva":
#      a. Insertar/Ignorar registros en tablas maestras.
#      b. Recuperar IDs generados mediante consultas SELECT inmediatas.
#      c. Vincular registros en las tablas dependientes (Album y Track).
#    - Utilizar la sentencia 'INSERT OR REPLACE' para actualizar registros de 
#      pistas existentes asegurando que no haya duplicados por título.
# 4. Optimizar el rendimiento del sistema mediante una gestión eficiente de 
#    transacciones, realizando un 'commit' único tras el procesado completo.
# 5. FOCO TÉCNICO: Normalización SQL, Integridad Referencial, ETL y SQLite3.
################################################################################

import sqlite3
import csv

conn = sqlite3.connect('trackdb.sqlite')
cur = conn.cursor()

# Limpieza y creación de tablas
cur.executescript('''
DROP TABLE IF EXISTS Artist;
DROP TABLE IF EXISTS Genre;                   
DROP TABLE IF EXISTS Album;
DROP TABLE IF EXISTS Track;

CREATE TABLE Artist (
    id  INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT UNIQUE,
    name    TEXT UNIQUE
);

CREATE TABLE Genre (
    id  INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT UNIQUE,
    name    TEXT UNIQUE
);

CREATE TABLE Album (
    id  INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT UNIQUE,
    artist_id  INTEGER,
    title   TEXT UNIQUE
);

CREATE TABLE Track (
    id  INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT UNIQUE,
    title TEXT UNIQUE,
    album_id  INTEGER,
    genre_id  INTEGER,
    len INTEGER, rating INTEGER, count INTEGER
);
''')

# Usamos csv.reader para manejar correctamente las comas internas
with open('tracks.csv', encoding='utf-8') as handle:
    reader = csv.reader(handle)
    
    # next(reader) # Descomenta esta línea si tu CSV tiene cabecera

    for row in reader:
        if len(row) < 7: continue

        # Asignación limpia
        name    = row[0]
        artist  = row[1]
        album   = row[2]
        count   = row[3]
        rating  = row[4]
        length  = row[5]
        genre   = row[6]

        print(name, artist, album, count, rating, length, genre)

        # 1. ARTISTA (Fabricante)
        cur.execute('INSERT OR IGNORE INTO Artist (name) VALUES (?)', (artist,))
        cur.execute('SELECT id FROM Artist WHERE name = ?', (artist,))
        artist_id = cur.fetchone()[0]

        # 2. ÁLBUM (Gama/Línea)
        cur.execute('INSERT OR IGNORE INTO Album (title, artist_id) VALUES (?, ?)', (album, artist_id))
        cur.execute('SELECT id FROM Album WHERE title = ?', (album,))
        album_id = cur.fetchone()[0]

        # 3. GÉNERO (Categoría)
        cur.execute('INSERT OR IGNORE INTO Genre (name) VALUES (?)', (genre,))
        cur.execute('SELECT id FROM Genre WHERE name = ?', (genre,))
        genre_id = cur.fetchone()[0]

        # 4. TRACK (Componente final)
        cur.execute('''INSERT OR REPLACE INTO Track
            (title, album_id, genre_id, len, rating, count) 
            VALUES (?, ?, ?, ?, ?, ?)''', 
            (name, album_id, genre_id, length, rating, count))

# Commit fuera del bucle para ganar velocidad
conn.commit()
print("\nBase de datos generada correctamente.")
cur.close()