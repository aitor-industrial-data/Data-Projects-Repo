import pandas as pd
import pvlib
from datetime import datetime
import sqlite3
import json
import logging
from sqlalchemy import create_engine, text
import numpy as np

import db_manager
import pv_generation_engine as pvgen

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)

logger = logging.getLogger(__name__)


def get_merged_silver_data(table_name_1: str = 'clean_clients', table_name_2: str = 'clean_weather') -> pd.DataFrame:
    """
    Extrae solo las ultimas lecturas de cada cliente y las devuelve como DataFrame.
    """
    try:
        db_path = db_manager.get_db_path()
        
        # 1. Conexión a la DB (usando str por seguridad de tipos)
        with sqlite3.connect(str(db_path)) as conn:
            # 2. Leemos la tabla entera directamente a un DataFrame
            query = f"""
            SELECT c.*,
                w.unix_time,
                w.forecast_time_utc,
                w.temp_celsius,          
                w.humidity_pct,        
                w.clouds_pct,        
                w.rain_prob_norm,        
                w.wind_speed_mps,          
                w.weather_id,          
                w.weather_main,           
                w.weather_description,
                w.is_daylight             
            FROM {table_name_1} AS c
            INNER JOIN {table_name_2} AS w ON c.client_id = w.client_id
            """
            df = pd.read_sql_query(query, conn)
            
        logger.info(f"✅ Extracción exitosa: {len(df)} registros extraidos de DB")
        return df

    except Exception as e:
        logger.error(f"❌ Error extrayendo de DB: {e}")
        return pd.DataFrame() # Devolvemos un DF vacío si falla
    


def transform_pv_generation(df_raw: pd.DataFrame) -> pd.DataFrame:
    """
    Calculo energetico
    """
    try:
        if df_raw.empty:
            return pd.DataFrame()
        
        df = df_raw.copy()
        
        data_to_clean = []
        
        for index, row in df.iterrows(): 
            # 1. Calcular la posición del sol (altura y dirección) para el instante dado
            alfa, azimuth  = pvgen.calculate_solar_position(row['latitude'],row['longitude'],row['forecast_time_utc'])

            # 2. Aplicas el "Candado de Ingeniería": Filtro de elevación mínima
            # Se usa < 2° porque cerca del horizonte los modelos físicos pierden precisión
            if alfa < 2:
                ghi = 0.0
                dni = 0.0
                dhi = 0.0
                poa = 0.0
                p_gen = 0.0
            else:
               # Si el sol está lo suficientemente alto para generar energía y cálculos fiables:
                
                # 1. Estimar la Radiación Global Horizontal (GHI) ajustada por nubosidad y tipo de fenómeno (Weather ID)
                ghi = pvgen.calculate_ghi(alfa, row['clouds_pct'], row['weather_id'])
                
                # 2. Descomponer la GHI en sus vectores Directo (DNI) y Difuso (DHI) mediante el modelo de Erbs
                dni, dhi = pvgen.decompose_erbs(ghi, alfa, row['forecast_time_utc'])
                
                # 3. Transponer las componentes al plano del panel (POA) considerando ángulo, orientación y albedo
                poa = pvgen.calculate_total_poa(dni, dhi, ghi, alfa, azimuth, row['angle'], row['aspect'])
                
                # 4. Calcular la temperatura de operación de la célula (Tcell) integrando el enfriamiento por convección (Viento)
                t_cell = pvgen.calculate_t_cell(row['temp_celsius'], row['wind_speed_mps'], poa)
                
                # 5. Calcular la potencia final (AC/DC) aplicando coeficientes de temperatura y pérdidas de eficiencia del sistema
                p_gen, pr = pvgen.calculate_power_output(poa, t_cell, row['pv_peak_power_kw'], row['loss_pct'])
                
                # 6. Simula el consumo dinámico: aplica curvas de carga horarias y el incremento de potencia por refrigeración ante altas temperaturas.
                p_con = pvgen.calculate_industrial_consumption(row['forecast_time_utc'], row['nominal_load_kw'], row['temp_celsius'])
            
            entry = {
                'client_id': row['client_id'],
                'unix_time': row['unix_time'],
                'forecast_time_utc': row['forecast_time_utc'],
                't_cell_celsius': round(t_cell,3),
                'poa_wm2': round(poa, 3),
                'pv_power_gen_kw': round(p_gen, 3),
                'pv_performance_ratio': round(pr, 3),
                'power_con_kw': round(p_con, 3),
                'self_consumption_kw':round(min(p_gen, p_con),3),
                'grid_export_kw':round(max(0, p_gen - p_con),3),
                'grid_import_kw':round(max(0, p_con - p_gen),3),
                'calculated_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                }
            
            data_to_clean.append(entry)
            
        df = pd.DataFrame(data_to_clean)
        
        return df
    

    except Exception as e:
        logger.error(f"❌ Error en el motor de cálculo PV: {e}")
        return pd.DataFrame()


def load_generation_to_silver(df: pd.DataFrame, table_name: str = "calculated_generation") -> bool:
    """
    Almacena los cálculos de rendimiento energético en la DB.
    Usa PK compuesta (client_id, unix_time) para evitar duplicados en el histórico.
    """
    db_path = db_manager.get_db_path()
    
    try:
        if df.empty:
            logger.warning(f"⚠️  DataFrame de generación vacío para '{table_name}'.")
            return False

        # 1. Preparación de datos (Copia para no mutar el original)
        df_sql = df.copy()
        
        # Aseguramos que forecast_time sea string si viene como datetime
        if pd.api.types.is_datetime64_any_dtype(df_sql['forecast_time_utc']):
            df_sql['forecast_time_utc'] = df_sql['forecast_time_utc'].dt.strftime('%Y-%m-%d %H:%M:%S')

        engine = create_engine(f"sqlite:///{db_path}")

        with engine.begin() as connection:
            # 2. Creación de tabla específica para GENERACIÓN
            create_table_query = f"""
            CREATE TABLE IF NOT EXISTS {table_name} (
                client_id               TEXT NOT NULL,
                unix_time               INTEGER NOT NULL,
                forecast_time_utc       TEXT NOT NULL,
                pv_power_gen_kw         REAL,
                pv_performance_ratio    REAL,
                poa_wm2                 REAL,
                t_cell_celsius          REAL,
                power_con_kw            REAL,
                self_consumption_kw     REAL,
                grid_export_kw          REAL,
                grid_import_kw          REAL,
                calculated_at           TEXT NOT NULL,
                PRIMARY KEY (client_id, unix_time)
            )
            """
            connection.execute(text(create_table_query))
            
            # 3. UPSERT (Insert or Replace)
            data = df_sql.to_dict(orient='records')
            
            # Construimos la query dinámicamente basada en las columnas del DF
            columns = list(df_sql.columns)
            placeholders = [f":{col}" for col in columns]
            
            upsert_query = text(f"""
                INSERT OR REPLACE INTO {table_name} 
                ({', '.join(columns)}) 
                VALUES ({', '.join(placeholders)})
            """)
            
            connection.execute(upsert_query, data)
        
        logger.info(f"✅ Generación guardada en SQL: {len(df)} registros en '{table_name}'.")
        return True

    except Exception as e:
        logger.error(f"❌ Error cargando generación a Silver: {e}")
        return False


def extract_generation_data() -> bool:
    try:
        # 1. Extracción (Capa Bronze)
        pv_genetation=get_merged_silver_data()
        
        # 2. Transformación (Limpieza y tipos)
        pv_genetation= transform_pv_generation(pv_genetation)
        
        # 3. Carga (Capa Silver)
        load_generation_to_silver(pv_genetation)
        
        return True

    except Exception as e:
        # Registramos el error con detalle para debuguear después
        logger.error(f"❌ Error crítico en el pipeline de extract_generation_data: {e}")
        return False

if __name__ == "__main__":

    logger.info(f"Iniciando extracción e ingesta de cálculos de rendimiento...")
    extract_generation_data()
    