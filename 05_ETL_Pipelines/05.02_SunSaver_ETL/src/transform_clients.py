import pandas as pd
import logging

import db_manager


logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)

logger = logging.getLogger(__name__)
    


def transform_clients_bronze_to_silver(df_raw: pd.DataFrame) -> pd.DataFrame:
    """
    Capa Silver: Limpia y valida los datos de clientes.
    """
    try:
        if df_raw.empty:
            logger.warning("⚠️  Silver: El DataFrame de entrada está vacío. Nada que transformar.")
            return pd.DataFrame()
        
        # 1. Copiamos el DF para no modificar el original (buena práctica)
        df_silver = df_raw.copy()

        # 2. Filtro de calidad: Eliminamos filas que no tengan ID o coordenadas
        # (Si no hay coordenadas, no podremos llamar a PVGIS luego)
        df_silver = df_silver.dropna(subset=['client_id', 'latitude', 'longitude'])

        # 3. Limpieza de strings: Nombres en mayúsculas y sin espacios extra
        if 'name' in df_silver.columns:
            df_silver['name'] = df_silver['name'].str.strip().str.upper()

        # 4. Validación de tipos (Aseguramos que sean números)
        numeric_cols = ['latitude', 'longitude', 'peak_power_kw', 'efficiency']
        for col in numeric_cols:
            if col in df_silver.columns:
                df_silver[col] = pd.to_numeric(df_silver[col], errors='coerce')


        # 5. Transformación de negocio: Ejemplo, convertir eficiencia de 0-100 a 0-1
        # Si en el Excel alguien puso "20" en vez de "0.20"
        mask = df_silver['efficiency'] > 1
        df_silver.loc[mask, 'efficiency'] = df_silver.loc[mask, 'efficiency'] / 100

        logger.info(f"✅ Transformación completada: {len(df_silver)} registros transformados.")
        return df_silver

    except Exception as e:
        logger.error(f"❌ Error en la transformación Silver: {e}")
        return pd.DataFrame()
    


if __name__ == "__main__":
    logger.info(f"Iniciando extraccion de clientes de capa bronze e ingesta de clientes en capa silver...")
    raw_clients=db_manager.extract_from_db('raw_clients')
    