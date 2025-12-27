"""
PV System Behavior Plotter
===========================
Pure visualization layer for PV system behavior analysis.

This plotter ONLY handles visual formatting and rendering.
All data processing is done by PVSystemAnalyzer.

Follows Single Responsibility Principle:
- Plotter: Visual formatting only
- Analyzer: Data processing only
- SizingResult: Data storage only
"""

from __future__ import annotations
from typing import Optional
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import numpy as np
from scipy.interpolate import make_interp_spline

try:
    from eclipse.simulation.analyzer import PeriodAnalysis
    from eclipse.simulation.system_sizer import SizingResult
except ImportError:
    PeriodAnalysis = None  # For type hints only
    SizingResult = None # For type hints only


class PVSystemBehaviorPlotter:
    """
    Pure visualization for PV system behavior.
    
    **Design Philosophy**:
   - This class is **stateless** (only static methods)
    - Accepts **pre-processed data** from PVSystemAnalyzer
    - Does **NO data processing** - only visual formatting
    - Can be reused for any similar data structure
    
    Example:
        >>> from eclipse.simulation.analyzer import PVSystemAnalyzer
        >>> from eclipse.plotting import PVSystemBehaviorPlotter
        >>> 
        >>> # Step 1: Process data (business logic)
        >>> analyzer = PVSystemAnalyzer(sizing_result)
        >>> period_data = analyzer.analyze_period('2024-06-01', '2024-06-07')
        >>> 
        >>> # Step 2: Visualize (presentation logic)
        >>> PVSystemBehaviorPlotter.plot(period_data, 
        >>>                               title='Summer Week',
        >>>                               output_path='summer.png')
        >>> 
        >>> # Data can be reused for other purposes!
        >>> save_to_database(period_data)
        >>> export_to_csv(period_data)
    """
    
    @staticmethod
    def plot(
        analysis: 'PeriodAnalysis',
        title: str = "PV System Behavior",
        output_path: Optional[str] = None,
        figsize: tuple = (14, 10),
        show_stats: bool = True
    ) -> Optional[str]:
        """
        Plot comprehensive system behavior from pre-processed data.
        
        Creates 3 subplots:
        1. Load vs PV Generation with self-consumption fill
        2. Consumption breakdown (self-consumed vs grid import)
        3. Grid import/export with net flow
        
        Args:
            analysis: PeriodAnalysis object with processed data
            title: Plot title suffix
            output_path: Path to save figure. If None, displays interactively.
            figsize: Figure size (width, height) in inches
            show_stats: If True, print period statistics
            
        Returns:
            Path to saved figure if output_path provided, else None.
        """
        # Create figure with 3 subplots
        fig, axes = plt.subplots(3, 1, figsize=figsize, sharex=True)
        
        # ========== Plot 1: Load vs PV Generation ==========
        ax1 = axes[0]
        ax1.plot(analysis.timestamps, analysis.consumption_kwh, label='Consumption', 
                 color='#004E89', linewidth=1.5, drawstyle='steps-post')
        ax1.plot(analysis.timestamps, analysis.pv_kwh, label='PV Production', 
                 color='#FF6B35', linewidth=1.5, alpha=0.8, drawstyle='steps-post')
        
        # Fill self-consumption area  
        ax1.fill_between(analysis.timestamps, 0, analysis.self_consumed_kwh, 
                          color='#90EE90', alpha=0.4, label='Self-Consumption', step='post')
        
        # Determine if this is a single day (for better formatting)
        duration_hours = (analysis.period_end - analysis.period_start).total_seconds() / 3600
        is_single_day = duration_hours <= 48  # Single day or less
        
        # Set Y-axis label based on data resolution
        if is_single_day:
            ax1.set_ylabel('Power (kW)', fontsize=11, fontweight='bold')
        else:
            ax1.set_ylabel('Energy (kWh)', fontsize=11, fontweight='bold')
        
        ax1.set_title(f'PV System Behavior - {title}', 
                      fontsize=13, fontweight='bold')
        ax1.legend(loc='upper right', fontsize=9)
        ax1.grid(True, alpha=0.3)
        
        # ========== Plot 2: Energy Flow Breakdown ==========
        ax2 = axes[1]
        
        # Stack plot showing energy breakdown
        ax2.fill_between(analysis.timestamps, 0, analysis.self_consumed_kwh,
                          color='#90EE90', alpha=0.6, label='Self-Consumed from PV', step='post')
        ax2.fill_between(analysis.timestamps, analysis.self_consumed_kwh, 
                          analysis.consumption_kwh,
                          color='#FFB6C1', alpha=0.6, label='Grid Import', step='post')
        
        ax2.set_ylabel('Consumption\nBreakdown (kWh)', fontsize=11, fontweight='bold')
        ax2.legend(loc='upper right', fontsize=9)
        ax2.grid(True, alpha=0.3)
        
        # ========== Plot 3: Grid Import/Export ==========
        ax3 = axes[2]
        
        # Plot net grid flow
        ax3.plot(analysis.timestamps, analysis.net_grid_kwh, label='Net Grid', 
                 color='#666666', linewidth=1.2, drawstyle='steps-post')
        
        # Fill import (positive values) in orange
        ax3.fill_between(analysis.timestamps, np.maximum(analysis.net_grid_kwh, 0), 0, 
                          color='#FFB366', alpha=0.5, label='Import',
                          step='post')
        
        # Fill export (negative values) in cyan
        ax3.fill_between(analysis.timestamps, np.minimum(analysis.net_grid_kwh, 0), 0, 
                          color='#66D9EF', alpha=0.5, label='Export',
                          step='post')
        
        ax3.axhline(y=0, color='black', linestyle='--', linewidth=0.8, alpha=0.5)
        ax3.set_ylabel('Grid (kWh)', fontsize=11, fontweight='bold')
        ax3.set_xlabel('Date/Time', fontsize=11, fontweight='bold')
        ax3.legend(loc='upper right', fontsize=9)
        ax3.grid(True, alpha=0.3)
        
        # Format X-axis based on time span
        if is_single_day:
            # For single day: show HH:MM format
            ax3.xaxis.set_major_formatter(mdates.DateFormatter('%H:%M'))
            ax3.xaxis.set_major_locator(mdates.HourLocator(interval=2))
            ax3.xaxis.set_minor_locator(mdates.HourLocator(interval=1))
        else:
            # For multi-day: show date format (e.g., 'Mar 15')
            ax3.xaxis.set_major_formatter(mdates.DateFormatter('%b %d'))
            ax3.xaxis.set_major_locator(mdates.DayLocator())
        
        plt.tight_layout()
        
        # Save or show plot
        if output_path:
            plt.savefig(output_path, dpi=150, bbox_inches='tight')
            plt.close()
            if show_stats:
                print(f"   ✓ Saved: {output_path}")
        else:
            plt.show()
        
        # Print summary statistics if requested
        if show_stats:
            PVSystemBehaviorPlotter._print_stats(analysis)
        
        return output_path
    
    @staticmethod
    def _print_stats(analysis: 'PeriodAnalysis'):
        """Print formatted summary statistics."""
        print(f"\n   Period Summary ({analysis.period_start.date()} to {analysis.period_end.date()}):")
        print(f"   Total Consumption:    {analysis.total_consumption:>8.1f} kWh")
        print(f"   Total PV Generation:  {analysis.total_pv:>8.1f} kWh")
        print(f"   Self-Consumed:        {analysis.total_self_consumed:>8.1f} kWh ({analysis.self_consumption_rate:.1f}% of PV)")
        print(f"   Grid Import:          {analysis.total_grid_import:>8.1f} kWh")
        print(f"   Grid Export:          {analysis.total_grid_export:>8.1f} kWh")
        print(f"   Net Grid:             {analysis.total_net_grid:>8.1f} kWh")

    @staticmethod
    def plot_monthly_energy_flows(
        monthly_data: 'pd.DataFrame',
        sizing_result: 'SizingResult',
        output_path: Optional[str] = None,
        figsize: tuple = (14, 10)
    ) -> Optional[str]:
        """
        Plot monthly energy flows with 2 panels: energy flows + grid import/export.
        
        Args:
            monthly_data: DataFrame with columns: consumption, pv, self_consumed, grid_import, grid_export
            sizing_result: SizingResult object with system metrics
            output_path: Path to save figure
            figsize: Figure size
            
        Returns:
            Path to saved figure if output_path provided, else None.
        """
        import matplotlib.pyplot as plt
        
        fig, (ax1, ax2) = plt.subplots(2, 1, figsize=figsize, sharex=True)
        
        # ========== Panel 1: Monthly Energy Flows ==========
        months = range(1, 13)
        month_names = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun',
                       'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
        
        x = range(len(months))
        width = 0.25
        
        ax1.bar([i - width for i in x], monthly_data['consumption'], 
                width, label='Consumption', color='#6B9BD1', alpha=0.8)
        ax1.bar(x, monthly_data['pv'], 
                width, label='PV Generation', color='#F4B942', alpha=0.8)
        ax1.bar([i + width for i in x], monthly_data['self_consumed'],
                width, label='Self-Consumed', color='#7FBA7A', alpha=0.8)
        
        ax1.set_ylabel('Energy (kWh)', fontsize=11)
        ax1.set_title(
            f'Monthly Energy Flows - {sizing_result.recommended_kwp:.2f} kWp System\n'
            f'Self-Sufficiency: {sizing_result.self_sufficiency_pct:.1f}% | Annual: {sizing_result.annual_generation_kwh:.0f} kWh PV, {sizing_result.annual_consumption_kwh:.0f} kWh Load',
            fontsize=12, fontweight='bold'
        )
        ax1.legend(loc='upper left', fontsize=9)
        ax1.grid(True, alpha=0.3, axis='y')
        
        # Add system info box
        info_text = (
            f'System: {sizing_result.recommended_kwp:.2f} kWp\n'
            f'Yield: {sizing_result.specific_yield_kwh_per_kwp:.0f} kWh/kWp/yr\n'
            f'Annual Import: {sizing_result.annual_grid_import_kwh:.0f} kWh\n'
            f'Annual Export: {sizing_result.annual_grid_export_kwh:.0f} kWh'
        )
        ax1.text(0.98, 0.97, info_text,
                transform=ax1.transAxes,
                fontsize=9,
                verticalalignment='top',
                horizontalalignment='right',
                bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.3))
        
        # ========== Panel 2: Grid Import vs Export ==========
        ax2.bar([i - width/2 for i in x], monthly_data['grid_import'],
                width, label='Grid Import', color='#E57373', alpha=0.8)
        ax2.bar([i + width/2 for i in x], monthly_data['grid_export'],
                width, label='Grid Export', color='#81C784', alpha=0.8)
        
        ax2.set_xlabel('Month', fontsize=11)
        ax2.set_ylabel('Energy (kWh)', fontsize=11)
        ax2.set_title('Grid Import vs Export', fontsize=11, fontweight='bold')
        ax2.set_xticks(x)
        ax2.set_xticklabels(month_names)
        ax2.legend(loc='upper left', fontsize=9)
        ax2.grid(True, alpha=0.3, axis='y')
        
        plt.tight_layout()
        
        if output_path:
            plt.savefig(output_path, dpi=150, bbox_inches='tight')
            plt.close()
            print(f"   ✓ Saved: {output_path}")
        else:
            plt.show()
        
        return output_path
    
    @staticmethod
    def plot_seasonal_daily_profiles(
        seasonal_profiles: dict,
        sizing_result: 'SizingResult',
        output_path: Optional[str] = None,
        figsize: tuple = (12, 6),
        smooth: bool = True
    ) -> Optional[str]:
        """
        Plot typical hourly PV production profiles for each season.
        
        Args:
            seasonal_profiles: Dict with keys 'winter', 'spring', 'summer', 'autumn'
                              Each value is a Series of hourly averages
            sizing_result: SizingResult object with system metrics
            output_path: Path to save figure
            figsize: Figure size
            
        Returns:
            Path to saved figure if output_path provided, else None.
        """
        import matplotlib.pyplot as plt
        
        fig, ax = plt.subplots(figsize=figsize)
        
        colors = {
            'winter': '#5DADE2',
            'spring': '#52BE80',
            'summer': '#EC7063',
            'autumn': '#F39C12'
        }
        
        labels = {
            'winter': 'Winter',
            'spring': 'Spring',
            'summer': 'Summer',
            'autumn': 'Autumn'
        }
        
        # Plot each season
        for season in ['winter', 'spring', 'summer', 'autumn']:
            profile = seasonal_profiles[season]
            x = profile.index.values
            y = profile.values
            
            if smooth and len(x) > 3:
                # Create a smoother x-axis (200 points)
                x_smooth = np.linspace(x.min(), x.max(), 200)
                # Apply cubic spline interpolation
                spline = make_interp_spline(x, y, k=3)
                y_smooth = spline(x_smooth)
                # Generation cannot be negative
                y_smooth = np.maximum(y_smooth, 0)
                
                ax.plot(x_smooth, y_smooth, 
                       label=labels[season], color=colors[season], 
                       linewidth=2.5, alpha=0.9)
            else:
                ax.plot(x, y, 
                       label=labels[season], color=colors[season], 
                       linewidth=2.5, alpha=0.9)
        
        ax.set_xlabel('Hours of Day', fontsize=12, fontweight='bold')
        ax.set_ylabel('Average PV Generation (kWh)', fontsize=12, fontweight='bold')
        ax.set_title(
            f'Seasonal Daily PV Production Profile ({sizing_result.recommended_kwp:.2f} kWp System)\n'
            f'Typical Hourly Generation Throughout the Day',
            fontsize=13, fontweight='bold'
        )
        ax.set_xlim(0, 23)
        
        # Format X-axis as HH:MM time
        hour_ticks = range(0, 25, 2)  # Every 2 hours: 0, 2, 4, ..., 24
        time_labels = [f'{h:02d}:00' for h in hour_ticks]
        ax.set_xticks(hour_ticks)
        ax.set_xticklabels(time_labels)
        
        ax.legend(loc='upper right', fontsize=10)
        ax.grid(True, alpha=0.3)
        
        # Add system info box
        info_text = (
            f'System Size: {sizing_result.recommended_kwp:.2f} kWp\n'
            f'Annual Yield: {sizing_result.annual_generation_kwh:.0f} kWh\n'
            f'Specific Yield: {sizing_result.specific_yield_kwh_per_kwp:.0f} kWh/kWp/yr'
        )
        ax.text(0.02, 0.98, info_text,
                transform=ax.transAxes,
                fontsize=9,
                verticalalignment='top',
                bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.3))
        
        plt.tight_layout()
        
        if output_path:
            plt.savefig(output_path, dpi=150, bbox_inches='tight')
            plt.close()
            print(f"   ✓ Saved: {output_path}")
        else:
            plt.show()
        
        return output_path
