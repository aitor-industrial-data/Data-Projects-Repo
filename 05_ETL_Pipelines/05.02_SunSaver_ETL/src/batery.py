import pandas as pd
import numpy as np
import logging
import sqlite3
from datetime import datetime
import db_manager

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)

logger = logging.getLogger(__name__)


def extract_gold_fact_energy_forecast_from_db(table_name: str = 'gold_fact_energy_forecast') -> pd.DataFrame:
    
    try:
        db_path = db_manager.get_db_path()
        
        # 1. Conexión a la DB (usando str por seguridad de tipos)
        with sqlite3.connect(str(db_path)) as conn:
            # 2. Leemos la tabla entera directamente a un DataFrame
            query = f"""
            SELECT *
            FROM {table_name}
            """
            df = pd.read_sql_query(query, conn)
            
        logger.info(f"✅ Extracción exitosa: {len(df)} registros extraidos de DB")
        return df

    except Exception as e:
        logger.error(f"❌ Error extrayendo de DB: {e}")
        return pd.DataFrame() # Devolvemos un DF vacío si falla

import pandas as pd

def simulate_battery_logic(df_data, battery_capacity_kwh, initial_soc_kwh, efficiency=0.95):
    """
    Simula el estado de la batería hora a hora, pero separando por cada cliente.
    """
    
    def _process_single_client(client_group):
        """Función interna para procesar el hilo temporal de UN solo cliente."""
        soc_history = []
        current_soc = initial_soc_kwh
        
        # Ordenamos cronológicamente el bloque del cliente
        client_group = client_group.sort_values('forecast_time_utc').reset_index(drop=True)

        for _, row in client_group.iterrows():
            net_energy = row['pv_power_gen_kw'] - row['power_consumption_kw']
            
            charge_action = 0
            discharge_action = 0
            
            if net_energy > 0:
                available_space = battery_capacity_kwh - current_soc
                charge_action = min(net_energy, available_space) * efficiency
                current_soc += charge_action
            
            elif net_energy < 0:
                energy_needed = abs(net_energy)
                discharge_action = min(energy_needed, current_soc) * efficiency
                current_soc -= (discharge_action / efficiency)
                
            soc_history.append({
                'client_id': row['client_id'], # Mantenemos el ID para el JOIN posterior
                'forecast_time_utc': row['forecast_time_utc'],
                'initial_soc_kwh': round(current_soc + (discharge_action if net_energy < 0 else -charge_action), 3),
                'battery_interaction_kw': round(charge_action - discharge_action, 3),
                'final_soc_kwh': round(current_soc, 3),
                'soc_percentage': round((current_soc / battery_capacity_kwh) * 100, 2)
            })
        return pd.DataFrame(soc_history)

    # --- MAGIA DE PANDAS ---
    # Aplicamos la función anterior a cada grupo de cliente y concatenamos los resultados
    df_results = df_data.groupby('client_id', group_keys=False).apply(_process_single_client)
    
    return df_results.reset_index(drop=True)

# Ejemplo de uso con tus datos de la DB
# df_final = simulate_battery_logic(df_gold, 10.0, 5.0)

def run_battery_transformation():
    # 1. Cargar datos de la DB (Mes 5: Databases with Python)
    # Aquí deberías tener ya una tabla con generación + precios
    try:
        # Simulamos carga de datos para el ejemplo
        #df = pd.read_sql("SELECT * FROM v_generation_prices", conn)
        logger.info("Calculando estrategia de batería...")
        
        # Parámetros del cliente (Ejemplo basado en tus metadatos)
        CAPACITY = 10.0 # kWh
        START_SOC = 5.0 # Empieza al 50%
        
        # [Aquí llamarías a simulate_battery_logic]
        
        # 3. Guardar en SQL (Capa Gold)
        # Este es el entregable que añade valor al proyecto
        logger.info("✅ Estrategia calculada y guardada en SQL.")
        
    except Exception as e:
        logger.error(f"Error en la transformación de batería: {e}")

if __name__ == "__main__":
    df=extract_gold_fact_energy_forecast_from_db()
    print(simulate_battery_logic(df,100,20))
    print(df)