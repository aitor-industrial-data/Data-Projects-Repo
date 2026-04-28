import pandas as pd
import pvlib
import logging
import numpy as np


logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)

logger = logging.getLogger(__name__)


def calculate_solar_position(latitude, longitude, forecast_time):
    """
    Calcula la elevación solar (alfa) y el azimut utilizando pvlib.
    Incluye manejo de excepciones para asegurar la continuidad del ETL.
    """
    try:
        # 1. Convertir forecast_time a objeto datetime de Pandas (UTC)
        dt = pd.to_datetime(forecast_time, utc=True)
        
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


def decompose_erbs(ghi, alfa, forecast_time):
    """
    Descompone la GHI en DNI y DHI utilizando el modelo de Erbs.
    Incluye validación de seguridad y manejo de excepciones.
    """
    try:
        # 1. Validación de seguridad: Sol muy bajo o sin radiación
        if ghi <= 0 or alfa < 2:
            return 0.0, 0.0

        # 2. Radiación extraterrestre
        dni_extra = pvlib.irradiance.get_extra_radiation(pd.to_datetime(forecast_time))
        
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
        logger.warning(f"Error procesando fila {forecast_time}: {e}")
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


def calculate_power_output(g_total, t_cell, peak_power, loss_pct):
    """
    Calcula la potencia de salida (kW) y el Performance Ratio (PR)
    aplicando correcciones térmicas y pérdidas.
    """
    try:
        # 1. Validación inicial: Si no hay radiación, la salida es 0
        if g_total <= 0:
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
        p_out = (g_total / 1000) * peak_power * pr
        
        return float(max(0, p_out)), float(pr)

    except Exception as e:
        # Capturamos el error para que el ETL no se detenga. 
        # En producción, podrías usar un logging profesional aquí.
        logger.warning(f"Error en el cálculo de potencia: {e}")
        return 0.0, 0.0


#if __name__ == "__main__":

