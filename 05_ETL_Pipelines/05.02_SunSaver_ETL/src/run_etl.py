import logging
import extract_clients as ec
import transform_clients as tc
import extract_openweather as ew
import transform_openweather as tw
import extract_generation_data as eg
import db_manager as dm


logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)

logger = logging.getLogger(__name__)



logger.info(f"Iniciando extraccion e ingesta de clientes en capa bronce de base de datos...")
ec.extract_clients()


logger.info(f"Iniciando extraccion de clientes de capa bronze e ingesta de clientes en capa silver...")
tc.transform_clients()

logger.info(f"Iniciando extraccion e ingesta de clima en capa bronce de base de datos...")
ew.extract_openweather()


logger.info(f"Iniciando extraccion de clima de capa bronze e ingesta de clientes en capa silver...")
tw.transform_openweather()


logger.info(f"Iniciando extraccion de calculos de generacion e ingesta en capa silver...")
eg.extract_generation_data()