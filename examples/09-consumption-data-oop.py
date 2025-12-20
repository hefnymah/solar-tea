"""
Example 09: ConsumptionData OOP API
===================================
Demonstrates the new OOP interface for loading and analyzing
consumption data from a specific CSV file.

Usage:
    python examples/09-consumption-data-oop.py
"""

import sys
import os

from eclipse.consumption import ConsumptionData, ConsumptionPlotter



print("=== ConsumptionData OOP Example ===\n")

# 1. Load a specific file
file_path = os.path.join(
    os.path.dirname(__file__), 
    '..', 'data', 'consumption', 
    '20251212_consumption-frq-60min-leap-yr.csv'
)

print(f"1. Loading: {os.path.basename(file_path)}")
data = ConsumptionData.from_file(file_path)
print(f"   {data}\n")

# 2. Access nested data
print("2. Data Access Examples")
print(f"   data.hourly.sum()         = {data.hourly.sum():.0f} kWh (annual total)")
print(f"   data.daily.mean()         = {data.daily.mean():.2f} kWh/day")
print(f"   data.monthly.max()        = {data.monthly.max():.1f} kWh (peak month)")
print(f"   data.seasons.winter.mean()= {data.seasons.winter.mean():.3f} kWh/h")
print(f"   data.seasons.summer.mean()= {data.seasons.summer.mean():.3f} kWh/h")
print()

# 3. Custom date slicing
print("3. Custom Date Slicing")
jan_week = data.slice("2024-01-15", "2024-01-21")
print(f"   Jan 15-21 total: {jan_week.sum():.1f} kWh")
print(f"   Jan 15-21 mean:  {jan_week.mean():.3f} kWh/h")
print()

# 4. Access underlying DataFrames
print("4. DataFrame Access")
print(f"   data.hourly.dataframe.head():")
print(data.hourly.dataframe.head().to_string())
print()

# 5. Seasonal profile
print("5. Seasonal Daily Profile (hourly averages)")
print(data.seasons.profile.head(6).to_string())
print()

# 6. Plotting (optional)
print("6. Generating Plots...")
output_dir = os.path.join(os.path.dirname(__file__), 'outputs', '09-oop-demo')

plotter = ConsumptionPlotter(data, output_dir=output_dir)
paths = plotter.plot_all(prefix="demo")

print(f"   Saved {len(paths)} plots to: {output_dir}")
for name, path in paths.items():
    print(f"   - {name}: {os.path.basename(path)}")

