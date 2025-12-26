"""
Example 11: PV + Battery System Sizing
=======================================
Demonstrates battery integration to achieve realistic self-sufficiency.

Compares:
- PV only (limited by timing mismatch)
- PV + Battery (stores surplus for later use)
"""

import os
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from eclipse.consumption import ConsumptionData
from eclipse.pvsim import PVSystemSizer, LocationConfig, RoofConfig, BatteryConfig

print("=== PV + Battery System Sizing Example ===\n")

# 1. Load consumption data
DATA_FILE = Path(__file__).parent.parent / "data" / "consumption" / "20251212_consumption-frq-60min-leap-yr.csv"
print(f"1. Loading consumption data: {DATA_FILE.name}")
data = ConsumptionData.load(str(DATA_FILE))
print(f"   {data}\n")

# 2. Configure location and roof
location = LocationConfig(latitude=47.38, longitude=8.54)
roof = RoofConfig(tilt=30, azimuth=180, max_area_m2=50)

# 3. Test PV WITHOUT battery
print("=" * 60)
print("SCENARIO 1: PV ONLY (No Battery)")
print("=" * 60)

sizer_no_battery = PVSystemSizer(data, location, roof)
result_no_battery = sizer_no_battery.size_for_self_sufficiency(target_percent=80)

print(f"\nTarget: 80% self-sufficiency")
print(f"System size: {result_no_battery.recommended_kwp} kWp")
print(f"Annual generation: {result_no_battery.annual_generation_kwh:.0f} kWh")
print(f"✅ Self-sufficiency achieved: {result_no_battery.self_sufficiency_pct:.1f}%")
print(f"   Self-consumption: {result_no_battery.self_consumption_pct:.1f}%")
print(f"   Grid import: {result_no_battery.annual_grid_import_kwh:.0f} kWh")
print(f"   Grid export: {result_no_battery.annual_grid_export_kwh:.0f} kWh")
print(f"\n⚠️  Problem: Only {result_no_battery.self_sufficiency_pct:.1f}% achieved due to timing mismatch!")

# 4.  Test PV WITH battery (10 kWh)
print("\n" + "=" * 60)
print("SCENARIO 2: PV + 10 kWh Battery")
print("=" * 60)

battery_10kwh = BatteryConfig(
    capacity_kwh=10.0,
    power_kw=5.0,
    efficiency=0.95
)

sizer_with_battery = PVSystemSizer(data, location, roof, battery_config=battery_10kwh)
result_with_battery = sizer_with_battery.size_for_self_sufficiency(target_percent=80)

print(f"\nTarget: 80% self-sufficiency")
print(f"System size: {result_with_battery.recommended_kwp} kWp")
print(f"Battery: {result_with_battery.battery_capacity_kwh} kWh @ {battery_10kwh.power_kw} kW")
print(f"Annual generation: {result_with_battery.annual_generation_kwh:.0f} kWh")
print(f"✅ Self-sufficiency achieved: {result_with_battery.self_sufficiency_pct:.1f}%")
print(f"   Self-consumption: {result_with_battery.self_consumption_pct:.1f}%")
print(f"   Grid import: {result_with_battery.annual_grid_import_kwh:.0f} kWh")
print(f"   Grid export: {result_with_battery.annual_grid_export_kwh:.0f} kWh")
print(f"\nBattery metrics:")
print(f"   Annual charge: {result_with_battery.battery_charge_kwh:.0f} kWh")
print(f"   Annual discharge: {result_with_battery.battery_discharge_kwh:.0f} kWh")
print(f"   Cycles/year: {result_with_battery.battery_cycles:.1f}")

# 5. Comparison
print("\n" + "=" * 60)
print("COMPARISON: Impact of Battery Storage")
print("=" * 60)

improvement_ss = result_with_battery.self_sufficiency_pct - result_no_battery.self_sufficiency_pct
improvement_grid = result_no_battery.annual_grid_import_kwh - result_with_battery.annual_grid_import_kwh

print(f"\n{'Metric':<30} {'PV Only':<15} {'PV + Battery':<15} {'Improvement':<15}")
print("-" * 80)
print(f"{'Self-Sufficiency':<30} {result_no_battery.self_sufficiency_pct:>10.1f}%  {result_with_battery.self_sufficiency_pct:>10.1f}%  {improvement_ss:>+10.1f}%")
print(f"{'Self-Consumption':<30} {result_no_battery.self_consumption_pct:>10.1f}%  {result_with_battery.self_consumption_pct:>10.1f}%  {result_with_battery.self_consumption_pct - result_no_battery.self_consumption_pct:>+10.1f}%")
print(f"{'Grid Import (kWh/year)':<30} {result_no_battery.annual_grid_import_kwh:>10.0f}  {result_with_battery.annual_grid_import_kwh:>10.0f}  {improvement_grid:>+10.0f}")
print(f"{'Grid Export (kWh/year)':<30} {result_no_battery.annual_grid_export_kwh:>10.0f}  {result_with_battery.annual_grid_export_kwh:>10.0f}  {result_with_battery.annual_grid_export_kwh - result_no_battery.annual_grid_export_kwh:>+10.0f}")

# 6. Test different battery sizes
print("\n" + "=" * 60)
print("SCENARIO 3: Battery Size Optimization")
print("=" * 60)

battery_sizes = [0, 5, 10, 15, 20]
print(f"\n{'Battery (kWh)':<15} {'PV (kWp)':<12} {'Self-Suff %':<15} {'Grid Import':<12} {'Cycles/yr'}")
print("-" * 70)

for bat_size in battery_sizes:
    if bat_size == 0:
        sizer_test = PVSystemSizer(data, location, roof)
    else:
        bat_config = BatteryConfig(capacity_kwh=bat_size, power_kw=min(bat_size/2, 5.0))
        sizer_test = PVSystemSizer(data, location, roof, battery_config=bat_config)
    
    result_test = sizer_test.size_for_self_sufficiency(target_percent=80)
    cycles = result_test.battery_cycles if result_test.battery_cycles else 0
    
    print(f"{bat_size:<15} {result_test.recommended_kwp:<12} {result_test.self_sufficiency_pct:<15.1f} {result_test.annual_grid_import_kwh:<12.0f} {cycles:<10.1f}")

print("\n💡 Key Insight: Battery enables significantly higher self-sufficiency!")
print("   - Without battery: Limited by timing mismatch")
print("   - With 10 kWh battery: Realistic 70-80%+ achievement")

# 7. Smart battery optimization
print("\n" + "=" * 60)
print("SCENARIO 4: Smart Battery Optimization")
print("=" * 60)

optimal = sizer_with_battery.optimize_battery_size(
    pv_kwp=result_with_battery.recommended_kwp,
    target_self_sufficiency=80.0
)

print(f"\n✅ Optimization complete!")
print(f"   Optimal battery size: {optimal['optimal_kwh']} kWh")
print(f"   Self-sufficiency achieved: {optimal['achieved_ss']:.1f}%")
print(f"\nSweep results:")
print(optimal['sweep_results'].to_string(index=False))

# 8. Visualize battery SOC
print("\n" + "=" * 60)
print("Generating Battery SOC Visualization")
print("=" * 60)

output_dir = Path(__file__).parent / "outputs" / "11-pv-battery"
output_dir.mkdir(parents=True, exist_ok=True)

soc_plot_path = output_dir / "battery_soc_profile.png"
result_with_battery.plot_battery_soc(output_path=str(soc_plot_path), days_to_show=7)
print(f"Battery SOC plot saved to: {soc_plot_path}")
