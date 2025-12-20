
"""
Example 06: Verify Specific Battery Capacity
============================================
This script allows you to manually "plug in" a specific battery capacity
(e.g., derived from optimization) and verify its detailed behavior.

It uses the same scenario parameters as Example 05 for consistency.
"""

import pandas as pd
import matplotlib.pyplot as plt
import sys
import os

# Ensure root is in path
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from src.config.equipments.batteries import pysam as battery
from src.battery import PySAMBatterySimulator
from src.synthetic_profiles import generate_scenario

# --- CONFIGURATION ---
TARGET_CAPACITY_KWH = 5.0  # <--- PLUG IN YOUR VALUE HERE
# ---------------------

def main():
    print(f"=== Verifying Battery Capacity: {TARGET_CAPACITY_KWH} kWh ===\n")
    
    # 1. Setup Data (Matches Example 05)
    print("1. Generating Scenario...")
    load_kw, pv_kw = generate_scenario(
        start_date='2024-01-01', 
        days=365,
        daily_load=15.0, 
        pv_size_kwp=8.0 
    )
    
    annual_load = load_kw.sum()
    print(f"   Annual Load: {annual_load:.0f} kWh")
    
    # 2. Run Simulation using OOP interface
    print(f"\n2. Simulating with {TARGET_CAPACITY_KWH} kWh Battery...")
    
    simulator = PySAMBatterySimulator(battery)
    results = simulator.simulate(load_kw, pv_kw, system_kwh=TARGET_CAPACITY_KWH)
    results.index = load_kw.index
    
    # 3. Analyze Results
    grid_import = results['grid_import'].sum()
    ss = 1.0 - (grid_import / annual_load)
    
    print(f"   Annual Grid Import: {grid_import:.1f} kWh")
    print(f"   Self-Sufficiency:   {ss:.1%}")
    
    # 4. Daily Breakdown (Representative Week)
    start_date = '2024-06-01'
    end_date = '2024-06-07'
    week_data = results.loc[start_date:end_date]
    
    print(f"\n3. Daily Breakdown ({start_date} to {end_date})")
    
    daily_week = week_data.resample('D').agg({
        'load': 'sum',
        'pv': 'sum',
        'grid_import': 'sum',
        'grid_export': 'sum',
        'battery_power': [
            ('Discharge', lambda x: x[x > 0].sum()),
            ('Charge', lambda x: abs(x[x < 0].sum()))
        ]
    })
    daily_week.columns = ['Load', 'PV', 'GridImp', 'GridExp', 'BatDisch', 'BatChg']
    
    header = f"   {'Date':<12} | {'Load':<8} | {'PV':<8} | {'GridImp':<8} | {'GridExp':<8} | {'BatDisch':<9} | {'BatChg':<8}"
    print("   " + "-" * len(header))
    print(header)
    print("   " + "-" * len(header))
    
    for date, row in daily_week.iterrows():
        d_str = date.strftime('%Y-%m-%d')
        print(f"   {d_str:<12} | {row['Load']:<8.1f} | {row['PV']:<8.1f} | {row['GridImp']:<8.1f} | {row['GridExp']:<8.1f} | {row['BatDisch']:<9.1f} | {row['BatChg']:<8.1f}")
    print("   " + "-" * len(header))
    
    # 5. Plotting
    print("\n4. Generating Plot...")
    try:
        fig, axes = plt.subplots(4, 1, figsize=(12, 12), sharex=True)
        
        # Load/PV
        ax1 = axes[0]
        ax1.plot(week_data.index, week_data['load'], 'k', label='Load')
        ax1.plot(week_data.index, week_data['pv'], 'orange', alpha=0.8, label='PV')
        ax1.fill_between(week_data.index, week_data['load'], color='gray', alpha=0.1)
        ax1.set_ylabel('Power (kW)')
        ax1.set_title(f'System Behavior ({TARGET_CAPACITY_KWH} kWh) - {start_date} to {end_date}')
        ax1.legend(loc='upper right')
        ax1.grid(True, alpha=0.3)
        
        # Battery Power
        ax2 = axes[1]
        ax2.plot(week_data.index, week_data['battery_power'], 'b', label='Battery Flow')
        ax2.fill_between(week_data.index, week_data['battery_power'], 0, where=(week_data['battery_power']>0), color='green', alpha=0.3, label='Discharging')
        ax2.fill_between(week_data.index, week_data['battery_power'], 0, where=(week_data['battery_power']<0), color='red', alpha=0.3, label='Charging')
        ax2.set_ylabel('Battery (kW)')
        ax2.legend(loc='upper right')
        ax2.grid(True, alpha=0.3)
        
        # Grid
        ax3 = axes[2]
        ax3.plot(week_data.index, week_data['grid_power'], 'gray', label='Net Grid')
        ax3.fill_between(week_data.index, week_data['grid_power'], 0, where=(week_data['grid_power']>0), color='orange', alpha=0.3, label='Import')
        ax3.fill_between(week_data.index, week_data['grid_power'], 0, where=(week_data['grid_power']<0), color='cyan', alpha=0.3, label='Export')
        ax3.set_ylabel('Grid (kW)')
        ax3.legend(loc='upper right')
        ax3.grid(True, alpha=0.3)
        
        # SOC
        ax4 = axes[3]
        ax4.plot(week_data.index, week_data['soc'], 'purple', linewidth=2, label='SOC')
        ax4.axhline(battery.min_soc, linestyle='--', color='red', label='Min SOC')
        ax4.axhline(battery.max_soc, linestyle='--', color='green', label='Max SOC')
        ax4.set_ylabel('SOC (%)')
        ax4.legend(loc='upper right')
        ax4.grid(True, alpha=0.3)
        
        plt.tight_layout()
        
        # Save to examples/outputs/
        output_dir = os.path.join(os.path.dirname(__file__), 'outputs')
        os.makedirs(output_dir, exist_ok=True)
        out_file = os.path.join(output_dir, '06-verify-battery-capacity.png')
        
        plt.savefig(out_file)
        print(f"   Plot saved to: {out_file}")
        
    except ImportError:
        print("   [Warning] matplotlib missing.")

if __name__ == "__main__":
    main()
