################################################################################
# 12_sqlalchemy_crud_lifecycle.py
# AUTOR: Aitor | Ingeniero Técnico Industrial | Data Engineer
# PROYECTO: Control Total de Ciclo de Vida de Datos (Python para Ingeniería)
#
# ENUNCIADO:
# 1. Desarrollar un sistema de gestión de datos utilizando el ORM SQLAlchemy 
#    para integrar una base de datos de origen (Source) con un modelo local (Target).
# 2. El objetivo es dominar las operaciones fundamentales CRUD (Create, Read, 
#    Update, Delete) asegurando la persistencia y calidad del dato.
# 3. El programa debe implementar las siguientes funcionalidades técnicas:
#    - Mapeo Objeto-Relacional (ORM): Definición de clases declarativas para 
#      estructurar la tabla 'Tracks' con tipos de datos estrictos.
#    - Ingesta Híbrida: Extracción de datos mediante SQL puro (text) desde una 
#      fuente externa y carga mediante objetos de Python en la base local.
#    - Limpieza de Datos Post-Ingesta: Aplicar lógica de negocio en Python para 
#      eliminar registros que no cumplan criterios de calidad (longitud mínima).
#    - Actualización Selectiva: Localización y modificación de registros 
#      específicos mediante filtros dinámicos del ORM.
# 4. GESTIÓN DE SESIONES Y TRANSACCIONES:
#    - Implementar un flujo robusto con manejo de excepciones (Try/Except/Finally).
#    - Uso de 'session.rollback()' para garantizar la integridad atómica en 
#      caso de fallo y 'session.close()' para la liberación de recursos.
#    - Optimización de carga mediante 'Batch Commits' tras el procesamiento de 
#      bloques de datos para minimizar el impacto en disco.
# 5. FOCO TÉCNICO: Abstracción de bases de datos con ORM, gestión avanzada de 
#    transacciones, filtrado en origen (SQL) vs filtrado en destino (Python).
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