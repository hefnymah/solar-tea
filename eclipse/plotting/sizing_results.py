"""
PV Sizing Results Plotter Module
=================================
Visualization functions for PV system sizing results.

Separates plotting logic from data structures for better maintainability.
"""

from __future__ import annotations

from typing import Optional, TYPE_CHECKING
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import numpy as np

if TYPE_CHECKING:
    from eclipse.simulation.system_sizer import SizingResult


class SizingResultPlotter:
    """
    Visualization class for PV sizing results.
    
    Provides various plotting methods for analyzing PV system performance
    and comparing generation with consumption.
    
    Example:
        from eclipse.plotting import SizingResultPlotter
        
        plotter = SizingResultPlotter(result)
        plotter.plot_monthly_comparison(output_path="comparison.png")
    """
    
    def __init__(self, result: 'SizingResult'):
        """
        Initialize plotter with sizing result.
        
        Args:
            result: SizingResult object to visualize.
        """
        self._result = result
    
    def plot_monthly_comparison(
        self,
        output_path: Optional[str] = None,
        figsize: tuple = (12, 10),
        show_self_consumed: bool = True
    ) -> Optional[str]:
        """
        Plots monthly PV generation vs consumption with grid flows.
        
        Creates a two-panel visualization:
        - Top: Monthly consumption vs PV generation
        - Bottom: Monthly grid import vs export
        
        Args:
            output_path: Path to save figure. If None, displays interactively.
            figsize: Figure size (width, height) in inches.
            show_self_consumed: If True, shows self-consumed energy as overlay.
            
        Returns:
            Path to saved figure if output_path provided, else None.
        """
        fig, (ax1, ax2) = plt.subplots(2, 1, figsize=figsize, 
                                        gridspec_kw={'height_ratios': [3, 2]})
        
        # Extract monthly data
        months = self._result.monthly_profile.index
        month_labels = [d.strftime('%b') for d in months]
        
        consumption = self._result.monthly_profile['Consumption_kWh'].values
        pv_generation = self._result.monthly_profile['PV_kWh'].values
        grid_import = self._result.monthly_profile['Grid_Import_kWh'].values
        grid_export = self._result.monthly_profile['Grid_Export_kWh'].values
        
        # Bar positions
        x = np.arange(len(month_labels))
        width = 0.35
        
        # === TOP PANEL: Consumption vs PV Generation ===
        bars1 = ax1.bar(x - width/2, consumption, width, 
                       label='Consumption', color='steelblue', alpha=0.8, edgecolor='black')
        bars2 = ax1.bar(x + width/2, pv_generation, width,
                       label='PV Generation', color='gold', alpha=0.8, edgecolor='black')
        
        # Optionally show self-consumed as overlay
        if show_self_consumed:
            self_consumed = self._result.monthly_profile['Self_Consumed_kWh'].values
            ax1.bar(x - width/2, self_consumed, width,
                   color='darkgreen', alpha=0.5, label='Self-Consumed')
        
        ax1.set_ylabel('Energy (kWh)', fontsize=11)
        ax1.set_title(
            f'Monthly Energy Flows - {self._result.recommended_kwp} kWp System\n'
            f'Self-Sufficiency: {self._result.self_sufficiency_pct:.1f}% | '
            f'Annual: {self._result.annual_generation_kwh:.0f} kWh PV, {self._result.annual_consumption_kwh:.0f} kWh Load',
            fontsize=12, fontweight='bold'
        )
        ax1.set_xticks(x)
        ax1.set_xticklabels([])  # Remove x-labels from top plot
        ax1.legend(loc='upper left')
        ax1.grid(axis='y', alpha=0.3, linestyle='--')
        
        # Add metrics text box to top panel
        textstr = '\n'.join((
            f'System: {self._result.recommended_kwp} kWp',
            f'Yield: {self._result.specific_yield_kwh_per_kwp:.0f} kWh/kWp/yr',
            f'Annual Import: {self._result.annual_grid_import_kwh:.0f} kWh',
            f'Annual Export: {self._result.annual_grid_export_kwh:.0f} kWh'
        ))
        props = dict(boxstyle='round', facecolor='wheat', alpha=0.7)
        ax1.text(0.98, 0.97, textstr, transform=ax1.transAxes, fontsize=9,
                verticalalignment='top', horizontalalignment='right', bbox=props)
        
        # === BOTTOM PANEL: Grid Import vs Export ===
        bars3 = ax2.bar(x - width/2, grid_import, width,
                       label='Grid Import', color='crimson', alpha=0.7, edgecolor='black')
        bars4 = ax2.bar(x + width/2, grid_export, width,
                       label='Grid Export', color='limegreen', alpha=0.7, edgecolor='black')
        
        ax2.set_xlabel('Month', fontsize=11)
        ax2.set_ylabel('Energy (kWh)', fontsize=11)
        ax2.set_title('Grid Import vs Export', fontsize=11, fontweight='bold')
        ax2.set_xticks(x)
        ax2.set_xticklabels(month_labels)
        ax2.legend(loc='upper left')
        ax2.grid(axis='y', alpha=0.3, linestyle='--')
        
        plt.tight_layout()
        
        if output_path:
            fig.savefig(output_path, dpi=150, bbox_inches='tight')
            plt.close(fig)
            return output_path
        else:
            plt.show()
            return None
    
    def plot_seasonal_daily_production(
        self,
        output_path: Optional[str] = None,
        figsize: tuple = (14, 8)
    ) -> Optional[str]:
        """
        Plots typical daily PV production profiles for each season.
        
        Creates a professional line plot showing how PV generation varies
        throughout the day across different seasons.
        
        Args:
            output_path: Path to save figure. If None, displays interactively.
            figsize: Figure size (width, height) in inches.
            
        Returns:
            Path to saved figure if output_path provided, else None.
        """
        # Season definitions (matching consumption module)
        SEASON_MONTHS = {
            'winter': [12, 1, 2],
            'spring': [3, 4, 5],
            'summer': [6, 7, 8],
            'autumn': [9, 10, 11]
        }
        
        # Professional color scheme
        season_colors = {
            'winter': '#3498db',    # Blue
            'spring': '#2ecc71',    # Green
            'summer': '#e74c3c',    # Red
            'autumn': '#f39c12'     # Orange
        }
        
        # Extract hourly PV data
        hourly_pv = self._result.hourly_data.copy()
        hourly_pv['month'] = hourly_pv.index.month
        hourly_pv['hour'] = hourly_pv.index.hour
        
        # Calculate typical daily profile for each season
        seasonal_profiles = {}
        for season, months in SEASON_MONTHS.items():
            # Filter data for this season
            season_mask = hourly_pv['month'].isin(months)
            season_data = hourly_pv[season_mask]
            
            # Average by hour of day
            if not season_data.empty:
                profile = season_data.groupby('hour')['PV_kWh'].mean()
                seasonal_profiles[season] = profile
        
        # Create plot
        fig, ax = plt.subplots(figsize=figsize)
        
        # Import smooth interpolation
        from scipy.interpolate import make_interp_spline
        
        # Plot each season
        season_order = ['winter', 'spring', 'summer', 'autumn']
        for season in season_order:
            if season in seasonal_profiles:
                profile = seasonal_profiles[season]
                hours = profile.index.values
                values = profile.values
                
                # Smooth interpolation for professional look
                if len(hours) > 3:
                    hours_smooth = np.linspace(hours.min(), hours.max(), 200)
                    spl = make_interp_spline(hours, values, k=3)
                    values_smooth = np.maximum(spl(hours_smooth), 0)  # Prevent negative
                    
                    ax.plot(hours_smooth, values_smooth, 
                           color=season_colors[season],
                           linewidth=2.5,
                           label=season.title(),
                           alpha=0.9)
                else:
                    # Fallback for insufficient data
                    ax.plot(hours, values, 
                           color=season_colors[season],
                           linewidth=2.5,
                           label=season.title(),
                           alpha=0.9)
        
        # Styling
        ax.set_xlabel('Hour of Day', fontsize=12, fontweight='bold')
        ax.set_ylabel('Average PV Generation (kWh)', fontsize=12, fontweight='bold')
        ax.set_title(
            f'Seasonal Daily PV Production Profile ({self._result.recommended_kwp} kWp System)\n'
            f'Typical Hourly Generation Throughout the Day',
            fontsize=14, fontweight='bold', pad=20
        )
        
        # X-axis
        ax.set_xticks(range(0, 24, 2))
        ax.set_xlim(-0.5, 23.5)
        
        # Grid
        ax.grid(True, alpha=0.3, linestyle='--', linewidth =0.8)
        ax.set_axisbelow(True)
        
        # Legend
        ax.legend(loc='upper right', framealpha=0.95, fontsize=11)
        
        # Add info box with system details
        textstr = '\n'.join((
            f'System Size: {self._result.recommended_kwp} kWp',
            f'Annual Yield: {self._result.annual_generation_kwh:.0f} kWh',
            f'Specific Yield: {self._result.specific_yield_kwh_per_kwp:.0f} kWh/kWp'
        ))
        props = dict(boxstyle='round', facecolor='white', alpha=0.85, edgecolor='gray')
        ax.text(0.02, 0.98, textstr, transform=ax.transAxes, fontsize=10,
               verticalalignment='top', bbox=props)
        
        # Professional styling
        ax.spines['top'].set_visible(False)
        ax.spines['right'].set_visible(False)
        ax.spines['left'].set_linewidth(1.2)
        ax.spines['bottom'].set_linewidth(1.2)
        
        plt.tight_layout()
        
        if output_path:
            fig.savefig(output_path, dpi=150, bbox_inches='tight')
            plt.close(fig)
            return output_path
        else:
            plt.show()
            return None
    
    def plot_battery_soc(
        self,
        output_path: Optional[str] = None,
        figsize: tuple = (14, 6),
        days_to_show: int = 7
    ) -> Optional[str]:
        """
        Plots battery state of charge over time.
        
        Shows typical week of battery operation.
        
        Args:
            output_path: Path to save figure. If None, displays interactively.
            figsize: Figure size (width, height) in inches.
            days_to_show: Number of days to display (default: 7).
            
        Returns:
            Path to saved figure if output_path provided, else None.
        """
        if not self._result.battery_enabled:
            print("No battery in this simulation. Skipping SOC plot.")
            return None
        
        fig, (ax1, ax2) = plt.subplots(2, 1, figsize=figsize,
                                        gridspec_kw={'height_ratios': [2, 1]})
        
        # Get data
        soc_data = self._result.battery_soc_profile
        hourly_data = self._result.hourly_data
        
        # Find representative summer week
        summer_mask = (hourly_data.index.month >= 6) & (hourly_data.index.month <= 7)
        summer_data = hourly_data[summer_mask]
        
        if len(summer_data) > days_to_show * 24:
            start_idx = len(summer_data) // 2
            plot_data = summer_data.iloc[start_idx:start_idx + days_to_show * 24]
            plot_soc = soc_data.iloc[start_idx:start_idx + days_to_show * 24]
        else:
            plot_data = hourly_data.iloc[:days_to_show * 24]
            plot_soc = soc_data.iloc[:days_to_show * 24]
        
        # Top: Battery SOC
        ax1.plot(plot_data.index, plot_soc.values, 
                color='#2ecc71', linewidth=2, label='State of Charge')
        ax1.fill_between(plot_data.index, 0, plot_soc.values, 
                         color='#2ecc71', alpha=0.3)
        ax1.axhline(y=100, color='red', linestyle='--', alpha=0.5, label='Max (100%)')
        ax1.axhline(y=10, color='orange', linestyle='--', alpha=0.5, label='Min (10%)')
        
        ax1.set_ylabel('SOC (%)', fontsize=11, fontweight='bold')
        ax1.set_title(
            f'Battery Operation ({self._result.battery_capacity_kwh} kWh)\n{days_to_show}-Day Profile',
            fontsize=12, fontweight='bold'
        )
        ax1.legend(loc='upper right')
        ax1.grid(True, alpha=0.3, linestyle='--')
        ax1.set_ylim(0, 105)
        
        # Bottom: PV vs Load
        ax2.plot(plot_data.index, plot_data['PV_kWh'].values, 
                color='gold', linewidth=1.5, label='PV', alpha=0.8)
        ax2.plot(plot_data.index, plot_data['Consumption_kWh'].values,
                color='steelblue', linewidth=1.5, label='Load', alpha=0.8)
        
        ax2.set_xlabel('Time', fontsize=11, fontweight='bold')
        ax2.set_ylabel('Power (kWh)', fontsize=11, fontweight='bold')
        ax2.legend(loc='upper right')
        ax2.grid(True, alpha=0.3, linestyle='--')
        ax2.xaxis.set_major_formatter(mdates.DateFormatter('%m/%d'))
        plt.setp(ax2.xaxis.get_majorticklabels(), rotation=45)
        
        plt.tight_layout()
        
        if output_path:
            fig.savefig(output_path, dpi=150, bbox_inches='tight')
            plt.close(fig)
            return output_path
        else:
            plt.show()
            return None
