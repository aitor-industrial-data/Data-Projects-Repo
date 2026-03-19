################################################################################
# 21_string_cleaning_logic.py
# AUTOR: Aitor | Ingeniero Técnico Industrial | Data Engineer
# PROYECTO: Motor de Normalización de Metadatos (Python Core)
#
# ENUNCIADO:
# 1. Desarrollar un motor de limpieza (Data Scrubbing) para nombres de pistas.
# 2. Implementar sanitización de ruido mediante eliminación de caracteres 
#    especiales (*, #, $, etc.) y limpieza de espacios en extremos.
# 3. Normalizar la estructura interna de las cadenas eliminando espacios 
#    redundantes mediante segmentación (split/join).
# 4. Programar una lógica de "Casing Inteligente" para corregir textos en 
#    mayúsculas sostenidas, preservando siglas técnicas o geográficas (ej: USA).
# 5. Garantizar la integridad del proceso mediante la gestión de valores 
#    nulos (None) y cadenas vacías, asignando etiquetas de seguridad.
# 6. Foco Técnico: Data Cleaning, String Methods, Control de Flujo y 
#    Normalización de Esquemas.
################################################################################

raw_tracks = [
    "  Let  There Be   Rock  ", 
    "***Batalha Do Forte***", 
    "  (I Can't  Get No) Satisfaction  ",
    "   ",
    "STAIRWAY TO HEAVEN",
    "the USA",
    None
]

def clean_track_name(raw_list):
    chars_to_remove = '*#$%@$€'
    clean_list = []

    for track in raw_list:
        # 1. Detección de Nulos o Vacíos
        if track is None or not track.strip():
            clean_list.append("Unknown Track")
            continue

        # 2. Limpieza y Normalización
        # Usamos translate para mayor eficiencia en limpieza de caracteres
        table = str.maketrans('', '', chars_to_remove)
        track = track.translate(table).strip()

        # 3. Segmentación para normalizar espacios
        words = track.split()
        
        # 4. Lógica de Casing Inteligente
        original_full_upper = track.isupper()
        temp_clean_words = []
        
        for word in words:
            # Preservar siglas si no es un grito generalizado
            if word.isupper() and not original_full_upper:
                temp_clean_words.append(word)
            else:
                temp_clean_words.append(word.capitalize())

        clean_list.append(" ".join(temp_clean_words))
        
    return clean_list # Retornamos la data limpia

# --- Punto de entrada del script ---
if __name__ == "__main__":
    results = clean_track_name(raw_tracks)
    
    # Aquí es donde se decide qué hacer con la data (imprimir, en este caso)
    for i, track in enumerate(results, 1):
        print(f"Track {i:02}: {track}")