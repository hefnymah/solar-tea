
"""
Example 05: Battery Optimization for 100% Self-Sufficiency
==========================================================
This script performs a sensitivity analysis to find the battery capacity 
required to eliminate grid import (achieve 100% Self-Sufficiency).

Algorithm:
1. Generate synthetic Load and PV data.
2. Use the PySAMBatterySimulator.optimize_size() method.
3. Plot the "Self-Sufficiency vs Capacity" curve.
4. Visualize optimal battery behavior.

Note: 100% Self-Sufficiency (Autarky) often requires massive seasonal storage 
in climates with winter deficits. This script demonstrates that diminishing return.
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import sys
import os

# Ensure root is in path
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from src.config.equipments.batteries import pysam as battery
from src.battery import PySAMBatterySimulator
from src.synthetic import generate_scenario

def main():
    print("=== Battery Optimization (Target: 100% Self-Sufficiency) ===\n")
    
    # 1. Setup Data
    # 5kW PV, 15kWh daily load (~5500kWh/yr)
    print("1. Generating Scenario...")
    load_kw, pv_kw = generate_scenario(
        start_date='2024-01-01', 
        days=365,
        daily_load=15.0, 
        pv_size_kwp=8.0 # Generous PV to potentially allow 100% SS
    )
    
    annual_load = load_kw.sum()
    annual_pv = pv_kw.sum()
    print(f"   Annual Load: {annual_load:.0f} kWh")
    print(f"   Annual PV:   {annual_pv:.0f} kWh")
    print(f"   PV/Load Ratio: {annual_pv/annual_load:.2f}")
    
    if annual_pv < annual_load:
        print("\n   [Warning] PV generation is less than Load. 100% Self-Sufficiency is impossible.")
    
    # 2. Optimization Sweep
    print("\n2. Running Optimization Sweep (0 - 100 kWh)...")
    
    # Create simulator instance
    simulator = PySAMBatterySimulator(battery)
    
    capacities = [0, 5, 10, 15, 20, 30, 40, 50, 75, 100]
    results_data = []
    
    for cap in capacities:
        print(f"   Simulating {cap:3.0f} kWh...", end="")
        
        if cap == 0:
            # No battery
            net = load_kw - pv_kw
            grid_import = net[net > 0].sum()
            ss = 1.0 - (grid_import / annual_load)
        else:
            sim_res = simulator.simulate(load_kw, pv_kw, system_kwh=float(cap))
            grid_import = sim_res['grid_import'].sum()
            ss = simulator.calculate_self_sufficiency(sim_res)
            
        print(f" -> Self-Sufficiency: {ss:.1%}")
        results_data.append({'Capacity_kWh': cap, 'SS_Percent': ss * 100.0, 'Import_kWh': grid_import})
        
    df_res = pd.DataFrame(results_data)
    
    # 3. Find Targets
    print("\n3. Analysis Results")
    # Interpolate to find specific targets if possible
    
    def find_capacity_for_target(target_ss_percent):
        # returns shortest capacity exceeding target
        if target_ss_percent >= 100.0:
            # For 100%, check for negligible import (< 1 kWh)
            matches = df_res[df_res['Import_kWh'] < 1.0]
        else:
            matches = df_res[df_res['SS_Percent'] >= target_ss_percent]
            
        if matches.empty:
            return None
        return matches.iloc[0]
        
    t90 = find_capacity_for_target(90.0)
    t95 = find_capacity_for_target(95.0)
    t99 = find_capacity_for_target(99.0)
    t100 = find_capacity_for_target(100.0)
    
    if t90 is not None: print(f"   Capacity for  90% SS: ~{t90['Capacity_kWh']:.0f} kWh")
    if t95 is not None: print(f"   Capacity for  95% SS: ~{t95['Capacity_kWh']:.0f} kWh")
    if t99 is not None: print(f"   Capacity for  99% SS: ~{t99['Capacity_kWh']:.0f} kWh")
    if t100 is not None: 
        print(f"   Capacity for 100% SS: ~{t100['Capacity_kWh']:.0f} kWh")
    else:
        print(f"   Capacity for 100% SS: > {capacities[-1]} kWh (Seasonal deficit likely)")
        
    # 4. Plotting
    try:
        fig, ax1 = plt.subplots(figsize=(10, 6))
        
        ax1.plot(df_res['Capacity_kWh'], df_res['SS_Percent'], marker='o', linestyle='-', color='b')
        ax1.set_xlabel('Battery Capacity (kWh)')
        ax1.set_ylabel('Self-Sufficiency (%)', color='b')
        ax1.tick_params(axis='y', labelcolor='b')
        ax1.grid(True, alpha=0.3)
        ax1.set_title('Self-Sufficiency vs Battery Capacity')
        
        # Add import curve
        ax2 = ax1.twinx()
        ax2.plot(df_res['Capacity_kWh'], df_res['Import_kWh'], marker='x', linestyle='--', color='r')
        ax2.set_ylabel('Annual Grid Import (kWh)', color='r')
        ax2.tick_params(axis='y', labelcolor='r')
        
        plt.tight_layout()
        
        # Save to examples/outputs/
        output_dir = os.path.join(os.path.dirname(__file__), 'outputs')
        os.makedirs(output_dir, exist_ok=True)
        output_file = os.path.join(output_dir, '05-battery-optimization.png')
        
        plt.savefig(output_file)
        print(f"\n4. Optimization Plot saved to: {output_file}")

        # --- Part 5: Visualize Behavior of Optimal Battery ---
        
        if t100 is not None:
            opt_cap = t100['Capacity_kWh']
            print(f"\n5. Visualizing Optimal Battery ({opt_cap:.0f} kWh)...")
            
            # Re-simulate for the specific optimal capacity to get time-series
            opt_results = simulator.simulate(load_kw, pv_kw, system_kwh=float(opt_cap))
            opt_results.index = load_kw.index # Restore datetime index
            
            # --- Helper Function for Plotting ---
            def plot_time_series(data, title_suffix, filename_suffix):
                # Calculate daily aggregates for table
                daily = data.resample('D').agg({
                    'load': 'sum',
                    'pv': 'sum',
                    'grid_import': 'sum',
                    'grid_export': 'sum',
                    'battery_power': [
                        ('Discharge', lambda x: x[x > 0].sum()),
                        ('Charge', lambda x: abs(x[x < 0].sum()))
                    ]
                })
                daily.columns = ['Load', 'PV', 'Grid Imp', 'Grid Exp', 'Bat Disch', 'Bat Chg']
                
                print(f"\n   [Daily Breakdown for {data.index[0].date()} to {data.index[-1].date()}]")
                header = f"   {'Date':<12} | {'Load':<8} | {'PV':<8} | {'GridImp':<8} | {'GridExp':<8} | {'BatDisch':<9} | {'BatChg':<8}"
                print("   " + "-" * len(header))
                print(header)
                print("   " + "-" * len(header))
                for date, row in daily.iterrows():
                    d_str = date.strftime('%Y-%m-%d')
                    print(f"   {d_str:<12} | {row['Load']:<8.1f} | {row['PV']:<8.1f} | {row['Grid Imp']:<8.1f} | {row['Grid Exp']:<8.1f} | {row['Bat Disch']:<9.1f} | {row['Bat Chg']:<8.1f}")
                print("   " + "-" * len(header) + "\n")

                # Plotting
                fig, axes = plt.subplots(4, 1, figsize=(12, 12), sharex=True)
                
                # Plot 1: Power Balance
                ax1 = axes[0]
                ax1.plot(data.index, data['load'], label='Load', color='black', linewidth=1.5)
                ax1.plot(data.index, data['pv'], label='PV Gen', color='orange', alpha=0.8)
                ax1.fill_between(data.index, data['load'], color='gray', alpha=0.1)
                ax1.set_ylabel('Power (kW)')
                ax1.set_title(f'Optimal System Behavior ({opt_cap:.0f} kWh) - {title_suffix}')
                ax1.legend(loc='upper right')
                ax1.grid(True, alpha=0.3)
                
                # Plot 2: Battery Power
                ax2 = axes[1]
                ax2.plot(data.index, data['battery_power'], label='Battery Flow', color='blue')
                ax2.fill_between(data.index, data['battery_power'], 0, where=(data['battery_power']>0), color='green', alpha=0.3, label='Discharging')
                ax2.fill_between(data.index, data['battery_power'], 0, where=(data['battery_power']<0), color='red', alpha=0.3, label='Charging')
                ax2.set_ylabel('Battery (kW)')
                ax2.legend(loc='upper right')
                ax2.grid(True, alpha=0.3)

                # Plot 3: Grid Power
                ax3 = axes[2]
                ax3.plot(data.index, data['grid_power'], label='Net Grid', color='gray')
                ax3.fill_between(data.index, data['grid_power'], 0, where=(data['grid_power']>0), color='orange', alpha=0.3, label='Import')
                ax3.fill_between(data.index, data['grid_power'], 0, where=(data['grid_power']<0), color='cyan', alpha=0.3, label='Export')
                ax3.set_ylabel('Grid (kW)')
                ax3.legend(loc='upper right')
                ax3.grid(True, alpha=0.3)
                
                # Plot 4: State of Charge
                ax4 = axes[3]
                ax4.plot(data.index, data['soc'], label='SOC', color='purple', linewidth=2)
                ax4.axhline(battery.min_soc, linestyle='--', color='red', label='Min SOC')
                ax4.axhline(battery.max_soc, linestyle='--', color='green', label='Max SOC')
                ax4.set_ylabel('SOC (%)')
                ax4.set_xlabel('Date')
                ax4.legend(loc='upper right')
                ax4.grid(True, alpha=0.3)
                
                plt.tight_layout()
                
                output_dir = os.path.join(os.path.dirname(__file__), 'outputs')
                os.makedirs(output_dir, exist_ok=True)
                output_path = os.path.join(output_dir, f'05-battery-optimization-{filename_suffix}.png')
                plt.savefig(output_path)
                print(f"   Plot saved to: {output_path}")

            # 1. Plot Representative Week (Summer)
            print("   --- Summer Week Analysis ---")
            plot_time_series(opt_results.loc['2024-06-01':'2024-06-07'], 'Summer Week', 'week')

            # 2. Plot Typical Winter Day (Jan 15)
            print("   --- Winter Day Analysis ---")
            # Select 24 hours of Jan 15 (if single day requested)
            winter_data = opt_results.loc['2024-01-15':'2024-01-15']
            if not winter_data.empty:
                plot_time_series(winter_data, 'Winter Day (Jan 15)', 'winter-day')
            else:
                print("   [Warning] Winter date not found in data.")

        else:
             print("\n   [Info] 100% SS target not found in range. Skipping time-series plot.")
        
    except ImportError:
        print("\n   [Warning] matplotlib not found. Skipping plot.")
        
if __name__ == "__main__":
    main()
