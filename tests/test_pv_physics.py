"""
Test Suite for PV Physics Simulation
====================================
Verifies the accuracy and reliability of the PV simulation logic.

Tests:
1. PVLib Integration: Ensures simulation runs without errors.
2. Specific Yield: Checks if calculated yield is within expected range for Switzerland (900-1100 kWh/kWp).
3. Capacity Scaling: Verifies linear scaling of generation with system size.
"""

import pytest
import pandas as pd
import numpy as np
from datetime import datetime
from eclipse.pvsim import LocationConfig, RoofConfig, PVSystemSizer
from eclipse.pvsim.system_sizer import SimulationAccessor
from eclipse.consumption import ConsumptionData

@pytest.fixture
def mock_consumption_data():
    """Create synthetic consumption data for testing."""
    # Create annual hourly index for 2024 (leap year)
    dates = pd.date_range(start='2024-01-01', end='2025-01-01', freq='h', inclusive='left')
    # Create pandas DataFrame instead of Series
    consumption = pd.DataFrame(
        {'Consumption_kWh': np.random.rand(len(dates))}, 
        index=dates
    )
    return ConsumptionData(hourly_df=consumption)

@pytest.fixture
def zurich_location():
    return LocationConfig(
        latitude=47.38,
        longitude=8.54,
        altitude=400,
        timezone='Europe/Zurich'
    )

@pytest.fixture
def optimal_roof():
    return RoofConfig(
        tilt=30,
        azimuth=180,  # South facing
        max_area_m2=50
    )

def test_simulation_accessor_initialization(zurich_location, optimal_roof, mock_consumption_data):
    """Test that SimulationAccessor initializes correctly."""
    sim = SimulationAccessor(zurich_location, optimal_roof, mock_consumption_data)
    assert sim._location == zurich_location
    assert sim._roof == optimal_roof

def test_specific_yield_zurich(zurich_location, optimal_roof, mock_consumption_data):
    """Test that specific yield for Zurich south-facing roof is reasonable."""
    sim = SimulationAccessor(zurich_location, optimal_roof, mock_consumption_data)
    
    # Specific yield in Zurich is typically ~900-1100 kWh/kWp/yr
    specific_yield = sim.specific_yield
    
    print(f"\nCalculated Specific Yield for Zurich: {specific_yield:.2f} kWh/kWp")
    
    # Allow wide range because weather data source (PVGIS/TMY) varies
    assert 850 < specific_yield < 1200, \
        f"Specific yield {specific_yield} outside expected range (850-1200)"

def test_generation_scaling(zurich_location, optimal_roof, mock_consumption_data):
    """Verify that generation scales linearly with system capacity."""
    sim = SimulationAccessor(zurich_location, optimal_roof, mock_consumption_data)
    
    gen_1kwp = sim.scale_to_capacity(1.0)
    gen_10kwp = sim.scale_to_capacity(10.0)
    
    # Check total energy
    total_1 = gen_1kwp.sum()
    total_10 = gen_10kwp.sum()
    
    assert np.isclose(total_10, total_1 * 10, rtol=0.01), \
        "Generation did not scale linearly with capacity"
    
    # Check individual timestamps (vectorized)
    assert np.allclose(gen_10kwp, gen_1kwp * 10, rtol=0.01), \
        "Hourly generation did not scale linearly"

def test_pv_system_sizer_simulation(zurich_location, optimal_roof, mock_consumption_data):
    """Test full PVSystemSizer simulation method."""
    sizer = PVSystemSizer(mock_consumption_data, zurich_location, optimal_roof)
    
    # Simulate 5 kWp system
    result = sizer.simulate(pv_kwp=5.0)
    
    assert result.annual_generation_kwh > 0
    assert result.self_sufficiency_pct >= 0
    assert result.self_sufficiency_pct <= 100
    
    # Verify relationships
    # Generation = Self-Consumed + Grid Export
    # (Allow small floating point differences)
    energy_balance = (
        result.annual_self_consumed_kwh + 
        result.annual_grid_export_kwh - 
        result.annual_generation_kwh
    )
    assert abs(energy_balance) < 1.0, f"Energy balance failed: {energy_balance}"

if __name__ == "__main__":
    pytest.main([__file__])
