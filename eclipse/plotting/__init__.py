"""
Eclipse Plotting Module
=======================
Centralized visualization utilities for all Eclipse modules.

This package provides domain-specific plotters:
- ConsumptionPlotter: Consumption data visualization
- SizingResultPlotter: PV system sizing visualization
- PVSystemBehaviorPlotter: Comprehensive system behavior analysis
- BatteryPlotter: Battery simulation results
- EconomicsPlotter: Financial analysis charts (future)
"""

from .consumption import ConsumptionPlotter
from .pvsim_plotter import SizingResultPlotter
from .system_behavior import PVSystemBehaviorPlotter
from .battery import BatteryPlotter

__all__ = ['ConsumptionPlotter', 'SizingResultPlotter', 'PVSystemBehaviorPlotter', 'BatteryPlotter']

