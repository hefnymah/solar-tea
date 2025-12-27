"""
Example 06: Integrated Solar + Battery System Sizing + Economic
=====================================================
End-to-end sizing workflow combining PV and battery sizing, with economic analysis.

Flow:
1. Define configurations (location, roof, battery)
2. Create sizer with all configs
3. Simulate with sizing mode ('max_roof' or 'match_load')
4. Battery is auto-sized internally using BatterySizer
5. Economic analysis is performed using the SimulationEngine
5.1 Estimating the Pronovo financials

Author: Eclipse Framework
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
from eclipse.simulation import (
    PVSystemSizer,
    LocationConfig,
    RoofConfig,
    BatteryConfig
)
from eclipse.simulation.simulation_engine import SimulationEngine

from eclipse.economics.subsidies.pronovo import calculate_subsidy
from eclipse.economics.enums import SystemCategory

# === Data Source ===
CONSUMPTION_FILE = project_root / "data" / "consumption" / "20251212_consumption-frq-15min-leap-yr.csv"

# ==========================================
# 1. DEFINE CONFIGURATIONS
# ==========================================
print("=" * 70)
print("INTEGRATED SOLAR + BATTERY SYSTEM SIZING")
print("=" * 70)

# Location configuration
# Altitude is optional - will be auto-detected from PVGIS
location = LocationConfig(
    latitude=46.8027,
    longitude=9.8360,
    altitude=None, # Auto-detect
    timezone='Europe/Zurich'
)

# Roof configuration
roof = RoofConfig(
    tilt=76,
    azimuth=180,  # Due South
    max_area_m2=50,
    module_efficiency=0.20,
    performance_ratio=0.75
)

# Battery configuration (auto-sizing enabled by default)
battery = BatteryConfig(
    max_soc=90,
    min_soc=10,
    simulator='simple',        # 'simple' (fast) or 'pysam' (accurate)
    sizing_target='optimal'    # 'optimal', 'autonomy', 'self_sufficiency'
)

print(f"\n Location: {location.latitude}°N, {location.longitude}°E")
print(f" Roof: {roof.max_area_m2} m² @ {roof.tilt}° tilt")
print(f" Battery: Auto-size with '{battery.sizing_target}' target")

# ==========================================
# 2. LOAD CONSUMPTION DATA
# ==========================================
print(f"\n>>> Loading consumption data: {CONSUMPTION_FILE.name}")
data = ConsumptionData.load(str(CONSUMPTION_FILE))
print(f"    {data}")

# ==========================================
# 3. CREATE SIZER AND RUN SIMULATION
# ==========================================
print("\n" + "=" * 70)
print("RUNNING SIMULATION")
print("=" * 70)

# Create sizer with all configurations
sizer = PVSystemSizer(
    consumption_data=data,
    location=location,
    roof=roof,
    battery=battery  # Battery sizing happens automatically!
)

# Run simulation with PV sizing mode
# Options: 'max_roof', 'match_load', or explicit kWp value
print(f"\n Sizing PV to fill roof ({roof.max_area_m2} m²)...")
result = sizer.simulate(pv_sizing='max_roof')

# ==========================================
# 4. ECONOMICS (PRONOVO SUBSIDY)
# ==========================================
print("\n" + "=" * 70)
print("FINANCIAL ESTIMATION (SUBSIDY)")
print("=" * 70)

print(f"Detected Altitude: {result.altitude:.1f} m")

# Calculate subsidy using simulation results
# Assuming standard attached roof for this example
subsidy = calculate_subsidy(
    capacity_kwp=result.recommended_kwp,
    category=SystemCategory.ATTACHED_ROOF,
    has_self_consumption=True,  # Standard EIV
    altitude_meters=result.altitude,
    tilt_angle_degrees=roof.tilt,
    parking_area_coverage=True
)

# ==========================================
# 5. RESULTS
# ==========================================
print("\n" + "=" * 70)
print("SYSTEM SIZING RESULTS")
print("=" * 70)

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
{row("PV System:", f"{result.recommended_kwp:>.2f}", "kWp")}
{row("Battery:", f"{result.battery_capacity_kwh or 0:>.1f}", "kWh (auto-sized)")}
├─────────────────────────────────────────────────────────────────────┤
│  ANNUAL PERFORMANCE                                                 │
├─────────────────────────────────────────────────────────────────────┤
{row("Self-Sufficiency:", f"{result.self_sufficiency_pct:>.1f}", "%")}
{row("Self-Consumption:", f"{result.self_consumption_pct:>.1f}", "%")}
{row("Grid Import:", f"{result.annual_grid_import_kwh:>.0f}", "kWh/year")}
{row("Grid Export:", f"{result.annual_grid_export_kwh:>.0f}", "kWh/year")}
├─────────────────────────────────────────────────────────────────────┤
│  ESTIMATED SUBSIDY (PRONOVO 2025)                                   │
├─────────────────────────────────────────────────────────────────────┤
{row("Base Subsidy:", f"{subsidy.base_contribution:>,.0f}", "CHF")}
{row("Tilt Angle Bonus:", f"{subsidy.tilt_bonus:>,.0f}", "CHF")}
{row("Height Bonus:", f"{subsidy.altitude_bonus:>,.0f}", "CHF")}
{row("Parking Bonus:", f"{subsidy.parking_bonus:>,.0f}", "CHF")}
{row("TOTAL FUNDING:", f"{subsidy.total:>,.0f}", "CHF")}
└─────────────────────────────────────────────────────────────────────┘
""")


