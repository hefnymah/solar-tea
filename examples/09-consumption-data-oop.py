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

#%%

hrs = data.hourly.dataframe
# Instead of relying on Variable Explorer, print or access directly:
print(data.hourly.dataframe.head())
print(data.daily.dataframe)
print(data.seasons.winter.dataframe)

# Or assign to simple variables for inspection:
hourly_df = data.hourly.dataframe
daily_df = data.daily.dataframe
seasons = data.seasons.summer.dataframe

#%%
# Get the seasonal daily profile
seasonal_profile = data.seasons.profile
print(seasonal_profile)
xxx = data.seasons.profile['winter'].max()

#%%
# Get hourly data for a season, then resample to daily
winter_hourly = data.seasons.winter.dataframe
winter_daily = winter_hourly.resample('D').sum()  # Daily totals

# Or directly get daily data for a season
winter_data = data.seasons.winter
winter_daily_series = winter_data.dataframe.resample('D').sum()

# Get a typical week for a season (new method!)
winter_week = data.seasons.get_typical_week('winter')  # Default: Jan 15-22
winter_week_df = winter_week.dataframe

# Custom week dates
summer_week = data.seasons.get_typical_week('summer', month=7, day=20)
summer_week_df = summer_week.dataframe

# Get extreme weeks (min/max consumption)
extremes = data.get_extreme_weeks()
max_week_df = extremes['max_week'].dataframe  # Highest consumption week
min_week_df = extremes['min_week'].dataframe  # Lowest consumption week

# Daily data from extreme weeks
max_week_daily = extremes['max_week'].dataframe.resample('D').sum()

# Get smoothed data for any period
jan_week = data.slice('2024-01-15', '2024-01-21')
jan_week_smooth = jan_week.smooth(method='spline', points=500)  # Smoothed DataFrame
#%%
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

plotter.plot_seasonal_daily_profile()

plotter.plot_extreme_weeks()

print(f"   Saved {len(paths)} plots to: {output_dir}")
for name, path in paths.items():
    print(f"   - {name}: {os.path.basename(path)}")

