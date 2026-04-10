import sqlite3
import urllib.request

# === 1. CONFIGURACIÓN DE LA BASE DE DATOS ===
# Establecemos conexión con el archivo de base de datos local
conn = sqlite3.connect('emaildb.sqlite')
cur = conn.cursor()

# Limpiamos la tabla anterior para asegurar una ejecución limpia desde cero
cur.execute('DROP TABLE IF EXISTS Counts')
cur.execute('CREATE TABLE Counts (org TEXT, count INTEGER)')

# === 2. CONFIGURACIÓN DE LA EXTRACCIÓN (HTTP) ===
url = 'http://www.py4e.com/code3/mbox.txt'

# Definimos cabeceras para simular un navegador y evitar el error 403 (Forbidden)
headers = {'User-Agent': 'Mozilla/5.0'}
solicitud = urllib.request.Request(url, headers=headers)

print(f'Conectando a: {url}...')

# === 3. PROCESAMIENTO DE DATOS (LECTURA Y TRANSFORMACIÓN) ===
try:
    with urllib.request.urlopen(solicitud) as manejador_archivo:
        for linea in manejador_archivo:
            # Convertimos bytes a texto y eliminamos espacios en blanco
            linea_texto = linea.decode().strip()
            
            # Filtro: Solo nos interesan las líneas que indican el remitente
            if not linea_texto.startswith('From: '): 
                continue
            
            # Transformación: Extraemos el dominio después del símbolo '@'
            # Ejemplo: "From: stephen.marquard@uct.ac.za" -> "uct.ac.za"
            partes = linea_texto.split()
            email = partes[1]
            dominio = email.split('@')[1]
            
            # === 4. CARGA DE DATOS (LÓGICA SQL) ===
            # Verificamos si la organización ya existe en la tabla
            cur.execute('SELECT count FROM Counts WHERE org = ? ', (dominio,))
            fila = cur.fetchone()
            
            if fila is None:
                # Si no existe, insertamos el primer registro
                cur.execute('INSERT INTO Counts (org, count) VALUES (?, 1)', (dominio,))
            else:
                # Si existe, incrementamos el contador actual
                cur.execute('UPDATE Counts SET count = count + 1 WHERE org = ?', (dominio,))

    # === 5. OPTIMIZACIÓN Y CIERRE ===
    # El commit se hace al final del bucle para mejorar drásticamente la velocidad de escritura
    conn.commit()
    print("Procesamiento completado con éxito.\n")

except Exception as e:
    print(f"Error durante la ejecución: {e}")

# Consulta final para mostrar el Top 10 de organizaciones con más correos
sqlstr = 'SELECT org, count FROM Counts ORDER BY count DESC LIMIT 10'

print('--- Ranking de Organizaciones ---')
for fila in cur.execute(sqlstr):
    print(f'Org: {fila[0]:<20} Mensajes: {fila[1]}')

# Cerramos los punteros y la conexión de forma segura
cur.close()
conn.close()