"""
Battery Simulation Package
==========================
Provides OOP interface for battery simulation with multiple backends.

Usage:
    from eclipse.battery import SimpleBatterySimulator, PySAMBatterySimulator
    from eclipse.config.equipments.batteries import pysam as battery
    
    sim = PySAMBatterySimulator(battery)
    results = sim.simulate(load_kw, pv_kw)
"""

from eclipse.battery.simulator import BatterySimulator
from eclipse.battery.simple import SimpleBatterySimulator
from eclipse.battery.pysam import PySAMBatterySimulator

__all__ = [
    'BatterySimulator',
    'SimpleBatterySimulator', 
    'PySAMBatterySimulator'
]
