import logging
import extract_clients as ec
import transform_clients as tc
import extract_openweather as ew
import transform_openweather as tw
import extract_energy_prices as ep
import transform_energy_prices as tp
import extract_power_data as eg




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


logger.info(f"Iniciando extraccion e ingesta de precios de luz en capa bronce de base de datos...")
ep.extract_energy_prices()


logger.info(f"Iniciando extraccion de precios de luz de capa bronze e ingesta de precios en capa silver...")
tp.transform_energy_prices()


logger.info(f"Iniciando extraccion de calculos de generacion e ingesta en capa silver...")
eg.extract_generation_data()