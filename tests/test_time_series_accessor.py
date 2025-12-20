"""
Unit tests for TimeSeriesAccessor class.
"""

import pandas as pd
import pytest

from eclipse.consumption.data import TimeSeriesAccessor


class TestTimeSeriesAccessor:
    """Test suite for TimeSeriesAccessor class."""
    
    def test_initialization_valid(self, sample_hourly_data):
        """Test successful initialization with valid DataFrame."""
        # Arrange & Act
        accessor = TimeSeriesAccessor(sample_hourly_data, 'Consumption_kWh')
        
        # Assert
        assert isinstance(accessor, TimeSeriesAccessor)
        assert len(accessor) == len(sample_hourly_data)
    
    def test_initialization_invalid_index_type(self):
        """Test that initialization fails with non-DatetimeIndex."""
        # Arrange
        df = pd.DataFrame({'Consumption_kWh': [1, 2, 3]})
        
        # Act & Assert
        with pytest.raises(TypeError, match="DatetimeIndex"):
            TimeSeriesAccessor(df, 'Consumption_kWh')
    
    def test_dataframe_property(self, sample_hourly_data):
        """Test dataframe property returns underlying DataFrame."""
        # Arrange
        accessor = TimeSeriesAccessor(sample_hourly_data, 'Consumption_kWh')
        
        # Act
        df = accessor.dataframe
        
        # Assert
        assert isinstance(df, pd.DataFrame)
        pd.testing.assert_frame_equal(df, sample_hourly_data)
    
    def test_series_property(self, sample_hourly_data):
        """Test series property returns the value column."""
        # Arrange
        accessor = TimeSeriesAccessor(sample_hourly_data, 'Consumption_kWh')
        
        # Act
        series = accessor.series
        
        # Assert
        assert isinstance(series, pd.Series)
        assert series.name == 'Consumption_kWh'
        pd.testing.assert_series_equal(series, sample_hourly_data['Consumption_kWh'])
    
    def test_index_property(self, sample_hourly_data):
        """Test index property returns DatetimeIndex."""
        # Arrange
        accessor = TimeSeriesAccessor(sample_hourly_data, 'Consumption_kWh')
        
        # Act
        index = accessor.index
        
        # Assert
        assert isinstance(index, pd.DatetimeIndex)
        pd.testing.assert_index_equal(index, sample_hourly_data.index)
    
    def test_values_property(self, sample_hourly_data):
        """Test values property returns NumPy array."""
        # Arrange
        accessor = TimeSeriesAccessor(sample_hourly_data, 'Consumption_kWh')
        
        # Act
        values = accessor.values
        
        # Assert
        assert isinstance(values, type(sample_hourly_data['Consumption_kWh'].values))
        assert len(values) == len(sample_hourly_data)
    
    def test_sum_method(self, sample_hourly_data):
        """Test sum aggregation method."""
        # Arrange
        accessor = TimeSeriesAccessor(sample_hourly_data, 'Consumption_kWh')
        expected_sum = sample_hourly_data['Consumption_kWh'].sum()
        
        # Act
        result = accessor.sum()
        
        # Assert
        assert isinstance(result, float)
        assert pytest.approx(result, rel=1e-9) == expected_sum
    
    def test_mean_method(self, sample_hourly_data):
        """Test mean aggregation method."""
        # Arrange
        accessor = TimeSeriesAccessor(sample_hourly_data, 'Consumption_kWh')
        expected_mean = sample_hourly_data['Consumption_kWh'].mean()
        
        # Act
        result = accessor.mean()
        
        # Assert
        assert isinstance(result, float)
        assert pytest.approx(result, rel=1e-9) == expected_mean
    
    def test_max_method(self, sample_hourly_data):
        """Test max aggregation method."""
        # Arrange
        accessor = TimeSeriesAccessor(sample_hourly_data, 'Consumption_kWh')
        expected_max = sample_hourly_data['Consumption_kWh'].max()
        
        # Act
        result = accessor.max()
        
        # Assert
        assert isinstance(result, float)
        assert pytest.approx(result, rel=1e-9) == expected_max
    
    def test_min_method(self, sample_hourly_data):
        """Test min aggregation method."""
        # Arrange
        accessor = TimeSeriesAccessor(sample_hourly_data, 'Consumption_kWh')
        expected_min = sample_hourly_data['Consumption_kWh'].min()
        
        # Act
        result = accessor.min()
        
        # Assert
        assert isinstance(result, float)
        assert pytest.approx(result, rel=1e-9) == expected_min
    
    def test_std_method(self, sample_hourly_data):
        """Test standard deviation method."""
        # Arrange
        accessor = TimeSeriesAccessor(sample_hourly_data, 'Consumption_kWh')
        expected_std = sample_hourly_data['Consumption_kWh'].std()
        
        # Act
        result = accessor.std()
        
        # Assert
        assert isinstance(result, float)
        assert pytest.approx(result, rel=1e-9) == expected_std
    
    def test_len_method(self, sample_hourly_data):
        """Test __len__ method."""
        # Arrange
        accessor = TimeSeriesAccessor(sample_hourly_data, 'Consumption_kWh')
        
        # Act
        length = len(accessor)
        
        # Assert
        assert length == len(sample_hourly_data)
    
    def test_repr_method(self, sample_hourly_data):
        """Test __repr__ method returns meaningful string."""
        # Arrange
        accessor = TimeSeriesAccessor(sample_hourly_data, 'Consumption_kWh')
        
        # Act
        repr_str = repr(accessor)
        
        # Assert
        assert "TimeSeriesAccessor" in repr_str
        assert str(len(sample_hourly_data)) in repr_str
        assert "sum=" in repr_str
