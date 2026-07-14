################################################################################
# 01_http_socket_connector.py
# AUTOR: Aitor | Ingeniero Técnico Industrial | Data Engineer
# PROYECTO: Cliente de Red de Bajo Nivel (Python para Ingeniería)
#
# ENUNCIADO:
# 1. El script debe establecer una conexión de red directa (Socket) con un
#    servidor web externo utilizando el protocolo TCP/IP.
# 2. El objetivo es recuperar un recurso específico (archivo .txt) mediante 
#    el envío manual de una solicitud HTTP/1.0.
# 3. El programa debe realizar los siguientes pasos técnicos:
#    - Configurar un socket de tipo AF_INET y SOCK_STREAM.
#    - Conectar al host 'data.pr4e.org' a través del puerto estándar 80.
#    - Codificar y enviar una cadena de comando GET que incluya la ruta 
#      '/intro-short.txt' y la cabecera 'Host' obligatoria.
#    - Implementar un bucle de recepción (recv) para capturar los datos en 
#      fragmentos (chunks) de 512 bytes.
#    - Decodificar los bytes recibidos a formato UTF-8 y mostrarlos por consola.
# 4. Asegurarse de cerrar la conexión del socket al finalizar la transferencia.
# 5. FOCO TÉCNICO: Protocolos de red, manejo de Sockets y estándar HTTP/1.1.
################################################################################

import socket

# 1. Creamos el objeto socket (IPv4 y flujo de datos TCP)
mysock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

# 2. Establecemos la conexión con el servidor y el puerto HTTP (80)
try:
    mysock.connect(('data.pr4e.org', 80))
    print("--- Conexión establecida con éxito ---\n")
    
    # 3. Preparamos el comando GET siguiendo el estándar estricto
    # Usamos \r\n (Carriage Return + Line Feed) que es el estándar de Internet
    comando = 'GET /intro-short.txt HTTP/1.0\r\nHost: data.pr4e.org\r\n\r\n'
    
    # Enviamos el comando codificado en bytes (UTF-8)
    mysock.send(comando.encode())

    # 4. Bucle para recibir la respuesta del servidor
    while True:
        data = mysock.recv(512) # Recibimos en trozos de 512 bytes
        if len(data) < 1:
            break # Si no llega más data, cerramos el bucle
        
        # Decodificamos de bytes a string para poder leerlo
        print(data.decode(), end='')

except Exception as e:
    print(f"Error en la conexión: {e}")

finally:
    # 5. Cerramos el socket siempre, ocurra o no un error
    mysock.close()
    print("\n\n--- Conexión cerrada ---")