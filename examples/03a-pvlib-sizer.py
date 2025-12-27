"""
PV System Analysis - Clean OOP Architecture
============================================
Demonstrates proper separation of concerns in Eclipse framework:

Layer 1: Data Storage    → SizingResult
Layer 2: Business Logic  → PVSystemAnalyzer  
Layer 3: Visualization   → PVSystemBehaviorPlotter

Author: Eclipse Framework
Date: 2024-12-23
"""

import sys
import os
from pathlib import Path
try:
    project_root = Path(__file__).parent.parent
except NameError:
    project_root = Path.cwd()

sys.path.insert(0, str(project_root))

from eclipse.consumption import ConsumptionData
from eclipse.pvsim import PVSystemSizer, LocationConfig, RoofConfig, PVSystemAnalyzer
from eclipse.plotting import PVSystemBehaviorPlotter

#%% Project Setting
# Handle both script and interactive execution

input_dir  = project_root / "data" / "consumption"
output_dir = project_root / "examples" / "outputs" / "example-03a-v2"
os.makedirs(output_dir, exist_ok=True)

#%%
print("=" * 70)
print("PV SYSTEM ANALYSIS - CLEAN OOP ARCHITECTURE")
print("=" * 70)

# 1. Load consumption data (Data Layer)
#DATA_FILE = input_dir / "20251212_consumption-frq-60min-leap-yr.csv"
DATA_FILE = input_dir / "20251212_consumption-frq-15min-leap-yr.csv"

data = ConsumptionData.load(str(DATA_FILE))
print(f"\n>>> Loaded: {data}")

#%% 2. Size PV system (Simulation Layer)
location = LocationConfig(latitude=47.38, longitude=8.54)
roof = RoofConfig(tilt=30, azimuth=180, max_area_m2=50)

sizer = PVSystemSizer(data, location, roof)
result = sizer.size_for_self_sufficiency(target_percent=80)

print(f"\n>>> PV System: {result.recommended_kwp} kWp")
print(f"    Self-sufficiency: {result.self_sufficiency_pct:.1f}%")

#%% 3. Analyze periods (Business Logic Layer)
print("\n" + "=" * 70)
print("DATA PROCESSING (Business Logic)")
print("=" * 70)

analyzer = PVSystemAnalyzer(result)

results_dic= analyzer.to_dict()

# Analyze different periods
print("\n>>> Processing summer week...")
summer_data = analyzer.analyze_period('2024-06-01', '2024-06-07')

print("\n>>> Processing winter day...")
winter_data = analyzer.analyze_day('2024-06-03')

print("\n>>> Processing spring week...")
spring_data = analyzer.analyze_period('2024-03-15', '2024-03-21')

# June month analysis
june_data = analyzer.analyze_period('2024-06-01', '2024-06-30')


# Print summaries
analyzer.print_summary(summer_data)
analyzer.print_summary(winter_data)

#%% 4. Visualize (Presentation Layer)
print("\n" + "=" * 70)
print("VISUALIZATION (Presentation Logic)")
print("=" * 70)


# Plot processed data
print("\n>>> Generating plots from processed data...")

PVSystemBehaviorPlotter.plot(
    summer_data,
    title='Summer Week',
    output_path=f"{output_dir}/summer_week.png"
)

PVSystemBehaviorPlotter.plot(
    winter_data,
    title='Winter Day',
    output_path=f"{output_dir}/winter_day.png"
)

PVSystemBehaviorPlotter.plot(
    spring_data,
    title='Spring Week',
    output_path=f"{output_dir}/spring_week.png"
)

PVSystemBehaviorPlotter.plot(
    june_data,
    title='June Month',
    output_path=f"{output_dir}/june_month.png"
)

# Additional comprehensive annual plots
print("\n>>> Generating comprehensive annual plots...")

# Monthly energy flows
monthly_flows = analyzer.get_monthly_energy_flows()
PVSystemBehaviorPlotter.plot_monthly_energy_flows(
    monthly_flows,
    result,
    output_path=f"{output_dir}/monthly_energy_flows.png"
)

# Seasonal daily profiles
seasonal_profiles = analyzer.get_seasonal_daily_profiles()
PVSystemBehaviorPlotter.plot_seasonal_daily_profiles(
    seasonal_profiles,
    result,
    output_path=f"{output_dir}/seasonal_daily_profiles.png"
)
