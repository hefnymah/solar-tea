"""
Battery Simulation Package
==========================
Provides OOP interface for battery simulation with multiple backends.

Usage:
    from eclipse.battery import SimpleBatterySimulator, PySAMBatterySimulator
    from eclipse.config.equipments.batteries import pysam as battery
    
    sim = PySAMBatterySimulator(battery)
    results = sim.simulate(load_kw, pv_kw)
    
    # Sizing
    from eclipse.battery import BatterySizer
    sizer = BatterySizer(pv_kwp=6.0, daily_load_kwh=15.0)
    result = sizer.recommend(load_kw, pv_kw, target_autonomy_days=1.0)
"""

from eclipse.battery.simulator import BatterySimulator
from eclipse.battery.simple import SimpleBatterySimulator
from eclipse.battery.sizer import BatterySizer, SizingResult

# PySAM is optional - only import if available
try:
    from eclipse.battery.pysam import PySAMBatterySimulator
    _PYSAM_AVAILABLE = True
except ImportError:
    PySAMBatterySimulator = None
    _PYSAM_AVAILABLE = False

__all__ = [
    'BatterySimulator',
    'SimpleBatterySimulator', 
    'PySAMBatterySimulator',
    'BatterySizer',
    'SizingResult'
]
