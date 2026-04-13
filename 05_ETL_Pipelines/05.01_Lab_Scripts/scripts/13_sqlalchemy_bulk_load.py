################################################################################
# 13_sqlalchemy_bulk_load.py
# AUTOR: Aitor | Ingeniero Técnico Industrial | Data Engineer
# PROYECTO: Optimización de Carga Masiva (Bulk Load)
#
# ENUNCIADO:
# 1. Desarrollar un proceso de carga optimizado para manejar volúmenes mayores
#    de datos sin comprometer el rendimiento del sistema de archivos.
# 2. Implementar una estrategia de "Commit por Lotes" (Batching) para reducir
#    el overhead de transacciones en SQLite.
# 3. El programa debe implementar las siguientes funcionalidades técnicas:
#    - Ingesta masiva desde 'Source' a 'Target' con seguimiento de registros.
#    - Lógica de Batching: Ejecución de 'session.commit()' cada 500 registros 
#      para optimizar el uso de memoria y E/S.
#    - Limpieza post-carga mediante filtrado por 'Blacklist' y actualización
#      selectiva de registros.
# 4. FOCO TÉCNICO: Eficiencia de inserción, escalabilidad de transacciones y
#    gestión de integridad referencial en procesos de carga pesada.
################################################################################

from sqlalchemy import create_engine, text, Column, Integer, String, Float
from sqlalchemy.orm import declarative_base, sessionmaker

# --- CONFIGURACIÓN DE MOTORES (ENGINE CONFIGURATION) ---
# Usamos 'source' para la base de datos de origen y 'target' para la de destino
source_engine = create_engine('sqlite:///Chinook_Sqlite.sqlite')
target_engine = create_engine('sqlite:///CRUD_TRACK.db', echo=False)

Base = declarative_base()

# --- DEFINICIÓN DEL MODELO (ENTITY DEFINITION) ---
class Track(Base):
    """Modelo ORM para la tabla Tracks en la base de datos Target"""
    __tablename__ = 'Tracks'
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String)
    composer = Column(String)
    album = Column(String)
    genre = Column(String)
    unit_price = Column(Float)

# Inicialización del esquema DDL en la base de datos Target
Base.metadata.drop_all(target_engine)
Base.metadata.create_all(target_engine)

# Configuración de la sesión vinculada al Target
Session = sessionmaker(bind=target_engine)
session = Session()


try:
    #--- PASO 1: READ & CREATE
    print("--- PASO 1: READ & CREATE (Ingesta desde Source a Target) ---")
    with source_engine.connect() as connection:
        # [READ]: Extracción con filtrado estructural en el origen (Source)
        query = text("""
            SELECT t.Name, t.Composer, t.UnitPrice, g.name as GenreName, a.Title as AlbumTitle 
            FROM Track t 
            INNER JOIN Album a ON t.AlbumId = a.AlbumId 
            INNER JOIN Genre g ON t.GenreId = g.GenreId          
            WHERE t.Composer IS NOT NULL
            
        """)
        
        result = connection.execute(query)

        records_count = 0
        for row in result.mappings():
            # [CREATE]: Instanciación y preparación de carga en el Target
            new_track = Track(
                name=row['Name'], 
                composer=row['Composer'], 
                album=row['AlbumTitle'], 
                genre=row['GenreName'], 
                unit_price=row['UnitPrice']
            )
            session.add(new_track)

            records_count += 1
            BATCH_SIZE = 500  # Tamaño del lote para el commit
            # --- Lógica de Batching ---
            if records_count % BATCH_SIZE == 0:
                session.commit()
                print(f"Batch procesado: {records_count} registros cargados...")
        
        session.commit() # Consolidación de datos en Target
        print("Éxito: Datos importados correctamente en la base de datos Target.")


    #--- PASO 2: DELETE
    print("\n--- PASO 2: DELETE (Limpieza de calidad en Target) ---")
    # [DELETE]: Aplicación de reglas de limpieza post-carga
    # Lista de compositores prohibidos por derechos de autor o política de empresa
    blacklist = ["Compay Segundo", "Unknown Artist"]

    tracks_to_check = session.query(Track).filter(Track.composer.in_(blacklist)).all()
    for t in tracks_to_check:
        print(f"Eliminando {t.composer} por políticas de contenido.")
        session.delete(t)

    print(f"Éxito: {len(tracks_to_check)} registros eliminados en Target.")


    #--- PASO 3: UPDATE
    print("\n--- PASO 3: UPDATE (Modificación en Target) ---")
    # [UPDATE]: Mantenimiento de registros específicos
    target_track_name = "Fast As a Shark"
    track_to_update = session.query(Track).filter_by(name=target_track_name).first()
    
    if track_to_update:
        track_to_update.unit_price = 1.99
        session.commit()
        print(f"Éxito: Registro '{target_track_name}' actualizado.")

except Exception as e:
    session.rollback()
    print(f"Error Crítico en el Pipeline: {e}")

finally:
    session.close()
    print("\n--- Proceso Finalizado: Sesión Cerrada ---")