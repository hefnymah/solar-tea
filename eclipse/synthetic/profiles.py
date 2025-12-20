
import pandas as pd
import numpy as np
from typing import Tuple, Optional

def generate_load_profile(
    times: pd.DatetimeIndex,
    daily_avg_kwh: float = 10.0,
    morning_peak_hour: int = 8,
    evening_peak_hour: int = 19,
    base_load_ratio: float = 0.2, # Fraction of peak
    noise_level: float = 0.2
) -> pd.Series:
    """
    Generates a synthetic residential load profile.
    
    Args:
        times: DatetimeIndex for the simulation period.
        daily_avg_kwh: Target average daily consumption.
        morning_peak_hour: Hour of morning peak (0-23).
        evening_peak_hour: Hour of evening peak (0-23).
        base_load_ratio: Base load as a fraction of the variable load component.
        noise_level: Magnitude of random noise (0.0 to 1.0).
        
    Returns:
        pd.Series: Load profile in kW.
    """
    hour = times.hour.values
    
    # Double-bell curve shape
    # Morning peak
    morning = np.exp(-0.5 * ((hour - morning_peak_hour) / 2)**2)
    # Evening peak (typically higher)
    evening = 1.5 * np.exp(-0.5 * ((hour - evening_peak_hour) / 2)**2)
    
    raw_shape = base_load_ratio + morning + evening
    
    # Add noise
    noise = np.random.normal(1.0, noise_level, len(times))
    raw_profile = raw_shape * noise
    raw_profile = np.maximum(raw_profile, 0)
    
    # Scale to match target daily energy
    current_daily_avg = raw_profile.mean() * 24 
    # (mean power kW * 24h = daily kWh) -> Wait, mean() is avg kW. 
    # daily kWh = sum(kW * 1h) / days
    # daily kWh = mean(kW) * 24
    
    scaling_factor = daily_avg_kwh / (raw_profile.mean() * 24)
    final_profile = raw_profile * scaling_factor
    
    return pd.Series(final_profile, index=times)


def generate_pv_profile(
    times: pd.DatetimeIndex,
    kwp: float = 5.0,
    peak_hour: int = 12,
    seasonality: float = 0.4, # 0.0=flat year, 1.0=strong variation
    weather_noise: float = 0.6 # Beta distribution alpha parameter proxy (lower = more volatile)
) -> pd.Series:
    """
    Generates a synthetic PV production profile.
    
    Args:
        times: DatetimeIndex.
        kwp: Installed capacity in kWp.
        peak_hour: Hour of maximum daily generation.
        seasonality: Strength of summer/winter difference.
        weather_noise: Cloud cover variability.
        
    Returns:
        pd.Series: PV generation in kW.
    """
    hour = times.hour.values
    day_of_year = times.dayofyear.values
    
    # 1. Daily Solar Geometry (Simple Cosine)
    # 0 at night, peak at noon
    daily_shape = np.maximum(0, np.cos(2 * np.pi * (hour - peak_hour) / 24) - 0.5) * 2
    
    # 2. Seasonality (Peak in Summer/June ~Day 172)
    seasonal_factor = 1.0 + seasonality * np.cos(2 * np.pi * (day_of_year - 172) / 365)
    
    # 3. Weather / Cloud Noise
    # Use Beta distribution for realistic cloud cover (skewed towards sunny or cloudy)
    # High alpha/beta = consistent, Low = volatile
    # We'll simplify: simple multiplicative noise biased towards 1.0 (sunny) but with tails
    # 'weather_noise' will control the spread.
    
    # Using Beta(a, b): Mean = a/(a+b). We want mean ~ 1.0 relative to clear sky? 
    # Actually, clear sky is the max. Clouds reduce it.
    # So we multiply by a factor <= 1.0.
    
    # Let's use a simple bounded random walk or just per-hour noise for speed
    cloud_factor = np.random.beta(5, 1, len(times)) # Mean ~0.83, mostly sunny
    
    final_profile = daily_shape * seasonal_factor * cloud_factor * kwp
    
    return pd.Series(final_profile, index=times)

def generate_scenario(
    start_date: str = '2024-01-01',
    days: int = 365,
    daily_load: float = 20.0,
    pv_size_kwp: float = 8.0
) -> Tuple[pd.Series, pd.Series]:
    """
    Convenience wrapper to generate synchronized profiles for a scenario.
    """
    times = pd.date_range(start=start_date, periods=days*24, freq='h', tz='UTC')
    
    load = generate_load_profile(times, daily_avg_kwh=daily_load)
    pv = generate_pv_profile(times, kwp=pv_size_kwp)
    
    return load, pv
