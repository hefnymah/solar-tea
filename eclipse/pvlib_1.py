
import pandas as pd
import numpy as np
import pvlib
from pvlib.location import Location
from pvlib.pvsystem import PVSystem
from pvlib.modelchain import ModelChain
from pvlib.temperature import TEMPERATURE_MODEL_PARAMETERS

# --- Configuration Constants ---
LATITUDE = 47.3769  # Zurich
LONGITUDE = 8.5417
ALTITUDE = 408
TIMEZONE = 'Europe/Zurich'

ROOF_TILT = 30
ROOF_AZIMUTH = 180  # South
MAX_CAPACITY_KWP = 15.0
PERFORMANCE_RATIO = 0.85
TARGET_CONSUMPTION_COL = 'Consumption_kWh'

def simulate_pv_generation(df_consumption):
    """
    Simulates PV generation using pvlib.
    1. Sizes the system to specific yield (Target: 100% of annual consumption).
    2. Constrains by roof area.
    3. Simulates generation.
    4. Calculates Self-Consumption metrics.
    """
    print("\n--- Starting PV Simulation ---")
    
    # 1. Annual Consumption
    total_consumption_kwh = df_consumption[TARGET_CONSUMPTION_COL].sum()
    print(f"Annual Consumption: {total_consumption_kwh:.0f} kWh")
    
    # 2. Fetch Weather Data (PVGIS)
    print("Fetching weather data from PVGIS...")
    try:
        # get_pvgis_tmy returns a tuple: (data, metadata, variable_definitions, ...) depending on version
        try:
            # pvlib >= 0.9.0 returns 4 values: (data, months_selected, inputs, metadata)
            # older versions or different output formats might return 2: (data, metadata)
            pvgis_data = pvlib.iotools.get_pvgis_tmy(LATITUDE, LONGITUDE, map_variables=True)
            
            if len(pvgis_data) == 4:
                weather, _, _, _ = pvgis_data
            elif len(pvgis_data) == 3: 
                 # Some versions/calls might return 3? Just in case.
                 weather = pvgis_data[0]
            else:
                weather = pvgis_data[0]
                
        except Exception as unpack_err:
             print(f"Unpacking error: {unpack_err}. Raw return type: {type(pvgis_data) if 'pvgis_data' in locals() else 'Unknown'}")
             raise unpack_err
        
        # Standardize weather year to consumption year to allow alignment
        # Default to current year or the year from consumption data
        if not df_consumption.empty:
            sim_year = pd.Series(df_consumption.index.year).mode()[0]
        else:
            sim_year = 2024
            
        weather.index = weather.index.map(lambda t: t.replace(year=sim_year))
        print(f"Weather data loaded for simulation year: {sim_year}")
    except Exception as e:
        print(f"Error fetching PVGIS data: {e}. Aborting PV simulation.")
        return None, None

    # 3. Reference Simulation (1 kWp) to get Specific Yield
    location = Location(LATITUDE, LONGITUDE, TIMEZONE, ALTITUDE)
    temp_params = TEMPERATURE_MODEL_PARAMETERS['sapm']['open_rack_glass_glass']
    
    # Define a generic system for reference
    system_ref = PVSystem(
        surface_tilt=ROOF_TILT,
        surface_azimuth=ROOF_AZIMUTH,
        module_parameters={'pdc0': 1000, 'gamma_pdc': -0.004}, # Simple efficiency model
        inverter_parameters={'pdc0': 1000},
        temperature_model_parameters=temp_params
    )
    
    mc_ref = ModelChain(system_ref, location, aoi_model='physical', spectral_model='no_loss')
    mc_ref.run_model(weather)
    
    # Calculate Specific Yield (kWh per kWp)
    # ModelChain output is AC power in Watts (usually). 
    # Check units: pvlib defaults to power in Watts.
    # We convert to kWh: Power(W) * 1h / 1000
    ref_ac_kwh = (mc_ref.results.ac / 1000.0) * PERFORMANCE_RATIO
    specific_yield = ref_ac_kwh.sum()
    print(f"Specific Yield: {specific_yield:.0f} kWh/kWp/year")
    
    # 4. Sizing
    # Target: 100% Offset
    if specific_yield > 0:
        required_kwp = total_consumption_kwh / specific_yield
    else:
        required_kwp = 0
        
    print(f"Capacity needed for 100% offset: {required_kwp:.2f} kWp")
    
    if required_kwp > MAX_CAPACITY_KWP:
        installed_capacity = MAX_CAPACITY_KWP
        print(f"Limited by Roof Area! Installing max: {installed_capacity:.2f} kWp")
    else:
        installed_capacity = required_kwp
        print(f"Optimal Sizing (Fits on roof): {installed_capacity:.2f} kWp")
        
    # Scale reference results to installed capacity
    pv_generation_kwh = ref_ac_kwh * installed_capacity
    pv_generation_kwh.name = 'PV_Generation_kWh'
    
    # 5. Metrics & Alignment
    # Create combined DF for calculation
    df_combined = df_consumption.copy()
    
    # Handle Timezones and Alignment
    # PVGIS TMY is usually UTC. Consumption is local (naive or specific).
    # We strip timezone from PV to align with naive consumption timestamps if necessary.
    if pv_generation_kwh.index.tz is not None:
         # Convert to naive loop local time if consumption is naive, or match timezone
        if df_consumption.index.tz is None:
             pv_generation_kwh.index = pv_generation_kwh.index.tz_convert(TIMEZONE).tz_localize(None)
        else:
             pv_generation_kwh.index = pv_generation_kwh.index.tz_convert(df_consumption.index.tz)

        
    # Reindex PV to match Consumption exactly (Handles missing rows or slight offsets)
    # Ensure no duplicates in PV index before reindexing to avoid ValueError
    pv_generation_kwh = pv_generation_kwh[~pv_generation_kwh.index.duplicated(keep='first')]
    
    pv_aligned = pv_generation_kwh.reindex(df_combined.index, fill_value=0)
    
    df_combined['PV_kWh'] = pv_aligned
    
    # Self-Consumption (SC) logic
    # Energy consumed directly from PV = min(PV, Consumption)
    df_combined['Self_Consumed_kWh'] = np.minimum(df_combined['PV_kWh'], df_combined[TARGET_CONSUMPTION_COL])
    
    # Grid Export = PV - Self_Consumed
    df_combined['Grid_Export_kWh'] = df_combined['PV_kWh'] - df_combined['Self_Consumed_kWh']
    
    # Grid Import = Consumption - Self_Consumed
    df_combined['Grid_Import_kWh'] = df_combined[TARGET_CONSUMPTION_COL] - df_combined['Self_Consumed_kWh']
    
    # Aggregates
    total_pv = df_combined['PV_kWh'].sum()
    total_sc = df_combined['Self_Consumed_kWh'].sum()
    total_cons = df_combined[TARGET_CONSUMPTION_COL].sum()
    
    metrics = {
        'Capacity_kWp': installed_capacity,
        'Specific_Yield': specific_yield,
        'Total_PV_Gen_kWh': total_pv,
        'Total_Consumption_kWh': total_cons,
        'Self_Consumption_kWh': total_sc,
        'Self_Consumption_Ratio': (total_sc / total_pv * 100) if total_pv > 0 else 0, # % of PV used
        'Self_Sufficiency_Ratio': (total_sc / total_cons * 100) if total_cons > 0 else 0 # % of Load covered
    }
    
    print("\n--- Sizing Results ---")
    print(f"Installed Capacity: {metrics['Capacity_kWp']:.2f} kWp")
    print(f"Total PV Generation: {metrics['Total_PV_Gen_kWh']:.0f} kWh")
    print(f"Self-Consumption: {metrics['Self_Consumption_Ratio']:.1f}% (of PV energy used)")
    print(f"Autarchy (Sufficiency): {metrics['Self_Sufficiency_Ratio']:.1f}% (of Home energy covered)")
    
    return df_combined, metrics

if __name__ == "__main__":
    # Create dummy consumption data for standalone execution
    print("Generating dummy consumption data...")
    dates = pd.date_range(start='2024-01-01', end='2024-12-31 23:00', freq='h')
    
    # Simple synthetic load: constant base + random noise + evening peak
    base_load = 0.5 # kW
    noise = np.random.normal(0, 0.1, len(dates))
    evening_peak = 1.0 * np.exp(-0.5 * ((dates.hour - 19) / 2)**2) # Peak at 19:00
    
    consumption = base_load + noise + evening_peak
    consumption = np.maximum(consumption, 0) # Ensure no negative load
    
    df_dummy = pd.DataFrame(index=dates)
    df_dummy[TARGET_CONSUMPTION_COL] = consumption
    
    simulate_pv_generation(df_dummy)
