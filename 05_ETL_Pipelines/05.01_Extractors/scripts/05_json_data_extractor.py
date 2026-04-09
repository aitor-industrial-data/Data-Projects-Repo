################################################################################
# 05_json_data_extractor.py
# AUTOR: Aitor | Ingeniero Técnico Industrial | Data Engineer
# PROYECTO: Pipeline de Ingesta JSON para Análisis de Métricas
#
# ENUNCIADO:
# Desarrollar un componente de ingesta que consuma una API REST o endpoint JSON
# para auditar métricas de participación. El sistema debe:
# 1. Realizar una petición HTTP persistente utilizando la librería 'requests'.
# 2. Validar la integridad de la respuesta (Status Codes).
# 3. Mapear el esquema JSON dinámico para extraer el campo 'count' dentro de la 
#    entidad 'comments'.
# 4. Procesar la información mediante listas de comprensión para optimizar 
#    el rendimiento de memoria.
# 5. Generar un reporte técnico con el volumen de datos y el agregado final.
#
# FOCO TÉCNICO: Consumo de APIs, List Comprehensions, Robustez de Red.
################################################################################

import requests
import sys

def main():
    # 1. Configuración de la fuente de datos
    # URL por defecto del curso de Michigan
    default_url = 'http://py4e-data.dr-chuck.net/comments_2383801.json'
    
    url = input(f'Introduzca la URL [Enter para default]: ').strip()
    if not url:
        url = default_url

    print(f'\n[INFO] Iniciando conexión con: {url}')

    try:
        # 2. Extracción (Fase Extract del Robot ETL)
        # requests maneja automáticamente SSL y decodificación
        respuesta = requests.get(url, timeout=10)
        
        # Validamos que el servidor respondió correctamente (200 OK)
        respuesta.raise_for_status()
        
        print(f'[INFO] Conexión exitosa. Tamaño: {len(respuesta.text)} caracteres.')

        # 3. Transformación (Fase Transform)
        # .json() convierte la respuesta directamente en un diccionario
        datos = respuesta.json()
        
        # Obtenemos la lista de comentarios (seguro ante claves inexistentes)
        comentarios = datos.get('comments', [])
        
        # Técnica PRO: Usamos List Comprehension para mayor velocidad
        # Extraemos el valor 'count' solo si existe en el ítem
        valores = [int(item['count']) for item in comentarios if 'count' in item]

        # 4. Reporte de Resultados
        print("-" * 40)
        print(f"ESTADÍSTICAS DEL DATASET")
        print("-" * 40)
        print(f"Items procesados: {len(valores)}")
        print(f"Suma acumulada:   {sum(valores)}")
        print("-" * 40)

    except requests.exceptions.HTTPError as err:
        print(f"[ERROR] Error HTTP: {err}")
    except requests.exceptions.RequestException as e:
        print(f"[ERROR] Error de red o conexión: {e}")
    except KeyError:
        print("[ERROR] El JSON no tiene el formato esperado ('comments' -> 'count')")
    except Exception as e:
        print(f"[ERROR] Error inesperado: {e}")

if __name__ == "__main__":
    main()