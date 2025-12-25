"""
Consumption Analysis Package
============================
Provides tools for analyzing energy consumption data.

Classes:
    ConsumptionData: OOP data accessor with nested structure (hourly, daily, seasons).
    ConsumptionPlotter: Separated plotting logic for visualization.
    ConsumptionAnalyzer: Backward-compatible facade.

Example:
    from eclipse.consumption import ConsumptionData, ConsumptionPlotter
    
    data = ConsumptionData.from_file("load_2025.csv")
    print(data.hourly.sum())         # Total kWh
    print(data.seasons.winter.mean()) # Winter avg
    
    plotter = ConsumptionPlotter(data, output_dir="./output")
    plotter.plot_all()

Example (Legacy API):
    from eclipse.consumption import ConsumptionAnalyzer
    
    analyzer = ConsumptionAnalyzer(output_dir="./output")
    analyzer.load_data("consumption.csv")
    analyzer.plot_all()
"""

from eclipse.consumption.data import ConsumptionData, TimeSeriesAccessor, SeasonalAccessor
from eclipse.consumption.analyzer import ConsumptionAnalyzer

__all__ = [
    'ConsumptionData',
    'TimeSeriesAccessor',
    'SeasonalAccessor',
    'ConsumptionAnalyzer',
]
