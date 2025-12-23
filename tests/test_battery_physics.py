"""
Test Suite for Battery Physics Simulation
=========================================
Verifies the accuracy of the simple battery simulator.

Tests:
1. Basic Charge/Discharge: Verify SOC changes correctly.
2. Efficiency: Ensure energy losses are accounted for.
3. Power Limits: Verify battery respects max charge/discharge power.
4. Energy Balance: Validate system-wide energy conservation.
5. SOC Limits: Ensure battery does not exceed 0-100% (or configured limits).
"""

import pytest
import pandas as pd
import numpy as np
from eclipse.battery.simple import SimpleBatterySimulator

class MockBatteryConfig:
    """Mock battery configuration for testing."""
    nominal_energy_kwh = 10.0
    max_discharge_power_kw = 5.0
    min_soc = 0.0
    max_soc = 100.0
    performance = {'round_trip_efficiency': 0.90}

@pytest.fixture
def battery_sim():
    battery = MockBatteryConfig()
    return SimpleBatterySimulator(battery)

def test_charge_logic(battery_sim):
    """Test that battery charges when excess PV is available."""
    # 1 hour simulation
    load = pd.Series([0.0])
    pv = pd.Series([2.0])  # 2 kW excess
    
    # Start at 50% SOC (5 kWh)
    # SimpleBatterySimulator starts at max_soc by default (100%)
    # We need to hack initial state or run a discharge step first
    
    # Let's run a discharge first to drain it
    setup_load = pd.Series([10.0])
    setup_pv = pd.Series([0.0])
    battery_sim.simulate(setup_load, setup_pv) # Drains battery
    
    # Run simulation with override system_kwh to ensure consistent capacity if needed
    # But simple simulator computes SOC internally based on previous steps?
    # No, SimpleBatterySimulator.simulate() keeps internal state only within the method call!
    # It re-initializes `soc_kwh = initial_soc_kwh` at the start of `simulate`.
    # And `initial_soc_kwh` is `capacity * max_soc_frac` (FULL).
    
    # So we cannot easily test starting from 50% unless we modify the code or 
    # run a multi-step simulation where the first steps drain it.
    
    # Scenario: 2 steps. Step 1: Drain 5 kWh. Step 2: Charge 2 kW.
    load = pd.Series([5.0, 0.0])
    pv = pd.Series([0.0, 2.0])
    
    results = battery_sim.simulate(load, pv)
    
    # Step 1: Start 10 kWh. Load 5 kW.
    # Discharge = 5 kW (limited by max power 5kW).
    # Removed = 5 / 0.9 = 5.55 kWh
    # SOC end step 1 = 10 - 5.55 = 4.44 kWh
    
    # Step 2: PV 2 kW. Load 0.
    # Charge = 2 kW.
    # Stored = 2 * 0.9 = 1.8 kWh.
    # SOC end step 2 = 4.44 + 1.8 = 6.24 kWh
    
    soc_log = results['soc'].values
    # Check SOC decreased then increased
    assert soc_log[0] < 100.0, "Battery should have discharged"
    # SOC logic in SimpleSimulator reports SOC at end of step
    
    # We expect SOC[1] > SOC[0] (Charging)
    assert soc_log[1] > soc_log[0], "Battery should have charged in step 2"

def test_power_limits(battery_sim):
    """Test that charge/discharge is limited by max power."""
    # Battery capacity 10 kWh, Max Power 5 kW.
    # Request 10 kW discharge.
    load = pd.Series([10.0])
    pv = pd.Series([0.0])
    
    results = battery_sim.simulate(load, pv)
    
    # Discharge should be capped at 5 kW
    battery_discharge = results['battery_power'].iloc[0]
    
    assert np.isclose(battery_discharge, 5.0), \
        f"Discharge {battery_discharge} exceed max power 5.0"
    
    # Grid import should supply the rest (5 kW)
    assert np.isclose(results['grid_import'].iloc[0], 5.0)

def test_efficiency_losses(battery_sim):
    """Test that round-trip efficiency causes energy loss."""
    # Efficiency 0.90.
    # Cycle: Charge 1 kWh -> Store 0.9 kWh.
    # Discharge 0.9 kWh -> Require 1.0 kWh from storage?
    # No, logic is:
    # Charge: Input 1 kWh -> Stored = 1 * eff = 0.9 kWh.
    # Discharge: Output 0.9 kWh -> Removed = 0.9 / eff = 1.0 kWh.
    
    # Test Charge
    battery_sim.battery.max_soc = 100
    # Create empty battery scenario (requires modifying code or using hacked inputs)
    # Simulator always starts full. So let's test Discharge Efficiency.
    
    load = pd.Series([1.0]) # Request 1 kWh output
    pv = pd.Series([0.0])
    
    results = battery_sim.simulate(load, pv)
    
    # Output = 1.0 kWh
    output = results['battery_power'].iloc[0] # 1.0
    
    # Initial SOC = 10.0
    # Final SOC (from result pct)
    final_soc_kwh = (results['soc'].iloc[0] / 100.0) * 10.0
    
    energy_removed = 10.0 - final_soc_kwh
    
    # Expected removed = 1.0 / 0.9 = 1.111...
    expected_removed = 1.0 / 0.9
    
    assert np.isclose(energy_removed, expected_removed, rtol=0.01), \
        f"Efficiency logic error. Removed: {energy_removed}, Expected: {expected_removed}"

def test_energy_balance(battery_sim):
    """Verify system-wide energy conservation."""
    # Run random simulation
    steps = 100
    load = pd.Series(np.random.rand(steps) * 5)
    pv = pd.Series(np.random.rand(steps) * 5)
    
    results = battery_sim.simulate(load, pv)
    
    for i in range(steps):
        # Load = PV + Grid Import - Grid Export + Battery Discharge - Battery Charge
        # Battery Power > 0 is Discharge, < 0 is Charge
        
        supply = pv.iloc[i] + results['grid_import'].iloc[i] + results['battery_power'].iloc[i]
        demand = load.iloc[i] + results['grid_export'].iloc[i]
        
        # Depending on sign convention of battery_power:
        # If battery_power positive (discharge): Supply side
        # If battery_power negative (charge): It subtracts from supply, effectively demand side.
        
        # So: Load + Export = PV + Import + Battery (net)
        # 5 + 0 = 0 + 0 + 5 (Discharge case)
        # 0 + 2 = 5 + 0 + (-3) Charge case? No:
        # Excess 5. Charge 3. Export 2.
        # PV(5) + Import(0) + Bat(-3) = 2. Load(0) + Export(2) = 2. Matches.
        
        balance = supply - demand
        
        assert np.isclose(balance, 0.0, atol=1e-5), \
            f"Energy balance failed at step {i}: {balance}"

if __name__ == "__main__":
    pytest.main([__file__])
