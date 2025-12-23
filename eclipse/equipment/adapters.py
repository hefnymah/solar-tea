"""
Equipment Adapters Module
=========================
Converts between different equipment database formats.

Example:
    from eclipse.equipment import SandiaModuleAdapter, CECInverterAdapter
    
    module = SandiaModuleAdapter.adapt('Module_Name', row)
    inverter = CECInverterAdapter.adapt('Inverter_Name', row)
"""

import pandas as pd
from eclipse.config.equipment_models import MockModule, MockInverter


class SandiaModuleAdapter:
    """
    Converts Sandia Module Database format to MockModule.
    
    The Sandia database uses different field names and may lack
    physical dimensions, which this adapter estimates when needed.
    """
    
    @staticmethod
    def adapt(name: str, row: pd.Series) -> MockModule:
        """
        Convert Sandia database row to MockModule.
        
        Args:
            name: Module name.
            row: Pandas Series with Sandia module data.
            
        Returns:
            MockModule instance.
            
        Note:
            If dimensions are missing, estimates based on area
            with standard 1.6 aspect ratio.
        """
        # Check if already a MockModule row (from curated DB)
        if 'power_watts' in row:
            # Reconstruct MockModule from existing data
            valid_fields = {
                k: v for k, v in row.items() 
                if k in MockModule.__dataclass_fields__
            }
            return MockModule(**valid_fields)
        
        # Estimate dimensions if not present
        area = row.get('Area', 1.7)  # Fallback to standard 1.7m²
        width = (area / 1.6) ** 0.5
        height = width * 1.6
        
        # Create MockModule with Sandia fields
        mod = MockModule(
            name=name,
            power_watts=row.get('Impo', 0) * row.get('Vmpo', 0),  # Pmp = Imp * Vmp
            width_m=width,
            height_m=height,
            vmpp=row.get('Vmpo', 0),
            impp=row.get('Impo', 0),
            voc=row.get('Voc', row.get('Voco', 0)),
            isc=row.get('Isc', row.get('Isco', 0)),
        )
        
        # Store Sandia-specific parameters
        params = {}
        for key, val in row.items():
            if key not in ['name', 'Area', 'Material', 'Notes']:
                params[key] = val
        
        mod.model_params = params
        return mod


class CECInverterAdapter:
    """
    Converts CEC Inverter Database format to MockInverter.
    
    The CEC database uses specific field names for electrical
    parameters and efficiency coefficients.
    """
    
    @staticmethod
    def adapt(name: str, row: pd.Series) -> MockInverter:
        """
        Convert CEC database row to MockInverter.
        
        Args:
            name: Inverter name.
            row: Pandas Series with CEC inverter data.
            
        Returns:
            MockInverter instance.
        """
        # Check if already a MockInverter row (from curated DB)
        if 'max_ac_power' in row:
            valid_fields = {
                k: v for k, v in row.items() 
                if k in MockInverter.__dataclass_fields__
            }
            return MockInverter(**valid_fields)
        
        # Create MockInverter with CEC fields
        inv = MockInverter(
            name=name,
            max_ac_power=row.get('Paco', 0),  # AC Power Rating
            mppt_low_v=row.get('Mppt_low', row.get('Vdcmin', 100)),
            mppt_high_v=row.get('Mppt_high', row.get('Vdcmax', 500)),
            max_input_voltage=row.get('Vdcmax', 600),
            max_input_current=row.get('Idcmax', 15),
        )
        
        # Store CEC-specific parameters
        params = {}
        cec_fields = ['Vac', 'Pso', 'Paco', 'Pdco', 'Vdco', 
                      'C0', 'C1', 'C2', 'C3', 'Pnt']
        for field in cec_fields:
            if field in row:
                params[field] = row[field]
        
        inv.model_params = params
        return inv
