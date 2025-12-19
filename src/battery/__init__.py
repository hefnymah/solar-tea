"""
Battery Simulation Package
==========================
Provides OOP interface for battery simulation with multiple backends.

Usage:
    from src.battery import SimpleBatterySimulator, PySAMBatterySimulator
    from src.config.equipments.batteries import pysam as battery
    
    sim = PySAMBatterySimulator(battery)
    results = sim.simulate(load_kw, pv_kw)
"""

from src.battery.simulator import BatterySimulator
from src.battery.simple import SimpleBatterySimulator
from src.battery.pysam import PySAMBatterySimulator

__all__ = [
    'BatterySimulator',
    'SimpleBatterySimulator', 
    'PySAMBatterySimulator'
]
