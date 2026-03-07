raw_data = [
    "S01:25.5:OK", "S02:40.0:WARNING", "S03:error:CRITICAL", 
    "S04:15.2:OK", "S01:110.5:CRITICAL", "invalid_line", 
    "S05:-999:ERROR", "S02:35.8:OK", None, "S06:22:OK"
]

def parse_sensor_data(line):
    """Limpia y valida una sola línea. Devuelve un dict o None."""
    try:
        parts = line.split(":")
        if len(parts) != 3: return None
        
        sensor_id = parts[0]
        temp = float(parts[1])
        status = parts[2]
        
        # Validación de rango
        if -50 < temp < 150:
            return {"id": sensor_id, "temp": temp, "status": status}
    except (ValueError, TypeError, AttributeError):
        pass
    return None

def generate_report(data):
    clean_records = []
    discarded = 0
    
    # Procesamos una sola vez la lista
    for entry in data:
        parsed = parse_sensor_data(entry)
        if parsed:
            clean_records.append(parsed)
            # Alerta inmediata
            if parsed["status"] == "CRITICAL":
                print(f"[ALERTA] Sensor {parsed['id']} a {parsed['temp']} grados!")
        else:
            discarded += 1
            
    # Cálculos finales sobre datos limpios
    if clean_records:
        avg_temp = sum(r["temp"] for r in clean_records) / len(clean_records)
        print(f"\nTemperatura media: {avg_temp:.2f} grados")
    
    print(f"Lecturas descartadas: {discarded}")

generate_report(raw_data)

