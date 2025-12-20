"""
Example 08: Custom Date Range Plotting
========================================
Demonstrates how to plot consumption for any custom date range.
"""

import sys
import os

# Ensure root is in path
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from src.consumption.analyzer import ConsumptionAnalyzer


#%%
data_file = os.path.join(os.path.dirname(__file__), '..', 'data', 'consumption', '20251212_consumption-frq-15min.csv')
output_dir = os.path.join(os.path.dirname(__file__), 'outputs', 'custom_ranges')
os.makedirs(output_dir, exist_ok=True)

# Initialize analyzer and load data
analyzer = ConsumptionAnalyzer()

#%%

def main():
    print("=== Custom Date Range Plotting Demo ===\n")
    
    # Setup
    data_file = os.path.join(os.path.dirname(__file__), '..', 'data', 'consumption', '20251212_consumption-frq-15min.csv')
    output_dir = os.path.join(os.path.dirname(__file__), 'outputs', 'custom_ranges')
    os.makedirs(output_dir, exist_ok=True)
    
    # Initialize analyzer and load data
    analyzer = ConsumptionAnalyzer()
    
    if not analyzer.load_data(data_file):
        print("Failed to load data")
        return
    
    print("\n" + "="*60)
    print("EXAMPLE 1: Single Day (Jan 15, 2024)")
    print("="*60)
    analyzer.plot_date_range(
        start_date='2024-01-15',
        end_date='2024-01-15',
        output_path=os.path.join(output_dir, '01_single_day.png'),
        title='Single Day Consumption - Jan 15, 2024'
    )
    
    print("\n" + "="*60)
    print("EXAMPLE 2: One Week (Jan 15-21, 2024)")
    print("="*60)
    analyzer.plot_date_range(
        start_date='2024-01-15',
        end_date='2024-01-21',
        output_path=os.path.join(output_dir, '02_one_week.png'),
        title='Weekly Consumption Pattern'
    )
    
    print("\n" + "="*60)
    print("EXAMPLE 3: One Month (March 2024)")
    print("="*60)
    analyzer.plot_date_range(
        start_date='2024-03-01',
        end_date='2024-03-31',
        output_path=os.path.join(output_dir, '03_one_month.png'),
        title='March 2024 - Full Month'
    )
    
    print("\n" + "="*60)
    print("EXAMPLE 4: Custom Range (Summer: June-August 2024)")
    print("="*60)
    analyzer.plot_date_range(
        start_date='2024-06-01',
        end_date='2024-08-31',
        output_path=os.path.join(output_dir, '04_summer_quarter.png'),
        title='Summer Period (Jun-Aug 2024)'
    )
    
    print("\n" + "="*60)
    print("EXAMPLE 5: Without Smoothing")
    print("="*60)
    analyzer.plot_date_range(
        start_date='2024-01-15',
        end_date='2024-01-17',
        output_path=os.path.join(output_dir, '05_no_smoothing.png'),
        title='Raw Data (No Smoothing)',
        smooth=False
    )
    
    print("\n✅ All custom range plots generated successfully!")
    print(f"📂 Output directory: {output_dir}")

if __name__ == "__main__":
    main()
