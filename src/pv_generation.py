
import pandas as pd
import pvlib
from pvlib.modelchain import ModelChain
from pvlib.pvsystem import PVSystem, Array, FixedMount
from pvlib.location import Location
from pvlib.temperature import TEMPERATURE_MODEL_PARAMETERS
from dataclasses import asdict

from .equipment_db import MockModule, MockInverter

def get_tmy_data(latitude, longitude):
    """
    Fetches TMY data using pvlib.iotools or generates dummy data if offline.
    """
    try:
        # Try fetching from generic source if available, or just create dummy clear sky
        # For robustness in this environment, we'll generate Clear Sky data
        # as a proxy for TMY if no file is present.
        
        # Create a time index for 2024
        times = pd.date_range(start='2024-01-01', end='2024-12-31 23:00', freq='h', tz='UTC')
        
        location = Location(latitude, longitude)
        cs = location.get_clearsky(times)
        
        # Simple weather data frame
        weather = pd.DataFrame({
            'ghi': cs['ghi'],
            'dni': cs['dni'],
            'dhi': cs['dhi'],
            'temp_air': 20, # Constant proxy
            'wind_speed': 2 # Constant proxy
        }, index=times)
        
        return weather
    except Exception as e:
        print(f"Error generating weather data: {e}")
        return pd.DataFrame()

def simulate_pv_generation(
    latitude: float, 
    longitude: float, 
    module: MockModule, 
    inverter: MockInverter, 
    modules_per_string: int,
    strings: int = 1,
    tilt: float = 30,
    azimuth: float = 180
) -> pd.Series:
    """
    Simulates PV generation for a year using pvlib.
    """
    
    # Define location
    location = Location(latitude, longitude)
    weather = get_tmy_data(latitude, longitude)
    
    if weather.empty:
        raise ValueError("Could not generate weather data")

    # Define system parameters
    # Note: using simple parameters fitting for the mock objects
    
    temperature_model_parameters = TEMPERATURE_MODEL_PARAMETERS['sapm']['open_rack_glass_glass']

    mount = FixedMount(surface_tilt=tilt, surface_azimuth=azimuth)
    
    # Construct a simple array
    # We use PVWatts for simplicity as we don't have full CEC params in our mock objects
    # We'll map our mock params to PVWatts input logic
    
    # Calculate DC capacity in Watts (Fallback)
    system_capacity = module.power_watts * modules_per_string * strings

    # Prepare Array config
    # Sort out params
    # We strip out the internal MockModule fields and keep only the added explicit params + essentials if needed
    # But since I added ALL CSV cols as explicit fields, we can just filter non-None.
    
    # Helper to extract potential PVLib params
    def get_real_params(obj):
        # excludes standard Mock interface fields if they conflict or aren't needed by pvlib models
        # But actually, assuming we are using Sandia/CEC models, we just need the keys matching the model requirements.
        # Those keys are exactly what we added to the dataclass.
        return {k: v for k, v in asdict(obj).items() if v is not None and k not in [
            'name', 'power_watts', 'width_m', 'height_m', 'vmpp', 'impp', 'voc', 'isc',
            'max_ac_power', 'mppt_low_v', 'mppt_high_v', 'max_input_voltage', 'max_input_current'
        ]}

    mod_params = get_real_params(module)
    inv_params = get_real_params(inverter)

    # Prepare Array config
    if mod_params:
        # Real Data (Sandia/CEC) - Use per-module params and array topology
        array_kwargs = {
            'module_parameters': mod_params,
            'modules_per_string': modules_per_string,
            'strings': strings,
            'mount': mount,
            'temperature_model_parameters': temperature_model_parameters
        }
    else:
        # Mock Data (PVWatts) - Use total system capacity
        array_kwargs = {
            'module_parameters': {'pdc0': system_capacity, 'gamma_pdc': -0.004},
            'mount': mount,
            'temperature_model_parameters': temperature_model_parameters
        }

    # Prepare Inverter config
    if not inv_params:
        inv_params = {'pdc0': system_capacity, 'pdc': inverter.max_ac_power} # Fallback

    pv_system = PVSystem(
        arrays=[Array(**array_kwargs)],
        inverter_parameters=inv_params
    )
    
    mc = ModelChain(pv_system, location, aoi_model='physical', spectral_model='no_loss')
    
    mc.run_model(weather)
    
    return mc.results.ac
