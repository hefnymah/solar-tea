

import pandas as pd
import numpy as np

import pandas as pd
import numpy as np

from equipment_db import (
    MODULE_DB, INVERTER_DB, 
    check_module_inverter_compat, get_compatible_inverter,
    get_real_databases, search_equipment, adapt_sandia_module, adapt_cec_inverter
)
from roof_sizing import suggest_best_orientation

from pv_generation import simulate_pv_generation
from battery_sizing import optimize_battery_size, optimize_battery_cost, simulate_battery
from battery_pysam import simulate_pysam_battery
from equipment_db import MODULE_DB, INVERTER_DB # Correction import

def main():
    print("=== Perplexity PV & Battery Sizing Tool ===\n")
    
    # 1. Inputs
    # Location: Zurich, Switzerland
    lat, lon = 47.3769, 8.5417
    
    # Roof: 10m x 6m available area
    roof_w, roof_h = 10, 6 
    
    # Load: Simple dummy profile (avg 10kWh/day -> ~400W constant baseline with peaks)
    print("1. Generating Load Profile...")
    times = pd.date_range(start='2024-01-01', end='2024-12-31 23:00', freq='h', tz='UTC')
    # Create a synthetic load profile: Morning peak, Evening peak, low base
    hour_of_day = times.hour
    base_load = 300 # Watts
    morning_peak = 1000 * np.exp(-0.5 * ((hour_of_day - 8) / 2)**2)
    evening_peak = 1500 * np.exp(-0.5 * ((hour_of_day - 19) / 2)**2)
    load_watts = base_load + morning_peak + evening_peak
    
    # Add some random noise
    load_watts += np.random.normal(0, 50, len(times))
    load_watts = np.maximum(load_watts, 0) # No negative load
    
    load_series = pd.Series(load_watts, index=times)
    daily_load_kwh = load_series.resample('D').sum().mean() / 1000
    print(f"   Avg Daily Load: {daily_load_kwh:.2f} kWh")
    
    # -- Initialize Real DBs --
    print("\n   [Initializing Real Equipment Databases...]")
    sandia_mods, cec_invs = get_real_databases()
    
    # 2. Roof Fitting
    print("\n2. Checking Roof Capacity...")
    
    # Try to find a real module
    print("   Searching for 'Canadian Solar' modules...")
    matches = search_equipment(sandia_mods, "Canadian_Solar", limit=3)
    if not matches.empty:
        # Pick the first one
        mod_name = matches.index[0]
        real_mod_row = matches.iloc[0]
        print(f"   found: {mod_name}")
        target_module = adapt_sandia_module(mod_name, real_mod_row)
    else:
        print("   No match found, utilizing Mock DB.")
        target_module = MODULE_DB[1] # Failback
    
    orientation, num_modules = suggest_best_orientation(roof_w, roof_h, target_module)
    print(f"   Selected Module: {target_module.name} ({target_module.power_watts:.1f}W)")
    print(f"   Best Orientation: {orientation}")

    print(f"   Max Modules: {num_modules}")
    print(f"   Total DC Capacity: {num_modules * target_module.power_watts / 1000:.2f} kWp")
    
    # 3. Equipment Selection
    print("\n3. Selecting Inverter...")
    
    # Try to find a real inverter
    # Simplified search for a ~5kW inverter
    print("   Searching for 'Fronius' 5kW inverters...")
    matches = search_equipment(cec_invs, "Fronius", limit=20)
    # Filter for power near 5000W
    matches = matches[ (matches['Paco'] > 4500) & (matches['Paco'] < 5500) ]
    
    if not matches.empty:
         inv_name = matches.index[0]
         real_inv_row = matches.iloc[0]
         inverter = adapt_cec_inverter(inv_name, real_inv_row)
    else:
         inverter = get_compatible_inverter(target_module, num_modules)
    
    print(f"   Selected Inverter: {inverter.name} ({inverter.max_ac_power:.1f}W AC)")
    
    # Verify strict compatibility
    compat = check_module_inverter_compat(target_module, inverter, modules_per_string=num_modules) 

    print(f"   Compatibility Check: {compat}")
    
    # 4. PV Simulation
    print("\n4. Simulating PV Generation with PVLib...")
    # Assume 1 string of 'num_modules'
    ac_power = simulate_pv_generation(lat, lon, target_module, inverter, modules_per_string=num_modules)
    total_gen_kwh = ac_power.sum() / 1000
    print(f"   Annual PV Generation: {total_gen_kwh:.2f} kWh")
    
    # 5. Battery Sizing
    print("\n5. Optimizing Battery Size...")
    # Method 1: Heuristic (1 day autonomy)
    heuristic_size = optimize_battery_size(load_series, ac_power, target_autonomy_days=1, daily_load_kwh=daily_load_kwh)
    print(f"   Heuristic Size (1 day autonomy): {heuristic_size:.2f} kWh")
    
    # Method 2: Cost Optimization
    opt_size = optimize_battery_cost(load_series, ac_power)
    print(f"   Cost-Optimal Size: {opt_size:.2f} kWh")
    
    # 6. Final Simulation Check
    print("\n6. Running Final Simulation with Optimal Battery...")
    
    # Custom Simulation
    final_sim = simulate_battery(load_series, ac_power / 1000, opt_size) # Ensure Units (Watts -> KW handled? simulated_battery expects Watts/kWh mixed in sizing but let's check input)
    # Checking simulate_battery input expectations... it takes Series.
    # In main, ac_power is from pvlib (Watts). load_series is Watts.
    # simulate_battery converts W to kWh by / 1000.
    
    self_sufficiency = 1 - (final_sim['grid_import'].sum() / (load_series.sum() / 1000))
    print(f"   [Custom Model] Projected Self-Sufficiency: {self_sufficiency:.1%}")
    
    # PySAM Simulation
    if opt_size > 0:
        print("\n7. Validating with NREL PySAM...")
        # PySAM Wrapper expects kW inputs
        pysam_sim = simulate_pysam_battery(
            load_profile_kw=load_series / 1000, 
            pv_production_kw=ac_power / 1000, 
            battery_kwh=opt_size
        )
        pysam_ss = 1 - (pysam_sim['grid_import'].sum() / (load_series.sum() / 1000))
        print(f"   [NREL PySAM]   Projected Self-Sufficiency: {pysam_ss:.1%}")
        
    print(f"   Generaton/Load Ratio: {total_gen_kwh / (load_series.sum()/1000):.2f}")

if __name__ == "__main__":
    main()
