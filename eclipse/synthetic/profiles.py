
import pandas as pd
import numpy as np
from typing import Tuple, Optional

def generate_load_profile(
    times: pd.DatetimeIndex,
    daily_avg_kwh: float = 10.0,
    profile_type: str = 'residential', # 'residential' or 'daytime_peak'
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
        profile_type: 'residential' (double peak) or 'daytime_peak' (commercial/industrial).
        morning_peak_hour: Hour of morning peak (0-23).
        evening_peak_hour: Hour of evening peak (0-23).
        base_load_ratio: Base load as a fraction of the variable load component.
        noise_level: Magnitude of random noise (0.0 to 1.0).
        
    Returns:
        pd.Series: Load profile in kW.
    """
    hour = times.hour.values + times.minute.values / 60.0
    
    if profile_type == 'industrial':
        # Industrial/Commercial shape: Block/Rectangular Pulse
        # Night: Low Base
        # Day (08:00-17:00): High Plateau
        
        base_load_val = 0.15
        peak_load_val = 1.0
        
        # Create the base block
        raw_profile = np.full_like(hour, base_load_val)
        
        # Apply "Day Shift" block (08:00 to 17:00)
        day_mask = (hour >= 8.0) & (hour <= 17.0)
        raw_profile[day_mask] = peak_load_val
        
        # Lunch Dip (12:00 - 13:00) - Explicitly carve out a dip
        lunch_center = 12.5
        # Dip factor: 1.0 = no dip
        dip_factor = 1.0 - (0.4 * np.exp(-0.5 * ((hour - lunch_center) / 0.3)**2))
        
        # Apply dip only to the high load
        raw_profile = raw_profile * dip_factor
        
        # Smoothing (To avoid purely vertical lines)
        series_profile = pd.Series(raw_profile)
        # Rolling window of ~1 hour (4 steps for 15min, 1 step for hourly)
        # Determine window size based on frequency if possible, else default to 4
        # Just use a small window
        smooth_profile = series_profile.rolling(window=4, center=True, min_periods=1).mean()
        
        # Add Low Noise
        noise = np.random.normal(1.0, 0.05, len(times))
        
        raw_profile = smooth_profile.values * noise
        raw_shape = np.maximum(raw_profile, 0)
        
        # Scaling is handled below generically
        raw_profile = raw_shape

    elif profile_type == 'daytime_peak':
        # Legacy/Smoother Commercial shape
        # Industrial/Commercial shape: High usage during day (8am-5pm), Low at night
        # Using a Super-Gaussian (boxier bell curve) centered at 12:30
        center = 12.5
        width = 4.0 # Controls width of the "shift"
        # shape ~ exp(-((x-mu)/sig)^4) for flat top
        main_shape = np.exp(-0.5 * ((hour - center) / width)**4)
        raw_shape = base_load_ratio + main_shape
        
        # Add noise
        noise = np.random.normal(1.0, noise_level, len(times))
        raw_profile = raw_shape * noise
        raw_profile = np.maximum(raw_profile, 0)

    else:
        # Residential: Double-bell curve shape
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
    # We need to account for the actual time delta to get kWh correct
    # But usually daily_avg_kwh implies the sum of energy over 24h
    
    # Calculate average power of the current shape
    avg_power_current = raw_profile.mean()
    
    # Target average power = daily_kwh / 24 hours
    avg_power_target = daily_avg_kwh / 24.0
    
    if avg_power_current > 0:
        scaling_factor = avg_power_target / avg_power_current
    else:
        scaling_factor = 0
        
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
    # Use fractional hours for smooth sub-hourly resolution
    hour = times.hour.values + times.minute.values / 60.0

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
    pv_size_kwp: float = 8.0,
    freq: str = 'h',
    profile_type: str = 'residential'
) -> Tuple[pd.Series, pd.Series]:
    """
    Convenience wrapper to generate synchronized profiles for a scenario.
    
    Args:
        start_date: Start date string (YYYY-MM-DD)
        days: Number of days to simulate
        daily_load: Daily average consumption in kWh
        pv_size_kwp: PV system size in kWp
        freq: Frequency string (e.g. 'h' for hourly, '15min' for 15-minute)
        profile_type: Load profile type ('residential', 'industrial', 'daytime_peak')
    """
    # Calculate number of periods based on frequency
    # Only support basic pandas frequencies that map to fixed counts easily or just let pandas handle it
    times = pd.date_range(start=start_date, periods=None, end=pd.Timestamp(start_date) + pd.Timedelta(days=days), freq=freq, inclusive='left', tz='UTC')
    # Correction: 'periods' with freq is safer if we want exact count, but 'days' implies duration.
    # Let's use simple date range logic:
    end_date = pd.Timestamp(start_date) + pd.Timedelta(days=days)
    times = pd.date_range(start=start_date, end=end_date, freq=freq, inclusive='left', tz='UTC')
    
    load = generate_load_profile(times, daily_avg_kwh=daily_load, profile_type=profile_type)
    pv = generate_pv_profile(times, kwp=pv_size_kwp)
    
    return load, pv
