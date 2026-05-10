import pandas as pd
import pvlib
import numpy as np
from pathlib import Path
from typing import Tuple

from logger_config import setup_logging

"""
PHOTOVOLTAIC & CONSUMPTION ANALYTICS ENGINE
-------------------------------------------
Author: Aitor Asin
Description: Core physics engine for solar energy forecasting and industrial 
             load modeling. Implements clear-sky models, irradiance 
             decomposition (Erbs), and thermal derating (Faiman).
"""

logger = setup_logging()

# ─────────────────────────────────────────────────────────────────────────────
# ASTROPHYSICS: SOLAR GEOMETRY
# ─────────────────────────────────────────────────────────────────────────────

def calculate_solar_position(latitude: float, longitude: float, forecast_time_utc: str) -> Tuple[float, float]:
    """
    Computes solar elevation and azimuth using NREL's SPA algorithm via pvlib.
    Essential for determining the angle of incidence (AOI) on tilted planes.
    """
    try:
        dt = pd.to_datetime(forecast_time_utc, utc=True)
        # We wrap in a Series to ensure consistent pvlib behavior
        sol_pos = pvlib.solarposition.get_solarposition(dt, latitude, longitude)
        
        elevation = float(sol_pos["elevation"].iloc[0])
        azimuth = float(sol_pos["azimuth"].iloc[0])
        
        return elevation, azimuth

    except Exception as exc:
        logger.warning("[ENGINE] Solar position calculation failed: %s", exc)
        return 0.0, 0.0


# ─────────────────────────────────────────────────────────────────────────────
# ATMOSPHERIC PHYSICS: IRRADIANCE MODELING
# ─────────────────────────────────────────────────────────────────────────────

def calculate_ghi(alfa: float, clouds_pct: int, weather_id: int) -> float:
    """
    Estimates Global Horizontal Irradiance (GHI).
    Combines the Haurwitz clear-sky model with Kasten-Czeplak cloud attenuation 
    and empirical weather-type transmittance factors.
    """
    if alfa <= 0:
        return 0.0

    # Empirical transmittance factors based on OpenWeather IDs
    weather_factors = {
        "storm": 0.40, "rain": 0.70, "atmosphere": 0.60, 
        "clear": 1.00, "clouds_light": 0.95, "clouds_heavy": 0.80
    }

    if   weather_id < 300: f_w = weather_factors["storm"]
    elif weather_id < 700: f_w = weather_factors["rain"]
    elif weather_id < 800: f_w = weather_factors["atmosphere"]
    elif weather_id == 800: f_w = weather_factors["clear"]
    elif weather_id <= 802: f_w = weather_factors["clouds_light"]
    else:                  f_w = weather_factors["clouds_heavy"]

    try:
        sin_alfa = np.sin(np.radians(alfa))
        # Haurwitz Model for Clear Sky
        g_clear = 1098 * sin_alfa * np.exp(-0.057 / max(0.001, sin_alfa))
        # Cloud & Weather attenuation
        ghi = g_clear * (1 - 0.75 * (clouds_pct / 100) ** 3) * f_w
        
        return float(max(0, ghi))
    except Exception as exc:
        logger.warning("[ENGINE] GHI estimation error: %s", exc)
        return 0.0



def decompose_erbs(ghi: float, alfa: float, forecast_time_utc: str) -> Tuple[float, float]:
    """
    Decomposes GHI into DNI (Direct) and DHI (Diffuse) using the Erbs model.
    Crucial for calculating energy on tilted surfaces (POA).
    """
    if ghi <= 0 or alfa < 2:
        return 0.0, 0.0

    try:
        # Extraterrestrial radiation for Clearness Index (kt) calculation
        dni_extra = pvlib.irradiance.get_extra_radiation(pd.to_datetime(forecast_time_utc))
        ghi_extra_h = dni_extra * np.sin(np.radians(alfa))
        
        kt = ghi / ghi_extra_h if ghi_extra_h > 0 else 0
        kt = max(0, min(kt, 1))

        # Erbs Polynomial correlation
        if kt <= 0.22:
            diff_frac = 1.0 - 0.09 * kt
        elif kt <= 0.80:
            diff_frac = 0.9511 - 0.1604 * kt + 4.388 * kt**2 - 16.638 * kt**3 + 12.336 * kt**4
        else:
            diff_frac = 0.165

        dhi = ghi * diff_frac
        dni = (ghi - dhi) / np.sin(np.radians(alfa)) if alfa > 1 else 0
        
        return float(max(0, dni)), float(max(0, dhi))
    except Exception as exc:
        logger.warning("[ENGINE] Erbs decomposition error: %s", exc)
        return 0.0, 0.0


# ─────────────────────────────────────────────────────────────────────────────
# PHOTOVOLTAIC PERFORMANCE
# ─────────────────────────────────────────────────────────────────────────────

def calculate_total_poa(dni: float, dhi: float, ghi: float, alfa: float, 
                        azimuth_solar: float, angle: float, aspect: float) -> float:
    """
    Calculates Plane of Array (POA) irradiance.
    Sum of Beam (Cosine law), Diffuse (Sky Isotropic), and Ground Albedo.
    """
    if ghi <= 0 or alfa < 2:
        return 0.0

    try:
        zenith = 90 - alfa
        # Angle of Incidence on the tilted surface
        theta = pvlib.irradiance.aoi(angle, aspect, zenith, azimuth_solar)
        
        g_beam = max(0, dni * np.cos(np.radians(theta)))
        g_diff = dhi * (1 + np.cos(np.radians(angle))) / 2
        g_albedo = ghi * 0.2 * (1 - np.cos(np.radians(angle))) / 2 # Albedo fixed at 0.2
        
        return float(max(0, g_beam + g_diff + g_albedo))
    except Exception as exc:
        logger.warning("[ENGINE] POA calculation error: %s", exc)
        return 0.0


def calculate_power_output(poa: float, t_ambient: float, wind_speed: float, 
                           peak_power: float, loss_pct: float) -> Tuple[float, float]:
    """
    Predicts AC Power output (kW).
    Includes Faiman Cell Temperature model and thermal derating (-0.4%/°C).
    """
    if poa <= 0:
        return 0.0, 0.0

    try:
        # 1. Thermal Modeling (Faiman Model)
        u0, u1 = 24.9, 6.1
        t_cell = t_ambient + (poa / (u0 + u1 * max(0, wind_speed)))
        
        # 2. Performance Ratio & Derating
        gamma = -0.004  # -0.4%/C standard for crystalline silicon
        f_temp = 1 + gamma * (t_cell - 25)
        pr = f_temp * (1 - (loss_pct / 100))
        
        # 3. Final AC Power
        p_out = (poa / 1000) * peak_power * pr
        
        return float(max(0, p_out)), float(pr)
    except Exception as exc:
        logger.warning("[ENGINE] Power model error: %s", exc)
        return 0.0, 0.0


# ─────────────────────────────────────────────────────────────────────────────
# LOAD PROFILING: INDUSTRIAL CONSUMPTION
# ─────────────────────────────────────────────────────────────────────────────

def calculate_industrial_consumption(forecast_time_utc: str, nominal_load_kw: float, 
                                     temp_ambient: float) -> float:
    """
    Models synthetic industrial demand.
    Simulates operational shifts, weekend baseloads, and HVAC thermal sensitivity.
    """
    try:
        dt = pd.to_datetime(forecast_time_utc)
        hour, weekday = dt.hour, dt.weekday()

        # Operational Shifts (Standard 8h-18h intensity)
        if weekday < 5:  # Monday-Friday
            if   hour < 6:  base = 0.15
            elif hour < 9:  base = 0.90
            elif hour < 17: base = 0.80
            elif hour < 22: base = 0.50
            else:           base = 0.15
        else:            # Weekend baseload
            base = 0.10 if weekday == 6 else 0.20

        # Thermal Sensitivity (HVAC Load Simulation)
        thermal = max(0, (temp_ambient - 25) * 0.02) if temp_ambient > 25 else 0
        
        # Stochastic variability (Real-world noise)
        noise = np.random.normal(1.0, 0.03)
        
        return float(nominal_load_kw * (base + thermal) * noise)

    except Exception as exc:
        logger.warning("[ENGINE] Consumption model error: %s", exc)
        return 0.0


if __name__ == "__main__":
    # Test sample for Alazigoyen, Navarra
    logger.info("[TEST] Running engine standalone verification...")
    # ... (Keep your test block as it was, it's perfect for debugging)