"""
Example 05: Integrated Solar + Battery System Sizing
=====================================================
End-to-end sizing workflow combining PV and battery optimization.

Flow:
1. Define configurations (location, roof, battery)
2. Create sizer with all configs
3. Simulate with sizing mode ('max_roof' or 'match_load')
4. Battery is auto-sized internally using BatterySizer

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
from eclipse.pvsim import (
    PVSystemSizer, LocationConfig, RoofConfig, BatteryConfig
)

# ==========================================
# CONFIGURATION
# ==========================================
output_dir = project_root / "examples" / "outputs" / "example-05-system-sizing"
os.makedirs(output_dir, exist_ok=True)

# === Data Source ===
CONSUMPTION_FILE = project_root / "data" / "consumption" / "20251212_consumption-frq-15min-leap-yr.csv"

# ==========================================
# 1. DEFINE CONFIGURATIONS
# ==========================================
print("=" * 70)
print("INTEGRATED SOLAR + BATTERY SYSTEM SIZING")
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
print(f"\n🔬 Sizing PV to fill roof ({roof.max_area_m2} m²)...")
result = sizer.simulate(pv_sizing='max_roof')

# ==========================================
# 4. RESULTS
# ==========================================
print("\n" + "=" * 70)
print("SYSTEM SIZING RESULTS")
print("=" * 70)

print(f"""
┌─────────────────────────────────────────────────────────────────────┐
│  RECOMMENDED SYSTEM                                                 │
├─────────────────────────────────────────────────────────────────────┤
│  PV System:        {result.recommended_kwp:>8.2f} kWp                                  │
│  Battery:          {result.battery_capacity_kwh or 0:>8.1f} kWh (auto-sized)                       │
├─────────────────────────────────────────────────────────────────────┤
│  ANNUAL PERFORMANCE                                                 │
├─────────────────────────────────────────────────────────────────────┤
│  Self-Sufficiency: {result.self_sufficiency_pct:>8.1f}%                                   │
│  Self-Consumption: {result.self_consumption_pct:>8.1f}%                                   │
│  Grid Import:      {result.annual_grid_import_kwh:>8.0f} kWh/year                              │
│  Grid Export:      {result.annual_grid_export_kwh:>8.0f} kWh/year                              │
└─────────────────────────────────────────────────────────────────────┘
""")

# ==========================================
# 5. ALTERNATIVE: PV-ONLY (NO BATTERY)
# ==========================================
print("\n>>> For comparison: PV-only system (no battery)...")

sizer_pv_only = PVSystemSizer(data, location, roof)  # No battery parameter
result_pv_only = sizer_pv_only.simulate(pv_sizing='max_roof')

print(f"    PV-only Self-Sufficiency: {result_pv_only.self_sufficiency_pct:.1f}%")
print(f"    With Battery:             {result.self_sufficiency_pct:.1f}%")
print(f"    Improvement:              +{result.self_sufficiency_pct - result_pv_only.self_sufficiency_pct:.1f}%")

# ==========================================
# 5b. EXPORT RESULTS TO FILES
# ==========================================
import json

# Create comprehensive results dictionary
results_dict = {
    "system_configuration": {
        "location": {
            "latitude": location.latitude,
            "longitude": location.longitude,
            "altitude": location.altitude,
            "timezone": location.timezone
        },
        "roof": {
            "tilt_deg": roof.tilt,
            "azimuth_deg": roof.azimuth,
            "area_m2": roof.max_area_m2,
            "module_efficiency": roof.module_efficiency,
            "performance_ratio": roof.performance_ratio
        },
        "battery": {
            "auto_sized": True,
            "sizing_target": battery.sizing_target,
            "min_soc_pct": battery.min_soc,
            "max_soc_pct": battery.max_soc,
            "simulator": battery.simulator
        }
    },
    "sizing_results": {
        "pv_kwp": result.recommended_kwp,
        "battery_kwh": result.battery_capacity_kwh,
        "pv_sizing_mode": "max_roof"
    },
    "annual_performance": {
        "self_sufficiency_pct": round(result.self_sufficiency_pct, 2),
        "self_consumption_pct": round(result.self_consumption_pct, 2),
        "grid_import_kwh": round(result.annual_grid_import_kwh, 1),
        "grid_export_kwh": round(result.annual_grid_export_kwh, 1),
        "annual_consumption_kwh": round(result.annual_consumption_kwh, 1),
        "annual_pv_generation_kwh": round(result.annual_generation_kwh, 1),
        "annual_self_consumed_kwh": round(result.annual_self_consumed_kwh, 1)
    },
    "comparison": {
        "pv_only_self_sufficiency_pct": round(result_pv_only.self_sufficiency_pct, 2),
        "battery_improvement_pct": round(result.self_sufficiency_pct - result_pv_only.self_sufficiency_pct, 2)
    }
}

# Save to JSON
json_path = output_dir / "sizing_results.json"
with open(json_path, 'w') as f:
    json.dump(results_dict, f, indent=2)
print(f"\n>>> Exported results to: {json_path.name}")

# ==========================================
# 6. VISUALIZATIONS
# ==========================================
print("\n" + "=" * 70)
print("GENERATING VISUALIZATIONS")
print("=" * 70)

from eclipse.pvsim import PVSystemAnalyzer
from eclipse.plotting import PVSystemBehaviorPlotter, BatteryPlotter

# --- PV System Analysis ---
print("\n>>> Analyzing PV system behavior...")
analyzer = PVSystemAnalyzer(result)

# Analyze different periods
summer_data = analyzer.analyze_period('2024-06-15', '2024-06-21')
winter_data = analyzer.analyze_period('2024-01-15', '2024-01-21')
spring_data = analyzer.analyze_period('2024-03-15', '2024-03-21')
june_data = analyzer.analyze_period('2024-06-01', '2024-06-30')

# Plot seasonal weeks
print("\n>>> Generating seasonal PV behavior plots...")
PVSystemBehaviorPlotter.plot(
    summer_data,
    title='Summer Week (June)',
    output_path=f"{output_dir}/summer_week.png"
)
print(f"    Saved: summer_week.png")

PVSystemBehaviorPlotter.plot(
    winter_data,
    title='Winter Week (January)',
    output_path=f"{output_dir}/winter_week.png"
)
print(f"    Saved: winter_week.png")

PVSystemBehaviorPlotter.plot(
    spring_data,
    title='Spring Week (March)',
    output_path=f"{output_dir}/spring_week.png"
)
print(f"    Saved: spring_week.png")

PVSystemBehaviorPlotter.plot(
    june_data,
    title='June Month',
    output_path=f"{output_dir}/june_month.png"
)
print(f"    Saved: june_month.png")

# --- Additional comprehensive annual plots ---
print("\n>>> Generating comprehensive annual plots...")

# Monthly energy flows
monthly_flows = analyzer.get_monthly_energy_flows()
PVSystemBehaviorPlotter.plot_monthly_energy_flows(
    monthly_flows,
    result,
    output_path=f"{output_dir}/monthly_energy_flows.png"
)
print(f"    Saved: monthly_energy_flows.png")

# Seasonal daily profiles
seasonal_profiles = analyzer.get_seasonal_daily_profiles()
PVSystemBehaviorPlotter.plot_seasonal_daily_profiles(
    seasonal_profiles,
    result,
    output_path=f"{output_dir}/seasonal_daily_profiles.png"
)
print(f"    Saved: seasonal_daily_profiles.png")

# --- Battery Operation Plots (if battery was sized) ---
if result.battery_capacity_kwh and result.battery_capacity_kwh > 0:
    print("\n>>> Generating battery operation plots...")
    
    # Run a dedicated battery simulation for visualization
    from eclipse.battery import SimpleBatterySimulator
    from eclipse.config.equipment_models import MockBattery
    
    mock_battery = MockBattery(
        nominal_energy_kwh=result.battery_capacity_kwh,
        max_charge_power_kw=result.battery_capacity_kwh * 0.5,
        max_discharge_power_kw=result.battery_capacity_kwh * 0.5,
        min_soc=battery.min_soc,
        max_soc=battery.max_soc
    )
    
    # Get hourly data for battery simulation
    pv_kwp = result.recommended_kwp
    hourly_pv = sizer.simulation.scale_to_capacity(pv_kwp)
    hourly_load = data.hourly.series
    
    sim = SimpleBatterySimulator(mock_battery)
    battery_results = sim.simulate(hourly_load, hourly_pv, system_kwh=result.battery_capacity_kwh)
    battery_results.index = hourly_load.index
    
    # Create battery plotter
    plotter = BatteryPlotter()
    
    # Plot representative periods
    periods = [
        ('2024-06-15', '2024-06-16', 'battery_summer_day.png', 'Summer Day Battery Operation'),
        ('2024-03-15', '2024-03-19', 'battery_spring_week.png', 'Spring Week Battery Operation'),
    ]
    
    for start, end, filename, title in periods:
        try:
            plot_df = battery_results.loc[start:end]
            if len(plot_df) > 0:
                plot_path = output_dir / filename
                plotter.plot_operation(
                    plot_df,
                    plot_path,
                    title=f"{title} ({result.battery_capacity_kwh:.0f} kWh)"
                )
                print(f"    Saved: {filename}")
        except Exception as e:
            print(f"    Could not plot {title}: {e}")

print("\n" + "=" * 70)
print("System sizing complete!")
print(f"Output directory: {output_dir}")
print("=" * 70)

