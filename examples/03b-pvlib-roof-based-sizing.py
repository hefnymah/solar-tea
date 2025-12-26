"""
PV System Roof-Based Sizing - Clean OOP Architecture
====================================================
Demonstrates sizing based on available roof area using clean 3-layer architecture.

Layer 1: Data Storage    → SizingResult
Layer 2: Business Logic  → PVSystemAnalyzer  
Layer 3: Visualization   → PVSystemBehaviorPlotter

Author: Eclipse Framework
Date: 2024-12-23
"""

import sys
import os
from pathlib import Path
# Handle both script and interactive execution
try:
    project_root = Path(__file__).parent.parent
except NameError:
    project_root = Path.cwd()
sys.path.insert(0, str(project_root))

from eclipse.consumption import ConsumptionData
from eclipse.pvsim import (
    PVSystemSizer, LocationConfig, RoofConfig, PVSystemAnalyzer,
    SizingUtilities, ResultsFormatter
)
from eclipse.plotting import PVSystemBehaviorPlotter

#%% Project Setting
input_dir  = project_root / "data" / "consumption"
output_dir = project_root / "examples" / "outputs" / "example-03b"
os.makedirs(output_dir, exist_ok=True)

latitude          = 47.38
longitude         = 8.54
roof_area_m2      = 50
roof_tilt         = 30
roof_azimuth      = 180
module_efficiency = 0.20

#%%
print("=" * 70)
print("PV SYSTEM ROOF-BASED SIZING - CLEAN OOP ARCHITECTURE")
print("=" * 70)

# 1. Load consumption data
DATA_FILE = input_dir / "20251212_consumption-frq-15min-leap-yr.csv"
print(f"\n>>> Loading consumption data: {DATA_FILE.name}")
data = ConsumptionData.load(str(DATA_FILE))
print(f"   {data}\n")

#%% 2. Configure roof and calculate maximum capacity
print("=" * 70)
print("ROOF SPECIFICATIONS")
print("=" * 70)

# Calculate maximum PV capacity
max_kwp = roof_area_m2 * module_efficiency
print(f"\n   → Maximum PV capacity: {max_kwp:.2f} kWp")

#%% 3. Simulate PV system at maximum capacity
location = LocationConfig(
    latitude=latitude, 
    longitude=longitude,
    altitude=400,
    timezone='Europe/Zurich'
)

roof = RoofConfig(
    tilt=roof_tilt, 
    azimuth=roof_azimuth, 
    max_area_m2=roof_area_m2,
    module_efficiency=module_efficiency,
    performance_ratio=0.75
)

sizer = PVSystemSizer(
    consumption_data=data,
    location=location,
    roof=roof,
    battery_config=None    
)

print("\n" + "=" * 70)
print("SIMULATING PV SYSTEM")
print("=" * 70)
print(f"\n🔬 Running simulation for {max_kwp:.2f} kWp system...")

print(f"   {sizer}\n")

result = sizer.simulate(pv_kwp=max_kwp, battery_kwh=0.0)

#%%
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



#%% 4. Display results using ResultsFormatter
ResultsFormatter.print_summary(result)

#%% 5. Analysis using ResultsFormatter
ResultsFormatter.print_analysis(result)

#%% 6. What-if scenarios using SizingUtilities
# Generate test sizes dynamically based on roof capacity
sizes = SizingUtilities.generate_test_sizes(max_kwp, percentages=[0.25, 0.50, 0.75, 1.0])

# Run all scenarios
scenarios = SizingUtilities.run_scenarios(sizer, sizes)

# Display comparison table
ResultsFormatter.print_scenario_comparison(scenarios)

# Generate visual comparison chart
ResultsFormatter.plot_scenario_comparison(
    scenarios,
    output_path=f"{output_dir}/scenario_comparison.png",
    title=f"PV System Sizing Comparison (Max: {max_kwp:.1f} kWp)"
)
