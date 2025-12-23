"""
Equipment Compatibility Module
==============================
Validates electrical compatibility between equipment components.

Example:
    from eclipse.equipment import CompatibilityChecker
    
    checks = CompatibilityChecker.check_module_inverter(module, inverter, 10)
    inverter = CompatibilityChecker.find_compatible_inverter(module, total_modules)
"""

from typing import Optional
from eclipse.config.equipment_models import MockModule, MockInverter


class CompatibilityChecker:
    """
    Validates electrical compatibility between equipment.
    
    Checks voltage, current, and power constraints to ensure
    safe and optimal equipment pairing.
    """
    
    @staticmethod
    def check_module_inverter(
        module: MockModule,
        inverter: MockInverter,
        modules_per_string: int = 1
    ) -> dict:
        """
        Check electrical compatibility between modules and inverter.
        
        Args:
            module: Solar module to check.
            inverter: Inverter to check.
            modules_per_string: Number of modules in series.
            
        Returns:
            Dictionary with compatibility check results:
            - voc_limit: True if string Voc is within inverter limits
            - mppt_range: True if string Vmp is within MPPT range
            - current_limit: True if string current is safe
            - dc_ac_ratio: True if DC/AC ratio is reasonable
            
        Example:
            >>> checks = CompatibilityChecker.check_module_inverter(mod, inv, 10)
            >>> if all(checks.values()):
            ...     print("Compatible!")
        """
        # Calculate string parameters
        # Voc increases at cold temperatures (15% margin)
        string_voc_cold = module.voc * modules_per_string * 1.15
        string_vmpp = module.vmpp * modules_per_string
        string_imp = module.impp
        
        # Total DC power
        total_dc_power = module.power_watts * modules_per_string
        
        # Perform compatibility checks
        checks = {
            "voc_limit": string_voc_cold <= inverter.max_input_voltage,
            "mppt_range": inverter.mppt_low_v <= string_vmpp <= inverter.mppt_high_v,
            "current_limit": string_imp <= inverter.max_input_current,
            "dc_ac_ratio": total_dc_power / inverter.max_ac_power <= 1.5
        }
        
        return checks
    
    @staticmethod
    def find_compatible_inverter(
        module: MockModule,
        total_modules: int
    ) -> Optional[MockInverter]:
        """
        Find a suitable inverter for given modules.
        
        Args:
            module: Solar module type.
            total_modules: Total number of modules to connect.
            
        Returns:
            Compatible MockInverter or None if none found.
            
        Note:
            Uses simplified logic assuming single string configuration.
            For production use, consider multiple string configurations.
        """
        from eclipse.config.equipments import INVERTER_DB
        
        total_power = module.power_watts * total_modules
        
        # Search for compatible inverter
        for inverter in INVERTER_DB:
            # Check if power sizing is reasonable (80-130% of inverter capacity)
            power_ratio = total_power / inverter.max_ac_power
            if not (0.8 <= power_ratio <= 1.3):
                continue
            
            # Check electrical compatibility
            checks = CompatibilityChecker.check_module_inverter(
                module, inverter, total_modules
            )
            
            # Require at least Voc limit to pass
            if checks["voc_limit"]:
                return inverter
        
        # Fallback to second inverter in database for demo
        return INVERTER_DB[1] if len(INVERTER_DB) > 1 else None
