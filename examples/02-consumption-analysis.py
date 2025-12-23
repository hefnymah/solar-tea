"""
Example 09: ConsumptionData OOP API
===================================
Demonstrates the new OOP interface for loading and analyzing
consumption data from a specific CSV file.
"""

import sys
import os

# Ensure project root is in path
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from eclipse.consumption import ConsumptionData
from eclipse.plotting import ConsumptionPlotter
#%%
print("=== ConsumptionData ===\n")

# 1. Load a specific file
file_path = os.path.join(
    os.path.dirname(__file__), 
    '..', 'data', 'consumption', 
    '20251212_consumption-frq-60min-leap-yr.csv'
)

print(f"1. Loading: {os.path.basename(file_path)}")
data = ConsumptionData.from_file(file_path)
print(f"   {data}\n")

#%% Load DataFrames

hrs     = data.hourly.dataframe
hrs_sum = hrs.sum()

daily   = data.daily.dataframe
weekly  = data.weekly.dataframe
monthly = data.monthly.dataframe

#%% Custom Date Slicing
jan_week = data.slice("2024-01-15", "2024-01-21")
total = jan_week.sum()
print(f"   Jan 15-21 total: {total:.1f} kWh")

#%% Seasonal Data
summer_hr = data.seasons.summer.dataframe
summer_min = data.seasons.profile['summer'].min()

winter_hr = data.seasons.winter.dataframe
winter_max = data.seasons.profile['winter'].max()

spring_hr = data.seasons.spring.dataframe
spring_mean = data.seasons.profile['spring'].mean()

autumn_hr = data.seasons.autumn.dataframe
autumn_median = data.seasons.profile['autumn'].median()

# Get the seasonal daily profile
seasonal_profile = data.seasons.profile
print(seasonal_profile)

#%%
# Get hourly data for a season, then resample to daily
winter_hourly  = data.seasons.winter.dataframe
winter_daily   = winter_hourly.resample('D').sum()  # Daily totals
winter_weekly  = winter_daily.resample('W').sum()   # Weekly totals
winter_monthly = winter_daily.resample('M').sum()   # Monthly totals
winter_monthly = winter_daily.resample('ME').sum()  # ME is Monthly End   
winter_annual  = winter_daily.resample('Y').sum()   # Annual totals
winter_annual  = winter_daily.resample('YE').sum()   # YE is Year End

#%% Get a typical week for a season (new method!)

winter_week_default = data.seasons.get_typical_week('winter') # Default: Winter uses Jan 15th as start

# Custom Star Date: e.g. Start on Feb 1st
winter_week_custom = data.seasons.get_typical_week('winter', month=2, day=1)

print(f"Default Winter Week Start: {winter_week_default.index[0]}")
print(f"Custom Winter Week Start:  {winter_week_custom.index[0]}")

winter_week = winter_week_custom.dataframe

# Custom week dates
summer_week = data.seasons.get_typical_week('summer', month=7, day=20)
summer_week = summer_week.dataframe

#%% Get extreme weeks (min/max consumption)
extremes = data.get_extreme_weeks()
max_week_df = extremes['max_week'].dataframe  # Highest consumption week
min_week_df = extremes['min_week'].dataframe  # Lowest consumption week

# Daily data from extreme weeks
max_week_daily = extremes['max_week'].dataframe.resample('D').sum()

# Get smoothed data for any period
jan_week = data.slice('2024-01-15', '2024-01-21')
jan_week_smooth = jan_week.smooth(method='spline', points=500)  # Smoothed DataFrame

#%% 6. Plotting (optional)
print("6. Generating Plots...")
output_dir = os.path.join(os.path.dirname(__file__), 'outputs', 'ex-2')

plotter = ConsumptionPlotter(data, output_dir=output_dir)
#paths = plotter.plot_all(prefix="demo")

plotter.plot_seasonal_daily_profile()
plotter.plot_monthly()
plotter.plot_heatmap()
plotter.plot_extreme_weeks()
plotter.plot_seasonal_weeks(seasonal_weeks={
    'winter': (1, 1),   # month=1 (Jan), day=20
    'spring': (4, 15),   # month=4 (Apr), day=15
    'summer': (9, 2),    # month=8 (Aug), day=1
    'autumn': (10, 5)    # month=10 (Oct), day=5
    })

print(f"   Plots saved to: {output_dir}")

