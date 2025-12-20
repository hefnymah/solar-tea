"""
Pytest configuration and shared fixtures for eclipse tests.
"""

import os
import tempfile
from pathlib import Path
from typing import Generator

import pandas as pd
import pytest


@pytest.fixture
def sample_hourly_data() -> pd.DataFrame:
    """
    Creates a sample hourly DataFrame for a full year (leap year).
    
    Returns:
        DataFrame with DatetimeIndex and 'Consumption_kWh' column.
    """
    dates = pd.date_range('2024-01-01', '2024-12-31 23:00:00', freq='h')
    
    # Create realistic consumption pattern
    # Higher in winter, lower in summer, daily variation
    hour_of_day = dates.hour
    month = dates.month
    
    # Base load
    base = 0.2
    
    # Seasonal variation (higher in winter)
    seasonal = 0.1 * (1 - (month - 1) / 11)
    
    # Daily variation (higher evening, lower night)
    daily = 0.15 * (1 + pd.Series(hour_of_day).apply(
        lambda h: 0.5 if 6 <= h < 22 else -0.5
    ).values)
    
    consumption = base + seasonal + daily
    
    df = pd.DataFrame({
        'Consumption_kWh': consumption
    }, index=dates)
    
    return df


@pytest.fixture
def sample_csv_file(sample_hourly_data: pd.DataFrame, tmp_path: Path) -> str:
    """
    Creates a temporary CSV file with sample consumption data.
    
    Args:
        sample_hourly_data: Hourly DataFrame fixture.
        tmp_path: Pytest tmp_path fixture.
        
    Returns:
        Path to the temporary CSV file.
    """
    csv_path = tmp_path / "test_consumption.csv"
    
    # Reset index to make timestamp a column
    df = sample_hourly_data.copy()
    df.index.name = 'zeit'
    df.reset_index(inplace=True)
    df.columns = ['zeit', 'stromverbrauch_kwh']
    
    df.to_csv(csv_path, index=False)
    
    return str(csv_path)


@pytest.fixture
def output_dir(tmp_path: Path) -> str:
    """
    Creates a temporary output directory for plots.
    
    Args:
        tmp_path: Pytest tmp_path fixture.
        
    Returns:
        Path to the temporary output directory.
    """
    out_dir = tmp_path / "outputs"
    out_dir.mkdir(exist_ok=True)
    return str(out_dir)


@pytest.fixture
def mock_consumption_data(sample_hourly_data: pd.DataFrame):
    """
    Creates a ConsumptionData instance from sample data.
    
    Args:
        sample_hourly_data: Hourly DataFrame fixture.
        
    Returns:
        ConsumptionData instance.
    """
    from eclipse.consumption.data import ConsumptionData
    
    # Rename column to match expected name
    df = sample_hourly_data.copy()
    df.rename(columns={'Consumption_kWh': ConsumptionData.VALUE_COL}, inplace=True)
    
    metadata = {
        'source_file': 'test.csv',
        'rows_raw': len(df),
        'rows_hourly': len(df),
    }
    
    return ConsumptionData(df, metadata)
