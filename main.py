
import pandas as pd
import numpy as np

import sys
import os
# Ensure root is in path for imports
sys.path.append(os.path.dirname(__file__))

from eclipse.config.equipments import MODULE_DB, INVERTER_DB
from eclipse.config.equipments import modules
from eclipse.config.equipments import inverters
from eclipse.config.equipments import batteries

# Initialize defaults using new API
module = modules.default()
inverter = inverters.default()
battery = batteries.default()

# Modern equipment management - OOP-based
from eclipse.equipment import (
    EquipmentDatabase,
    SandiaModuleAdapter,
    CECInverterAdapter,
    CompatibilityChecker
)

# Modern PV simulation - OOP-based
from eclipse.simulation import PVSystemSizer, LocationConfig, RoofConfig, suggest_module_layout
from eclipse.consumption import ConsumptionData

from eclipse.synthetic import generate_load_profile

def main():
    print("=== Solar PV & Battery Sizing Tool ===\n")
    
    # 1. Inputs
    # Location: Zurich, Switzerland
    lat, lon = 47.3769, 8.5417
    
    # Roof: 10m x 6m available area
    roof_w, roof_h = 10, 6 
    
    # Load: Simple dummy profile (avg 10kWh/day)
    print("1. Generating Load Profile...")
    times = pd.date_range(start='2024-01-01', end='2024-12-31 23:00', freq='h', tz='UTC')
    
    # Generate load profile in kW
    load_series_kw = generate_load_profile(times, daily_avg_kwh=10.0)
    load_series = load_series_kw * 1000  # Convert kW -> W for battery simulation compatibility
    daily_load_kwh = load_series.resample('D').sum().mean() / 1000
    print(f"   Avg Daily Load: {daily_load_kwh:.2f} kWh")
    
    # -- Initialize Real DBs --
    print("\n   [Initializing Real Equipment Databases...]")
    db = EquipmentDatabase()
    sandia_mods, cec_invs = db.get_databases()
    
    # 2. Roof Fitting with Modern Utility
    print("\n2. Checking Roof Capacity...")
    
    # Try to find a real module
    target_name = module.name.split('_')[0]  # e.g. "Trina"
    print(f"   Searching for '{target_name}' modules...")
    matches = db.search_modules(target_name, limit=3)
    
    if not matches.empty and False:  # Disable Real DB usage to enforce Mock usage for validation
        # Pick the first one
        mod_name = matches.index[0]
        real_mod_row = matches.iloc[0]
        print(f"   found: {mod_name}")
        target_module = SandiaModuleAdapter.adapt(mod_name, real_mod_row)
    else:
        print("   Using Default Mock Module.")
        target_module = module
    
    # Use modern suggest_module_layout utility
    orientation, num_modules, total_area = suggest_module_layout(
        roof_w, roof_h, 
        target_module.width_m, target_module.height_m, 
        setback_m=0.5
    )
    
    print(f"   Selected Module: {target_module.name} ({target_module.power_watts:.1f}W)")
    print(f"   Best Orientation: {orientation}")
    print(f"   Max Modules: {num_modules}")
    print(f"   Total DC Capacity: {num_modules * target_module.power_watts / 1000:.2f} kWp")
    
    # 3. Equipment Selection
    print("\n3. Selecting Inverter...")
    
    # Try to find a real inverter
    target_inv_name = inverter.name.split('_')[0]
    print(f"   Searching for '{target_inv_name}' inverters...")
    matches = db.search_inverters(target_inv_name, limit=20)
    # Filter for power near 5000W
    matches = matches[ (matches['max_ac_power'] > 4000) ]
    
    if not matches.empty and False:
         inv_name = matches.index[0]
         real_inv_row = matches.iloc[0]
         target_inverter = CECInverterAdapter.adapt(inv_name, real_inv_row)
    else:
         print(f"   Using Default Mock Inverter: {inverter.name}")
         target_inverter = inverter
    
    print(f"   Selected Inverter: {target_inverter.name} ({target_inverter.max_ac_power:.1f}W AC)")
    
    # Verify strict compatibility
    compat = CompatibilityChecker.check_module_inverter(target_module, target_inverter, modules_per_string=num_modules) 
    print(f"   Compatibility Check: {compat}")
    
    # 4. PV Simulation with Modern PVSystemSizer
    print("\n4. Simulating PV Generation with PVLib...")
    
    # Create ConsumptionData from load profile
    load_df = pd.DataFrame({
        'Consumption_kWh': load_series_kw.values
    }, index=load_series_kw.index.tz_localize(None))  # Remove timezone for compatibility
    consumption_data = ConsumptionData(load_df, 'Consumption_kWh')
    
    # Configure PV system
    location_cfg = LocationConfig(
        latitude=lat,
        longitude=lon,
        altitude=408,
        timezone='Europe/Zurich'
    )
    
    roof_cfg = RoofConfig(
        tilt=30,
        azimuth=180,
        max_area_m2=total_area,
        module_efficiency=0.20,
        performance_ratio=0.75
    )
    
    # Create sizer
    sizer = PVSystemSizer(
        consumption_data=consumption_data,
        location=location_cfg,
        roof=roof_cfg
    )
    
    # Get PV generation for actual installed capacity
    installed_kwp = num_modules * target_module.power_watts / 1000
    ac_power_kwh = sizer.simulation.scale_to_capacity(installed_kwp)
    ac_power = ac_power_kwh * 1000  # Convert to W for battery simulation
    
    total_gen_kwh = ac_power.sum() / 1000
    print(f"   Annual PV Generation: {total_gen_kwh:.2f} kWh")
    print(f"   Specific Yield: {sizer.simulation.specific_yield:.0f} kWh/kWp/year")
    
    # 5. Summary
    print("\n5. System Summary...")
    annual_consumption = load_series.sum() / 1000
    generation_ratio = total_gen_kwh / annual_consumption
    print(f"   Annual Consumption: {annual_consumption:.2f} kWh")
    print(f"   Annual Generation: {total_gen_kwh:.2f} kWh")
    print(f"   Generation/Load Ratio: {generation_ratio:.2f}")
    print(f"   System covers {min(generation_ratio * 100, 100):.1f}% of annual consumption")

if __name__ == "__main__":
    main()
