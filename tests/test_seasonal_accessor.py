"""
Unit tests for SeasonalAccessor class.
"""

import pandas as pd
import pytest

from eclipse.consumption.data import SeasonalAccessor, TimeSeriesAccessor


class TestSeasonalAccessor:
    """Test suite for SeasonalAccessor class."""
    
    def test_initialization(self, sample_hourly_data):
        """Test successful initialization."""
        # Arrange & Act
        accessor = SeasonalAccessor(sample_hourly_data, 'Consumption_kWh')
        
        # Assert
        assert isinstance(accessor, SeasonalAccessor)
    
    def test_winter_property(self, sample_hourly_data):
        """Test winter property returns correct TimeSeriesAccessor."""
        # Arrange
        accessor = SeasonalAccessor(sample_hourly_data, 'Consumption_kWh')
        
        # Act
        winter = accessor.winter
        
        # Assert
        assert isinstance(winter, TimeSeriesAccessor)
        # Winter months: Dec, Jan, Feb (12, 1, 2)
        assert all(winter.dataframe.index.month.isin([12, 1, 2]))
    
    def test_spring_property(self, sample_hourly_data):
        """Test spring property returns correct subset."""
        # Arrange
        accessor = SeasonalAccessor(sample_hourly_data, 'Consumption_kWh')
        
        # Act
        spring = accessor.spring
        
        # Assert
        assert isinstance(spring, TimeSeriesAccessor)
        # Spring months: Mar, Apr, May (3, 4, 5)
        assert all(spring.dataframe.index.month.isin([3, 4, 5]))
    
    def test_summer_property(self, sample_hourly_data):
        """Test summer property returns correct subset."""
        # Arrange
        accessor = SeasonalAccessor(sample_hourly_data, 'Consumption_kWh')
        
        # Act
        summer = accessor.summer
        
        # Assert
        assert isinstance(summer, TimeSeriesAccessor)
        # Summer months: Jun, Jul, Aug (6, 7, 8)
        assert all(summer.dataframe.index.month.isin([6, 7, 8]))
    
    def test_autumn_property(self, sample_hourly_data):
        """Test autumn property returns correct subset."""
        # Arrange
        accessor = SeasonalAccessor(sample_hourly_data, 'Consumption_kWh')
        
        # Act
        autumn = accessor.autumn
        
        # Assert
        assert isinstance(autumn, TimeSeriesAccessor)
        # Autumn months: Sep, Oct, Nov (9, 10, 11)
        assert all(autumn.dataframe.index.month.isin([9, 10, 11]))
    
    def test_all_seasons_cover_full_year(self, sample_hourly_data):
        """Test that all seasons together cover the entire year."""
        # Arrange
        accessor = SeasonalAccessor(sample_hourly_data, 'Consumption_kWh')
        
        # Act
        total_length = (
            len(accessor.winter) + 
            len(accessor.spring) + 
            len(accessor.summer) + 
            len(accessor.autumn)
        )
        
        # Assert
        assert total_length == len(sample_hourly_data)
    
    def test_seasonal_caching(self, sample_hourly_data):
        """Test that seasonal data is cached (same object returned)."""
        # Arrange
        accessor = SeasonalAccessor(sample_hourly_data, 'Consumption_kWh')
        
        # Act
        winter1 = accessor.winter
        winter2 = accessor.winter
        
        # Assert
        assert winter1 is winter2  # Same object reference
    
    def test_profile_property(self, sample_hourly_data):
        """Test profile property returns DataFrame with hourly averages."""
        # Arrange
        accessor = SeasonalAccessor(sample_hourly_data, 'Consumption_kWh')
        
        # Act
        profile = accessor.profile
        
        # Assert
        assert isinstance(profile, pd.DataFrame)
        assert profile.index.name == 'Hour'
        assert len(profile) == 24  # 24 hours
        assert all(col in profile.columns for col in ['winter', 'spring', 'summer', 'autumn'])
    
    def test_profile_column_order(self, sample_hourly_data):
        """Test that profile columns are in expected order."""
        # Arrange
        accessor = SeasonalAccessor(sample_hourly_data, 'Consumption_kWh')
        
        # Act
        profile = accessor.profile
        
        # Assert
        expected_order = ['winter', 'spring', 'summer', 'autumn']
        assert list(profile.columns) == expected_order
    
    def test_month_to_season_mapping(self):
        """Test static method for month to season mapping."""
        # Arrange & Act & Assert
        assert SeasonalAccessor._month_to_season(12) == 'winter'
        assert SeasonalAccessor._month_to_season(1) == 'winter'
        assert SeasonalAccessor._month_to_season(2) == 'winter'
        assert SeasonalAccessor._month_to_season(3) == 'spring'
        assert SeasonalAccessor._month_to_season(4) == 'spring'
        assert SeasonalAccessor._month_to_season(5) == 'spring'
        assert SeasonalAccessor._month_to_season(6) == 'summer'
        assert SeasonalAccessor._month_to_season(7) == 'summer'
        assert SeasonalAccessor._month_to_season(8) == 'summer'
        assert SeasonalAccessor._month_to_season(9) == 'autumn'
        assert SeasonalAccessor._month_to_season(10) == 'autumn'
        assert SeasonalAccessor._month_to_season(11) == 'autumn'
    
    def test_repr_method(self, sample_hourly_data):
        """Test __repr__ method."""
        # Arrange
        accessor = SeasonalAccessor(sample_hourly_data, 'Consumption_kWh')
        
        # Act
        repr_str = repr(accessor)
        
        # Assert
        assert "SeasonalAccessor" in repr_str
        assert "winter=" in repr_str
        assert "summer=" in repr_str
