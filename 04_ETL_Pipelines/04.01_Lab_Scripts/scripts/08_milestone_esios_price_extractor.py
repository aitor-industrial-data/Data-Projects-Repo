################################################################################
# 08_milestone_esios_price_extractor.py
# AUTOR: Aitor | Ingeniero Técnico Industrial | Data Engineer
# PROYECTO: Ingesta Automatizada de Precios Eléctricos (Mercado PVPC)
#
# ENUNCIADO:
# Desarrollar un componente de extracción (Scraper/API Consumer) que actúe como
# la primera fase de un Pipeline ETL profesional. El objetivo es recuperar los 
# datos del Precio Voluntario para el Pequeño Consumidor (PVPC) publicados por 
# Red Eléctrica de España (ESIOS). 
#
# El script debe realizar las siguientes tareas técnicas:
# 1. Configurar una conexión segura mediante peticiones HTTP autenticadas.
# 2. Gestionar la respuesta JSON, navegando por estructuras de datos profundas.
# 3. Realizar una limpieza de datos crítica: 
#    - Conversión de formato decimal europeo (coma) a estándar de ingeniería (punto).
#    - Agregación de las tres componentes del precio (Energía + Peajes + Comercialización).
# 4. Normalizar las referencias temporales combinando campos de día y hora en 
#    objetos DateTime ISO-8601.
# 5. Implementar un control de errores robusto para garantizar la continuidad 
#    del proceso ante datos corruptos o caídas de red.
#
# FOCO TÉCNICO: Requests, Autenticación por Headers, Limpieza de Tipos, 
# Manejo de Fechas y Robustez de Pipeline.
################################################################################

import requests
import sys
from datetime import datetime

def main():
    """
    Lógica principal del proceso ETL: Extrae datos de la red, 
    transforma los tipos y estructura la carga final.
    """
    # 1. Configuración de la fuente de datos
    # Endpoint oficial de ESIOS para el archivo 70 (Precios PVPC)
    url = 'https://api.esios.ree.es/archives/70/download_json?locale=es'
    
    # 2. Configuración de Autenticación (Hito del Día 124)
    # Aunque este endpoint específico permite descarga libre, las APIs profesionales
    # requieren un Token. Dejamos la estructura lista para tu Token personal.
    api_token = "TU_TOKEN_ESIOS_AQUI" 
    headers = {
        'Accept': 'application/json',
        'Content-Type': 'application/json',
        'Authorization': f'Token token={api_token}',
    }

    print(f'\n[INFO] Iniciando ingesta de datos desde ESIOS (Red Eléctrica)...')

    try:
        # 3. Fase de Extracción (ETL - Extract)
        # Realizamos la petición enviando los headers de seguridad
        response = requests.get(url, headers=headers, timeout=15)
        
        # Validamos que el servidor responda con un estado 200 (Éxito)
        response.raise_for_status()
        
        print(f'[INFO] Conexión exitosa. Tamaño del paquete: {len(response.text)} caracteres.')

        # 4. Fase de Transformación (ETL - Transform)
        raw_data = response.json()
        normalized_data = []

        # Verificamos que la clave principal 'PVPC' existe para evitar errores de ejecución
        if 'PVPC' not in raw_data:
            raise KeyError("No se encontró la clave 'PVPC' en la respuesta del servidor.")

        for entry in raw_data['PVPC']:
            try:
                # LIMPIEZA DE DATOS: Pasamos de string con coma (es) a float con punto (en)
                # Usamos .get() con valor '0' para evitar que el script muera si falta un componente
                energy_comp = float(entry.get('PCB', '0').replace(',', '.'))
                tolls_comp = float(entry.get('TEUPCB', '0').replace(',', '.'))
                marketing_comp = float(entry.get('CCVPCB', '0').replace(',', '.'))
                
                # Cálculo del precio final del pool por MWh (Suma de componentes)
                total_price_mwh = round(energy_comp + tolls_comp + marketing_comp, 2)

                # NORMALIZACIÓN DE FECHA Y HORA
                # Extraemos la hora de inicio del formato "00:00 - 01:00"
                start_hour = entry['Hora'].split('-')[0].strip()
                date_string = f"{entry['Dia']} {start_hour}"
                
                # Convertimos a objeto datetime para poder operar/ordenar en el futuro
                date_object = datetime.strptime(date_string, "%d/%m/%Y %H")
                
                # Creamos el registro estructurado (Formato Diccionario/JSON)
                record = {
                    'timestamp': date_object.strftime("%Y-%m-%d %H:%M:%S"),
                    'price_mwh': total_price_mwh,
                    'unit': 'EUR/MWh'
                }
                normalized_data.append(record)
        
            except (ValueError, TypeError) as e:
                # Si una fila está mal, la saltamos pero continuamos con el resto
                print(f"[ADVERTENCIA] Saltando registro corrupto: {e}")
                continue

        # 5. Reporte de Resultados y Salida
        print("-" * 60)
        print(f"{'DATOS PROCESADOS DEL SISTEMA ELÉCTRICO':^60}")
        print("-" * 60)
        
        # Mostramos los primeros 3 registros como muestra de validación
        for item in normalized_data[:3]:
            print(f"Fecha: {item['timestamp']} | Precio: {item['price_mwh']} {item['unit']}")
        
        print(f"...")
        print(f"Total de registros procesados con éxito: {len(normalized_data)}")
        print("-" * 60)

    except requests.exceptions.HTTPError as http_err:
        print(f"[ERROR] Fallo en la conexión HTTP: {http_err}")
    except requests.exceptions.RequestException as req_err:
        print(f"[ERROR] Error de red o tiempo de espera agotado: {req_err}")
    except KeyError as k_err:
        print(f"[ERROR] El formato del JSON ha cambiado: {k_err}")
    except Exception as e:
        print(f"[ERROR] Fallo inesperado en el sistema: {e}")

if __name__ == "__main__":
    main()