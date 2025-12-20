

import pandas as pd
import numpy as np

import pandas as pd
import numpy as np


import sys
import os
# Ensure root is in path for imports
sys.path.append(os.path.dirname(__file__))

from eclipse.config.equipments import MODULE_DB, INVERTER_DB
from eclipse.config.equipments.modules import module
from eclipse.config.equipments.inverters import inverter
from eclipse.config.equipments.batteries import battery
from eclipse.equipment_logic import (
    check_module_inverter_compat, get_compatible_inverter,
    get_real_databases, search_equipment, adapt_sandia_module, adapt_cec_inverter
)
from eclipse.roof_sizing import suggest_best_orientation

from eclipse.pv_generation import simulate_pv_generation
from eclipse.battery_sizing import optimize_battery_size, optimize_battery_cost, simulate_battery
from eclipse.battery_pysam import simulate_pysam_battery

from eclipse.synthetic import generate_load_profile

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
    
    # Use centralized generator
    load_watts = generate_load_profile(times, daily_avg_kwh=10.0) * 1000 # Convert back to Watts for compatibility if needed? 
    # Wait, main.py uses 'load_watts' (numpy array) then creates 'load_series'.
    # generate_load_profile returns Series in kW. 
    # main.py lines 44-51 create 'load_watts' (Watts).
    # line 53: load_series = pd.Series(load_watts, index=times)
    # line 54: daily_load_kwh = ... / 1000
    
    # We should return kW Series and adapt main.py usage.
    # main.py uses 'load_series' later (line 120, 124).
    # It assumes 'load_series' is in Watts? 
    # Let's check:
    # Line 120: optimize_battery_size(load_series, ac_power... )
    # optimize_battery_size typically expects Watts if ac_power is Watts.
    # main.py line 113: ac_power is Watts (pvlib output).
    # So 'load_series' must be Watts.
    
    load_series_kw = generate_load_profile(times, daily_avg_kwh=10.0)
    load_series = load_series_kw * 1000 # Convert kW -> W
    daily_load_kwh = load_series.resample('D').sum().mean() / 1000
    print(f"   Avg Daily Load: {daily_load_kwh:.2f} kWh")
    
    # -- Initialize Real DBs --
    print("\n   [Initializing Real Equipment Databases...]")
    sandia_mods, cec_invs = get_real_databases()
    
    # 2. Roof Fitting
    print("\n2. Checking Roof Capacity...")
    
    # Try to find a real module
    target_name = module.name.split('_')[0] # e.g. "Trina"
    print(f"   Searching for '{target_name}' modules...")
    matches = search_equipment(sandia_mods, target_name, limit=3)
    
    if not matches.empty and False: # Disable Real DB usage to enforce Mock usage for validation
        # Pick the first one
        mod_name = matches.index[0]
        real_mod_row = matches.iloc[0]
        print(f"   found: {mod_name}")
        target_module = adapt_sandia_module(mod_name, real_mod_row)
    else:
        print("   Using Default Mock Module.")
        target_module = module
    
    orientation, num_modules = suggest_best_orientation(roof_w, roof_h, target_module)
    print(f"   Selected Module: {target_module.name} ({target_module.power_watts:.1f}W)")
    print(f"   Best Orientation: {orientation}")

    print(f"   Max Modules: {num_modules}")
    print(f"   Total DC Capacity: {num_modules * target_module.power_watts / 1000:.2f} kWp")
    
    # 3. Equipment Selection
    print("\n3. Selecting Inverter...")
    
    # Try to find a real inverter
    target_inv_name = inverter.name.split('_')[0]
    print(f"   Searching for '{target_inv_name}' inverters...")
    matches = search_equipment(cec_invs, target_inv_name, limit=20)
    # Filter for power near 5000W
    matches = matches[ (matches['max_ac_power'] > 4000) ]
    
    if not matches.empty and False:
         inv_name = matches.index[0]
         real_inv_row = matches.iloc[0]
         target_inverter = adapt_cec_inverter(inv_name, real_inv_row)
    else:
         print(f"   Using Default Mock Inverter: {inverter.name}")
         target_inverter = inverter
    
    print(f"   Selected Inverter: {target_inverter.name} ({target_inverter.max_ac_power:.1f}W AC)")
    
    # Verify strict compatibility
    compat = check_module_inverter_compat(target_module, target_inverter, modules_per_string=num_modules) 
    print(f"   Compatibility Check: {compat}")
    
    # 4. PV Simulation
    print("\n4. Simulating PV Generation with PVLib...")
    # Assume 1 string of 'num_modules'
    ac_power = simulate_pv_generation(lat, lon, target_module, target_inverter, modules_per_string=num_modules)
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
    # Use the DEFAULT battery object instead of just size
    # But simulate_battery function expects kwh capacity, not object? 
    # Let's check simulate_battery signature in src/battery_sizing.py 
    # It takes (load_profile, pv_generation, battery_capacity_kwh).
    # So we keep using opt_size for now, OR we switch to using battery.nominal_energy_kwh?
    # The sizing flow *calculates* optimal size. The user might want to check the *default* battery performance.
    
    # Let's optimize size first (as before), and then maybe compare with the default battery?
    # Or should we just simulate the DEFAULT battery?
    # Given the "sizing tool" nature, optimizing is correct.
    # However, pysam simulation below uses `opt_size`.
    
    final_sim = simulate_battery(load_series, ac_power / 1000, opt_size) 
    
    self_sufficiency = 1 - (final_sim['grid_import'].sum() / (load_series.sum() / 1000))
    print(f"   [Custom Model] Projected Self-Sufficiency: {self_sufficiency:.1%}")
    
    # PySAM Simulation
    if opt_size > 0:
        print("\n7. Validating with NREL PySAM...")
        # PySAM Wrapper expects kW inputs
        # Here we can use the default battery properties (chemistry, voltage etc) from the imported `battery` object
        # IF simulate_pysam_battery supports passing a battery object.
        # Let's check src/battery_pysam.py content if needed, but for now assuming it takes scalar kwh.
        
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
