"""
Example 04a: Intelligent Battery Sizing
=======================================
Calculates optimal battery size based on two conflicting constraints:
1. Production Limit: Max capacity the PV system can reliably charge (Chargeability).
2. Consumption Limit: Capacity required to survive N days off-grid (Autonomy).

Methodology:
- Chargeability: 80th percentile of Daily Excess PV (PV Production - Load).
  This implies the battery can be fully charged 80% of the days from surplus alone.
- Autonomy: Daily Load * Target Days / Depth of Discharge.

The script simulates the recommended configuration to verify performance.
"""

import sys
import os
from pathlib import Path
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

# Ensure project root is in path
try:
    project_root = Path(__file__).parent.parent
except NameError:
    project_root = Path.cwd()
sys.path.insert(0, str(project_root))

from eclipse.config.equipments import batteries
from eclipse.battery import PySAMBatterySimulator, BatterySizer
from eclipse.synthetic import generate_scenario
from eclipse.plotting.battery import BatteryPlotter

output_dir = project_root / "examples" / "outputs" / "example-04-battery-sizing"
os.makedirs(output_dir, exist_ok=True)

# ==========================================
# 1. Configuration & Constraints
# ==========================================
# User Inputs
PV_SIZE_KWP           = 6.0           # Your PV System Size
DAILY_LOAD_KWH        = 15.0          # Your Average Daily Consumption
TARGET_AUTONOMY_DAYS  = 1.0           # How many days you want to survive without grid
TARGET_SOC_MAX        = 90.0          # Max charge target (%)
MIN_SOC               = 10.0          # Min reserve (%)

# Simulation Mode
# Set to True to inject realistic anomalies (cloudy days, load spikes)
# Set to False for ideal/systematic patterns
INCLUDE_ANOMALIES     = True          # Toggle realistic variability

print("="*60)
print(f"BATTERY SIZING ANALYSIS")
print(f"PV: {PV_SIZE_KWP} kWp | Load: {DAILY_LOAD_KWH} kWh/day | Autonomy: {TARGET_AUTONOMY_DAYS} days")
print(f"Mode: {'Realistic (with anomalies)' if INCLUDE_ANOMALIES else 'Ideal (systematic)'}")
print("="*60)

# ==========================================
# 2. Data Generation (Annual)
# ==========================================
print("\n>>> Generating annual scenario for analysis...")
# We generate a full year to get statistical significance
load_kw, pv_kw = generate_scenario(
    start_date='2024-01-01',
    days=365,
    daily_load=DAILY_LOAD_KWH,
    pv_size_kwp=PV_SIZE_KWP,
    freq='15min',
    profile_type='residential',       # or 'industrial'
    include_anomalies=True  # <<< NEW: Toggle realistic variability
)

# Create a DataFrame for analysis
df = pd.DataFrame({'load': load_kw, 'pv': pv_kw}, index=load_kw.index)
# Resample to daily sums for sizing logic
daily = df.resample('D').sum()
daily['excess_pv'] = (daily['pv'] - daily['load']).clip(lower=0)

# ==========================================
# 3. Sizing Logic (Using OOP BatterySizer)
# ==========================================

# Create sizer instance
sizer = BatterySizer(
    pv_kwp=PV_SIZE_KWP,
    daily_load_kwh=DAILY_LOAD_KWH,
    max_soc=TARGET_SOC_MAX,
    min_soc=MIN_SOC,
    simulator='pysam'  # Use simple simulator for reliability (pysam or simple)
)

sizing_result = sizer.recommend(load_kw, pv_kw, target='optimal')
print(sizer.summary(sizing_result))

# Extract recommended capacity for simulation
recommended_capacity = sizing_result.recommended_kwh

# ==========================================
# 4. Simulation Verification
# ==========================================
print(f"\n>>> Verifying with simulation (7 days in Summer)...")

from eclipse.config.equipments import batteries
from eclipse.battery import SimpleBatterySimulator, PySAMBatterySimulator

battery = batteries.default()
simulator = SimpleBatterySimulator(battery)
results = simulator.simulate(load_kw, pv_kw, system_kwh=recommended_capacity,
max_soc=TARGET_SOC_MAX,min_soc=MIN_SOC)

results.index = load_kw.index

# ==========================================
# 5. Visualization
# ==========================================
print("\n>>> Generating verificaton plot...")
plotter = BatteryPlotter()

# Plot a representative week (e.g., Summer to show charging)
start_plot = '2024-03-01'
end_plot = '2024-03-05'
plot_df = results.loc[start_plot:end_plot]


plot_path = output_dir / "04a_sized_verification.png"

plotter.plot_operation(
    plot_df, 
    plot_path,
    title=f"Sized Battery Verification ({recommended_capacity} kWh)"
)

print(f"Plot saved to: {plot_path}")
print("Done.")

