
from dataclasses import dataclass, field
from typing import List, Optional, Dict

@dataclass
class Equipment:
    """Base class for all PV equipment."""
    name: str = ""
    
    # Metadata containers
    dimensions: Optional[Dict] = None
    economics: Optional[Dict] = None
    warranty: Optional[Dict] = None
    certifications: Optional[Dict] = None
    performance: Optional[Dict] = None
    
    # Generic model parameters bucket (Sandia, CEC, PVWatts etc.)
    # All non-standard electrical params go here (e.g., gamma_pdc, C0, A0)
    model_params: Dict = field(default_factory=dict)
    
    @property
    def annual_degradation_rate(self) -> float:
        """
        Returns the annual linear degradation rate as a percentage (e.g., 0.55).
        Calculated from warranty data.
        """
        if not self.warranty:
            return 0.55 # Conservative default
            
        w = self.warranty
        p1 = w.get('performance_guarantee_year_1', 98.0)
        
        # Find endpoint
        if 'performance_guarantee_year_30' in w:
            p_end = w['performance_guarantee_year_30']
            y_end = 30
        elif 'performance_guarantee_year_25' in w:
            p_end = w['performance_guarantee_year_25']
            y_end = 25
        else:
            p_end = 84.8 # Standard fallback
            y_end = 25
            
        total_deg_period = p1 - p_end
        years_period = y_end - 1
        return round(total_deg_period / years_period, 3)

    def get_degradation_at_year(self, year: int) -> float:
        """
        Calculates the degradation percentage at a specific year based on warranty data.
        Returns percentage lost (e.g., 15.2 for 15.2% degradation).
        """
        if not self.warranty:
            return 0.0
            
        w = self.warranty
        p1 = w.get('performance_guarantee_year_1', 98.0)
        
        if year <= 1:
            return float(100.0 - p1)
        
        annual_deg = self.annual_degradation_rate
        current_perf = p1 - (annual_deg * (year - 1))
        return round(100.0 - current_perf, 2)


@dataclass
class MockModule(Equipment):
    """Solar Module Representation."""
    power_watts: float = 0.0
    width_m: float = 0.0
    height_m: float = 0.0
    vmpp: float = 0.0
    impp: float = 0.0
    voc: float = 0.0
    isc: float = 0.0
    
    # Additional specific fields
    mechanical: Optional[Dict] = None
    environmental: Optional[Dict] = None
    Notes: Optional[str] = None
    
    def __post_init__(self):
        # Support kwargs-like behavior for backward compatibility if needed, 
        # or just strictly enforce model_params usage.
        pass


@dataclass
class MockInverter(Equipment):
    """Inverter Representation."""
    max_ac_power: float = 0.0
    mppt_low_v: float = 0.0
    mppt_high_v: float = 0.0
    max_input_voltage: float = 0.0
    max_input_current: float = 0.0
    
    features: Optional[Dict] = None
    interfaces: Optional[Dict] = None


@dataclass
class MockBattery(Equipment):
    """Battery Representation."""
    nominal_energy_kwh: float = 0.0
    nominal_voltage_v: float = 0.0
    max_charge_power_kw: float = 0.0
    max_discharge_power_kw: float = 0.0
    
    min_soc: float = 20.0
    max_soc: float = 95.0
    initial_soc: float = 95.0
    
    chem: int = 1 # 0=LeadAcid, 1=Li-ion
    
    # Cell parameters can be considered "model_params" too, but some are structural.
    # We'll keep explicit ones for now if they are common.
    # But ideally, move specialized chemistry params to model_params too.
    # For now, keeping them to minimize disruption to battery logic.
    
    # Cell Specs (Defaults for Li-ion)
    v_nom_cell: float = 3.6
    v_max_cell: float = 4.1
    v_min_cell: float = 3.0
    q_full_cell: float = 3.0
    resistance: float = 0.01
    
    # Shepherd Model (Voltage Curve) - Move to model_params?
    # Keeping mostly explicit for now, but cleaner. 
    # Actually, Shepherd params are model params.
    # Let's clean them up? The prompt asked to delete unnecessary lines.
    # I will keep them explicit as they are used in `battery_pysam.py` directly by attribute.
    
    v_exp: Optional[float] = None
    q_exp: Optional[float] = None
    q_nom: Optional[float] = None
    v_nom_curve: Optional[float] = None 
    c_rate: Optional[float] = None
    
    q10: Optional[float] = None
    q20: Optional[float] = None
    qn: Optional[float] = None
    tn: Optional[float] = None
