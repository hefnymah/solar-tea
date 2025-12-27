"""
Example 13: Ultimate Joint PV + Battery Optimization
=====================================================
The smartest optimization - jointly optimizes BOTH PV size AND battery capacity.

This ultimate algorithm:
- Tests different PV sizes (respecting roof constraints)
- For each PV size, optimizes battery with physics-based limits
- Finds the best combination to achieve target self-sufficiency
- Can prioritize 'performance' (max self-sufficiency) or 'economy' (min cost)
"""

import os
import sys
from pathlib import Path
# Add parent directory to path
try:
    project_root = Path(__file__).parent.parent
except NameError:
    project_root = Path.cwd()
sys.path.insert(0, str(project_root))

from eclipse.consumption import ConsumptionData
from eclipse.simulation import PVSystemSizer, LocationConfig, RoofConfig, BatteryConfig

print("=== ULTIMATE: Joint PV + Battery Optimization ===\n")

#%% Project Setting
input_dir  = project_root / "data" / "consumption"
output_dir = project_root / "examples" / "outputs" / "example-13"
os.makedirs(output_dir, exist_ok=True)

latitude          = 47.38
longitude         = 8.54
roof_area_m2      = 50
roof_tilt         = 30
roof_azimuth      = 180
module_efficiency = 0.20

#%%
# 1. Load consumption data

DATA_FILE = input_dir / "20251212_consumption-frq-60min-leap-yr.csv"
print(f"1. Loading consumption data: {DATA_FILE.name}")
data = ConsumptionData.load(str(DATA_FILE))
print(f"   Annual consumption: {data.hourly.sum():.0f} kWh/year\n")

#%%

# 2. Configure location and roof
print("2. System Configuration")
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
    module_efficiency=module_efficiency
)

print(f"   Roof: {roof.max_area_m2} m² → max {roof.max_capacity_kwp} kWp PV\n")

# 3. Create sizer
sizer = PVSystemSizer(
    consumption_data=data,
    location=location,
    roof=roof,
    battery_config=None    
)

#%%
# ============================================================================
# OPTIMIZATION 1: Performance Priority (Max Self-Sufficiency)
# ============================================================================
print("\n" + "=" * 70)
print("OPTIMIZATION 1: Performance Priority")
print("=" * 70)
print("Goal: Maximize self-sufficiency within roof constraints\n")

optimal_performance = sizer.optimize_system(
    target_self_sufficiency=80.0,
    pv_step_kwp=0.5,
    prioritize='performance'
)

print("\nPerformance-Optimized System:")
print(f"  PV: {optimal_performance['optimal_pv_kwp']} kWp")
print(f"  Battery: {optimal_performance['optimal_battery_kwh']} kWh")
print(f"  Self-Sufficiency: {optimal_performance['achieved_ss']:.1f}%")

result_perf = optimal_performance['result']
print(f"\n  Annual Metrics:")
print(f"    Generation: {result_perf.annual_generation_kwh:.0f} kWh")
print(f"    Grid Import: {result_perf.annual_grid_import_kwh:.0f} kWh")
print(f"    Grid Export: {result_perf.annual_grid_export_kwh:.0f} kWh")
print(f"    Battery Cycles: {result_perf.battery_cycles:.1f}/year")

#%%
# ============================================================================
# OPTIMIZATION 2: Economy Priority (Minimize Cost)
# ============================================================================
print("\n" + "=" * 70)
print("OPTIMIZATION 2: Economy Priority")
print("=" * 70)
print("Goal: Minimize system size while achieving 80% target\n")

optimal_economy = sizer.optimize_system(
    target_self_sufficiency=80.0,
    pv_step_kwp=0.5,
    prioritize='economy'
)

print("\nEconomy-Optimized System:")
print(f"  PV: {optimal_economy['optimal_pv_kwp']} kWp")
print(f"  Battery: {optimal_economy['optimal_battery_kwh']} kWh")
print(f"  Self-Sufficiency: {optimal_economy['achieved_ss']:.1f}%")

if optimal_economy['result']:
    result_econ = optimal_economy['result']
    print(f"\n  Annual Metrics:")
    print(f"    Generation: {result_econ.annual_generation_kwh:.0f} kWh")
    print(f"    Grid Import: {result_econ.annual_grid_import_kwh:.0f} kWh")
    print(f"    Battery Cycles: {result_econ.battery_cycles:.1f}/year")

#%%
# ============================================================================
# COMPARISON TABLE
# ============================================================================
print("\n" + "=" * 70)
print("COMPARISON: Performance vs Economy")
print("=" * 70)

print(f"\n{'Metric':<30} {'Performance':<20} {'Economy':<20}")
print("-" * 70)
print(f"{'PV Size (kWp)':<30} {optimal_performance['optimal_pv_kwp']:<20} {optimal_economy['optimal_pv_kwp']:<20}")
print(f"{'Battery Size (kWh)':<30} {optimal_performance['optimal_battery_kwh']:<20} {optimal_economy['optimal_battery_kwh']:<20}")
print(f"{'Self-Sufficiency (%)':<30} {optimal_performance['achieved_ss']:<20.1f} {optimal_economy['achieved_ss']:<20.1f}")
print(f"{'Grid Import (kWh/yr)':<30} {result_perf.annual_grid_import_kwh:<20.0f} {result_econ.annual_grid_import_kwh if result_econ else 'N/A':<20}")

# Rough cost estimate
cost_perf = optimal_performance['optimal_pv_kwp'] * 1500 + optimal_performance['optimal_battery_kwh'] * 600
cost_econ = optimal_economy['optimal_pv_kwp'] * 1500 + optimal_economy['optimal_battery_kwh'] * 600
print(f"{'Est. Cost (€)':<30} {cost_perf:<20,.0f} {cost_econ:<20,.0f}")

#%%
# ============================================================================
# VISUALIZATIONS
# ============================================================================
print("\n" + "=" * 70)
print("Generating Visualizations")
print("=" * 70)

# Visualize performance-optimized system
monthly_plot = output_dir / "monthly_performance.png"
result_perf.plot_monthly_comparison(output_path=str(monthly_plot))
print(f"  ✅ Monthly comparison: {monthly_plot}")

soc_plot = output_dir / "battery_soc_performance.png"
result_perf.plot_battery_soc(output_path=str(soc_plot))
print(f"  ✅ Battery SOC: {soc_plot}")

# Show all tested combinations
print(f"\n  All tested combinations saved to optimization dataframe")
combinations_file = output_dir / "all_combinations.csv"
optimal_performance['all_combinations'].to_csv(combinations_file, index=False)
print(f"  📊 {combinations_file}")

print(f"\n{'='*70}")
print("✅ Ultimate Optimization Complete!")
print(f"{'='*70}")
print(f"\n💡 Key Insight:")
print(f"   The joint PV+battery optimization automatically:")
print(f"   1. Respects roof constraints ({roof.max_capacity_kwp} kWp max)")
print(f"   2. Physics-based battery sizing (2-day storage rule)")
print(f"   3. Tests all PV sizes to find global optimum")
print(f"   4. Balances performance vs cost based on priority")
print(f"\n   This is the SMARTEST way to design a solar+storage system! 🎯⚡🔋")
