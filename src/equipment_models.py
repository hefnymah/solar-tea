
from dataclasses import dataclass, field
from typing import List, Optional, Tuple

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


@dataclass
class MockBattery:
    name: str
    nominal_energy_kwh: float  # Capacity
    nominal_voltage_v: float
    max_charge_power_kw: float
    max_discharge_power_kw: float
    
    # Chemistry / PySAM Params
    chem: int = 1 # 0=LeadAcid, 1=Li-ion
    min_soc: float = 20.0
    max_soc: float = 95.0
    initial_soc: float = 95.0
    
    
    # Cell Specs (Defaults for Li-ion)
    v_nom_cell: float = 3.6
    v_max_cell: float = 4.1
    v_min_cell: float = 3.0
    q_full_cell: float = 3.0
    resistance: float = 0.01
    
    # Shepherd Model (Voltage Curve)
    v_exp: Optional[float] = None
    q_exp: Optional[float] = None
    q_nom: Optional[float] = None
    v_nom_curve: Optional[float] = None # Vnom for curve logic might differ slightly from v_nom_cell
    c_rate: Optional[float] = None
    
    # Lead Acid Specifics (Optional)
    q10: Optional[float] = None
    q20: Optional[float] = None
    qn: Optional[float] = None
    tn: Optional[float] = None
