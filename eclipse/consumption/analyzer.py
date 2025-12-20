"""
Consumption Analyzer Module (Refactored)
=========================================
Backward-compatible facade that composes ConsumptionData and ConsumptionPlotter.

For new code, prefer using ConsumptionData and ConsumptionPlotter directly:
    from eclipse.consumption import ConsumptionData, ConsumptionPlotter
    
    data = ConsumptionData.load("path/to/file.csv")
    plotter = ConsumptionPlotter(data, output_dir="./output")
    plotter.plot_all()

For legacy code, ConsumptionAnalyzer still works:
    analyzer = ConsumptionAnalyzer(output_dir="./output")
    analyzer.load_data("path/to/file.csv")
    analyzer.analyze()
    analyzer.plot_all()
"""

from __future__ import annotations

import os
from typing import Optional, Dict, Any

from eclipse.consumption.data import ConsumptionData, TimeSeriesAccessor, SeasonalAccessor
from eclipse.consumption.plotter import ConsumptionPlotter


class ConsumptionAnalyzer:
    """
    Backward-compatible analyzer that wraps ConsumptionData and ConsumptionPlotter.
    
    This class maintains the original API while delegating to the new OOP classes.
    For new code, use ConsumptionData and ConsumptionPlotter directly.
    
    Attributes:
        data: The underlying ConsumptionData object (accessible after load_data).
        plotter: The underlying ConsumptionPlotter object (accessible after load_data).
    """
    
    def __init__(self, output_dir: Optional[str] = None):
        """
        Initialize the analyzer.
        
        Args:
            output_dir: Directory to save generated plots.
        """
        self.output_dir = output_dir
        self._data: Optional[ConsumptionData] = None
        self._plotter: Optional[ConsumptionPlotter] = None
        
        # Legacy attribute for raw hourly DataFrame access
        self.df_hourly = None
        self.daily_profile_seasonal = None
        
        # Configuration (legacy)
        self.target_col = 'Consumption_kWh'
        self.time_col_candidates = ['zeit', 'timestamp', 'date', 'time']
        self.cons_col_candidates = ['stromverbrauch_kwh', 'verbrauch_kwh', 'consumption', 'consumption_kwh', 'wert']
        
        # Season mapping (legacy)
        self.seasons = {
            'Winter': [12, 1, 2],
            'Spring': [3, 4, 5],
            'Summer': [6, 7, 8],
            'Autumn': [9, 10, 11]
        }
        self.season_colors = {
            'Winter': 'blue',
            'Spring': 'green',
            'Summer': 'red',
            'Autumn': 'orange'
        }
        
        # Seasonal representative weeks
        self.seasonal_weeks_config = {
            'Winter': (1, 15),
            'Spring': (4, 15),
            'Summer': (7, 15),
            'Autumn': (10, 15)
        }
    
    @property
    def data(self) -> Optional[ConsumptionData]:
        """Returns the underlying ConsumptionData object."""
        return self._data
    
    @property
    def plotter(self) -> Optional[ConsumptionPlotter]:
        """Returns the underlying ConsumptionPlotter object."""
        return self._plotter
    
    def _get_season(self, month: int) -> str:
        """Legacy method for season mapping."""
        for season, months in self.seasons.items():
            if month in months:
                return season
        return 'Unknown'
    
    def load_data(self, file_path: str) -> bool:
        """
        Loads CSV data using the new ConsumptionData class.
        
        Args:
            file_path: Path to CSV file.
            
        Returns:
            True if successful, False otherwise.
        """
        print(f"Loading: {os.path.basename(file_path)}")
        
        try:
            self._data = ConsumptionData.load(file_path)
            
            # Update legacy attributes for backward compatibility
            self.df_hourly = self._data.hourly.dataframe.copy()
            self.df_hourly['Month'] = self.df_hourly.index.month
            self.df_hourly['Hour'] = self.df_hourly.index.hour
            self.df_hourly['Season'] = self.df_hourly['Month'].apply(self._get_season)
            
            # Create plotter with custom config
            seasonal_weeks_lower = {k.lower(): v for k, v in self.seasonal_weeks_config.items()}
            season_colors_lower = {k.lower(): v for k, v in self.season_colors.items()}
            
            self._plotter = ConsumptionPlotter(
                self._data, 
                output_dir=self.output_dir,
                season_colors=season_colors_lower,
                seasonal_weeks=seasonal_weeks_lower
            )
            
            print(f"   Loaded and resampled to {len(self.df_hourly)} hourly records.")
            return True
            
        except Exception as e:
            print(f"Error loading {file_path}: {e}")
            return False
    
    def _validate(self) -> None:
        """Legacy validation method."""
        if self._data is not None:
            self._data.validate()
    
    def analyze(self) -> None:
        """
        Performs aggregation analysis.
        Updates daily_profile_seasonal for legacy access.
        """
        if self._data is None:
            return
        
        # Compute seasonal daily profile for legacy access
        self.daily_profile_seasonal = self._data.seasons.profile
        
        # Rename columns to match legacy format (capitalized)
        self.daily_profile_seasonal.columns = [c.title() for c in self.daily_profile_seasonal.columns]
    
    def plot_all(self, filename_prefix: str = '') -> Dict[str, str]:
        """
        Generates all standard plots.
        
        Args:
            filename_prefix: Prefix for filenames.
            
        Returns:
            Dictionary mapping plot names to file paths.
        """
        if self._plotter is None:
            return {}
        
        return self._plotter.plot_all(prefix=filename_prefix)
    
    def plot_date_range(
        self, 
        start_date: str, 
        end_date: str, 
        output_path: Optional[str] = None,
        title: Optional[str] = None,
        smooth: bool = True
    ) -> Optional[str]:
        """
        Plot consumption for a custom date range.
        
        Args:
            start_date: Start date (e.g., '2024-01-15').
            end_date: End date (inclusive).
            output_path: Full path to save. If None, displays interactively.
            title: Custom plot title.
            smooth: Apply spline smoothing.
            
        Returns:
            Path to saved plot if output_path provided.
        """
        if self._plotter is None:
            print("Error: No data loaded. Call load_data() first.")
            return None
        
        return self._plotter.plot_date_range(start_date, end_date, output_path, title, smooth)
