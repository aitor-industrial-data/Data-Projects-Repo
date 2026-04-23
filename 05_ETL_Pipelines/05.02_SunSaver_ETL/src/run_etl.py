import logging
import extract_clients as ec
import transform_clients as tc
import db_manager as dm


logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)

logger = logging.getLogger(__name__)



logger.info(f"Iniciando extraccion e ingesta de clientes en base de datos...")
clientes=ec.extract_clients_from_excel()
ec.ingest_clients_to_bronze(clientes,'raw_clients')

logger.info(f"Iniciando extraccion de clientes de capa bronze e ingesta de clientes en capa silver...")
bronce=dm.extract_from_db('raw_clients')
silver=tc.transform_clients_bronze_to_silver(bronce)
tc.load_df_to_db(silver, 'clean_clients')
#print(silver)