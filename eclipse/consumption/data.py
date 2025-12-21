"""
Consumption Data Module - OOP Data Accessors
=============================================
Provides a Reaktoro-inspired composition-based design for accessing
consumption data through nested accessors.

Example Usage:
    data = ConsumptionData.load("path/to/consumption.csv")
    
    # Access nested data
    print(data.hourly.sum())           # Total annual kWh
    print(data.daily.dataframe.head()) # Daily DataFrame
    print(data.seasons.winter.mean())  # Avg winter hourly consumption
"""

from __future__ import annotations

import os
from typing import Optional, Dict, Any, TYPE_CHECKING

import pandas as pd
import numpy as np

if TYPE_CHECKING:
    from numpy.typing import NDArray


class TimeSeriesAccessor:
    """
    Wraps a pandas DataFrame/Series with DatetimeIndex, providing
    convenient accessor methods for common operations.
    
    Attributes:
        dataframe: The underlying pandas DataFrame.
        index: The DatetimeIndex of the data.
        values: NumPy array of the primary data column.
    """
    
    def __init__(self, df: pd.DataFrame, value_col: str = 'Consumption_kWh'):
        """
        Initialize the accessor.
        
        Args:
            df: DataFrame with DatetimeIndex.
            value_col: Name of the primary value column.
        """
        if not isinstance(df.index, pd.DatetimeIndex):
            raise TypeError("DataFrame must have a DatetimeIndex")
        self._df = df
        self._value_col = value_col
    
    @property
    def dataframe(self) -> pd.DataFrame:
        """Returns the underlying DataFrame."""
        return self._df
    
    @property
    def series(self) -> pd.Series:
        """Returns the primary value column as a Series."""
        return self._df[self._value_col]
    
    @property
    def index(self) -> pd.DatetimeIndex:
        """Returns the DatetimeIndex."""
        return self._df.index
    
    @property
    def values(self) -> 'NDArray[np.floating]':
        """Returns the primary values as a NumPy array."""
        return self._df[self._value_col].values
    
    def sum(self) -> float:
        """Returns the sum of all values."""
        return float(self._df[self._value_col].sum())
    
    def mean(self) -> float:
        """Returns the mean of all values."""
        return float(self._df[self._value_col].mean())
    
    def max(self) -> float:
        """Returns the maximum value."""
        return float(self._df[self._value_col].max())
    
    def min(self) -> float:
        """Returns the minimum value."""
        return float(self._df[self._value_col].min())
    
    def std(self) -> float:
        """Returns the standard deviation."""
        return float(self._df[self._value_col].std())
    
    def smooth(self, method: str = 'spline', points: int = 300) -> pd.DataFrame:
        """
        Returns smoothed version of the time series.
        
        Args:
            method: Smoothing method ('spline' or 'rolling').
            points: Number of interpolation points for spline.
            
        Returns:
            DataFrame with smoothed values and interpolated timestamps.
        """
        if len(self._df) < 4:
            # Not enough points for smoothing
            return self._df.copy()
        
        if method == 'spline':
            try:
                from scipy.interpolate import make_interp_spline
                x = np.arange(len(self._df))
                y = self.values
                x_smooth = np.linspace(x.min(), x.max(), points)
                spl = make_interp_spline(x, y, k=3)
                y_smooth = np.maximum(spl(x_smooth), 0)  # Prevent negative values
                
                # Create interpolated timestamps
                time_smooth = pd.date_range(
                    start=self.index[0],
                    end=self.index[-1],
                    periods=points
                )
                return pd.DataFrame({self._value_col: y_smooth}, index=time_smooth)
            except ImportError:
                # Fallback to rolling average if scipy not available
                return self._df.rolling(window=min(24, len(self._df)//10), center=True).mean()
        else:
            # Rolling average
            window = min(24, len(self._df) // 10)
            return self._df.rolling(window=window, center=True).mean()
    
    def __len__(self) -> int:
        return len(self._df)
    
    def __repr__(self) -> str:
        return f"TimeSeriesAccessor({len(self._df)} rows, sum={self.sum():.1f})"


class SeasonalAccessor:
    """
    Provides access to seasonal subsets of consumption data.
    
    Attributes:
        winter: TimeSeriesAccessor for winter months (Dec, Jan, Feb).
        spring: TimeSeriesAccessor for spring months (Mar, Apr, May).
        summer: TimeSeriesAccessor for summer months (Jun, Jul, Aug).
        autumn: TimeSeriesAccessor for autumn months (Sep, Oct, Nov).
        profile: DataFrame with typical daily profile per season.
    """
    
    SEASON_MONTHS = {
        'winter': [12, 1, 2],
        'spring': [3, 4, 5],
        'summer': [6, 7, 8],
        'autumn': [9, 10, 11]
    }
    
    def __init__(self, hourly_df: pd.DataFrame, value_col: str = 'Consumption_kWh'):
        """
        Initialize seasonal accessor.
        
        Args:
            hourly_df: Full hourly DataFrame with DatetimeIndex.
            value_col: Name of the primary value column.
        """
        self._hourly_df = hourly_df
        self._value_col = value_col
        self._cache: Dict[str, TimeSeriesAccessor] = {}
    
    def _get_season(self, name: str) -> TimeSeriesAccessor:
        """Lazily retrieves or creates a seasonal accessor."""
        if name not in self._cache:
            months = self.SEASON_MONTHS[name]
            mask = self._hourly_df.index.month.isin(months)
            df_season = self._hourly_df.loc[mask].copy()
            self._cache[name] = TimeSeriesAccessor(df_season, self._value_col)
        return self._cache[name]
    
    @property
    def winter(self) -> TimeSeriesAccessor:
        """Winter data (Dec, Jan, Feb)."""
        return self._get_season('winter')
    
    @property
    def spring(self) -> TimeSeriesAccessor:
        """Spring data (Mar, Apr, May)."""
        return self._get_season('spring')
    
    @property
    def summer(self) -> TimeSeriesAccessor:
        """Summer data (Jun, Jul, Aug)."""
        return self._get_season('summer')
    
    @property
    def autumn(self) -> TimeSeriesAccessor:
        """Autumn data (Sep, Oct, Nov)."""
        return self._get_season('autumn')
    
    @property
    def profile(self) -> pd.DataFrame:
        """
        Returns a DataFrame with the typical daily profile (hourly mean)
        for each season. Index is Hour (0-23), columns are season names.
        """
        df = self._hourly_df.copy()
        df['Hour'] = df.index.hour
        df['Season'] = df.index.month.map(self._month_to_season)
        
        profile = df.groupby(['Season', 'Hour'])[self._value_col].mean().unstack(level=0)
        
        # Reorder columns
        season_order = ['winter', 'spring', 'summer', 'autumn']
        existing = [s for s in season_order if s in profile.columns]
        return profile[existing]
    
    @staticmethod
    def _month_to_season(month: int) -> str:
        """Maps month number to season name."""
        for season, months in SeasonalAccessor.SEASON_MONTHS.items():
            if month in months:
                return season
        return 'unknown'
    
    def get_typical_week(
        self, 
        season: str, 
        month: Optional[int] = None, 
        day: Optional[int] = None
    ) -> TimeSeriesAccessor:
        """
        Returns a representative week of data for the specified season.
        
        Args:
            season: Season name ('winter', 'spring', 'summer', 'autumn').
            month: Optional specific month (otherwise uses mid-season default).
            day: Optional specific day (otherwise uses 15th).
            
        Returns:
            TimeSeriesAccessor containing one week of data.
        """
        # Default typical weeks
        defaults = {
            'winter': (1, 15),
            'spring': (4, 15),
            'summer': (7, 15),
            'autumn': (10, 15)
        }
        
        if month is None or day is None:
            month, day = defaults.get(season, (1, 15))
        
        # Determine year from data
        year = int(pd.Series(self._hourly_df.index.year).mode()[0])
        
        try:
            start_date = pd.Timestamp(year=year, month=month, day=day)
            end_date = start_date + pd.Timedelta(days=7)
            mask = (self._hourly_df.index >= start_date) & (self._hourly_df.index < end_date)
            df_week = self._hourly_df.loc[mask].copy()
            return TimeSeriesAccessor(df_week, self._value_col)
        except ValueError:
            # Invalid date, return empty
            return TimeSeriesAccessor(
                pd.DataFrame([], columns=[self._value_col]).set_index(pd.DatetimeIndex([])),
                self._value_col
            )
    
    def __repr__(self) -> str:
        return f"SeasonalAccessor(winter={len(self.winter)}, summer={len(self.summer)} rows)"


class ConsumptionData:
    """
    Main entry point for consumption data analysis.
    
    Provides a Reaktoro-inspired OOP interface for accessing consumption
    data at various aggregation levels through nested accessors.
    
    Example:
        data = ConsumptionData.load("consumption.csv")
        print(data.hourly.sum())         # Total kWh
        print(data.daily.mean())         # Avg daily kWh
        print(data.seasons.winter.sum()) # Winter total
    
    Attributes:
        hourly: TimeSeriesAccessor for hourly data.
        daily: TimeSeriesAccessor for daily aggregated data.
        monthly: TimeSeriesAccessor for monthly aggregated data.
        seasons: SeasonalAccessor for seasonal data.
        metadata: Dictionary with file info and statistics.
    """
    
    # Column name configuration
    VALUE_COL = 'Consumption_kWh'
    TIME_COL_CANDIDATES = ['zeit', 'timestamp', 'date', 'time']
    CONS_COL_CANDIDATES = ['stromverbrauch_kwh', 'verbrauch_kwh', 'consumption', 'consumption_kwh', 'wert']
    
    def __init__(self, hourly_df: pd.DataFrame, metadata: Optional[Dict[str, Any]] = None):
        """
        Initialize ConsumptionData from an hourly DataFrame.
        
        Args:
            hourly_df: DataFrame with DatetimeIndex and VALUE_COL column.
            metadata: Optional metadata dictionary.
        """
        if not isinstance(hourly_df.index, pd.DatetimeIndex):
            raise TypeError("hourly_df must have a DatetimeIndex")
        if self.VALUE_COL not in hourly_df.columns:
            raise ValueError(f"DataFrame must contain '{self.VALUE_COL}' column")
        
        self._hourly = hourly_df
        self._metadata = metadata or {}
        
        # Lazy initialization
        self._daily: Optional[pd.DataFrame] = None
        self._monthly: Optional[pd.DataFrame] = None
        self._seasons: Optional[SeasonalAccessor] = None
    
    @classmethod
    def load(cls, file_path: str) -> 'ConsumptionData':
        """
        Factory method to load consumption data from a CSV file.
        
        Args:
            file_path: Path to the CSV file.
            
        Returns:
            ConsumptionData instance.
            
        Raises:
            FileNotFoundError: If file doesn't exist.
            ValueError: If data cannot be parsed.
        """
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"File not found: {file_path}")
        
        # Load CSV
        df = pd.read_csv(file_path, sep=None, engine='python')
        df.columns = [c.strip().lower() for c in df.columns]
        
        # Identify time column
        time_col = next((c for c in df.columns if c in cls.TIME_COL_CANDIDATES), df.columns[0])
        
        # Identify consumption column
        cons_col = next((c for c in df.columns if c in cls.CONS_COL_CANDIDATES), None)
        if cons_col is None and len(df.columns) > 1:
            cons_col = df.columns[1]
        if cons_col is None:
            raise ValueError("Could not identify consumption column")
        
        # Parse datetime
        try:
            df[time_col] = pd.to_datetime(df[time_col])
        except ValueError:
            df[time_col] = pd.to_datetime(df[time_col], dayfirst=True)
        
        df.set_index(time_col, inplace=True)
        
        # Resample to hourly
        df_hourly = df[[cons_col]].resample('h').sum()
        df_hourly.rename(columns={cons_col: cls.VALUE_COL}, inplace=True)
        
        # Create metadata
        metadata = {
            'source_file': os.path.basename(file_path),
            'source_path': file_path,
            'rows_raw': len(df),
            'rows_hourly': len(df_hourly),
            'date_range': (df_hourly.index.min(), df_hourly.index.max()),
        }
        
        instance = cls(df_hourly, metadata)
        instance.validate()
        
        return instance
    
    @classmethod
    def from_file(cls, file_path: str) -> 'ConsumptionData':
        """
        Alias for load(). Loads consumption data from a CSV file.
        
        Args:
            file_path: Path to the CSV file.
            
        Returns:
            ConsumptionData instance.
        """
        return cls.load(file_path)
    
    def validate(self) -> None:
        """
        Validates data quality.
        
        Raises:
            ValueError: If data fails validation.
        """
        n = len(self._hourly)
        if n not in (8760, 8784):
            # Warning only, don't raise
            print(f"Warning: Expected full-year hourly data (8760/8784 rows), got {n}")
        
        if (self._hourly[self.VALUE_COL] < 0).any():
            raise ValueError("Consumption data contains negative values")
    
    @property
    def hourly(self) -> TimeSeriesAccessor:
        """Hourly consumption data."""
        return TimeSeriesAccessor(self._hourly, self.VALUE_COL)
    
    @property
    def daily(self) -> TimeSeriesAccessor:
        """Daily aggregated consumption data."""
        if self._daily is None:
            self._daily = self._hourly[[self.VALUE_COL]].resample('D').sum()
        return TimeSeriesAccessor(self._daily, self.VALUE_COL)
    
    @property
    def monthly(self) -> TimeSeriesAccessor:
        """Monthly aggregated consumption data."""
        if self._monthly is None:
            self._monthly = self._hourly[[self.VALUE_COL]].resample('ME').sum()
        return TimeSeriesAccessor(self._monthly, self.VALUE_COL)
    
    @property
    def seasons(self) -> SeasonalAccessor:
        """Seasonal data accessor."""
        if self._seasons is None:
            self._seasons = SeasonalAccessor(self._hourly, self.VALUE_COL)
        return self._seasons
    
    @property
    def metadata(self) -> Dict[str, Any]:
        """Returns metadata dictionary."""
        return self._metadata.copy()
    
    def slice(self, start: str, end: str) -> TimeSeriesAccessor:
        """
        Returns a TimeSeriesAccessor for a custom date range.
        
        Args:
            start: Start date (e.g., '2024-01-15').
            end: End date (e.g., '2024-01-21').
            
        Returns:
            TimeSeriesAccessor for the specified range.
        """
        mask = (self._hourly.index >= pd.to_datetime(start)) & \
               (self._hourly.index <= pd.to_datetime(end))
        return TimeSeriesAccessor(self._hourly.loc[mask].copy(), self.VALUE_COL)
    
    def get_extreme_weeks(self) -> Dict[str, Any]:
        """
        Identifies and returns data for weeks with maximum and minimum total consumption.
        
        Returns:
            Dictionary with keys:
                - 'max_week': TimeSeriesAccessor for highest consumption week
                - 'min_week': TimeSeriesAccessor for lowest consumption week
                - 'max_total': Total kWh for max week
                - 'min_total': Total kWh for min week
                - 'max_dates': (start_date, end_date) for max week
                - 'min_dates': (start_date, end_date) for min week
        """
        # Resample to weekly and find extreme weeks
        weekly_totals = self._hourly[self.VALUE_COL].resample('W').sum()
        max_week_end = weekly_totals.idxmax()
        min_week_end = weekly_totals.idxmin()
        
        def get_week_data(end_date):
            start = end_date - pd.Timedelta(days=6)
            end_slice = end_date + pd.Timedelta(hours=23, minutes=59)
            mask = (self._hourly.index >= start) & (self._hourly.index <= end_slice)
            df_week = self._hourly.loc[mask].copy()
            total = df_week[self.VALUE_COL].sum()
            return TimeSeriesAccessor(df_week, self.VALUE_COL), total, start, end_date
        
        max_accessor, max_total, max_start, max_end = get_week_data(max_week_end)
        min_accessor, min_total, min_start, min_end = get_week_data(min_week_end)
        
        return {
            'max_week': max_accessor,
            'min_week': min_accessor,
            'max_total': max_total,
            'min_total': min_total,
            'max_dates': (max_start, max_end),
            'min_dates': (min_start, min_end)
        }
    
    def __repr__(self) -> str:
        total = self.hourly.sum()
        src = self._metadata.get('source_file', 'unknown')
        return f"ConsumptionData(source='{src}', total={total:.0f} kWh)"
