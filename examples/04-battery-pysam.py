
"""
Example 04: Battery Sizing and Annual Behavior (PySAM)
======================================================
This example demonstrates how to:
1. Import the default battery configuration.
2. Generate synthetic PV generation and Load profiles.
3. Simulate battery behavior over a full year using NREL PySAM.
4. Analyze the results (Self-sufficiency, Monthly Patterns).
"""

import pandas as pd
import numpy as np
import sys
import os

# Ensure root is in path
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from eclipse.config.equipments.batteries import pysam as battery
from eclipse.battery import PySAMBatterySimulator
from eclipse.synthetic import generate_scenario

def main():
    print(f"=== Battery Simulation Example ({battery.name}) ===\n")
    
    # 1. Setup Data
    print("1. Generating Synthetic Data...")
    
    # Use central synthetic profile generator
    load_kw, pv_kw = generate_scenario(
        start_date='2024-01-01',
        days=365,
        daily_load=20.0, # kWh/day (approx 7300/yr)
        pv_size_kwp=5.0  # 5kW system
    )
    
    total_load_kwh = load_kw.sum()
    total_pv_kwh = pv_kw.sum()
    
    print(f"   Annual Load: {total_load_kwh:.0f} kWh")
    print(f"   Annual PV:   {total_pv_kwh:.0f} kWh")
    
    # 2. Simulate using OOP interface
    chemistry = battery.performance.get('chemistry', 'Unknown') if isinstance(battery.performance, dict) else getattr(battery.performance, 'chemistry', 'Unknown')
    print(f"\n2. Simulating with Battery: {battery.nominal_energy_kwh} kWh, {chemistry}...")
    
    # Create simulator instance
    simulator = PySAMBatterySimulator(battery)
    
    # Run simulation
    results = simulator.simulate(load_kw, pv_kw)
    
    # Restore index for analysis
    results.index = load_kw.index
    
    # 3. Analyze Results
    print("\n3. Results Analysis")
    
    # Calculate Self-Sufficiency
    # Grid Import = What we bought (Load - PV - BatteryDischarge)
    total_import = results['grid_import'].sum()
    self_sufficiency = 1 - (total_import / total_load_kwh)
    
    print(f"   Grid Import: {total_import:.0f} kWh")
    print(f"   Self-Sufficiency: {self_sufficiency:.1%}")
    
    # Monthly Aggregation
    print("\n   [Monthly Breakdown]")
    results['Month'] = results.index.month
    monthly = results.groupby('Month').agg({
        'pv': 'sum',
        'load': 'sum',
        'grid_import': 'sum',
        'battery_power': lambda x: x[x>0].sum() # Discharge sum
    })
    
    monthly['Self_Sufficiency'] = 1 - (monthly['grid_import'] / monthly['load'])
    
    print(f"   {'Month':<5} | {'Load (kWh)':<10} | {'PV (kWh)':<10} | {'Disch.(kWh)':<12} | {'S.S. (%)':<8}")
    print("   " + "-"*58)
    for m in monthly.index:
        row = monthly.loc[m]
        print(f"   {m:<5} | {row['load']:<10.0f} | {row['pv']:<10.0f} | {row['battery_power']:<12.0f} | {row['Self_Sufficiency']:.1%}")

    # 4. Plotting
    print("\n4. Generating Plot...")
    try:
        import matplotlib.pyplot as plt
        
        # Pick a representative week (e.g., first week of June)
        start_date = '2024-06-01'
        end_date = '2024-06-07'
        week_data = results.loc[start_date:end_date]
        
        fig, axes = plt.subplots(4, 1, figsize=(12, 12), sharex=True)
        
        # --- Print Daily Breakdown for the week ---
        print(f"\n   [Daily Breakdown for {start_date} to {end_date}]")
        
        # Calculate daily aggregates for the week
        daily_week = week_data.resample('D').agg({
            'load': 'sum',
            'pv': 'sum',
            'grid_import': 'sum',
            'grid_export': 'sum',
            # Split battery power into charge and discharge
            'battery_power': [
                ('Discharge (kWh)', lambda x: x[x > 0].sum()),
                ('Charge (kWh)', lambda x: abs(x[x < 0].sum()))
            ]
        })
        
        # Flatten columns
        daily_week.columns = ['Load', 'PV', 'Grid Imp', 'Grid Exp', 'Bat Disch', 'Bat Chg']
        
        # Print Table Header
        header = f"   {'Date':<12} | {'Load':<8} | {'PV':<8} | {'GridImp':<8} | {'GridExp':<8} | {'BatDisch':<9} | {'BatChg':<8}"
        print("   " + "-" * len(header))
        print(header)
        print("   " + "-" * len(header))
        
        for date, row in daily_week.iterrows():
            d_str = date.strftime('%Y-%m-%d')
            print(f"   {d_str:<12} | {row['Load']:<8.1f} | {row['PV']:<8.1f} | {row['Grid Imp']:<8.1f} | {row['Grid Exp']:<8.1f} | {row['Bat Disch']:<9.1f} | {row['Bat Chg']:<8.1f}")
        print("   " + "-" * len(header) + "\n")

        
        # Plot 1: Power Balance
        ax1 = axes[0]
        ax1.plot(week_data.index, week_data['load'], label='Load', color='black', linewidth=1.5)
        ax1.plot(week_data.index, week_data['pv'], label='PV Gen', color='orange', alpha=0.8)
        ax1.fill_between(week_data.index, week_data['load'], color='gray', alpha=0.1)
        ax1.set_ylabel('Power (kW)')
        ax1.set_title(f'System Behavior (Week 24) - {battery.nominal_energy_kwh} kWh Battery')
        ax1.legend(loc='upper right')
        ax1.grid(True, alpha=0.3)
        
        # Plot 2: Battery Power
        ax2 = axes[1]
        ax2.plot(week_data.index, week_data['battery_power'], label='Battery Flow', color='blue')
        ax2.fill_between(week_data.index, week_data['battery_power'], 0, where=(week_data['battery_power']>0), color='green', alpha=0.3, label='Discharging')
        ax2.fill_between(week_data.index, week_data['battery_power'], 0, where=(week_data['battery_power']<0), color='red', alpha=0.3, label='Charging')
        ax2.set_ylabel('Battery (kW)')
        ax2.legend(loc='upper right')
        ax2.grid(True, alpha=0.3)

        # Plot 3: Grid Power (Import/Export)
        ax3 = axes[2]
        # Calculate Net Grid manually if not present, but simulate_pysam_battery provides 'grid_import' and 'grid_export'
        # Let's verify columns. We know 'grid_import' and 'grid_export' exist.
        # Let's plot Net Grid Power: +Import, -Export
        # results['grid_power'] = results['grid_import'] - results['grid_export']
        # But wait, original code calculated 'grid_power' = load - pv - battery.
        # And simulate_pysam_battery returns that column too!
        
        ax3.plot(week_data.index, week_data['grid_power'], label='Net Grid', color='gray')
        ax3.fill_between(week_data.index, week_data['grid_power'], 0, where=(week_data['grid_power']>0), color='orange', alpha=0.3, label='Import')
        ax3.fill_between(week_data.index, week_data['grid_power'], 0, where=(week_data['grid_power']<0), color='cyan', alpha=0.3, label='Export')
        ax3.set_ylabel('Grid (kW)')
        ax3.legend(loc='upper right')
        ax3.grid(True, alpha=0.3)
        
        # Plot 4: State of Charge
        ax4 = axes[3]
        ax4.plot(week_data.index, week_data['soc'], label='SOC', color='purple', linewidth=2)
        ax4.axhline(battery.min_soc, linestyle='--', color='red', label='Min SOC')
        ax4.axhline(battery.max_soc, linestyle='--', color='green', label='Max SOC')
        ax4.set_ylabel('SOC (%)')
        ax4.set_xlabel('Date')
        ax4.legend(loc='upper right')
        ax4.grid(True, alpha=0.3)
        
        plt.tight_layout()
        
        # Save to examples/outputs/
        output_dir = os.path.join(os.path.dirname(__file__), 'outputs')
        os.makedirs(output_dir, exist_ok=True)
        output_file = os.path.join(output_dir, '04-battery-pysam.png')
        
        plt.savefig(output_file)
        print(f"   Plot saved to: {output_file}")
        # plt.show() # Uncomment to show interactive window
        
    except ImportError:
        print("   [Warning] matplotlib not found. Skipping plot generation.")

if __name__ == "__main__":
    main()
