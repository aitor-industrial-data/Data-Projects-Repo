# FASE EXTRACT (Fuente B): Simulación de Generación Fotovoltaica
# Esta función actúa como un gemelo digital de una planta solar, consultando el sistema 
# PVGIS de la Comisión Europea. Utiliza modelos de irradiación satelital históricos 
# para estimar la producción horaria (Wh) en función de la ubicación geográfica (lat/lon) 
# y la potencia instalada (peak_power). El objetivo es obtener un perfil de generación 
# teórico para contrastarlo con los precios reales del mercado eléctrico.


def extract_solar_forecast(lat, lon, peak_power=50):
    """Extrae la producción estimada hora a hora de PVGIS."""
    url = "https://re.jrc.ec.europa.eu/api/v2/seriescalc"
    
    params = {
        "lat": lat,
        "lon": lon,
        "peakpower": peak_power,
        "loss": 14,
        "outputformat": "json",
        "startyear": 2020, # Usamos un año de referencia histórico cercano
        "endyear": 2020
    }
    
    try:
        response = requests.get(url, params=params, timeout=20)
        response.raise_for_status()
        data = response.json()
        
        # PVGIS devuelve mucha info, nos interesan ['outputs']['hourly']
        hourly_data = data.get('outputs', {}).get('hourly', [])
        return hourly_data
        
    except Exception as e:
        logger.error(f"Error extrayendo Fuente B (PVGIS): {e}")
        return []