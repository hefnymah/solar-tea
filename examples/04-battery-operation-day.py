
"""
Example 4b: Battery Operation - Daily Verification
==================================================
Deep dive into a single day of operation to verify the underlying calculations.

Focus:
- 24-Hour Profile
- Detailed Power Flow (Net Load calculation)
- Math Verification Table
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

from eclipse.config.equipments import batteries
from eclipse.battery import PySAMBatterySimulator
from eclipse.synthetic import generate_scenario
from eclipse.plotting.battery import BatteryPlotter

#%%
# ==========================================
# 1. Configuration
# ==========================================

output_dir = project_root / "examples" / "outputs" / "example-04"
os.makedirs(output_dir, exist_ok=True)
daily_plot_path = output_dir / "04_daily_verification.png"


BATTERY_CAPACITY_KWH = 13.5
PV_SIZE_KWP = 6.0
# Increase load to match the "Industrial/Daytime" scale relative to PV
DAILY_LOAD_KWH = 30.0
battery_model = batteries.default()

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
    profile_type='industrial'      # Use the blocky industrial shape or 'residential' for smooth shape
)

# Extract times index for later use
times = load_kw.index
#%%
# ==========================================
# 2. Simulation
# ==========================================

print("Simulating battery...")
simulator = PySAMBatterySimulator(battery_model)
results = simulator.simulate(
    load_kw, pv_kw, 
    system_kwh=BATTERY_CAPACITY_KWH,
    max_soc=90.0,
    min_soc=10.0
)
results.index = load_kw.index
#%%
# ==========================================
# 3. Select Period to Analyze
# ==========================================
# Configure the analysis period (can be a single day, week, or month)
START_DATE = '2024-01-01'  # Start date for analysis
END_DATE = '2024-01-07'    # End date (same as start = single day)

# Alternative examples:
# Week: START_DATE = '2024-07-01', END_DATE = '2024-07-07'
# Month: START_DATE = '2024-07-01', END_DATE = '2024-07-31'

# Extract the selected period
period_df = results.loc[START_DATE:END_DATE].copy()

print(f"\nAnalyzing period: {START_DATE} to {END_DATE}")
print(f"Total timesteps: {len(period_df)}")
print(f"SOC Range: {period_df['soc'].min():.1f}% to {period_df['soc'].max():.1f}%")
print(f"Total Grid Import: {period_df['grid_import'].sum():.2f} kWh")
print(f"Total Grid Export: {period_df['grid_export'].sum():.2f} kWh")

#%%
# ==========================================
# 4. Visualization
# ==========================================
# Use the new OOP Plotter
plotter = BatteryPlotter()

# Generate operation plot for the selected period
plotter.plot_operation(period_df, daily_plot_path)

# Export to CSV
csv_path = output_dir / "4b_battery_analysis.csv"
print("Exporting to CSV...")
period_df.to_csv(csv_path)
print(f"CSV saved to: {csv_path}")
