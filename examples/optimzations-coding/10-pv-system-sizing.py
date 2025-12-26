"""
Example 10: PV System Sizing with OOP API
==========================================
Demonstrates the new PVSystemSizer class for sizing solar systems
based on consumption data and self-sufficiency targets.
"""

import os
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from eclipse.consumption import ConsumptionData
from eclipse.pvsim import PVSystemSizer, LocationConfig, RoofConfig

print("=== PV System Sizing Example ===\n")

# 1. Load consumption data
DATA_FILE = Path(__file__).parent.parent / "data" / "consumption" / "20251212_consumption-frq-60min-leap-yr.csv"
print(f"1. Loading consumption data: {DATA_FILE.name}")
data = ConsumptionData.load(str(DATA_FILE))
print(f"   {data}\n")

# 2. Configure location (Zurich, Switzerland)
location = LocationConfig(
    latitude=47.38,
    longitude=8.54,
    altitude=400,
    timezone='Europe/Zurich'
)
print(f"2. Location: Zurich ({location.latitude}, {location.longitude})\n")

# 3. Configure roof
roof = RoofConfig(
    tilt=30,  # 30° tilt (typical for Swiss roofs)
    azimuth=180,  # South-facing
    max_area_m2=50,  # 50 m² available
    module_efficiency=0.20,  # 20% efficient modules
    performance_ratio=0.75  # 75% performance ratio
)
print(f"3. Roof configuration:")
print(f"   Tilt: {roof.tilt}°, Azimuth: {roof.azimuth}° (South)")
print(f"   Max area: {roof.max_area_m2} m²")
print(f"   Max capacity: {roof.max_capacity_kwp} kWp\n")

# 4. Create sizer
print("4. Initializing PV system sizer...")
sizer = PVSystemSizer(
    consumption_data=data,
    location=location,
    roof=roof
)
print(f"   {sizer}\n")

# 5. Size for different self-sufficiency targets
print("5. Sizing for different SELF-SUFFICIENCY targets:\n")

targets = [50, 75, 80, 100]
for target in targets:
    print(f"   Target: {target}% self-sufficiency")
    result = sizer.size_for_self_sufficiency(target_percent=target)
    print(f"   → System size: {result.recommended_kwp} kWp")
    print(f"   → Annual generation: {result.annual_generation_kwh:.0f} kWh")
    print(f"   → Self-sufficiency achieved: {result.self_sufficiency_pct:.1f}%")
    print(f"   → Self-consumption: {result.self_consumption_pct:.1f}%")
    if result.constrained_by_roof:
        print(f"   ⚠️  Limited by roof area!")
    print()

# 5b. Size for different self-consumption targets
print("5b. Sizing for different SELF-CONSUMPTION targets:\n")

sc_targets = [60, 70, 80]
for target in sc_targets:
    print(f"   Target: {target}% self-consumption")
    result = sizer.size_for_self_consumption(target_percent=target)
    print(f"   → System size: {result.recommended_kwp} kWp")
    print(f"   → Annual generation: {result.annual_generation_kwh:.0f} kWh")
    print(f"   → Self-consumption achieved: {result.self_consumption_pct:.1f}%")
    print(f"   → Self-sufficiency: {result.self_sufficiency_pct:.1f}%")
    print()

# 5c. Using generic optimize() method
print("5c. Using generic optimize() method:\n")
result_opt = sizer.optimize(target_metric='self_consumption', target_percent=75)
print(f"   Optimized for 75% self-consumption:")
print(f"   → {result_opt.recommended_kwp} kWp system")
print(f"   → Self-consumption: {result_opt.self_consumption_pct:.1f}%")
print(f"   → Self-sufficiency: {result_opt.self_sufficiency_pct:.1f}%")
print()

# 6. Detailed analysis for 80% target
print("6. Detailed analysis for 80% self-sufficiency:\n")
result_80 = sizer.size_for_self_sufficiency(target_percent=80)
print(result_80)
print()

# 7. Monthly breakdown
print("7. Monthly energy flow (first 6 months):")
print(result_80.monthly_profile.head(6).to_string())
print()

# 8. Export monthly profile
output_dir = Path(__file__).parent / "outputs" / "10-pv-sizing"
output_dir.mkdir(parents=True, exist_ok=True)
csv_path = output_dir / "monthly_energy_flow.csv"
result_80.monthly_profile.to_csv(csv_path)
print(f"8. Monthly profile saved to: {csv_path}")

# 9. Plot monthly comparison
print("\n9. Generating monthly comparison plot...")
plot_path = output_dir / "monthly_pv_vs_consumption.png"
result_80.plot_monthly_comparison(output_path=str(plot_path), show_self_consumed=True)
print(f"   Plot saved to: {plot_path}")

# 9b. Plot seasonal daily PV production
print("\n9b. Generating seasonal daily PV production plot...")
seasonal_plot_path = output_dir / "seasonal_daily_pv_production.png"
result_80.plot_seasonal_daily_production(output_path=str(seasonal_plot_path))
print(f"   Plot saved to: {seasonal_plot_path}")

# 10. Summary
print("\n=== Summary ===")
print(f"Annual consumption: {result_80.annual_consumption_kwh:.0f} kWh")
print(f"Recommended system: {result_80.recommended_kwp} kWp")
print(f"Annual PV generation: {result_80.annual_generation_kwh:.0f} kWh")
print(f"Self-sufficiency: {result_80.self_sufficiency_pct:.1f}%")
print(f"Grid independence: {100 - (result_80.annual_grid_import_kwh / result_80.annual_consumption_kwh * 100):.1f}%")
print(f"Grid import reduced by: {result_80.annual_self_consumed_kwh:.0f} kWh/year")
