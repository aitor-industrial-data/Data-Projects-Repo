import requests
import pandas as pd


def extract_weather():
   
    url = "https://api.preciodelaluz.org/v1/prices/all?zone=PCB"

    

       
    # Identificarnos ayuda a evitar bloqueos (Rate Limiting)
    headers = {
        'User-Agent': 'SunSaver-ETL-Project/1.0 (Contact: tu-email@ejemplo.com)',
        'Accept': 'application/json'
        }
    
    try:
        # Añadimos los headers a la petición
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()

        all_data = response.json()

        if not all_data:
            logger.error("OpenWeather devolvió una lista vacía — sin datos para procesar")
            raise ValueError("OpenWeather devolvió una lista vacía")

        logger.info(f"✅ Extracción completada: {len(all_data)} registros obtenidos.")
        return all_data

    except requests.exceptions.RequestException as e:
        logger.error(f"❌ Error de conexión con OpenWeather: {e}")
        raise

def extract_energy_prices():
    # URL oficial que elegimos
    url = "https://api.preciodelaluz.org/v1/prices/all?zone=PCB"
    
    print(f"🌐 Conectando a la API...")
    
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        data = response.json()
        
        prices_list = []
        for hour_range, info in data.items():
            # Extraemos '00', '01', etc.
            start_hour = hour_range.split("-")[0]
            
            prices_list.append({
                "hour": start_hour,
                "price_eur_mwh": float(info['price']),
                "price_eur_kwh": float(info['price']) / 1000
            })
            
        df = pd.DataFrame(prices_list)
        print("✅ ¡Datos reales extraídos!")
        return df

    except Exception as e:
        print(f"❌ Sigue fallando: {e}")
        return None

if __name__ == "__main__":
    df_precios = extract_energy_prices()
    if df_precios is not None:
        print(df_precios.head())