# Iterating through your programs
apps = {"DB": "SQLite", "IDE": "VS Code", "Container": "Docker"}

for category, name in apps.items():
    print(f"For {category} I use {name}")

    # Si 'pressure' no existe, devuelve None o un valor por defecto que tú elijas
current_pressure = sensor.get("pressure", 0.0) 
print(f"Pressure is: {current_pressure}")