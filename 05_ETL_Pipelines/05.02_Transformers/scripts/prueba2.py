from sqlalchemy import create_engine, text



# El nombre del archivo debe ser exacto (Chinook_Sqlite.sqlite)
engine = create_engine('sqlite:///Chinook_Sqlite.sqlite') 

try:
    # Usamos .begin() para que maneje la transacción automáticamente
    with engine.connect() as connection:
        # Optimizamos la query: El conteo se hace en la DB, no en Python
        query = text("SELECT COUNT(TrackId),* AS total FROM Track")
        
        result = connection.execute(query)
        
        # Al ser un conteo, solo esperamos una fila
        row = result.mappings()
        print(row)
        if row:
            print(f"Número total de tracks: {row['total']}")
            
except Exception as e:
    print(f"Error de conexión o consulta: {e}")