import pandas as pd
import pvlib
import numpy as np

from logger_config import setup_logging


logger = setup_logging()


# ─────────────────────────────────────────────────────────────────────────────
# SOLAR POSITION
# ─────────────────────────────────────────────────────────────────────────────

def calculate_solar_position(latitude, longitude, forecast_time_utc):
    """
    Computes solar elevation (alfa) and azimuth using pvlib.
    Returns (0.0, 0.0) on any parsing or computation error.
    """
    try:
        dt      = pd.to_datetime(forecast_time_utc, utc=True)
        sol_pos = pvlib.solarposition.get_solarposition(dt, latitude, longitude)
        alfa    = float(sol_pos["elevation"].values[0])
        azimuth = float(sol_pos["azimuth"].values[0])
        return alfa, azimuth

    except Exception as exc:
        logger.warning(
            "[ENGINE] Solar position failed for t=%s (lat=%.4f, lon=%.4f): %s — defaulting to (0, 0)",
            forecast_time_utc, latitude, longitude, exc,
        )
        return 0.0, 0.0


# ─────────────────────────────────────────────────────────────────────────────
# IRRADIANCE — GHI
# ─────────────────────────────────────────────────────────────────────────────

def calculate_ghi(alfa, clouds_pct, weather_id):
    """
    Estimates Global Horizontal Irradiance (GHI) using the Haurwitz clear-sky
    model attenuated by the Kasten-Czeplak cloud factor and a weather-type
    transmittance coefficient.  Returns 0.0 when the sun is below the horizon.
    """
    try:
        if alfa <= 0:
            return 0.0

        weather_factors = {
            "thunderstorm":  0.40,
            "drizzle":       0.85,
            "rain":          0.70,
            "snow":          0.75,
            "atmosphere":    0.60,
            "clear":         1.00,
            "clouds_light":  0.95,
            "clouds_heavy":  0.80,
        }

        wid = int(weather_id)
        if   wid < 300: f_w = weather_factors["thunderstorm"]
        elif wid < 500: f_w = weather_factors["drizzle"]
        elif wid < 600: f_w = weather_factors["rain"]
        elif wid < 700: f_w = weather_factors["snow"]
        elif wid < 800: f_w = weather_factors["atmosphere"]
        elif wid == 800: f_w = weather_factors["clear"]
        elif wid <= 802: f_w = weather_factors["clouds_light"]
        else:            f_w = weather_factors["clouds_heavy"]

        sin_alfa = np.sin(np.radians(alfa))
        g_clear  = 1098 * sin_alfa * np.exp(-0.057 / max(0.001, sin_alfa))
        ghi      = g_clear * (1 - 0.75 * (clouds_pct / 100) ** 3) * f_w

        return float(max(0, ghi))

    except Exception as exc:
        logger.warning("[ENGINE] GHI calculation failed (alfa=%.2f, clouds=%s, wid=%s): %s", alfa, clouds_pct, weather_id, exc)
        return 0.0


# ─────────────────────────────────────────────────────────────────────────────
# IRRADIANCE — ERBS DECOMPOSITION
# ─────────────────────────────────────────────────────────────────────────────

def decompose_erbs(ghi, alfa, forecast_time_utc):
    """
    Decomposes GHI into Direct Normal Irradiance (DNI) and Diffuse Horizontal
    Irradiance (DHI) using the Erbs clearness-index model.
    Returns (0.0, 0.0) when the sun is too low or GHI is zero.
    """
    try:
        if ghi <= 0 or alfa < 2:
            return 0.0, 0.0

        dni_extra  = pvlib.irradiance.get_extra_radiation(pd.to_datetime(forecast_time_utc))
        sin_alfa   = np.sin(np.radians(alfa))
        ghi_extra_h = dni_extra * sin_alfa
        kt          = ghi / ghi_extra_h if ghi_extra_h > 0 else 0
        kt          = max(0, min(kt, 1))

        if kt <= 0.22:
            diff_frac = 1.0 - 0.09 * kt
        elif kt <= 0.80:
            diff_frac = 0.9511 - 0.1604 * kt + 4.388 * kt**2 - 16.638 * kt**3 + 12.336 * kt**4
        else:
            diff_frac = 0.165

        dhi = ghi * diff_frac
        dni = (ghi - dhi) / sin_alfa if sin_alfa > 0.01 else 0
        dni = min(dni, dni_extra)

        return float(max(0, dni)), float(max(0, dhi))

    except Exception as exc:
        logger.warning("[ENGINE] Erbs decomposition failed for t=%s: %s", forecast_time_utc, exc)
        return 0.0, 0.0


# ─────────────────────────────────────────────────────────────────────────────
# IRRADIANCE — PLANE OF ARRAY (POA)
# ─────────────────────────────────────────────────────────────────────────────

def calculate_total_poa(dni, dhi, ghi, alfa, azimuth_solar, angle, aspect):
    """
    Calculates total irradiance on the tilted panel plane (POA) by summing
    beam, isotropic-diffuse (Liu-Jordan) and ground-albedo components.
    """
    try:
        if ghi <= 0 or alfa < 2:
            return 0.0

        zenith   = 90 - alfa
        theta    = pvlib.irradiance.aoi(angle, aspect, zenith, azimuth_solar)
        g_beam   = max(0, dni * np.cos(np.radians(theta)))
        g_diff   = dhi * (1 + np.cos(np.radians(angle))) / 2
        g_albedo = ghi * 0.2 * (1 - np.cos(np.radians(angle))) / 2
        poa      = g_beam + g_diff + g_albedo

        return float(max(0, poa))

    except Exception as exc:
        logger.warning("[ENGINE] POA calculation failed (alfa=%.2f, angle=%s, aspect=%s): %s", alfa, angle, aspect, exc)
        return 0.0


# ─────────────────────────────────────────────────────────────────────────────
# CELL TEMPERATURE — FAIMAN MODEL
# ─────────────────────────────────────────────────────────────────────────────

def calculate_t_cell(temp_ambient, wind_speed, poa):
    """
    Estimates cell operating temperature using the Faiman model.
    Falls back to ambient temperature when POA is zero.
    """
    u0, u1 = 24.9, 6.1   # Faiman coefficients for standard open-rack mounting

    try:
        if poa <= 0:
            return float(temp_ambient)

        divisor = u0 + u1 * max(0, wind_speed)
        t_cell  = temp_ambient + (poa / divisor)
        return float(t_cell)

    except Exception as exc:
        logger.warning("[ENGINE] T_cell calculation failed — using ambient temperature: %s", exc)
        return float(temp_ambient)


# ─────────────────────────────────────────────────────────────────────────────
# POWER OUTPUT
# ─────────────────────────────────────────────────────────────────────────────

def calculate_power_output(poa, t_cell, peak_power, loss_pct):
    """
    Calculates AC power output (kW) and Performance Ratio (PR) applying
    thermal derating (γ = -0.4 %/°C) and system losses.
    """
    try:
        if poa <= 0:
            return 0.0, 0.0

        gamma  = -0.004                          # Thermal coefficient: -0.4 %/°C
        f_temp = 1 + gamma * (t_cell - 25)
        pr     = f_temp * (1 - (loss_pct / 100))
        p_out  = (poa / 1000) * peak_power * pr

        return float(max(0, p_out)), float(pr)

    except Exception as exc:
        logger.warning("[ENGINE] Power output calculation failed (poa=%.2f, t_cell=%.2f): %s", poa, t_cell, exc)
        return 0.0, 0.0


# ─────────────────────────────────────────────────────────────────────────────
# INDUSTRIAL CONSUMPTION MODEL
# ─────────────────────────────────────────────────────────────────────────────

def calculate_industrial_consumption(forecast_time_utc, nominal_load_kw, temp_ambient_celsius):
    """
    High-fidelity industrial consumption simulation scaled to nominal load.
    Models shift patterns, HVAC thermal load and Gaussian process variability.
    Excludes deferrable loads (EVs, batteries) to allow downstream optimisation.
    """
    try:
        dt      = pd.to_datetime(forecast_time_utc)
        hour    = dt.hour
        weekday = dt.weekday()

        if weekday < 5:
            if   hour < 5:  base = 0.10
            elif hour < 6:  base = 0.40
            elif hour < 9:  base = 0.95
            elif hour < 13: base = 0.85
            elif hour < 15: base = 0.60
            elif hour < 18: base = 0.90
            elif hour < 22: base = 0.60
            else:           base = 0.12
        else:
            base = 0.10 if weekday == 6 else 0.20

        thermal = 0.0
        if temp_ambient_celsius > 25:
            thermal = (temp_ambient_celsius - 25) * 0.02
        elif temp_ambient_celsius < 15:
            thermal = (15 - temp_ambient_celsius) * 0.01

        variability = np.random.normal(1.0, 0.03)
        consumption = nominal_load_kw * (base + thermal) * variability

        return float(max(0, consumption))

    except Exception as exc:
        logger.warning("[ENGINE] Industrial consumption calculation failed for t=%s: %s", forecast_time_utc, exc)
        return 0.0


# ─────────────────────────────────────────────────────────────────────────────
# STANDALONE TEST
# ─────────────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    lat          = 42.803852359174265
    lon          = -1.701961806168645
    forecast_t   = "2026-05-01 15:00:00"
    pv_peak      = 16
    loss         = 14
    clouds       = 82
    weather_id   = 803
    angle        = 30
    aspect       = 0
    temp_ambient = 20.29
    wind         = 5.54

    logger.info("[TEST] ── PV engine standalone run ─────────────────────────")

    alfa, azimuth = calculate_solar_position(lat, lon, forecast_t)
    logger.info("[TEST] Solar position — elevation: %.2f° | azimuth: %.2f°", alfa, azimuth)

    ghi = calculate_ghi(alfa, clouds, weather_id)
    logger.info("[TEST] GHI: %.2f W/m²", ghi)

    dni, dhi = decompose_erbs(ghi, alfa, forecast_t)
    logger.info("[TEST] DNI: %.2f W/m² | DHI: %.2f W/m²", dni, dhi)

    poa = calculate_total_poa(dni, dhi, ghi, alfa, azimuth, angle, aspect)
    logger.info("[TEST] POA: %.2f W/m²", poa)

    t_cell = calculate_t_cell(temp_ambient, wind, poa)
    logger.info("[TEST] T_cell: %.2f °C", t_cell)

    p_gen, pr = calculate_power_output(poa, t_cell, pv_peak, loss)
    logger.info("[TEST] P_gen: %.3f kW | PR: %.3f", p_gen, pr)

    p_con = calculate_industrial_consumption(forecast_t, pv_peak, temp_ambient)
    logger.info("[TEST] P_consumption: %.3f kW", p_con)

    logger.info("[TEST] ── Standalone run complete ──────────────────────────")
