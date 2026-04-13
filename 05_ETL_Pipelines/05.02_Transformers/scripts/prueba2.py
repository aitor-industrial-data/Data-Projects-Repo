from sqlalchemy import create_engine, text, Column, Integer, String, Float
from sqlalchemy.orm import declarative_base, sessionmaker

# --- CONFIGURACIÓN DE MOTORES ---
engine = create_engine('sqlite:///CRUD_TRACK.db', echo=False)
engine_chinook = create_engine('sqlite:///Chinook_Sqlite.sqlite')

Base = declarative_base()

# --- DEFINICIÓN DEL MODELO ---
class Track(Base):
    __tablename__ = 'Tracks'
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String)
    composer = Column(String)
    album = Column(String)
    unit_price = Column(Float)

# Reinicio de tabla
Base.metadata.drop_all(engine)
Base.metadata.create_all(engine)

Session = sessionmaker(bind=engine)
session = Session()

try:
    print("--- PASO 1: READ & CREATE ---")
    with engine_chinook.connect() as connection:
        # [READ]: Consultamos datos de una fuente externa (Chinook)
        # Aplicamos un filtro estructural (IS NOT NULL) directamente en el origen
        query = text("""
            SELECT t.Name, t.Composer, t.UnitPrice, a.Title as AlbumTitle 
            FROM Track t 
            INNER JOIN Album a ON t.AlbumId = a.AlbumId 
            WHERE t.Composer IS NOT NULL
            LIMIT 20
        """)
        
        result = connection.execute(query)
        for row in result.mappings():
            # [CREATE]: Creamos una nueva instancia del objeto Track (Insert)
            new_track = Track(
                name=row['Name'], 
                composer=row['Composer'], 
                album=row['AlbumTitle'], 
                unit_price=row['UnitPrice']
            )
            session.add(new_track)
        
        # Confirmamos la creación masiva en la base de datos
        session.commit()
        print("Éxito: Datos limpios importados.")

    print("\n--- PASO 2: DELETE ---")
    # [READ]: Primero buscamos los registros que cumplen una regla de calidad
    # [DELETE]: Borramos registros cuyo compositor tiene menos de 5 caracteres
    short_names = session.query(Track).filter(text("length(composer) < 5")).all()
    
    for t in short_names:
        print(f"Eliminando por nombre corto: {t.composer}")
        session.delete(t)
    
    # Confirmamos la eliminación de los registros
    session.commit()
    print(f"Éxito: {len(short_names)} registros eliminados por regla de longitud.")

    print("\n--- PASO 3: UPDATE ---")
    # [READ]: Buscamos el registro específico que queremos modificar
    target_track = "Fast As a Shark"
    track_to_update = session.query(Track).filter_by(name=target_track).first()
    
    # [UPDATE]: Si el registro existe, modificamos su atributo unit_price
    if track_to_update:
        track_to_update.unit_price = 1.99
        # Confirmamos la actualización en la base de datos
        session.commit()
        print(f"Éxito: Precio actualizado para '{target_track}'.")

except Exception as e:
    # Gestión de errores: si algo falla en el CRUD, deshacemos los cambios pendientes
    session.rollback()
    print(f"Error Crítico: {e}")

finally:
    # Cerramos la sesión para liberar los recursos del sistema
    session.close()
    print("\n--- Proceso Finalizado: Sesión Cerrada ---")