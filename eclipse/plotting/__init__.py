"""
Eclipse Plotting Module
=======================
Centralized visualization utilities for all Eclipse modules.

This package provides domain-specific plotters:
- ConsumptionPlotter: Consumption data visualization
- SizingResultPlotter: PV system sizing visualization
- BatteryPlotter: Battery simulation results (future)
- EconomicsPlotter: Financial analysis charts (future)
"""

from .consumption import ConsumptionPlotter
from .pvsim_plotter import SizingResultPlotter

__all__ = ['ConsumptionPlotter', 'SizingResultPlotter']
