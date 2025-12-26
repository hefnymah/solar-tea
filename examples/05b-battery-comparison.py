"""
Example 05a: PV + Battery System Comparison
============================================
Compares system performance with and without battery storage
using a fixed PV system size (manual kWp input).

This example demonstrates:
1. Explicit PV sizing (10 kWp instead of 'max_roof')
2. Side-by-side comparison: PV-only vs PV+Battery
3. Quantifying the battery value-add

Author: Eclipse Framework
"""

import sys
import os
import json
from pathlib import Path

# Handle both script and interactive execution
try:
    project_root = Path(__file__).parent.parent
except NameError:
    project_root = Path.cwd()
sys.path.insert(0, str(project_root))

from eclipse.consumption import ConsumptionData
from eclipse.pvsim import (
    PVSystemSizer, LocationConfig, RoofConfig, BatteryConfig
)

# ==========================================
# CONFIGURATION
# ==========================================
output_dir = project_root / "examples" / "outputs" / "example-05a-comparison"
os.makedirs(output_dir, exist_ok=True)

# === System Parameters ===
PV_SIZE_KWP = 10.0  # Fixed PV system size

# === Data Source ===
CONSUMPTION_FILE = project_root / "data" / "consumption" / "20251212_consumption-frq-15min-leap-yr.csv"

# ==========================================
# 1. DEFINE CONFIGURATIONS
# ==========================================
print("=" * 70)
print("PV + BATTERY SYSTEM COMPARISON")
print("=" * 70)

# Location configuration
location = LocationConfig(
    latitude=47.38,
    longitude=8.54,
    altitude=400,
    timezone='Europe/Zurich'
)

# Roof configuration
roof = RoofConfig(
    tilt=30,
    azimuth=180,
    max_area_m2=100,  # Large enough for any system
    module_efficiency=0.20,
    performance_ratio=0.75
)

# Battery configuration (for auto-sizing)
battery = BatteryConfig(
    max_soc=90,
    min_soc=10,
    simulator='simple',
    sizing_target='optimal'
)

print(f"\n Location: {location.latitude}°N, {location.longitude}°E")
print(f" Fixed PV Size: {PV_SIZE_KWP} kWp")
print(f" Battery: Auto-size with '{battery.sizing_target}' target")

# ==========================================
# 2. LOAD CONSUMPTION DATA
# ==========================================
print(f"\n>>> Loading consumption data: {CONSUMPTION_FILE.name}")
data = ConsumptionData.load(str(CONSUMPTION_FILE))
print(f"    {data}")

# ==========================================
# 3. SIMULATE: PV-ONLY SYSTEM
# ==========================================
print("\n" + "=" * 70)
print("SCENARIO 1: PV-ONLY SYSTEM")
print("=" * 70)

sizer_pv_only = PVSystemSizer(data, location, roof)  # No battery

# Use explicit kWp value instead of 'max_roof'
print(f"\n Simulating {PV_SIZE_KWP} kWp PV system (no battery)...")
result_pv_only = sizer_pv_only.simulate(pv_sizing=PV_SIZE_KWP)

print(f"""
    PV System:        {result_pv_only.recommended_kwp:.2f} kWp
    Self-Sufficiency: {result_pv_only.self_sufficiency_pct:.1f}%
    Self-Consumption: {result_pv_only.self_consumption_pct:.1f}%
    Grid Import:      {result_pv_only.annual_grid_import_kwh:.0f} kWh/year
    Grid Export:      {result_pv_only.annual_grid_export_kwh:.0f} kWh/year
""")

# ==========================================
# 4. SIMULATE: PV + BATTERY SYSTEM
# ==========================================
print("=" * 70)
print("SCENARIO 2: PV + BATTERY SYSTEM")
print("=" * 70)

sizer_with_battery = PVSystemSizer(data, location, roof, battery=battery)

# Use the same explicit kWp value
print(f"\n🔬 Simulating {PV_SIZE_KWP} kWp PV system + auto-sized battery...")
result_with_battery = sizer_with_battery.simulate(pv_sizing=PV_SIZE_KWP)

print(f"""
    PV System:        {result_with_battery.recommended_kwp:.2f} kWp
    Battery:          {result_with_battery.battery_capacity_kwh:.1f} kWh (auto-sized)
    Self-Sufficiency: {result_with_battery.self_sufficiency_pct:.1f}%
    Self-Consumption: {result_with_battery.self_consumption_pct:.1f}%
    Grid Import:      {result_with_battery.annual_grid_import_kwh:.0f} kWh/year
    Grid Export:      {result_with_battery.annual_grid_export_kwh:.0f} kWh/year
""")

# ==========================================
# 5. COMPARISON SUMMARY
# ==========================================
print("=" * 70)
print("COMPARISON SUMMARY")
print("=" * 70)

ss_improvement = result_with_battery.self_sufficiency_pct - result_pv_only.self_sufficiency_pct
sc_improvement = result_with_battery.self_consumption_pct - result_pv_only.self_consumption_pct
import_reduction = result_pv_only.annual_grid_import_kwh - result_with_battery.annual_grid_import_kwh
export_reduction = result_pv_only.annual_grid_export_kwh - result_with_battery.annual_grid_export_kwh

print(f"""
┌──────────────────────────────────────────────────────────────────────────┐
│  METRIC                          │  PV-ONLY   │  PV+BATTERY  │  DELTA    │
├──────────────────────────────────┼────────────┼──────────────┼───────────┤
│  Self-Sufficiency                │  {result_pv_only.self_sufficiency_pct:>6.1f}%   │    {result_with_battery.self_sufficiency_pct:>6.1f}%   │  +{ss_improvement:>5.1f}%   │
│  Self-Consumption                │  {result_pv_only.self_consumption_pct:>6.1f}%   │    {result_with_battery.self_consumption_pct:>6.1f}%   │  +{sc_improvement:>5.1f}%   │
│  Grid Import (kWh/yr)            │  {result_pv_only.annual_grid_import_kwh:>7.0f}   │    {result_with_battery.annual_grid_import_kwh:>7.0f}   │  -{import_reduction:>5.0f}    │
│  Grid Export (kWh/yr)            │  {result_pv_only.annual_grid_export_kwh:>7.0f}   │    {result_with_battery.annual_grid_export_kwh:>7.0f}   │  -{export_reduction:>5.0f}    │
├──────────────────────────────────┴────────────┴──────────────┴───────────┤
│  Battery Size:  {result_with_battery.battery_capacity_kwh:>5.1f} kWh                                                │
│  Battery adds:  +{ss_improvement:.1f}% self-sufficiency                                     │
└──────────────────────────────────────────────────────────────────────────┘
""")

# ==========================================
# 6. EXPORT RESULTS
# ==========================================
comparison_results = {
    "pv_size_kwp": PV_SIZE_KWP,
    "battery_kwh": result_with_battery.battery_capacity_kwh,
    "pv_only": {
        "self_sufficiency_pct": round(result_pv_only.self_sufficiency_pct, 2),
        "self_consumption_pct": round(result_pv_only.self_consumption_pct, 2),
        "grid_import_kwh": round(result_pv_only.annual_grid_import_kwh, 1),
        "grid_export_kwh": round(result_pv_only.annual_grid_export_kwh, 1)
    },
    "pv_plus_battery": {
        "self_sufficiency_pct": round(result_with_battery.self_sufficiency_pct, 2),
        "self_consumption_pct": round(result_with_battery.self_consumption_pct, 2),
        "grid_import_kwh": round(result_with_battery.annual_grid_import_kwh, 1),
        "grid_export_kwh": round(result_with_battery.annual_grid_export_kwh, 1)
    },
    "battery_improvement": {
        "self_sufficiency_delta_pct": round(ss_improvement, 2),
        "self_consumption_delta_pct": round(sc_improvement, 2),
        "grid_import_reduction_kwh": round(import_reduction, 1),
        "grid_export_reduction_kwh": round(export_reduction, 1)
    }
}

json_path = output_dir / "comparison_results.json"
with open(json_path, 'w') as f:
    json.dump(comparison_results, f, indent=2)
print(f"\n>>> Exported results to: {json_path}")

print("\n" + "=" * 70)
print("Comparison complete!")
print("=" * 70)
