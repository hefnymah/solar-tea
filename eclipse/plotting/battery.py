import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import pandas as pd
from pathlib import Path
from eclipse.plotting.themes import apply_eclipse_style, COLORS

class BatteryPlotter:
    """
    Dedicated plotter for Battery Energy Storage Systems (BESS).
    
    Adheres to the "Industrial/Digital" aesthetic:
    - Step plots for power flows
    - Clean SOC curves
    - Precise grid alignment
    """
    
    def __init__(self, battery_kwh: float = None):
        """
        Initialize the battery plotter.
        
        Args:
            battery_kwh: Battery capacity in kWh. If provided, all plots will show
                        a secondary Y-axis with absolute SOC in kWh.
        """
        apply_eclipse_style()
        self.battery_kwh = battery_kwh
        
    def plot_operation(self, df: pd.DataFrame, output_path: Path, title: str = None, battery_kwh: float = None):
        """
        Generates the standard 2-panel battery operation plot for any time period.
        Top: SOC (%) with optional secondary axis showing absolute kWh
        Bottom: Power Flow (kW) in Step style
        
        Args:
            df: DataFrame with battery simulation results (must include: soc, load, pv, battery_power, grid_import, grid_export)
            output_path: Path to save the plot
            title: Optional custom title (auto-generated if None)
            battery_kwh: Override battery capacity for this plot (uses instance value if not provided)
        """
        # Use provided value, fall back to instance value, then try df.attrs
        if battery_kwh is not None:
            pass  # Use provided value
        elif self.battery_kwh is not None:
            battery_kwh = self.battery_kwh
        elif 'battery_kwh' in df.attrs:
            battery_kwh = df.attrs['battery_kwh']  # Auto-read from simulation results
        
        # Determine time range for adaptive formatting
        time_range = (df.index[-1] - df.index[0]).total_seconds() / 3600  # hours
        
        # Auto-generate title if not provided
        if title is None:
            start_str = df.index[0].strftime('%Y-%m-%d')
            end_str = df.index[-1].strftime('%Y-%m-%d')
            if start_str == end_str:
                title = f"Battery Operation: {start_str}"
            else:
                title = f"Battery Operation: {start_str} to {end_str}"
        
        fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(12, 10), sharex=True, gridspec_kw={'height_ratios': [1, 2]})
        plt.subplots_adjust(hspace=0.1)
        
        # ==========================================
        # Panel 1: SOC
        # ==========================================
        ax1.set_title(title, fontsize=16, fontweight='bold', pad=15)
        
        # SOC Curve
        ax1.plot(df.index, df['soc'], color='#8e44ad', linewidth=3, label='SOC')
        ax1.fill_between(df.index, df['soc'], 0, color='#9b59b6', alpha=0.1)
        
        # Limits
        ax1.axhline(90, color='green', linestyle='--', alpha=0.5, label='Max (90%)')
        ax1.axhline(10, color='red', linestyle='--', alpha=0.5, label='Min (10%)')
        
        # Styling for primary Y-axis (%)
        ax1.set_ylabel("SOC (%)", fontsize=12, fontweight='bold', color='#8e44ad')
        ax1.tick_params(axis='y', labelcolor='#8e44ad')
        ax1.tick_params(axis='both', which='major', length=6, width=1, direction='out')
        ax1.set_ylim(0, 105)
        ax1.grid(True, alpha=0.3)
        ax1.legend(loc='upper left', frameon=True, facecolor='white', 
                   edgecolor='black', framealpha=0.9)
        
        # Add thick black border around SOC subplot
        for spine in ax1.spines.values():
            spine.set_linewidth(1.0)
            spine.set_color('black')
        
        # Add secondary Y-axis for absolute SOC in kWh (if battery_kwh provided)
        if battery_kwh is not None and battery_kwh > 0:
            ax1_right = ax1.twinx()
            # Scale: 0-100% maps to 0-battery_kwh
            ax1_right.set_ylim(0, battery_kwh * 1.05)  # 5% margin like the % axis
            ax1_right.set_ylabel("SOC (kWh)", fontsize=12, fontweight='bold', color='#2c3e50')
            ax1_right.tick_params(axis='y', labelcolor='#2c3e50')
        
        # ==========================================
        # Panel 2: Power Flow (Step Plot)
        # ==========================================
        
        # 1. Net Grid Impact (Filled Background Layers)
        # Grid Import (Orange)
        ax2.fill_between(df.index, df['grid_import'], 0, step='post',
                         color='#e67e22', alpha=0.7, label='Grid Import')
                         
        # Grid Export (Purple - plot as negative)
        if 'grid_export' in df.columns:
            export_plot = df['grid_export'] * -1
            ax2.fill_between(df.index, export_plot, 0, step='post',
                             color='#9b59b6', alpha=0.6, label='Grid Export')
        
        # 2. Battery Action (Overlay Fills)
        # Discharge (Green - Positive)
        ax2.fill_between(df.index, df['battery_power'], 0, where=(df['battery_power']>0),
                         step='post', color='#2ecc71', alpha=0.6, label='Bat Discharge')
                         
        # Charge (Red - Negative)
        ax2.fill_between(df.index, df['battery_power'], 0, where=(df['battery_power']<0),
                         step='post', color='#e74c3c', alpha=0.6, label='Bat Charge')
        
        # 3. Component Lines (Top Layer)
        # Load
        ax2.plot(df.index, df['load'], color='black', linewidth=1, linestyle='-', drawstyle='steps-post', label='Load')
        
        # PV
        ax2.plot(df.index, df['pv'], color='#f1c40f', linewidth=1, linestyle='-', drawstyle='steps-post', label='PV Gen')
        
        # Styling
        ax2.set_ylabel("Power (kW)", fontsize=12, fontweight='bold')
        ax2.tick_params(axis='both', which='major', length=6, width=1, direction='out')
        ax2.grid(True, alpha=0.3)
        ax2.legend(loc='upper left', ncol=2, frameon=True, fancybox=True, edgecolor='black', framealpha=0.9)
        
        # Add thick black border around Power subplot
        for spine in ax2.spines.values():
            spine.set_linewidth(1.0)
            spine.set_color('black')
        
        # Calculate and display statistics
        dt = 0.25  # 15-minute intervals in hours
        total_load = (df['load'] * dt).sum()
        total_pv = (df['pv'] * dt).sum()
        total_grid_import = (df['grid_import'] * dt).sum()
        total_grid_export = (df['grid_export'] * dt).sum()
        
        # Self-sufficiency: % of load met without grid import
        self_sufficiency = ((total_load - total_grid_import) / total_load * 100) if total_load > 0 else 0
        
        # Self-consumption: % of PV used locally (not exported)
        self_consumption = ((total_pv - total_grid_export) / total_pv * 100) if total_pv > 0 else 0
        
        # Create stats text
        stats_text = (
            "Stats:\n"
            f"Load: {total_load:.1f} kWh\n"
            f"PV: {total_pv:.1f} kWh\n"
            f"Grid Import: {total_grid_import:.1f} kWh\n"
            f"Grid Export: {total_grid_export:.1f} kWh\n"
            f"Self-Sufficiency: {self_sufficiency:.1f}%\n"
            f"Self-Consumption: {self_consumption:.1f}%"
        )
        
        # Add text box to top right
        ax2.text(0.98, 0.98, stats_text, transform=ax2.transAxes, 
                fontsize=9, verticalalignment='top', horizontalalignment='right',
                bbox=dict(boxstyle='round', facecolor='white', alpha=0.9, edgecolor='gray'))
        
        # Adaptive X-Axis formatting
        if time_range <= 48:  # <= 2 days: Show hours
            ax2.set_xlabel("Hour of Day", fontsize=12, fontweight='bold')
            ax2.xaxis.set_major_formatter(mdates.DateFormatter('%H:%M'))
            ax2.xaxis.set_major_locator(mdates.HourLocator(interval=2))
        else:  # > 2 days: Show dates
            ax2.set_xlabel("Date", fontsize=12, fontweight='bold')
            ax2.xaxis.set_major_formatter(mdates.DateFormatter('%m-%d'))
            ax2.xaxis.set_major_locator(mdates.DayLocator(interval=1))
            plt.setp(ax2.xaxis.get_majorticklabels(), rotation=45, ha='right')
        
        plt.tight_layout()
        plt.savefig(output_path, dpi=150, bbox_inches='tight')
        plt.close()
        print(f"Operation plot saved to: {output_path}")

    
