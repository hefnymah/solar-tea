"""
Consumption Plotter Module
==========================
Provides separated plotting logic for consumption data visualization.

Example Usage:
    from eclipse.consumption import ConsumptionData, ConsumptionPlotter
    
    data = ConsumptionData.load("path/to/consumption.csv")
    plotter = ConsumptionPlotter(data, output_dir="./output")
    plotter.plot_all()
"""

from __future__ import annotations

import os
from typing import Optional, Dict, Any, TYPE_CHECKING

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

if TYPE_CHECKING:
    from eclipse.consumption.data import ConsumptionData

from eclipse.consumption.data import TimeSeriesAccessor


class ConsumptionPlotter:
    """
    Visualization class for consumption data.
    
    Separates plotting logic from data handling for maintainability.
    All plot methods can be overridden in subclasses for customization.
    
    Attributes:
        data: The ConsumptionData object to visualize.
        output_dir: Directory to save generated plots.
        season_colors: Color mapping for seasons.
    """
    
    # Default color scheme
    SEASON_COLORS = {
        'winter': 'blue',
        'spring': 'green',
        'summer': 'red',
        'autumn': 'orange'
    }
    
    # Seasonal representative weeks (Month, Day)
    SEASONAL_WEEKS = {
        'winter': (1, 15),
        'spring': (4, 15),
        'summer': (7, 15),
        'autumn': (10, 15)
    }
    
    def __init__(
        self, 
        data: 'ConsumptionData', 
        output_dir: Optional[str] = None,
        season_colors: Optional[Dict[str, str]] = None,
        seasonal_weeks: Optional[Dict[str, tuple]] = None
    ):
        """
        Initialize the plotter.
        
        Args:
            data: ConsumptionData object.
            output_dir: Output directory for saved plots.
            season_colors: Optional custom color mapping.
            seasonal_weeks: Optional custom week definitions (month, day) per season.
        """
        self._data = data
        self.output_dir = output_dir or 'output'
        self.season_colors = season_colors or self.SEASON_COLORS.copy()
        self.seasonal_weeks = seasonal_weeks or self.SEASONAL_WEEKS.copy()
    
    @property
    def data(self) -> 'ConsumptionData':
        """Returns the associated data object."""
        return self._data
    
    def _ensure_output_dir(self) -> None:
        """Creates output directory if it doesn't exist."""
        os.makedirs(self.output_dir, exist_ok=True)
    
    def _save_figure(self, fig: plt.Figure, filename: str) -> str:
        """Saves figure and returns the path."""
        self._ensure_output_dir()
        path = os.path.join(self.output_dir, filename)
        fig.savefig(path)
        plt.close(fig)
        return path
    
    def plot_all(self, prefix: str = '') -> Dict[str, str]:
        """
        Generates all standard plots.
        
        Args:
            prefix: Filename prefix for all plots.
            
        Returns:
            Dictionary mapping plot names to file paths.
        """
        prefix = f"{prefix}_" if prefix else ""
        
        paths = {}
        paths['monthly'] = self.plot_monthly(f"{prefix}monthly_consumption.png")
        paths['extreme_weeks'] = self.plot_extreme_weeks(f"{prefix}extreme_weeks_profile.png")
        paths['seasonal_weeks'] = self.plot_seasonal_weeks(f"{prefix}seasonal_weeks_profile.png")
        paths['seasonal_daily'] = self.plot_seasonal_daily_profile(f"{prefix}seasonal_daily_profile.png")
        paths['heatmap'] = self.plot_heatmap(f"{prefix}consumption_heatmap.png")
        
        return paths
    
    def plot_monthly(self, filename: str = 'monthly_consumption.png') -> str:
        """
        Plots monthly consumption bar chart.
        
        Args:
            filename: Output filename.
            
        Returns:
            Path to saved plot.
        """
        monthly = self._data.monthly
        annual_kwh = monthly.sum()
        
        fig, ax = plt.subplots(figsize=(10, 6))
        
        # Create bar chart
        x = range(len(monthly.dataframe))
        ax.bar(x, monthly.values, color='steelblue', edgecolor='black')
        
        # Format x-axis with month names
        month_labels = [d.strftime('%b') for d in monthly.index]
        ax.set_xticks(x)
        ax.set_xticklabels(month_labels, rotation=0)
        
        ax.set_title(f"Monthly Consumption (Total: {annual_kwh:.0f} kWh)")
        ax.set_ylabel("Energy (kWh)")
        ax.set_xlabel("Month")
        ax.grid(axis='y', alpha=0.3)
        
        plt.tight_layout()
        return self._save_figure(fig, filename)
    
    def plot_extreme_weeks(self, filename: str = 'extreme_weeks_profile.png') -> str:
        """
        Plots the weeks with maximum and minimum total consumption.
        
        Args:
            filename: Output filename.
            
        Returns:
            Path to saved plot.
        """
        # Get extreme weeks data from ConsumptionData
        extremes = self._data.get_extreme_weeks()
        max_week = extremes['max_week']
        min_week = extremes['min_week']
        max_dates = extremes['max_dates']
        min_dates = extremes['min_dates']
        
        fig, ax = plt.subplots(figsize=(12, 6))
        
        if len(max_week) > 0:
            x_max = np.arange(len(max_week))
            ax.plot(x_max, max_week.values, color='red', 
                   label=f"Max Week ({max_dates[0].strftime('%b %d')} - {max_dates[1].strftime('%b %d')})", 
                   linewidth=2)
        
        if len(min_week) > 0:
            x_min = np.arange(len(min_week))
            ax.plot(x_min, min_week.values, color='green',
                   label=f"Min Week ({min_dates[0].strftime('%b %d')} - {min_dates[1].strftime('%b %d')})",
                   linewidth=2)
        
        ax.set_title("Extreme Weeks Consumption Analysis (High vs Low)")
        ax.set_ylabel("Consumption (kWh)")
        ax.set_xlabel("Day of Week")
        
        ticks = np.arange(0, 168 + 24, 24)
        labels = [f"Day {i+1}" for i in range(len(ticks))]
        ax.set_xticks(ticks)
        ax.set_xticklabels(labels)
        
        ax.grid(True, linestyle='--', alpha=0.5)
        ax.legend()
        plt.tight_layout()
        
        return self._save_figure(fig, filename)
    
    def plot_seasonal_weeks(
        self, 
        filename: str = 'seasonal_weeks_profile.png',
        seasonal_weeks: Optional[Dict[str, tuple]] = None
    ) -> str:
        """
        Plots a representative week for each season with smooth curves.
        
        Args:
            filename: Output filename.
            seasonal_weeks: Optional dict to override week definitions.
                           Format: {'winter': (month, day), 'spring': (month, day), ...}
                           If not provided, uses defaults from __init__.
            
        Returns:
            Path to saved plot.
        """
        # Use provided weeks or fall back to instance defaults
        weeks_to_use = seasonal_weeks or self.seasonal_weeks
        
        fig, axes = plt.subplots(4, 1, figsize=(12, 16), sharey=False)
        season_order = ['winter', 'spring', 'summer', 'autumn']
        
        for i, season in enumerate(season_order):
            ax = axes[i]
            
            if season in weeks_to_use:
                month, day = weeks_to_use[season]
                # Get typical week using data.py method
                week_data = self._data.seasons.get_typical_week(season, month, day)
                
                if len(week_data) > 0:
                    df = week_data.dataframe
                    y = week_data.values
                    color = self.season_colors.get(season, 'black')
                    
                    # Scatter plot for raw data
                    ax.scatter(df.index, y, color=color, alpha=0.3, s=10)
                    
                    # Get smoothed data using new method
                    try:
                        smoothed = week_data.smooth(method='spline', points=500)
                        ax.plot(smoothed.index, smoothed[self._data.VALUE_COL], 
                               color=color, linewidth=2, label=f"{season.title()} (Smooth)")
                    except Exception:
                        # Fallback to non-smoothed
                        ax.plot(df.index, y, color=color, linewidth=2, label=season.title())
                    
                    start_date = df.index[0]
                    end_date = df.index[-1]
                    ax.set_title(f"{season.title()} Week ({start_date.date()} - {end_date.date()})")
                    ax.set_ylabel("kWh")
                    ax.grid(True, alpha=0.3)
                else:
                    ax.text(0.5, 0.5, "No Data", ha='center', va='center', transform=ax.transAxes)
                    ax.set_title(f"{season.title()} Week - N/A")
            else:
                ax.text(0.5, 0.5, "Config Missing", ha='center', va='center', transform=ax.transAxes)
        
        plt.tight_layout()
        return self._save_figure(fig, filename)
    
    def plot_seasonal_daily_profile(self, filename: str = 'seasonal_daily_profile.png') -> str:
        """
        Plots typical daily load profile by season.
        
        Args:
            filename: Output filename.
            
        Returns:
            Path to saved plot.
        """
        profile = self._data.seasons.profile
        
        fig, ax = plt.subplots(figsize=(10, 6))
        
        for season in profile.columns:
            # Create TimeSeriesAccessor for smoothing
            season_profile = pd.DataFrame({self._data.VALUE_COL: profile[season].values}, 
                                         index=pd.date_range('2024-01-01', periods=24, freq='h'))
            accessor = TimeSeriesAccessor(season_profile, self._data.VALUE_COL)
            
            color = self.season_colors.get(season, 'black')
            
            # Smooth the daily profile
            try:
                smoothed = accessor.smooth(method='spline', points=300)
                hours_smooth = np.linspace(0, 23, 300)
                ax.plot(hours_smooth, smoothed[self._data.VALUE_COL].values, 
                       label=season.title(), color=color, linewidth=2)
            except Exception:
                # Fallback to non-smoothed
                x = np.arange(24)
                ax.plot(x, profile[season].values, label=season.title(), color=color, linewidth=2)
        
        ax.set_title("Typical Daily Load Profile by Season")
        ax.set_xlabel("Hour of Day")
        ax.set_ylabel("Average Consumption (kWh)")
        ax.set_xticks(range(0, 24))
        ax.grid(True, linestyle='--', alpha=0.5)
        ax.legend()
        
        plt.tight_layout()
        return self._save_figure(fig, filename)
    
    def plot_heatmap(self, filename: str = 'consumption_heatmap.png') -> str:
        """
        Plots consumption heatmap (Hour vs Day of Year).
        
        Args:
            filename: Output filename.
            
        Returns:
            Path to saved plot.
        """
        hourly = self._data.hourly.dataframe
        value_col = self._data.VALUE_COL
        
        # Create pivot table
        df_with_hour = hourly.copy()
        df_with_hour['Hour'] = df_with_hour.index.hour
        pivoted = df_with_hour.pivot_table(
            index=df_with_hour.index.date, 
            columns='Hour', 
            values=value_col
        )
        
        if pivoted.empty:
            fig, ax = plt.subplots()
            ax.text(0.5, 0.5, "No Data", ha='center', va='center')
            return self._save_figure(fig, filename)
        
        fig, ax = plt.subplots(figsize=(12, 8))
        im = ax.imshow(pivoted.T, aspect='auto', cmap='plasma', origin='upper',
                       extent=[0, len(pivoted), 24, 0])
        plt.colorbar(im, label='kWh')
        
        ax.set_title("Consumption Heatmap (Hour vs Day)")
        ax.set_ylabel("Hour of Day")
        ax.set_xlabel("Day of Year")
        
        plt.tight_layout()
        return self._save_figure(fig, filename)
    
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
            Path to saved plot if output_path provided, else None.
        """
        data_slice = self._data.slice(start_date, end_date)
        
        if len(data_slice) == 0:
            print(f"No data found for range {start_date} to {end_date}")
            return None
        
        start = pd.to_datetime(start_date)
        end = pd.to_datetime(end_date)
        days_span = (end - start).days
        
        fig, ax = plt.subplots(figsize=(12, 6))
        
        df = data_slice.dataframe
        y = data_slice.values
        value_col = self._data.VALUE_COL
        
        if days_span == 0:
            # Single day: bar chart
            hours = df.index.hour
            ax.bar(hours, y, color='steelblue', edgecolor='darkblue', alpha=0.7, width=0.8)
            
            if smooth and len(hours) > 3:
                try:
                    from scipy.interpolate import make_interp_spline
                    x = np.arange(len(hours))
                    x_smooth = np.linspace(0, len(hours)-1, 200)
                    spl = make_interp_spline(x, y, k=3)
                    y_smooth = np.maximum(spl(x_smooth), 0)
                    hours_smooth = np.linspace(hours.min(), hours.max(), 200)
                    ax.plot(hours_smooth, y_smooth, color='red', linewidth=2, label='Trend', alpha=0.8)
                    ax.legend()
                except Exception:
                    pass
            
            ax.set_xlabel("Hour of Day")
            ax.set_xticks(range(0, 24))
            ax.set_xlim(-0.5, 23.5)
            
            if title is None:
                title = f"Hourly Consumption - {start.strftime('%b %d, %Y')}"
        else:
            # Multi-day: time series
            x = np.arange(len(df))
            ax.scatter(df.index, y, color='steelblue', alpha=0.3, s=10)
            
            if smooth and len(x) > 3:
                try:
                    from scipy.interpolate import make_interp_spline
                    x_smooth = np.linspace(x.min(), x.max(), min(500, len(x)*10))
                    spl = make_interp_spline(x, y, k=3)
                    y_smooth = np.maximum(spl(x_smooth), 0)
                    time_smooth = pd.date_range(start=df.index[0], end=df.index[-1], periods=len(x_smooth))
                    ax.plot(time_smooth, y_smooth, color='darkblue', linewidth=2, label='Consumption (Smoothed)')
                except Exception:
                    ax.plot(df.index, y, color='darkblue', linewidth=2, label='Consumption')
            else:
                ax.plot(df.index, y, color='darkblue', linewidth=2, label='Consumption')
            
            if title is None:
                days = days_span + 1
                title = f"Consumption: {start.strftime('%b %d, %Y')} - {end.strftime('%b %d, %Y')} ({days} days)"
            
            # Format x-axis
            import matplotlib.dates as mdates
            if days_span <= 7:
                ax.xaxis.set_major_formatter(mdates.DateFormatter('%b %d\n%H:%M'))
            elif days_span <= 60:
                ax.xaxis.set_major_formatter(mdates.DateFormatter('%b %d'))
            else:
                ax.xaxis.set_major_locator(mdates.WeekdayLocator())
                ax.xaxis.set_major_formatter(mdates.DateFormatter('%b %d'))
            
            ax.set_xlabel("Date")
            ax.legend()
            plt.xticks(rotation=45)
        
        ax.set_title(title)
        ax.set_ylabel("Consumption (kWh)")
        ax.grid(True, linestyle='--', alpha=0.5)
        
        plt.tight_layout()
        
        if output_path:
            fig.savefig(output_path)
            plt.close(fig)
            return output_path
        else:
            plt.show()
            return None
