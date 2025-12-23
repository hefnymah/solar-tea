"""
Eclipse Plotting Module
=======================
Centralized visualization utilities for all Eclipse modules.

This package provides domain-specific plotters:
- ConsumptionPlotter: Consumption data visualization
- BatteryPlotter: Battery simulation results (future)
- PVPlotter: PV system visualization (future)
- EconomicsPlotter: Financial analysis charts (future)
"""

from .consumption import ConsumptionPlotter

__all__ = ['ConsumptionPlotter']
