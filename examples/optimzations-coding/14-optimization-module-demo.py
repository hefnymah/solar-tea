"""
Example 14: Using the New Optimization Module
==============================================
Demonstrates the OOP optimization architecture with pluggable optimizers.

This example shows:
1. Using SweepOptimizer with physics-based constraints
2. Using objective functions from the optimization module
3. How the new architecture separates physics from optimization
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from eclipse.consumption import ConsumptionData
from eclipse.simulation import PVSystemSizer, LocationConfig, RoofConfig, BatteryConfig
from eclipse.optimization import (
    SweepOptimizer,
    OptimizationBounds,
    SelfSufficiencyObjective,
)

print("=" * 70)
print("Example 14: OOP Optimization Module Demo")
print("=" * 70)

# 1. Load consumption data
DATA_FILE = Path(__file__).parent.parent / "data" / "consumption" / "20251212_consumption-frq-60min-leap-yr.csv"
print(f"\n1. Loading data: {DATA_FILE.name}")
data = ConsumptionData.load(str(DATA_FILE))
print(f"   Annual consumption: {data.hourly.sum():.0f} kWh/year")

# 2. Configure system
location = LocationConfig(latitude=47.38, longitude=8.54)
roof = RoofConfig(tilt=30, azimuth=180, max_area_m2=50)

print(f"\n2. System Configuration")
print(f"   Roof: {roof.max_area_m2} m² → max {roof.max_capacity_kwp} kWp")

# 3. Create simulator (physics layer)
simulator = PVSystemSizer(data, location, roof)
print(f"\n3. Physics Simulator Created")
print(f"   Specific yield: {simulator.simulation.specific_yield:.0f} kWh/kWp/year")

# 4. Define objective function
print(f"\n4. Objective: Maximize Self-Sufficiency")

def self_sufficiency_objective(pv_kwp: float, battery_kwh: float) -> float:
    """Objective function for self-sufficiency (negative for minimization)."""
    result = simulator.simulate(pv_kwp, battery_kwh)
    return -result.self_sufficiency_pct  # Negative because we minimize

# 5. Set optimization bounds
bounds = OptimizationBounds(
    pv_min_kwp=1.0,
    pv_max_kwp=roof.max_capacity_kwp,
    battery_min_kwh=0.0,
    battery_max_kwh=20.0,
    pv_step_kwp=1.0,  # Coarse grid for demo speed
    battery_step_kwh=5.0
)
print(f"\n5. Optimization Bounds")
print(f"   PV: {bounds.pv_min_kwp} - {bounds.pv_max_kwp} kWp")
print(f"   Battery: {bounds.battery_min_kwh} - {bounds.battery_max_kwh} kWh")

# 6. Create optimizer (Strategy pattern - can swap algorithms here)
optimizer = SweepOptimizer(
    max_storage_days=2.0,
    priority='performance'
)
print(f"\n6. Optimizer: {optimizer.name}")

# 7. Run optimization
print(f"\n7. Running Optimization...")
result = optimizer.optimize(
    objective=self_sufficiency_objective,
    bounds=bounds,
    target_value=-80.0,  # Negative because we minimize (want 80% SS)
    verbose=True
)

# 8. Display results
print(f"\n" + "=" * 70)
print("OPTIMIZATION RESULT")
print("=" * 70)
print(result)

print(f"\n📊 Key Metrics:")
print(f"   Optimal PV: {result.optimal_pv_kwp} kWp")
print(f"   Optimal Battery: {result.optimal_battery_kwh} kWh")
print(f"   Self-Sufficiency: {-result.objective_value:.1f}%")
print(f"   Iterations: {result.iterations}")

# 9. Get full result for optimal configuration
print(f"\n9. Full Simulation for Optimal Config:")
final_result = simulator.simulate(result.optimal_pv_kwp, result.optimal_battery_kwh)
print(f"   Annual Generation: {final_result.annual_generation_kwh:.0f} kWh")
print(f"   Self-Sufficiency: {final_result.self_sufficiency_pct:.1f}%")
print(f"   Self-Consumption: {final_result.self_consumption_pct:.1f}%")
print(f"   Grid Import: {final_result.annual_grid_import_kwh:.0f} kWh/year")

print(f"\n" + "=" * 70)
print("✅ OOP Optimization Module Demo Complete!")
print("=" * 70)
print(f"\n💡 Benefits of this architecture:")
print(f"   - Optimizer is independent of physics")
print(f"   - Can swap SweepOptimizer for JAYA, NSGA-II, MILP...")
print(f"   - Objective functions are reusable")
print(f"   - Follows Strategy pattern (SOLID principles)")
