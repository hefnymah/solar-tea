"""
Example 12: Automatic PV + Battery Optimization
================================================
Demonstrates automatic optimization of both PV and battery sizes
based on user consumption profile and constraints.

Unlike Example 11 which uses fixed battery sizes, this example:
- Automatically sizes PV system for target self-sufficiency
- Automatically optimizes battery capacity
- Adapts to any consumption level and roof constraints
"""

import os
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from eclipse.consumption import ConsumptionData
from eclipse.pvsim import PVSystemSizer, LocationConfig, RoofConfig

print("=== Automatic PV + Battery System Optimization ===\n")

# 1. Load consumption data
DATA_FILE = Path(__file__).parent.parent / "data" / "consumption" / "20251212_consumption-frq-60min-leap-yr.csv"
print(f"1. Loading consumption data: {DATA_FILE.name}")
data = ConsumptionData.load(str(DATA_FILE))
print(f"   Annual consumption: {data.hourly.sum():.0f} kWh/year\n")

#%% 2. Configure location and roof
print("2. System Configuration")
location = LocationConfig(
    latitude=47.38,
    longitude=8.54,
    altitude=400,
    timezone='Europe/Zurich'
)
print(f"   Location: Zurich ({location.latitude}, {location.longitude})")

roof = RoofConfig(
    tilt=30,
    azimuth=180,
    max_area_m2=50,  # User's available roof area
    module_efficiency=0.20,
    performance_ratio=0.75
)
print(f"   Roof: {roof.max_area_m2} m² available")
print(f"   Max PV capacity: {roof.max_capacity_kwp} kWp\n")

#%% 3. Define optimization targets
target_self_sufficiency = 80.0  # User wants 80% independence
print(f"3. Optimization Target: {target_self_sufficiency}% self-sufficiency\n")

# ============================================================================
# STEP 1: Size PV system (without battery first)
# ============================================================================
print("=" * 70)
print("STEP 1: Sizing PV System (without battery)")
print("=" * 70)

sizer_no_battery = PVSystemSizer(data, location, roof)
result_no_battery = sizer_no_battery.size_for_self_sufficiency(target_percent=target_self_sufficiency)

print(f"\nPV-Only System:")
print(f"  Recommended PV size: {result_no_battery.recommended_kwp} kWp")
print(f"  Annual generation: {result_no_battery.annual_generation_kwh:.0f} kWh")
print(f"  Self-sufficiency achieved: {result_no_battery.self_sufficiency_pct:.1f}%")
print(f"  Grid import: {result_no_battery.annual_grid_import_kwh:.0f} kWh/year")
print(f"\n  ⚠️  Gap: Target {target_self_sufficiency}% vs Achieved {result_no_battery.self_sufficiency_pct:.1f}%")
print(f"      Reason: Timing mismatch (PV generates during day, consume 24/7)")
#%%
# ============================================================================
# STEP 2: Optimize battery size for the PV system
# ============================================================================
print("\n" + "=" * 70)
print("STEP 2: Optimizing Battery Size")
print("=" * 70)

# Use the battery optimization method
optimal_battery = sizer_no_battery.optimize_battery_size(
    pv_kwp=result_no_battery.recommended_kwp,
    target_self_sufficiency=target_self_sufficiency,
    battery_sizes=[0, 2.5, 5, 7.5, 10, 12.5, 15, 17.5, 20, 25, 30]  # Extended range
)

print(f"\n✅ Battery Optimization Complete!")
print(f"  Optimal battery size: {optimal_battery['optimal_kwh']} kWh")
print(f"  Self-sufficiency achieved: {optimal_battery['achieved_ss']:.1f}%")

if 'note' in optimal_battery:
    print(f"  Note: {optimal_battery['note']}")

# Show optimization sweep
print(f"\nOptimization Sweep Results:")
print(optimal_battery['sweep_results'].to_string(index=False))
#%%
# ============================================================================
# STEP 3: Final system with optimized battery
# ============================================================================
print("\n" + "=" * 70)
print("STEP 3: Final Optimized System")
print("=" * 70)

# Create final system with optimized battery
from eclipse.pvsim import BatteryConfig

if optimal_battery['optimal_kwh'] > 0:
    battery_config = BatteryConfig(
        capacity_kwh=optimal_battery['optimal_kwh'],
        power_kw=min(optimal_battery['optimal_kwh'] / 2, 10.0),  # C-rate 0.5
        efficiency=0.95
    )
    
    sizer_optimized = PVSystemSizer(data, location, roof, battery_config=battery_config)
    result_optimized = sizer_optimized.size_for_self_sufficiency(target_percent=target_self_sufficiency)
    
    print(f"\nOptimized PV + Battery System:")
    print(f"  PV: {result_optimized.recommended_kwp} kWp")
    print(f"  Battery: {result_optimized.battery_capacity_kwh} kWh")
    print(f"  Battery power: {battery_config.power_kw} kW")
    print(f"\n  Performance:")
    print(f"    Self-sufficiency: {result_optimized.self_sufficiency_pct:.1f}%")
    print(f"    Self-consumption: {result_optimized.self_consumption_pct:.1f}%")
    print(f"    Grid import: {result_optimized.annual_grid_import_kwh:.0f} kWh/year")
    print(f"    Grid export: {result_optimized.annual_grid_export_kwh:.0f} kWh/year")
    print(f"\n  Battery Metrics:")
    print(f"    Annual charge: {result_optimized.battery_charge_kwh:.0f} kWh")
    print(f"    Annual discharge: {result_optimized.battery_discharge_kwh:.0f} kWh")
    print(f"    Cycles per year: {result_optimized.battery_cycles:.1f}")
    print(f"    Battery health: {'✅ Excellent' if result_optimized.battery_cycles < 100 else '⚠️  Moderate' if result_optimized.battery_cycles < 200 else '❌ High wear'}")
else:
    result_optimized = result_no_battery
    print(f"\nNo battery needed (PV-only sufficient)")
#%%
# ============================================================================
# STEP 4: Comparison Summary
# ============================================================================
print("\n" + "=" * 70)
print("COMPARISON: System Evolution")
print("=" * 70)

print(f"\n{'Metric':<35} {'PV Only':<15} {'PV + Optimized Battery':<25}")
print("-" * 75)
print(f"{'PV System Size':<35} {result_no_battery.recommended_kwp:>10.2f} kWp {result_optimized.recommended_kwp:>10.2f} kWp")
print(f"{'Battery Size':<35} {0:>10.1f} kWh {optimal_battery['optimal_kwh']:>10.1f} kWh")
print(f"{'Self-Sufficiency':<35} {result_no_battery.self_sufficiency_pct:>10.1f}%  {result_optimized.self_sufficiency_pct:>10.1f}%")
print(f"{'Self-Consumption':<35} {result_no_battery.self_consumption_pct:>10.1f}%  {result_optimized.self_consumption_pct:>10.1f}%")
print(f"{'Grid Import (kWh/year)':<35} {result_no_battery.annual_grid_import_kwh:>10.0f}   {result_optimized.annual_grid_import_kwh:>10.0f}")
print(f"{'Grid Export (kWh/year)':<35} {result_no_battery.annual_grid_export_kwh:>10.0f}   {result_optimized.annual_grid_export_kwh:>10.0f}")

improvement_ss = result_optimized.self_sufficiency_pct - result_no_battery.self_sufficiency_pct
improvement_import = result_no_battery.annual_grid_import_kwh - result_optimized.annual_grid_import_kwh

print(f"\n{'Improvement with Battery:':<35}")
print(f"{'  Self-Sufficiency Gain':<35} {improvement_ss:>+10.1f}%")
print(f"{'  Grid Import Reduction':<35} {improvement_import:>+10.0f} kWh/year")
#%%
# ============================================================================
# STEP 5: Generate visualizations
# ============================================================================
print("\n" + "=" * 70)
print("Generating Visualizations")
print("=" * 70)

output_dir = Path(__file__).parent / "outputs" / "12-auto-optimization"
output_dir.mkdir(parents=True, exist_ok=True)

# Monthly comparison
monthly_plot = output_dir / "monthly_comparison.png"
result_optimized.plot_monthly_comparison(output_path=str(monthly_plot))
print(f"  ✅ Monthly comparison: {monthly_plot}")

# Seasonal PV production
seasonal_plot = output_dir / "seasonal_pv_production.png"
result_optimized.plot_seasonal_daily_production(output_path=str(seasonal_plot))
print(f"  ✅ Seasonal PV profile: {seasonal_plot}")

# Battery SOC (if battery exists)
if optimal_battery['optimal_kwh'] > 0:
    soc_plot = output_dir / "battery_soc_profile.png"
    result_optimized.plot_battery_soc(output_path=str(soc_plot), days_to_show=7)
    print(f"  ✅ Battery SOC profile: {soc_plot}")

print(f"\n{'='*70}")
print("✅ Optimization Complete!")
print(f"{'='*70}")
print(f"\n💡 Key Takeaway:")
print(f"   For {data.hourly.sum():.0f} kWh/year consumption:")
print(f"   → Optimal PV: {result_optimized.recommended_kwp} kWp")
print(f"   → Optimal Battery: {optimal_battery['optimal_kwh']} kWh")
print(f"   → Achieves: {result_optimized.self_sufficiency_pct:.1f}% self-sufficiency")
print(f"\nThis system adapts automatically to ANY consumption level! 🎯")
