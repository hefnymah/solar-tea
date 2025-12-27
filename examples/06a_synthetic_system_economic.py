
"""
Example 6a: Synthetic PV + Battery System with Economic Analysis
==================================================
Deep dive into a single day of operation to verify the underlying calculations.

Focus:
- 24-Hour Profile
- Detailed Power Flow (Net Load calculation)
- Math Verification Table
- Economic Analysis
    - Pronovo Subsidy Calculation
    - 
"""

import matplotlib.pyplot as plt
import pandas as pd
import numpy as np
import sys
import os
from pathlib import Path

# Ensure root is in path
try:
    project_root = Path(__file__).parent.parent
except NameError:
    project_root = Path.cwd()
sys.path.insert(0, str(project_root))

from eclipse.config.equipments import batteries, modules
from eclipse.battery import PySAMBatterySimulator
from eclipse.synthetic import generate_scenario
from eclipse.economics.subsidies.pronovo import calculate_subsidy
from eclipse.economics.capex import CapexCalculator
from eclipse.economics.enums import SystemCategory

#%%
# ==========================================
# 1. Configuration
# ==========================================

import pvlib

# Helper to fetch altitude if needed
def get_altitude_from_pvgis(lat, lon):
    try:
        print(f"Fetching altitude for {lat}°N, {lon}°E...")
        # Get TMY data which includes metadata
        # Return can be (data, months, inputs, meta) OR (data, months, inputs) depending on version/args
        res = pvlib.iotools.get_pvgis_tmy(lat, lon, map_variables=False)
        
        meta = {}
        if isinstance(res, tuple):
            # Scan tuple for the metadata dict (which contains 'elevation')
            for item in res:
                if isinstance(item, dict) and ('elevation' in item or 'location' in item):
                    meta = item
                    break
                # Deep search if needed
                if isinstance(item, dict):
                     if 'elevation' in str(item): # Quick check if key exists deep
                         meta = item
                         break

        # Robustly find elevation in metadata
        def find_elev(d):
            if 'elevation' in d: return d['elevation']
            for v in d.values():
                if isinstance(v, dict):
                    res = find_elev(v)
                    if res: return res
            return None
        
        elev = find_elev(meta)
        if elev:
            print(f"  -> Fetched Altitude: {elev} m")
            return float(elev)
        else:
            print("  Warning: Elevation not found in PVGIS metadata.")
    except Exception as e:
        print(f"Warning: Could not fetch altitude ({e}). Using default.")
    return 550.0  # Default fallback

BATTERY_CAPACITY_KWH = 13.5
PV_SIZE_KWP = 6.0
# Increase load to match the "Industrial/Daytime" scale relative to PV
DAILY_LOAD_KWH = 30.0

# User-defined location
LAT = 46.8027
LON = 9.8360
ALTITUDE_M = get_altitude_from_pvgis(LAT, LON)
TILT_DEG = 30.0

battery = batteries.default()

#%%
# ==========================================
# 2. Generate Data (The "Input")
# ==========================================
print("Generating scenario (15-min resolution)...")

# New centralized generation
load_kw, pv_kw = generate_scenario(
    start_date='2024-01-01',
    days=365,
    daily_load=DAILY_LOAD_KWH,
    pv_size_kwp=PV_SIZE_KWP,
    freq='15min',                  # 15-minute resolution
    profile_type='industrial',      # Use the blocky industrial shape or 'residential' for smooth shape
    include_anomalies=True
)

# Extract times index for later use
times = load_kw.index

#%%
# ==========================================
# 3. Simulation
# ==========================================

print("Simulating battery...")
simulator = PySAMBatterySimulator(battery)
results = simulator.simulate(
    load_kw, pv_kw, 
    system_kwh=BATTERY_CAPACITY_KWH,
    max_soc=90.0,
    min_soc=10.0
)
results.index = load_kw.index

# Calculate Annual Metrics
annual_load = results['load'].sum() / 4.0  # 15-min data -> kWh
annual_pv = results['pv'].sum() / 4.0
annual_import = results['grid_import'].sum() / 4.0
annual_export = results['grid_export'].sum() / 4.0

# Correct self-consumption calculation
# Self-consumed = Generation - Export
annual_self_consumed = annual_pv - annual_export
if annual_pv > 0:
    self_consumption_pct = (annual_self_consumed / annual_pv) * 100.0
else:
    self_consumption_pct = 0.0

if annual_load > 0:
    self_sufficiency_pct = ((annual_load - annual_import) / annual_load) * 100.0
else:
    self_sufficiency_pct = 100.0

# ==========================================
# 4. ECONOMICS (PRONOVO SUBSIDY)
# ==========================================
print("\n" + "=" * 70)
print("FINANCIAL ESTIMATION (SUBSIDY)")
print("=" * 70)

print(f"Detected Altitude: {ALTITUDE_M:.1f} m")

# Calculate subsidy using simulation results
subsidy = calculate_subsidy(
    capacity_kwp=PV_SIZE_KWP,
    category=SystemCategory.ATTACHED_ROOF,
    has_self_consumption=True,  # Standard EIV
    altitude_meters=ALTITUDE_M,
    tilt_angle_degrees=TILT_DEG,

    parking_area_coverage=True
)

# ==========================================
# 5. ECONOMICS (CAPEX)
# ==========================================
capex_calc = CapexCalculator()
# Use a specific module e.g. Trina550 or default
module_model = modules.Trina550() # MockModule(power_watts=550.0, ...)

capex_result = capex_calc.calculate_module_cost(
    system_size_kwp=PV_SIZE_KWP,
    module_model=module_model,
    margin_pct=0.20 # 20% Margin
)

#%%
# ==========================================
# 5. RESULTS
# ==========================================

# Helper for table rows
def row(label, value, unit=""):
    # Fixed width for value column to align units
    val_str = f"{value}"
    if unit:
        val_str += f" {unit}"
    
    # 2 spaces indent, label 20 chars, value aligned
    content = f"  {label:<18} {val_str}"
    return f"│ {content:<67} │"

print(f"""
┌─────────────────────────────────────────────────────────────────────┐
│  RECOMMENDED SYSTEM                                                 │
├─────────────────────────────────────────────────────────────────────┤
{row("PV System:", f"{PV_SIZE_KWP:>.2f}", "kWp")}
{row("Battery:", f"{BATTERY_CAPACITY_KWH:>.1f}", "kWh (Synthetic)")}
├─────────────────────────────────────────────────────────────────────┤
│  ANNUAL PERFORMANCE                                                 │
├─────────────────────────────────────────────────────────────────────┤
{row("Self-Sufficiency:", f"{self_sufficiency_pct:>.1f}", "%")}
{row("Self-Consumption:", f"{self_consumption_pct:>.1f}", "%")}
{row("Grid Import:", f"{annual_import:>.0f}", "kWh/year")}
{row("Grid Export:", f"{annual_export:>.0f}", "kWh/year")}
├─────────────────────────────────────────────────────────────────────┤
│  ESTIMATED SUBSIDY (PRONOVO 2025)                                   │
├─────────────────────────────────────────────────────────────────────┤
{row("Base Subsidy:", f"{subsidy.base_contribution:>,.0f}", "CHF")}
{row("Tilt Angle Bonus:", f"{subsidy.tilt_bonus:>,.0f}", "CHF")}
{row("Height Bonus:", f"{subsidy.altitude_bonus:>,.0f}", "CHF")}
{row("Parking Bonus:", f"{subsidy.parking_bonus:>,.0f}", "CHF")}
{row("TOTAL FUNDING:", f"{subsidy.total:>,.0f}", "CHF")}
├─────────────────────────────────────────────────────────────────────┤
│  CAPITAL EXPENDITURE (MODULES ONLY)                                 │
├─────────────────────────────────────────────────────────────────────┤
{row("Module Model:", f"{capex_result.module_model_name[:30]}")}
{row("Quantity:", f"{capex_result.module_count}", "units")}
{row("Base Cost:", f"{capex_result.module_cost_base:>,.2f}", capex_result.currency)}
{row("Margin (20%):", f"{capex_result.module_margin_amount:>,.2f}", capex_result.currency)}
{row("TOTAL MODULE RATE:", f"{capex_result.module_cost_total:>,.2f}", capex_result.currency)}
└─────────────────────────────────────────────────────────────────────┘
""")
