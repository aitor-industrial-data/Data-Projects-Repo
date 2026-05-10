import pandas as pd
import pvlib
import numpy as np

from logger_config import setup_logging


logger = setup_logging()


def calculate_solar_position(latitude, longitude, forecast_time_utc):
    """
    Calcula la elevación solar (alfa) y el azimut utilizando pvlib.
    Incluye manejo de excepciones para asegurar la continuidad del ETL.
    """
    try:
        # 1. Convertir forecast_time a objeto datetime de Pandas (UTC)
        dt = pd.to_datetime(forecast_time_utc, utc=True)
        
        # 2. Obtener la posición del sol
        # get_solarposition devuelve un DataFrame con 'elevation', 'azimuth', etc.
        sol_pos = pvlib.solarposition.get_solarposition(dt, latitude, longitude)

        # Extraer valores individuales
        azimuth_solar = float(sol_pos['azimuth'].values[0])
        alfa = float(sol_pos['elevation'].values[0]) # Ángulo de elevación solar

        return alfa, azimuth_solar

    except Exception as e:
        # Si hay un error en el formato de fecha o coordenadas, devolvemos 0,0
        logger.warning(f"Error calculando posición solar para {forecast_time}: {e}")
        return 0.0, 0.0



def calculate_ghi(alfa, clouds_pct, weather_id):
    """
    Calcula la Irradiación Global Horizontal (GHI) basada en nubes y posición solar.
    Utiliza el modelo de Haurwitz para cielo despejado y Kasten-Czeplak para nubes.
    """
    try:
        # 1. Filtro de seguridad: Si el sol está por debajo o en el horizonte, la radiación es 0
        if alfa <= 0:
            return 0.0

        # 2. Definir factores de transmitancia según el Weather ID.
        # Estos factores actúan como un 'freno' adicional a la luz.
        weather_factors = {
            'thunderstorm': 0.40,  # IDs 2xx: Tormentas (muy opaco)
            'drizzle': 0.85,       # IDs 3xx: Llovizna
            'rain': 0.70,          # IDs 5xx: Lluvia moderada/fuerte
            'snow': 0.75,          # IDs 6xx: Nieve (refleja, pero bloquea)
            'atmosphere': 0.60,    # IDs 7xx: Niebla, calima, polvo (mucha dispersión)
            'clear': 1.00,         # IDs 800: Cielo despejado
            'clouds_light': 0.95,  # IDs 801-802: Nubes dispersas
            'clouds_heavy': 0.80   # IDs 803-804: Muy nuboso/cubierto
        }

        # 3. Mapeo del ID numérico al factor
        # Convertimos el ID (int) a su categoría
        wid = int(weather_id)
        if wid < 300:   f_weather = weather_factors['thunderstorm']
        elif wid < 500: f_weather = weather_factors['drizzle']
        elif wid < 600: f_weather = weather_factors['rain']
        elif wid < 700: f_weather = weather_factors['snow']
        elif wid < 800: f_weather = weather_factors['atmosphere']
        elif wid == 800: f_weather = weather_factors['clear']
        elif wid <= 802: f_weather = weather_factors['clouds_light']
        else:           f_weather = weather_factors['clouds_heavy']

        # 4. Calcular G_clear (Modelo de Haurwitz)
        # Convertimos alfa a radianes para las funciones trigonométricas de numpy
        sin_alfa = np.sin(np.radians(alfa))
        
        # El modelo de Haurwitz estima la radiación máxima teórica
        # Usamos max(0.001, sin_alfa) para evitar división por cero absoluta
        g_clear = 1098 * sin_alfa * np.exp(-0.057 / max(0.001, sin_alfa))
        
        # 5. Ajustar por nubosidad (Kasten-Czeplak) y por Weather Factor
        # El clouds_pct da la cantidad, f_weather da la "calidad" o grosor de la nube
        # La relación exponencial (cubo) simula cómo las nubes bloquean la luz
        ghi = g_clear * (1 - 0.75 * (clouds_pct / 100)**3) * f_weather
        
        # 4. Asegurar que el resultado sea un float positivo
        return float(max(0, ghi))

    except Exception as e:
        # Si ocurre un error inesperado (ej. clouds_pct nulo), devolvemos 0 para no romper el ETL
        logger.warning(f"Error en el cálculo de GHI: {e}")
        return 0.0


def decompose_erbs(ghi, alfa, forecast_time_utc):
    """
    Descompone la GHI en DNI y DHI utilizando el modelo de Erbs.
    Incluye validación de seguridad y manejo de excepciones.
    """
    try:
        # 1. Validación de seguridad: Sol muy bajo o sin radiación
        if ghi <= 0 or alfa < 2:
            return 0.0, 0.0

        # 2. Radiación extraterrestre
        dni_extra = pvlib.irradiance.get_extra_radiation(pd.to_datetime(forecast_time_utc))
        
        # 3. Índice de Claridad (kt)
        sin_alfa = np.sin(np.radians(alfa))
        ghi_extra_h = dni_extra * sin_alfa
        
        # Evitamos división por cero con una validación simple
        kt = ghi / ghi_extra_h if ghi_extra_h > 0 else 0
        kt = max(0, min(kt, 1))
        
        # 4. Modelo de Erbs (Fracción difusa)
        if kt <= 0.22:
            diffuse_frac = 1.0 - 0.09 * kt
        elif kt <= 0.80:
            diffuse_frac = 0.9511 - 0.1604*kt + 4.388*kt**2 - 16.638*kt**3 + 12.336*kt**4
        else:
            diffuse_frac = 0.165
            
        # 5. DHI (Difusa Horizontal)
        dhi = ghi * diffuse_frac
        
        # 6. DNI (Directa Normal)
        # Protección contra inestabilidad matemática con epsilon (0.01)
        dni = (ghi - dhi) / sin_alfa if sin_alfa > 0.01 else 0
        
        # Restricción física fundamental
        dni = min(dni, dni_extra)
       
        return float(max(0, dni)), float(max(0, dhi))

    except Exception as e:
        # En un ETL real, aquí podrías usar un logger: logger.error(f"Error en Erbs: {e}")
        logger.warning(f"Error procesando fila {forecast_time_utc}: {e}")
        return 0.0, 0.0



def calculate_total_poa(dni, dhi, ghi, alfa, azimuth_solar, angle, aspect):
    """
    Calcula la irradiación total recibida por un panel inclinado (G_total / POA).
    Suma las componentes directa, difusa y de albedo.
    """
    try:
        # 1. Si no hay radiación global o el sol está bajo el horizonte, devolvemos 0
        if ghi <= 0 or alfa < 2:
            return 0.0

        # 2. Cálculo del Ángulo de Incidencia (theta)
        # El cénit es el ángulo complementario a la elevación (90 - alfa)
        zenith = 90 - alfa
        
        # theta es el ángulo entre el rayo de sol y la línea perpendicular al panel
        theta = pvlib.irradiance.aoi(angle, aspect, zenith, azimuth_solar)
        
        # 3. Irradiación Directa sobre el panel (Beam)
        # No puede ser negativa; si el sol está "detrás" del panel, es 0
        g_beam = dni * np.cos(np.radians(theta))
        g_beam = max(0, g_beam)
        
        # 4. Irradiación Difusa sobre el panel (Modelo Isotrópico de Liu-Jordan)
        # Considera que la luz del cielo llega de forma uniforme desde la bóveda celeste
        g_diffuse = dhi * (1 + np.cos(np.radians(angle))) / 2
        
        # 5. Irradiación de Albedo (Reflejo del suelo)
        # Usamos un factor de reflectancia estándar de 0.2 (suelo típico)
        g_albedo = ghi * 0.2 * (1 - np.cos(np.radians(angle))) / 2
        
        # 6. Suma total de las tres componentes en W/m2
        poa = g_beam + g_diffuse + g_albedo
        
        return float(max(0, poa))

    except Exception as e:
        # Captura cualquier error matemático o de tipos de datos para no detener el ETL
        logger.warning(f"Error en el cálculo de radiación total POA: {e}")
        return 0.0


def calculate_t_cell(temp_ambient, wind_speed, poa):
    """
    Calcula la temperatura de la célula usando el modelo de Faiman.
    Ajusta la temperatura ambiente según la radiación (POA) y el enfriamiento del viento.
    """
    # Coeficientes típicos para paneles estándar (pueden variar según el montaje)
    u0 = 24.9  # Coeficiente de pérdida constante
    u1 = 6.1   # Coeficiente de pérdida por viento
    
    try:
        # 1. Filtro de seguridad: Si no hay radiación, la célula está a temp ambiente
        if poa <= 0:
            return float(temp_ambient)
        
        # 2. Evitar división por cero o valores de viento inconsistentes
        # Usamos max(0, wind_speed) por seguridad si el sensor da error
        divisor = u0 + u1 * max(0, wind_speed)
        
        # 3. Aplicar fórmula de Faiman
        t_cell = temp_ambient + (poa / divisor)
        
        return float(t_cell)

    except Exception as e:
        # Si hay un error (ej. un valor None o NaN), devolvemos la temp ambiente como fallback
        logger.warning(f"Error calculando T_cell: {e}. Usando temp_ambient como respaldo.")
        return float(temp_ambient)


def calculate_power_output(poa, t_cell, peak_power, loss_pct):
    """
    Calcula la potencia de salida (kW) y el Performance Ratio (PR)
    aplicando correcciones térmicas y pérdidas.
    """
    try:
        # 1. Validación inicial: Si no hay radiación, la salida es 0
        if poa <= 0:
            return 0.0, 0.0

        # 2. Parámetros físicos estándar
        gamma = -0.004 # Coeficiente de temperatura: pérdida de -0.4% por cada °C sobre 25°C
        
        # 3. Factor de corrección por temperatura (f_temp)
        # Penaliza la eficiencia si la celda supera los 25°C
        f_temp = 1 + gamma * (t_cell - 25)

        # 4. Cálculo del PR (Performance Ratio)
        # Combina el efecto térmico y las pérdidas fijas del sistema (suciedad, cables, inversor)
        pr = f_temp * (1 - (loss_pct / 100))

        # 5. Potencia de salida (kW)
        # Normalizamos la irradiación (g_total / 1000) porque peak_power está definida a 1000 W/m2
        p_out = (poa / 1000) * peak_power * pr
        
        return float(max(0, p_out)), float(pr)

    except Exception as e:
        # Capturamos el error para que el ETL no se detenga. 
        # En producción, podrías usar un logging profesional aquí.
        logger.warning(f"Error en el cálculo de potencia: {e}")
        return 0.0, 0.0
    

def calculate_industrial_consumption(forecast_time_utc, nominal_load_kw, temp_ambient_celsius):
    """
    Simulación de alta fidelidad de consumo industrial.
    Simula el consumo de una fábrica escalado proporcionalmente a la potencia instalada.
    Relaciona el pico de consumo con la potencia pico fotovoltaica (ratio ~1.2).
    Incluye: Curvas de arranque, hora de almuerzo, estacionalidad térmica y ruido de alta frecuencia.
    Excluye: cargas gestionables (carretillas, baterías, procesos programables) 
    para permitir la optimización posterior del balance energético.
    """
    try:
        dt = pd.to_datetime(forecast_time_utc)
        hour = dt.hour
        minute = dt.minute # Para mayor resolución si fuera necesario
        weekday = dt.weekday()
        
        # 1. Definir el Techo de Consumo (Escala)
        # Una fábrica sana suele tener un pico de demanda un 20-30% mayor que su instalación PV
        max_factory_demand = nominal_load_kw 

        # 2. Lógica de Actividad por Procesos (Baseline)
        if weekday < 5:  # Lunes a Viernes
            if 0 <= hour < 5:
                base_factor = 0.10  # Solo servicios críticos y seguridad
            elif 5 <= hour < 6:
                base_factor = 0.40  # Pre-arranque y climatización de naves
            elif 6 <= hour < 9:
                base_factor = 0.95  # Arranque de maquinaria (Pico de carga)
            elif 9 <= hour < 13:
                base_factor = 0.85  # Operación estable Turno 1
            elif 13 <= hour < 15:
                base_factor = 0.60  # PARADA DE ALMUERZO (El "valle" que engaña al PV)
            elif 15 <= hour < 18:
                base_factor = 0.90  # Turno 2 - Máxima producción
            elif 18 <= hour < 22:
                base_factor = 0.60  # Turno tarde - Limpieza y procesos secundarios
            else:
                base_factor = 0.12  # Cierre
        else:  # Fin de semana
            base_factor = 0.10 if weekday == 6 else 0.20 # Domingo casi muerto, Sábado guardia

        # 3. Componente Termoeléctrica (HVAC)
        # Si hace más de 25°C o menos de 15°C, las máquinas de climatizacion consumen más.
        thermal_load = 0
        if temp_ambient_celsius > 25:
            thermal_load = (temp_ambient_celsius - 25) * 0.02  # +2% de consumo por cada grado extra
        elif temp_ambient_celsius < 15:
            thermal_load = (15 - temp_ambient_celsius) * 0.01  # +1% por calefacción/resistencias

        # 4. Composición Final con Ruido "Browniano" (Gausiano)
        # No usamos uniform, usamos normal para que los valores extremos sean raros
        variability = np.random.normal(1.0, 0.03) # Desviación estándar del 3%
        
        total_consumption = max_factory_demand * (base_factor + thermal_load) * variability

        return float(max(0, total_consumption))

    except Exception as e:
        logger.error(f"Error calculando consumo industrial: {e}")
        return 0.0


if __name__ == "__main__":

    lat=42.803852359174265
    lon=-1.701961806168645
    forecast_time='2026-05-01 15:00:00'
    pv_peak_power= 16
    loss_pct=14
    clouds_pct=82
    weather_id=803
    angle=30
    aspect=0
    temp_ambient=20.29
    wind_speed=5.54

    logger.info(f"Calculando posición del sol...")
    alfa, azimuth=calculate_solar_position(lat, lon, forecast_time)
    logger.info(f"alfa = {alfa}, azhimut = {azimuth}")

    logger.info(f"Calculando Irradiancia Global Horizontal (GHI)...")
    ghi=calculate_ghi(alfa, clouds_pct, weather_id)
    logger.info(f"Global Horizontal Irradiance (GHI) = {ghi} W/m²")

    logger.info(f"Calculando Direct Normal Irradiance (DNI) y Diffuse Horizontal Irradiance (DHI)...")
    dni, dhi=decompose_erbs(ghi, alfa, forecast_time)
    logger.info(f"Direct Normal Irradiance (DNI) = {dni} W/m², Diffuse Horizontal Irradiance (DHI) = {dhi} W/m²")

    logger.info(f"Calculando POA irradiance (POA)...")
    poa=calculate_total_poa(dni, dhi, ghi, alfa, azimuth, angle, aspect)
    logger.info(f"POA irradiance (POA) = {poa} W/m²")

    logger.info(f"Calculando temperatura de celula (T_CELL)...")
    tcell=calculate_t_cell(temp_ambient, wind_speed, poa)
    logger.info(f"Temperatura de celula(T_CELL) = {tcell} celsius")

    logger.info(f"Calculando potencia de generacion...")
    p_gen, pr=calculate_power_output(poa, tcell, pv_peak_power, loss_pct)
    logger.info(f"Potencia de generacion = {p_gen} kw, Performance ratio = {pr}")

    logger.info(f"Calculando potencia de consumo...")
    p_con=calculate_industrial_consumption(forecast_time, pv_peak_power, temp_ambient)
    logger.info(f"Potencia de consumo = {p_con} kw")


