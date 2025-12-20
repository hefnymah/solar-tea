"""
Unit tests for ConsumptionData class.
"""

import os

import pandas as pd
import pytest

from eclipse.consumption.data import ConsumptionData, TimeSeriesAccessor, SeasonalAccessor


class TestConsumptionDataInitialization:
    """Test suite for ConsumptionData initialization."""
    
    def test_initialization_valid(self, sample_hourly_data):
        """Test successful initialization with valid data."""
        # Arrange
        df = sample_hourly_data.copy()
        df.rename(columns={'Consumption_kWh': ConsumptionData.VALUE_COL}, inplace=True)
        metadata = {'source_file': 'test.csv'}
        
        # Act
        data = ConsumptionData(df, metadata)
        
        # Assert
        assert isinstance(data, ConsumptionData)
        assert data.metadata['source_file'] == 'test.csv'
    
    def test_initialization_no_datetime_index(self):
        """Test that initialization fails without DatetimeIndex."""
        # Arrange
        df = pd.DataFrame({'Consumption_kWh': [1, 2, 3]})
        
        # Act & Assert
        with pytest.raises(TypeError, match="DatetimeIndex"):
            ConsumptionData(df)
    
    def test_initialization_missing_value_column(self, sample_hourly_data):
        """Test that initialization fails without required column."""
        # Arrange
        df = sample_hourly_data.copy()
        df.rename(columns={'Consumption_kWh': 'WrongColumn'}, inplace=True)
        
        # Act & Assert
        with pytest.raises(ValueError, match="must contain"):
            ConsumptionData(df)


class TestConsumptionDataLoading:
    """Test suite for ConsumptionData.load() factory method."""
    
    def test_load_from_csv(self, sample_csv_file):
        """Test loading from CSV file."""
        # Arrange & Act
        data = ConsumptionData.load(sample_csv_file)
        
        # Assert
        assert isinstance(data, ConsumptionData)
        assert len(data.hourly.dataframe) > 0
    
    def test_load_from_csv_alternative_method(self, sample_csv_file):
        """Test from_file alias works."""
        # Arrange & Act
        data = ConsumptionData.from_file(sample_csv_file)
        
        # Assert
        assert isinstance(data, ConsumptionData)
    
    def test_load_nonexistent_file(self):
        """Test that loading nonexistent file raises error."""
        # Arrange
        fake_path = "/nonexistent/file.csv"
        
        # Act & Assert
        with pytest.raises(FileNotFoundError):
            ConsumptionData.load(fake_path)
    
    def test_load_updates_metadata(self, sample_csv_file):
        """Test that loading populates metadata correctly."""
        # Arrange & Act
        data = ConsumptionData.load(sample_csv_file)
        
        # Assert
        metadata = data.metadata
        assert 'source_file' in metadata
        assert 'source_path' in metadata
        assert 'rows_raw' in metadata
        assert 'rows_hourly' in metadata
        assert 'date_range' in metadata


class TestConsumptionDataAccessors:
    """Test suite for ConsumptionData nested accessors."""
    
    def test_hourly_accessor(self, mock_consumption_data):
        """Test hourly property returns TimeSeriesAccessor."""
        # Arrange & Act
        hourly = mock_consumption_data.hourly
        
        # Assert
        assert isinstance(hourly, TimeSeriesAccessor)
    
    def test_daily_accessor(self, mock_consumption_data):
        """Test daily property aggregates and returns TimeSeriesAccessor."""
        # Arrange & Act
        daily = mock_consumption_data.daily
        
        # Assert
        assert isinstance(daily, TimeSeriesAccessor)
        assert len(daily) <= len(mock_consumption_data.hourly)
    
    def test_daily_accessor_caching(self, mock_consumption_data):
        """Test that daily data is cached."""
        # Arrange & Act
        daily1 = mock_consumption_data.daily
        daily2 = mock_consumption_data.daily
        
        # Assert - underlying DataFrame should be the same object
        assert daily1.dataframe is daily2.dataframe
    
    def test_monthly_accessor(self, mock_consumption_data):
        """Test monthly property aggregates correctly."""
        # Arrange & Act
        monthly = mock_consumption_data.monthly
        
        # Assert
        assert isinstance(monthly, TimeSeriesAccessor)
        assert len(monthly) == 12  # Should have 12 months for full year
    
    def test_seasonal_accessor(self, mock_consumption_data):
        """Test seasons property returns SeasonalAccessor."""
        # Arrange & Act
        seasons = mock_consumption_data.seasons
        
        # Assert
        assert isinstance(seasons, SeasonalAccessor)
    
    def test_seasonal_accessor_caching(self, mock_consumption_data):
        """Test that seasonal accessor is cached."""
        # Arrange & Act
        seasons1 = mock_consumption_data.seasons
        seasons2 = mock_consumption_data.seasons
        
        # Assert
        assert seasons1 is seasons2


class TestConsumptionDataSlicing:
    """Test suite for ConsumptionData.slice() method."""
    
    def test_slice_date_range(self, mock_consumption_data):
        """Test slicing returns data for specified range."""
        # Arrange & Act
        sliced = mock_consumption_data.slice("2024-01-15", "2024-01-21")
        
        # Assert
        assert isinstance(sliced, TimeSeriesAccessor)
        assert len(sliced) > 0
        assert sliced.index.min() >= pd.Timestamp("2024-01-15")
        assert sliced.index.max() <= pd.Timestamp("2024-01-21")
    
    def test_slice_single_day(self, mock_consumption_data):
        """Test slicing a single day."""
        # Arrange & Act
        sliced = mock_consumption_data.slice("2024-06-01", "2024-06-01")
        
        # Assert
        assert len(sliced) >= 1  # At least 1 hour on that day
    
    def test_slice_preserves_data_integrity(self, mock_consumption_data):
        """Test that slicing doesn't modify original data."""
        # Arrange
        original_len = len(mock_consumption_data.hourly)
        
        # Act
        _ = mock_consumption_data.slice("2024-01-01", "2024-01-31")
        
        # Assert
        assert len(mock_consumption_data.hourly) == original_len


class TestConsumptionDataValidation:
    """Test suite for ConsumptionData.validate() method."""
    
    def test_validate_full_year(self, mock_consumption_data, capsys):
        """Test validation passes for full year data."""
        # Arrange & Act
        mock_consumption_data.validate()
        captured = capsys.readouterr()
        
        # Assert - should not print warning for 8784 rows (leap year)
        assert "Warning" not in captured.out or "8784" in captured.out
    
    def test_validate_partial_year(self, sample_hourly_data, capsys):
        """Test validation warns for partial year data."""
        # Arrange
        df = sample_hourly_data.iloc[:100].copy()  # Only 100 hours
        df.rename(columns={'Consumption_kWh': ConsumptionData.VALUE_COL}, inplace=True)
        data = ConsumptionData(df)
        
        # Act
        data.validate()
        captured = capsys.readouterr()
        
        # Assert
        assert "Warning" in captured.out
    
    def test_validate_negative_values(self, sample_hourly_data):
        """Test validation fails for negative consumption."""
        # Arrange
        df = sample_hourly_data.copy()
        df.iloc[0, 0] = -10  # Insert negative value
        df.rename(columns={'Consumption_kWh': ConsumptionData.VALUE_COL}, inplace=True)
        data = ConsumptionData(df)
        
        # Act & Assert
        with pytest.raises(ValueError, match="negative values"):
            data.validate()


class TestConsumptionDataRepr:
    """Test suite for ConsumptionData __repr__."""
    
    def test_repr_format(self, mock_consumption_data):
        """Test __repr__ returns meaningful string."""
        # Arrange & Act
        repr_str = repr(mock_consumption_data)
        
        # Assert
        assert "ConsumptionData" in repr_str
        assert "source=" in repr_str
        assert "total=" in repr_str
        assert "kWh" in repr_str
