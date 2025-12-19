
import os
import pandas as pd
import pvlib
from typing import Optional, List
import os
import sys
import pandas as pd
import pvlib
from typing import Optional, List
from src.config.equipment_models import MockModule, MockInverter, MockBattery

# Ensure root (solar-tea) is in path to find customization
# sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))
from src.config.equipments import INVERTER_DB

# --- Real Data Integration ---

DATA_DIR = os.path.join(os.path.dirname(__file__), '..', 'data')

def ensure_data_dir():
    if not os.path.exists(DATA_DIR):
        os.makedirs(DATA_DIR)

def get_real_databases():
    """
    Returns curated databases as DataFrames for compatibility with search logic.
    Source: src/config/equipments
    """
    from src.config.equipments import MODULE_DB, INVERTER_DB
    
    # Convert list of dataclasses to DataFrame
    # Transpose is NOT needed here because our list is row-based, 
    # but the original logic expected transposed frames (Rows=Modules).
    # Original logic: modules = modules.T where original SAM was Cols=Modules.
    # Here we build rows directly.
    
    # Modules
    mod_data = {m.name: m.__dict__ for m in MODULE_DB}
    modules_df = pd.DataFrame.from_dict(mod_data, orient='index')
    
    # Inverters
    inv_data = {inv.name: inv.__dict__ for inv in INVERTER_DB}
    inverters_df = pd.DataFrame.from_dict(inv_data, orient='index')
        
    return modules_df, inverters_df

def search_equipment(df: pd.DataFrame, query: str, limit: int = 5) -> pd.DataFrame:
    """Case-insensitive search on index."""
    matches = df[df.index.str.contains(query, case=False, na=False)]
    return matches.head(limit)

def adapt_sandia_module(name: str, row: pd.Series) -> MockModule:
    """
    Converts a Sandia Module row to MockModule format.
    Estimates dimensions if not present (Sandia often lacks explicit W/H, usually has Area).
    """
    # Check if already a MockModule row (from curated DB)
    if 'power_watts' in row:
        # Reconstruct MockModule from the row data
        # Filter row keys to match MockModule fields
        valid_fields = {k: v for k, v in row.items() if k in MockModule.__dataclass_fields__}
        return MockModule(**valid_fields)
        
    area = row.get('Area', 1.7) # Fallback to standard 1.7m2
    # Estimate dims assuming 1.6 aspect ratio standard for older panels, or 1.0:1.7
    # Width ~ sqrt(Area / 1.6), Height ~ Width * 1.6
    # This is a Rough Estimation for layout purposes if data missing.
    width = (area / 1.6) ** 0.5
    height = width * 1.6
    
    # Extract known keys for MockModule
    mod = MockModule(
        name=name,
        power_watts=row.get('Impo', 0) * row.get('Vmpo', 0), # Pmp = Imp * Vmp
        width_m=width,
        height_m=height,
        vmpp=row.get('Vmpo', 0),
        impp=row.get('Impo', 0),
        voc=row.get('Voc', row.get('Voco', 0)), # 'Voco' in Sandia, 'Voc' sometimes standard
        isc=row.get('Isc', row.get('Isco', 0)), # 'Isco' in Sandia
    )
    
    # Populate explicit Sandia params into model_params
    params = {}
    for key, val in row.items():
        # Heuristic: If it's not a standard field, put it in model_params
        # Or specifically target Sandia coeffs: A0..A4, B0..B5, C0..C7
        if key not in ['name', 'Area', 'Material', 'Notes']: 
             params[key] = val
             
    mod.model_params = params
                 
    return mod

def adapt_cec_inverter(name: str, row: pd.Series) -> MockInverter:

    """
    Converts a CEC Inverter row to MockInverter format.
    """
    # Check if already a MockInverter row (from curated DB)
    if 'max_ac_power' in row:
        valid_fields = {k: v for k, v in row.items() if k in MockInverter.__dataclass_fields__}
        return MockInverter(**valid_fields)

    inv = MockInverter(
        name=name,
        max_ac_power=row.get('Paco', 0), # AC Power Rating
        mppt_low_v=row.get('Mppt_low', row.get('Vdcmin', 100)), 
        mppt_high_v=row.get('Mppt_high', row.get('Vdcmax', 500)), 
        max_input_voltage=row.get('Vdcmax', 600),
        max_input_current=row.get('Idcmax', 15),
    )
    
    # Populate CEC params into model_params
    params = {}
    # Explicit list of CEC params to look for
    cec_fields = ['Vac', 'Pso', 'Paco', 'Pdco', 'Vdco', 'C0', 'C1', 'C2', 'C3', 'Pnt']
    for field in cec_fields:
        if field in row:
            params[field] = row[field]
            
    inv.model_params = params
                 
    return inv


# --- End Real Data Integration ---

def check_module_inverter_compat(module: MockModule, inverter: MockInverter, modules_per_string: int = 1) -> dict:
    """
    Checks electrical compatibility between a module string and an inverter.
    """
    string_voc_cold = module.voc * modules_per_string * 1.15 # Assuming 15% rise at cold temp
    string_vmpp = module.vmpp * modules_per_string
    string_imp = module.impp
    
    checks = {
        "voc_limit": string_voc_cold <= inverter.max_input_voltage,
        "mppt_range": inverter.mppt_low_v <= string_vmpp <= inverter.mppt_high_v,
        "current_limit": string_imp <= inverter.max_input_current,
        "dc_ac_ratio": (module.power_watts * modules_per_string) / inverter.max_ac_power <= 1.5 # Allow up to 1.5 DC/AC ratio
    }
    
    return checks

def get_compatible_inverter(module: MockModule, total_modules: int) -> Optional[MockInverter]:
    """
    Finds a suitable inverter for a given total number of modules.
    Simplified logic: Assumes 1 or 2 strings max for string inverters.
    """
    total_power = module.power_watts * total_modules
    
    for inverter in INVERTER_DB:
        # Simple size check first
        if 0.8 <= total_power / inverter.max_ac_power <= 1.3:
            # Check electricals for a single string configuration (simplified)
             if check_module_inverter_compat(module, inverter, total_modules)["voc_limit"]:
                 return inverter
                 
    return INVERTER_DB[1] # Default fallback for demo
