"""
Configuration Settings for PV Sizing
====================================

This file contains default parameters and conversion factors used by the 
kWpSizer and other PV simulation components. Users can adjust these values 
to customize the default behavior of the application.
"""

# ====================================
# General System Sizing Defaults 
# ====================================

# Combined system loss factor (1.15 = 15% losses from inverter, cabling, soiling, etc.)
DEFAULT_LOSS_FACTOR = 1.15

# Default target for self-sufficiency ratio (0.80 = 80% of consumption covered by PV)
# This is used when sizing a system to meet a daily consumption target.
DEFAULT_SELF_SUFFICIENCY = 0.80

# Fallback Peak Sun Hours (kWh/m²/day) used when PSH is not provided and 
# cannot be estimated (e.g., generic calc). Represents Central Europe average.
DEFAULT_PEAK_SUN_HOURS = 3.8


# ====================================
# Advanced PVGIS Simulation Defaults 
# ====================================

# Default module tilt angle in degrees (optimal for annual yield in many regions)
# 0 = horizontal, 90 = vertical
DEFAULT_TILT = 30.0

# Default module azimuth angle in degrees
# 180 = South, 90 = East, 270 = West (in Northern Hemisphere)
DEFAULT_AZIMUTH = 180.0

# Default Performance Ratio (PR) for simulation-based sizing
# 0.85 indicates the system outputs 85% of the DC rating after all losses.
DEFAULT_PERFORMANCE_RATIO = 0.85
