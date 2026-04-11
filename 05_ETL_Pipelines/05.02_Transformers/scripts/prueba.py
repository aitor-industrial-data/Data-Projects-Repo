import sqlite3

# 1. Conexión a la base de datos Chinook
# Asegúrate de que el archivo .db esté en la misma carpeta o usa la ruta completa
connection = sqlite3.connect('Chinook_Sqlite.sqlite')
cursor = connection.cursor()

# 2. Ejecutar una consulta SQL estándar
cursor.execute("SELECT * FROM artist LIMIT 5")

# 3. Recuperar y mostrar resultados
artists = cursor.fetchall()
print(artists)
for artist in artists:
    
    print(f"Artist Id: {artist[0]}")
    print(f"Artist Name: {artist[1]}")

connection.close()