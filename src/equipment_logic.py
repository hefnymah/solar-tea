
import os
import pandas as pd
import pvlib
from typing import Optional, List
import os
import sys
import pandas as pd
import pvlib
from typing import Optional, List
from .equipment_models import MockModule, MockInverter, MockBattery

# Ensure root (sys-size) is in path to find user_data
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))
from user_data.custom_equipment import INVERTER_DB

# --- Real Data Integration ---

DATA_DIR = os.path.join(os.path.dirname(__file__), '..', 'data')

def ensure_data_dir():
    if not os.path.exists(DATA_DIR):
        os.makedirs(DATA_DIR)

def get_real_databases():
    """
    Retrieves SandiaMod and CECInverter databases using pvlib.
    Caches them locally in sys-size/data/ to save bandwidth.
    """
    ensure_data_dir()
    
    mod_path = os.path.join(DATA_DIR, 'SandiaMod.csv')
    inv_path = os.path.join(DATA_DIR, 'CECInverter.csv')
    
    # Modules
    if os.path.exists(mod_path):
        modules = pd.read_csv(mod_path, index_col=0)
    else:
        print("Downloading Sandia Module Database...")
        modules = pvlib.pvsystem.retrieve_sam('SandiaMod')
        modules = modules.T # Transpose: Rows=Modules, Cols=Params
        modules.to_csv(mod_path)
        
    # Inverters
    if os.path.exists(inv_path):
        inverters = pd.read_csv(inv_path, index_col=0)
    else:
        print("Downloading CEC Inverter Database...")
        inverters = pvlib.pvsystem.retrieve_sam('cecinverter')
        inverters = inverters.T # Transpose: Rows=Inverters, Cols=Params
        inverters.to_csv(inv_path)
        
    return modules, inverters

def search_equipment(df: pd.DataFrame, query: str, limit: int = 5) -> pd.DataFrame:
    """Case-insensitive search on index."""
    matches = df[df.index.str.contains(query, case=False, na=False)]
    return matches.head(limit)

def adapt_sandia_module(name: str, row: pd.Series) -> MockModule:
    """
    Converts a Sandia Module row to MockModule format.
    Estimates dimensions if not present (Sandia often lacks explicit W/H, usually has Area).
    """
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
    
    # Populate explicit Sandia params
    for field_name in MockModule.__dataclass_fields__:
        if field_name not in ['name', 'power_watts', 'width_m', 'height_m', 'vmpp', 'impp', 'voc', 'isc']:
            if field_name in row:
                setattr(mod, field_name, row[field_name])
                
    return mod

def adapt_cec_inverter(name: str, row: pd.Series) -> MockInverter:

    """
    Converts a CEC Inverter row to MockInverter format.
    """
    inv = MockInverter(
        name=name,
        max_ac_power=row.get('Paco', 0), # AC Power Rating
        mppt_low_v=row.get('Mppt_low', row.get('Vdcmin', 100)), 
        mppt_high_v=row.get('Mppt_high', row.get('Vdcmax', 500)), 
        max_input_voltage=row.get('Vdcmax', 600),
        max_input_current=row.get('Idcmax', 15),
    )
    
    # Populate explicit CEC params
    for field_name in MockInverter.__dataclass_fields__:
        if field_name not in ['name', 'max_ac_power', 'mppt_low_v', 'mppt_high_v', 'max_input_voltage', 'max_input_current']:
             if field_name in row:
                setattr(inv, field_name, row[field_name])
                
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
