"""
Equipment Package
================
OOP-based equipment management for solar system design.

Provides:
- EquipmentDatabase: Manage and search equipment databases
- SandiaModuleAdapter: Convert Sandia format to MockModule
- CECInverterAdapter: Convert CEC format to MockInverter
- CompatibilityChecker: Validate equipment compatibility

Example:
    from eclipse.equipment import (
        EquipmentDatabase, 
        SandiaModuleAdapter, CECInverterAdapter,
        CompatibilityChecker
    )
    
    # Load and search equipment
    db = EquipmentDatabase()
    modules = db.search_modules('Trina', limit=5)
    
    # Adapt database formats
    module = SandiaModuleAdapter.adapt('Module_Name', row)
    
    # Check compatibility
    checks = CompatibilityChecker.check_module_inverter(module, inverter, 10)
"""

from .database import EquipmentDatabase
from .adapters import SandiaModuleAdapter, CECInverterAdapter
from .compatibility import CompatibilityChecker

__all__ = [
    'EquipmentDatabase',
    'SandiaModuleAdapter',
    'CECInverterAdapter',
    'CompatibilityChecker'
]
