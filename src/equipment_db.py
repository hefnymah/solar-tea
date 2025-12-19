
from dataclasses import dataclass, field
from typing import List, Optional, Tuple


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

BATTERY_DB = [
    MockBattery(
        name="Tesla_Powerwall_2",
        nominal_energy_kwh=13.5,
        nominal_voltage_v=50, 
        max_charge_power_kw=5.0,
        max_discharge_power_kw=5.0,
        min_soc=10.0,
        max_soc=100.0,
        # Standard Li-ion estimates
        v_exp=4.05, q_exp=0.05, q_nom=3.0, v_nom_curve=3.6, c_rate=1.0
    ),
    MockBattery(
        name="BYD_Battery-Box_Premium_HVS_10.2",
        nominal_energy_kwh=10.2,
        nominal_voltage_v=400,
        max_charge_power_kw=10.2,
        max_discharge_power_kw=10.2,
        min_soc=5.0,
        max_soc=100.0,
         # LiFePO4 approx
        v_nom_cell=3.2, v_max_cell=3.65, v_min_cell=2.5,
        v_exp=3.5, q_exp=0.02, q_nom=2.8, v_nom_curve=3.2, c_rate=1.0
    ),
    MockBattery(
        name="LG_Chem_RESU_10H",
        nominal_energy_kwh=9.8,
        nominal_voltage_v=400,
        max_charge_power_kw=5.0,
        max_discharge_power_kw=5.0,
        min_soc=5.0,
        max_soc=95.0,
        chem=1
    ),
    MockBattery(
        name="Generic_LeadAcid_10kWh",
        nominal_energy_kwh=10.0,
        nominal_voltage_v=48,
        max_charge_power_kw=2.0,
        max_discharge_power_kw=3.0,
        min_soc=40.0, # Lead Acid shouldn't go too deep
        max_soc=100.0,
        chem=0, # Lead Acid
        v_nom_cell=2.0, v_max_cell=2.4, v_min_cell=1.75,
        q10=100, q20=110, qn=100, tn=20 # Examples
    )
]
