"""
PV System Analyzer
==================
Business logic layer for PV system data processing and analysis.

Handles:
- Time period extraction
- Energy flow calculations  
- Statistical analysis
- Data aggregation

Separates data processing from visualization for reusability.
"""

from __future__ import annotations
from typing import TYPE_CHECKING, Optional
import pandas as pd
from dataclasses import dataclass

if TYPE_CHECKING:
    from eclipse.simulation.system_sizer import SimulationAccessor


@dataclass
class PeriodAnalysis:
    """
    Results of PV system analysis for a specific time period.
    
    This is a pure data container that can be:
    - Plotted by visualization layer
    - Saved to database
    - Exported to CSV
    - Used in further calculations
    
    Attributes:
        period_start: Start timestamp
        period_end: End timestamp
        timestamps: Time index
        consumption_kwh: Consumption energy series
        pv_kwh: PV generation energy series
        self_consumed_kwh: Self-consumed energy series
        grid_import_kwh: Grid import energy series
        grid_export_kwh: Grid export energy series
        net_grid_kwh: Net grid flow (import - export)
        total_consumption: Total consumption in period
        total_pv: Total PV generation in period
        total_self_consumed: Total self-consumed energy
        total_grid_import: Total grid import
        total_grid_export: Total grid export
        total_net_grid: Total net grid flow
        self_consumption_rate: % of PV used locally
    """
    # Time information
    period_start: pd.Timestamp
    period_end: pd.Timestamp
    timestamps: pd.DatetimeIndex
    
    # Energy flows (time series)
    consumption_kwh: pd.Series
    pv_kwh: pd.Series
    self_consumed_kwh: pd.Series
    grid_import_kwh: pd.Series
    grid_export_kwh: pd.Series
    net_grid_kwh: pd.Series
    
    # Aggregated statistics
    total_consumption: float
    total_pv: float
    total_self_consumed: float
    total_grid_import: float
    total_grid_export: float
    total_net_grid: float
    self_consumption_rate: float
    
    def to_dict(self) -> dict:
        """Convert to dictionary for serialization."""
        return {
            'period_start': self.period_start,
            'period_end': self.period_end,
            'totals': {
                'consumption': self.total_consumption,
                'pv': self.total_pv,
                'self_consumed': self.total_self_consumed,
                'grid_import': self.total_grid_import,
                'grid_export': self.total_grid_export,
                'net_grid': self.total_net_grid,
                'self_consumption_rate': self.self_consumption_rate
            }
        }


class PVSystemAnalyzer:
    """
    Analyzer for PV system performance data.
    
    Processes SizingResult data to extract meaningful insights
    for specific time periods. Separates business logic from
    data storage and visualization.
    
    Example:
        >>> analyzer = PVSystemAnalyzer(sizing_result)
        >>> # Analyze specific period
        >>> period = analyzer.analyze_period('2024-06-01', '2024-06-07')
        >>> print(f"Total PV: {period.total_pv:.1f} kWh")
        >>> 
        >>> # Process data for later use
        >>> data = analyzer.get_period_data('2024-06-15')
        >>> save_to_database(data)  # Reusable!
    """
    
    def __init__(self, sizing_result: 'SizingResult'):
        """
        Initialize analyzer with sizing result.
        
        Args:
            sizing_result: SizingResult object containing hourly data
        """
        self.result = sizing_result
        self.hourly_data = sizing_result.hourly_data
    
    def analyze_period(
        self,
        start_date: str | pd.Timestamp,
        end_date: str | pd.Timestamp | None = None
    ) -> PeriodAnalysis:
        """
        Analyze PV system performance for a specific time period.
        
        Args:
            start_date: Start date (YYYY-MM-DD or pandas Timestamp)
            end_date: End date (YYYY-MM-DD or pandas Timestamp).
                     If None, assumes single day (start_date only)
        
        Returns:
            PeriodAnalysis object with processed data and statistics
        """
        # Convert to timestamps
        start = pd.Timestamp(start_date)
        
        if end_date is None:
            # Single day analysis
            end = start + pd.Timedelta(days=1) - pd.Timedelta(seconds=1)
        else:
            end = pd.Timestamp(end_date)
        
        # Extract data for the period
        mask = (self.hourly_data.index >= start) & (self.hourly_data.index <= end)
        data = self.hourly_data[mask]
        
        if len(data) == 0:
            raise ValueError(f"No data available for period {start.date()} to {end.date()}")
        
        # Extract time series
        consumption = data['Consumption_kWh']
        pv = data['PV_kWh']
        self_consumed = data['Self_Consumed_kWh']
        grid_import = data['Grid_Import_kWh']
        grid_export = data['Grid_Export_kWh']
        
        # Calculate net grid flow
        net_grid = grid_import - grid_export
        
        # Calculate totals
        total_consumption = consumption.sum()
        total_pv = pv.sum()
        total_self_consumed = self_consumed.sum()
        total_grid_import = grid_import.sum()
        total_grid_export = grid_export.sum()
        total_net_grid = net_grid.sum()
        
        # Calculate self-consumption rate
        self_consumption_rate = (total_self_consumed / total_pv * 100) if total_pv > 0 else 0.0
        
        return PeriodAnalysis(
            period_start=start,
            period_end=end,
            timestamps=data.index,
            consumption_kwh=consumption,
            pv_kwh=pv,
            self_consumed_kwh=self_consumed,
            grid_import_kwh=grid_import,
            grid_export_kwh=grid_export,
            net_grid_kwh=net_grid,
            total_consumption=total_consumption,
            total_pv=total_pv,
            total_self_consumed=total_self_consumed,
            total_grid_import=total_grid_import,
            total_grid_export=total_grid_export,
            total_net_grid=total_net_grid,
            self_consumption_rate=self_consumption_rate
        )
    
    def analyze_summer_week(self, year: int = 2024) -> PeriodAnalysis:
        """Analyze typical summer week (June 1-7)."""
        return self.analyze_period(f'{year}-06-01', f'{year}-06-07')
    
    def analyze_winter_week(self, year: int = 2024) -> PeriodAnalysis:
        """Analyze typical winter week (January 15-21)."""
        return self.analyze_period(f'{year}-01-15', f'{year}-01-21')
    
    def analyze_day(self, date: str) -> PeriodAnalysis:
        """Analyze a specific day."""
        return self.analyze_period(date)
    
    def print_summary(self, analysis: PeriodAnalysis):
        """Print formatted summary of period analysis."""
        print(f"\n   Period Summary ({analysis.period_start.date()} to {analysis.period_end.date()}):")
        print(f"   Total Consumption:    {analysis.total_consumption:>8.1f} kWh")
        print(f"   Total PV Generation:  {analysis.total_pv:>8.1f} kWh")
        print(f"   Self-Consumed:        {analysis.total_self_consumed:>8.1f} kWh ({analysis.self_consumption_rate:.1f}% of PV)")
        print(f"   Grid Import:          {analysis.total_grid_import:>8.1f} kWh")
        print(f"   Grid Export:          {analysis.total_grid_export:>8.1f} kWh")
        print(f"   Net Grid:             {analysis.total_net_grid:>8.1f} kWh")

    def get_monthly_energy_flows(self) -> pd.DataFrame:
        """
        Aggregate energy flows by month for annual overview.
        
        Returns:
            DataFrame with monthly totals for consumption, PV, self-consumed,
            grid import, and grid export.
        """
        monthly = self.hourly_data.resample('ME').sum()
        
        return pd.DataFrame({
            'consumption': monthly['Consumption_kWh'],
            'pv': monthly['PV_kWh'],
            'self_consumed': monthly['Self_Consumed_kWh'],
            'grid_import': monthly['Grid_Import_kWh'],
            'grid_export': monthly['Grid_Export_kWh']
        })
    
    def get_seasonal_daily_profiles(self) -> dict:
        """
        Calculate typical daily PV production profiles for each season.
        
        Returns:
            Dictionary with keys: 'winter', 'spring', 'summer', 'autumn'
            Each value is a Series of average hourly PV production (kWh)
        """
        # Define seasons by month
        seasons = {
            'winter': [12, 1, 2],
            'spring': [3, 4, 5],
            'summer': [6, 7, 8],
            'autumn': [9, 10, 11]
        }
        
        profiles = {}
        
        for season_name, months in seasons.items():
            # Filter data for season months
            mask = self.hourly_data.index.month.isin(months)
            season_data = self.hourly_data[mask]
            
            # Group by hour of day and calculate mean
            profiles[season_name] = season_data.groupby(season_data.index.hour)['PV_kWh'].mean()
        
        return profiles

    def to_dict(self) -> dict:
        """
        Export EVERYTHING from analyzer to dictionary.
        
        Perfect for Spyder/Jupyter inspection - gives you access to ALL data:
        - System configuration and metrics
        - Monthly aggregations
        - Seasonal profiles
        - Full hourly timeseries (8,784+ hours)
        - Pre-computed period analyses (summer/winter weeks/days)
        - Statistical summaries
        
        Returns:
            Comprehensive dictionary with all analyzed data.
            
        Example:
            >>> analyzer_export = analyzer.to_dict()
            >>> # In Spyder, inspect analyzer_export to see everything!
            >>> analyzer_export['system']['kwp']  # 1.88
            >>> analyzer_export['precomputed_analyses']['summer_week']['total_pv']  # 31.3 kWh
            >>> analyzer_export['hourly_data']['pv_generation']  # Full year array
        """
        # Pre-compute common period analyses
        try:
            summer_week = self.analyze_summer_week()
            winter_week = self.analyze_winter_week()
            summer_day = self.analyze_day('2024-06-15')
            winter_day = self.analyze_day('2024-01-15')
            
            precomputed = {
                'summer_week': summer_week.to_dict(),
                'winter_week': winter_week.to_dict(),
                'summer_day': summer_day.to_dict(),
                'winter_day': winter_day.to_dict()
            }
        except:
            precomputed = {}
        
        return {
            # =================================================================
            # SYSTEM CONFIGURATION & METRICS
            # =================================================================
            'system': {
                'kwp': self.result.recommended_kwp,
                'specific_yield_kwh_per_kwp': self.result.specific_yield_kwh_per_kwp,
                'annual_generation_kwh': self.result.annual_generation_kwh,
                'annual_consumption_kwh': self.result.annual_consumption_kwh,
                'self_sufficiency_pct': self.result.self_sufficiency_pct,
                'self_consumption_pct': self.result.self_consumption_pct,
                'annual_grid_import_kwh': self.result.annual_grid_import_kwh,
                'annual_grid_export_kwh': self.result.annual_grid_export_kwh,
                'annual_self_consumed_kwh': self.result.annual_self_consumed_kwh
            },
            
            # =================================================================
            # MONTHLY AGGREGATIONS
            # =================================================================
            'monthly_flows': self.get_monthly_energy_flows().to_dict(orient='list'),
            
            # =================================================================
            # SEASONAL PROFILES (Hourly averages by season)
            # =================================================================
            'seasonal_profiles': {
                season: profile.to_dict()
                for season, profile in self.get_seasonal_daily_profiles().items()
            },
            
            # =================================================================
            # FULL HOURLY TIMESERIES DATA (All 8,784+ hours)
            # =================================================================
            'hourly_data': {
                'timestamps': self.hourly_data.index.tolist(),
                'consumption_kwh': self.hourly_data['Consumption_kWh'].tolist(),
                'pv_generation_kwh': self.hourly_data['PV_kWh'].tolist(),
                'self_consumed_kwh': self.hourly_data['Self_Consumed_kWh'].tolist(),
                'grid_import_kwh': self.hourly_data['Grid_Import_kWh'].tolist(),
                'grid_export_kwh': self.hourly_data['Grid_Export_kWh'].tolist(),
                'net_grid_kwh': (self.hourly_data['Grid_Import_kWh'] - self.hourly_data['Grid_Export_kWh']).tolist()
            },
            
            # =================================================================
            # PRE-COMPUTED PERIOD ANALYSES
            # =================================================================
            'precomputed_analyses': precomputed,
            
            # =================================================================
            # METADATA
            # =================================================================
            'metadata': {
                'total_hours': len(self.hourly_data),
                'start_date': str(self.hourly_data.index[0]),
                'end_date': str(self.hourly_data.index[-1]),
                'data_resolution': 'hourly',
                'year': self.hourly_data.index[0].year,
                'is_leap_year': self.hourly_data.index[0].is_leap_year
            }
        }
