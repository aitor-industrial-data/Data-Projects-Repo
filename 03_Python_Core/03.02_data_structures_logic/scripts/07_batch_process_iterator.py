################################################################################
# 07_batch_process_iterator.py
# AUTOR: Aitor | Ingeniero Técnico Industrial | Data Engineer
# PROYECTO: Procesamiento por Lotes de Sensores Industriales (Python Core)
#
# ENUNCIADO:
# 1. Recorrer una lista de IDs de sensores con formatos inconsistentes.
# 2. Normalizar los datos eliminando espacios y estandarizando mayúsculas.
# 3. Extraer componentes del ID (Prefijo/Sufijo) para clasificación técnica.
# 4. Implementar lógica de salto (continue) para equipos en mantenimiento.
# 5. Generar un reporte alineado con formato profesional de consola.
# 6. Foco Técnico: Iteración (For Loops), Unpacking y String Formatting.
################################################################################

# Lista de origen simulando datos crudos de planta
sensor_data = [" temp_01 ", " PRES_02", "temp_03", "volt_01", "  PRES_05  ", "temp_04"]

for sensor in sensor_data:
    # 1. LIMPIEZA Y NORMALIZACIÓN
    # Eliminamos espacios en blanco y convertimos a mayúsculas para evitar errores de coincidencia
    clean_sensor = sensor.strip().upper()
    
    # 2. DESEMPAQUETADO (UNPACKING)
    # Separamos el nombre del sensor del número correlativo usando el guion bajo como delimitador 
    prefix, suffix = clean_sensor.split('_')
    
    # 3. LÓGICA DE EXCLUSIÓN POR MANTENIMIENTO
    # Según protocolo, los equipos terminados en '05' están fuera de servicio
    if suffix == '05':
        print(f"[ALERTA]     ID: {suffix} | MANTENIMIENTO REQUERIDO")
        continue # El bucle salta directamente al siguiente elemento
    
    # 4. CLASIFICACIÓN TÉCNICA
    # Asignamos etiquetas y valores simulados según el tipo de sensor detectado
    if prefix == 'TEMP':
        reading = '25 ºC'
        type_label = 'Temperatura'
    elif prefix == 'PRES':
        reading = '1.2 bar'
        type_label = 'Presión'
    else:
        reading = 'N/A'
        type_label = 'Desconocido'
        
    # 5. OUTPUT FORMATEADO
    # Usamos especificadores de formato (:<12) para garantizar que las columnas queden alineadas
    print(f"[PROCESANDO] ID: {suffix} | Tipo: {type_label:<12} | Valor: {reading}")

print("\n" + "#" * 80)
print("SISTEMA: Procesamiento de lote finalizado con éxito.")
print("#" * 80)