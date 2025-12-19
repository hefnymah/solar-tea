
from dataclasses import dataclass, field
from typing import List, Optional, Tuple

import pandas as pd
import pvlib
import os

@dataclass
class MockModule:
    name: str
    power_watts: float
    width_m: float
    height_m: float
    vmpp: float  # Voltage at maximum power point
    impp: float  # Current at maximum power point
    voc: float   # Open circuit voltage
    isc: float   # Short circuit current
    
    # Sandia Parameters (Explicit)
    Vintage: Optional[str] = None
    Area: Optional[float] = None
    Material: Optional[str] = None
    Cells_in_Series: Optional[int] = None
    Parallel_Strings: Optional[int] = None
    Isco: Optional[float] = None
    Voco: Optional[float] = None
    Impo: Optional[float] = None
    Vmpo: Optional[float] = None
    Aisc: Optional[float] = None
    Aimp: Optional[float] = None
    C0: Optional[float] = None
    C1: Optional[float] = None
    Bvoco: Optional[float] = None
    Mbvoc: Optional[float] = None
    Bvmpo: Optional[float] = None
    Mbvmp: Optional[float] = None
    N: Optional[float] = None
    C2: Optional[float] = None
    C3: Optional[float] = None
    A0: Optional[float] = None
    A1: Optional[float] = None
    A2: Optional[float] = None
    A3: Optional[float] = None
    A4: Optional[float] = None
    B0: Optional[float] = None
    B1: Optional[float] = None
    B2: Optional[float] = None
    B3: Optional[float] = None
    B4: Optional[float] = None
    B5: Optional[float] = None
    DTC: Optional[float] = None
    FD: Optional[float] = None
    A: Optional[float] = None
    B: Optional[float] = None
    C4: Optional[float] = None
    C5: Optional[float] = None
    IXO: Optional[float] = None
    IXXO: Optional[float] = None
    C6: Optional[float] = None
    C7: Optional[float] = None
    Notes: Optional[str] = None


@dataclass
class MockInverter:
    name: str
    max_ac_power: float
    mppt_low_v: float
    mppt_high_v: float
    max_input_voltage: float
    max_input_current: float
    
    # CEC Parameters (Explicit)
    Vac: Optional[float] = None
    Pso: Optional[float] = None
    Paco: Optional[float] = None
    Pdco: Optional[float] = None
    Vdco: Optional[float] = None
    C0: Optional[float] = None
    C1: Optional[float] = None
    C2: Optional[float] = None
    C3: Optional[float] = None
    Pnt: Optional[float] = None
    Vdcmax: Optional[float] = None
    Idcmax: Optional[float] = None
    Mppt_low: Optional[float] = None
    Mppt_high: Optional[float] = None
    CEC_Date: Optional[str] = None
    CEC_Type: Optional[str] = None


# Mock Database (Preserved)
# Mock Database (Preserved)
# Using only mandatory fields, defaulting extended params to None
MODULE_DB = [
    MockModule(
        name="SunPower_X22_360", 
        power_watts=360, 
        width_m=1.046, 
        height_m=1.559, 
        vmpp=59.8, 
        impp=6.02, 
        voc=69.5, 
        isc=6.48,
        # Sandia Params
        Vintage=None, Area=None, Material=None, Cells_in_Series=None, Parallel_Strings=None,
        Isco=None, Voco=None, Impo=None, Vmpo=None, Aisc=None, Aimp=None,
        C0=None, C1=None, Bvoco=None, Mbvoc=None, Bvmpo=None, Mbvmp=None,
        N=None, C2=None, C3=None, A0=None, A1=None, A2=None, A3=None, A4=None,
        B0=None, B1=None, B2=None, B3=None, B4=None, B5=None,
        DTC=None, FD=None, A=None, B=None, C4=None, C5=None,
        IXO=None, IXXO=None, C6=None, C7=None, Notes=None
    ),
    MockModule(
        name="Trina_VertexS_400", 
        power_watts=400, 
        width_m=1.096, 
        height_m=1.754, 
        vmpp=34.2, 
        impp=11.7, 
        voc=41.2, 
        isc=12.28,
        # Sandia Params
        Vintage=None, Area=None, Material=None, Cells_in_Series=None, Parallel_Strings=None,
        Isco=None, Voco=None, Impo=None, Vmpo=None, Aisc=None, Aimp=None,
        C0=None, C1=None, Bvoco=None, Mbvoc=None, Bvmpo=None, Mbvmp=None,
        N=None, C2=None, C3=None, A0=None, A1=None, A2=None, A3=None, A4=None,
        B0=None, B1=None, B2=None, B3=None, B4=None, B5=None,
        DTC=None, FD=None, A=None, B=None, C4=None, C5=None,
        IXO=None, IXXO=None, C6=None, C7=None, Notes=None
    ),
    MockModule(
        name="CanadianSolar_450", 
        power_watts=450, 
        width_m=1.048, 
        height_m=2.108, 
        vmpp=41.3, 
        impp=10.9, 
        voc=49.3, 
        isc=11.6,
        # Sandia Params
        Vintage=None, Area=None, Material=None, Cells_in_Series=None, Parallel_Strings=None,
        Isco=None, Voco=None, Impo=None, Vmpo=None, Aisc=None, Aimp=None,
        C0=None, C1=None, Bvoco=None, Mbvoc=None, Bvmpo=None, Mbvmp=None,
        N=None, C2=None, C3=None, A0=None, A1=None, A2=None, A3=None, A4=None,
        B0=None, B1=None, B2=None, B3=None, B4=None, B5=None,
        DTC=None, FD=None, A=None, B=None, C4=None, C5=None,
        IXO=None, IXXO=None, C6=None, C7=None, Notes=None
    ),
]

INVERTER_DB = [
    MockInverter(
        name="SunnyBoy_3.0", 
        max_ac_power=3000, 
        mppt_low_v=100, 
        mppt_high_v=500, 
        max_input_voltage=600, 
        max_input_current=15,
        # CEC Params
        Vac=None, Pso=None, Paco=None, Pdco=None, Vdco=None,
        C0=None, C1=None, C2=None, C3=None, Pnt=None,
        Vdcmax=None, Idcmax=None, Mppt_low=None, Mppt_high=None,
        CEC_Date=None, CEC_Type=None
    ),
    MockInverter(
        name="Fronius_Primo_5.0", 
        max_ac_power=5000, 
        mppt_low_v=80, 
        mppt_high_v=800, 
        max_input_voltage=1000, 
        max_input_current=18,
        # CEC Params
        Vac=None, Pso=None, Paco=None, Pdco=None, Vdco=None,
        C0=None, C1=None, C2=None, C3=None, Pnt=None,
        Vdcmax=None, Idcmax=None, Mppt_low=None, Mppt_high=None,
        CEC_Date=None, CEC_Type=None
    ),
    MockInverter(
        name="Enphase_IQ7", 
        max_ac_power=290, 
        mppt_low_v=27, 
        mppt_high_v=45, 
        max_input_voltage=60, 
        max_input_current=10,
        # CEC Params
        Vac=None, Pso=None, Paco=None, Pdco=None, Vdco=None,
        C0=None, C1=None, C2=None, C3=None, Pnt=None,
        Vdcmax=None, Idcmax=None, Mppt_low=None, Mppt_high=None,
        CEC_Date=None, CEC_Type=None
    ), 
]


# --- Real Data Integration ---

DATA_DIR = os.path.join(os.path.dirname(__file__), 'data')

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
