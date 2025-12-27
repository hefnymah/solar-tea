
"""
PV Simulation Engine

This module provides a high-standard OOP approach to PV simulation, specifically 
addressing the challenge of aligning generation data with variable load profiles 
(different resolutions, leap years, etc.).

Key Concept: "Target Index Driven Simulation"
Instead of generating generic data and trying to fit the load to it, we take the 
Load Profile's time index as the "Master Index" and force the PV simulation 
to conform to it.
"""

from __future__ import annotations
from dataclasses import dataclass
from typing import Optional, Union, List
import pandas as pd
import numpy as np

import pvlib
from pvlib.location import Location
from pvlib.pvsystem import PVSystem
from pvlib.modelchain import ModelChain
from pvlib.temperature import TEMPERATURE_MODEL_PARAMETERS

@dataclass
class SimulationConfig:
    """Configuration for the simulation engine."""
    latitude: float
    longitude: float
    altitude: float = 0
    timezone: str = 'UTC'
    
    # physical parameters
    module_type: str = 'glass_glass' # for temperature model
    inverter_efficiency: float = 0.96
    system_loss: float = 0.14 # 14% system loss typically

class PVSimulationEngine:
    """
    Robust engine for generating PV profiles aligned to specific time indexes.
    """
    
    def __init__(self, config: SimulationConfig):
        self.config = config
        self.location = Location(
            config.latitude, 
            config.longitude, 
            config.timezone, 
            config.altitude
        )
        
    def create_system(self, tilt: float, azimuth: float, capacity_kwp: float) -> PVSystem:
        """Creates a PVSystem object with simplified PVWatts parameters."""
        
        # PVWatts-style parameters for simplicity and robustness
        module_parameters = {
            'pdc0': capacity_kwp * 1000, 
            'gamma_pdc': -0.003, # Typical temp coeff
        }
        inverter_parameters = {
            'pdc0': (capacity_kwp * 1000) / self.config.inverter_efficiency
        }
        
        # Select temp model
        temp_params = TEMPERATURE_MODEL_PARAMETERS['sapm']['open_rack_glass_glass']
        
        return PVSystem(
            surface_tilt=tilt,
            surface_azimuth=azimuth,
            module_parameters=module_parameters,
            inverter_parameters=inverter_parameters,
            temperature_model_parameters=temp_params,
            inverter=None # PVWatts model doesn't need specific inverter
        )

    def simulate(
        self, 
        system: PVSystem, 
        target_index: pd.DatetimeIndex, 
        weather_source: str = 'clearsky'
    ) -> pd.Series:
        """
        Run simulation aligned EXACTLY to the target_index.
        
        This solves the "Leap Year" and "Resolution" mismatch problems:
        1. If target_index is 15-min, we generate/resample to 15-min.
        2. If target_index is Leap Year, we ensure coverage.
        
        Args:
            system: Configured PVSystem.
            target_index: The 'Master' time index from the Consumption/Load profile.
            weather_source: 'clearsky' or 'pvgis_tmy' (simulated fetching).
        
        Returns:
            pd.Series: AC Power in Watts, indexed by target_index.
        """
        
        # 1. Determine simulation bounds from target index
        start_time = target_index.min()
        end_time = target_index.max()
        
        # 2. Weather Data Generation
        # Strategy: Generate high-res weather data covering the full range
        # We always simulate at least at the target resolution or higher.
        
        local_weather = None
        
        if weather_source == 'clearsky':
            # Clear Sky is mathematical, so we can generate it EXACTLY at the target points.
            # This is the most accurate method for 15-min intervals if no real sensor data exists.
            print(f"Calculating Clear Sky irradiance for {len(target_index)} points...")
            local_weather = self.location.get_clearsky(target_index)
            
            # Add dummy temp/wind if missing (vital for ModelChain)
            local_weather['temp_air'] = 20
            local_weather['wind_speed'] = 1
            
        elif weather_source == 'pvgis_tmy':
            # PVGIS TMY is usually Hourly and Generic Year.
            # We must fetch, normalize year, and then INTERPOLATE to target index.
            print("Fetching PVGIS TMY...")
            try:
                tmy_data, _, _ = pvlib.iotools.get_pvgis_tmy(
                    self.config.latitude, self.config.longitude, map_variables=True
                )
                
                # TMY has a generic year (often 2005 or mixed). 
                # We need to shift it to match the target index year(s).
                target_year = target_index[0].year
                
                # Create a specific year version of TMY
                # Note: This simple shift assumes target covers ~1 year. 
                # For multi-year targets, we'd need to tile the TMY.
                tmy_data.index = tmy_data.index.map(lambda t: t.replace(year=target_year))
                
                # HANDLING LEAP YEARS (Feb 29)
                # TMY standard usually excludes Feb 29. If target has Feb 29, we must fill it.
                if target_index.is_leap_year.any() and not ((tmy_data.index.month == 2) & (tmy_data.index.day == 29)).any():
                     # Fill Feb 29 by interpolating Feb 28 and Mar 1
                     # Or simply reindexing will create NaNs, which we interpolate later.
                     pass

                # 3. Alignment Strategy: Reindex -> Interpolate
                # This upsamples (Hourly -> 15min) automatically.
                # method='time' respects the time distance (good for uneven gaps)
                local_weather = tmy_data.reindex(target_index).interpolate(method='time')
                
                # Fill edge cases (start/end) if TMY didn't cover slightly
                local_weather = local_weather.bfill().ffill()
                
            except Exception as e:
                print(f"Warning: PVGIS fetch failed ({e}). Falling back to Clear Sky.")
                local_weather = self.location.get_clearsky(target_index)
                local_weather['temp_air'] = 20
                local_weather['wind_speed'] = 1

        # 3. Model Execution
        mc = ModelChain(system, self.location, aoi_model='physical', spectral_model='no_loss')
        
        # Run model on the ALIGNED weather data
        mc.run_model(local_weather)
        
        return mc.results.ac.fillna(0)

# Example Usage logic (commented out)
"""
# Load 15-min consumption profile with leap year
load_profile = pd.read_csv('consumption_15min_leap.csv', parse_dates=True, index_col=0)

# Initialize Engine
engine = PVSimulationEngine(config=SimulationConfig(lat=47.3, lon=8.5, timezone='Europe/Zurich'))
system = engine.create_system(tilt=30, azimuth=180, capacity_kwp=5.0)

# Simulate EXACTLY matching the load profile index
pv_generation = engine.simulate(system, target_index=load_profile.index, weather_source='clearsky')

# Now simple arithmetic is possible (no shape mismatch!)
net_load = load_profile['kwh'] - (pv_generation / 4000) # W -> kWh/15min
"""
