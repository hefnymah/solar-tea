
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
    
    def __post_init__(self):
        # Convert dictionaries to SimpleNamespace for dot notation access
        # e.g. module.performance.efficiency instead of module.performance['efficiency']
        from types import SimpleNamespace
        
        def dict_to_ns(d):
            if isinstance(d, dict):
                return SimpleNamespace(**d)
            return d

        if self.dimensions and isinstance(self.dimensions, dict): self.dimensions = dict_to_ns(self.dimensions)
        if self.economics and isinstance(self.economics, dict): self.economics = dict_to_ns(self.economics)
        if self.warranty and isinstance(self.warranty, dict): self.warranty = dict_to_ns(self.warranty)
        if self.certifications and isinstance(self.certifications, dict): self.certifications = dict_to_ns(self.certifications)
        if self.performance and isinstance(self.performance, dict): self.performance = dict_to_ns(self.performance)

        # Automatic Interpolation for Degradation
        # Safely get a value from either dict or SimpleNamespace
        def get_w(key):
            obj = self.warranty
            if isinstance(obj, dict):
                return obj.get(key)
            elif obj:
                return getattr(obj, key, None)
            return None
            
        def set_w(key, value):
            if isinstance(self.warranty, dict):
                self.warranty[key] = value
            elif self.warranty:
                setattr(self.warranty, key, value)
        
        p1 = get_w('performance_guarantee_year_1')
        p25 = get_w('performance_guarantee_year_25')
        p30 = get_w('performance_guarantee_year_30')
        
        # If we have p1 and (p30 only), interpolate p25
        if p1 is not None and p30 is not None and p25 is None:
            # Linear degradation: rate per year
            # (p1 - p30) / (30 - 1)
            rate = (p1 - p30) / 29.0
            p25_calc = p1 - (rate * 24.0)
            set_w('performance_guarantee_year_25', round(p25_calc, 1))

        # If we have p1 and (p25 only), extrapolate p30 (if warranty allows > 25)
        # However, usually p30 is the input if the warranty is 30 years.
        # But for completeness:
        if p1 is not None and p25 is not None and p30 is None:
             rate = (p1 - p25) / 24.0
             p30_calc = p1 - (rate * 29.0)
             set_w('performance_guarantee_year_30', round(p30_calc, 1))

    @property
    def degradation_yearly(self) -> float:
        """Alias for annual_degradation_rate as requested."""
        return self.annual_degradation_rate

    @property
    def annual_degradation_rate(self) -> float:
        """
        Returns the annual linear degradation rate as a percentage (e.g., 0.55).
        Calculated from warranty data.
        """
        # Handle case where warranty was converted to SimpleNamespace
        w = self.warranty
        if not w:
            return 0.55 # Conservative default
            
        # Helper to get attr or Item
        def get(obj, key, default):
            if isinstance(obj, dict): return obj.get(key, default)
            return getattr(obj, key, default)
            
        # Check if SimpleNamespace or dict
        p1 = get(w, 'performance_guarantee_year_1', 98.0)
        
        # Find endpoint
        if get(w, 'performance_guarantee_year_30', None):
            p_end = get(w, 'performance_guarantee_year_30', 84.8)
            y_end = 30
        elif get(w, 'performance_guarantee_year_25', None):
            p_end = get(w, 'performance_guarantee_year_25', 84.8)
            y_end = 25
        else:
            p_end = 84.8 
            y_end = 25
            
        total_deg_period = p1 - p_end
        years_period = y_end - 1
        return round(total_deg_period / years_period, 3)

    def get_degradation_at_year(self, year: int) -> float:
        """
        Calculates the degradation percentage at a specific year based on warranty data.
        Returns percentage lost (e.g., 15.2 for 15.2% degradation).
        """
        # Access annual_degradation_rate which handles the generic access
        if not self.warranty:
            return 0.0
            
        # We need p1 again
        def get(obj, key, default):
            if isinstance(obj, dict): return obj.get(key, default)
            return getattr(obj, key, default)
            
        p1 = get(self.warranty, 'performance_guarantee_year_1', 98.0)
        
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
    
    @property
    def area_m2(self) -> float:
        """Calculates module area in square meters."""
        return round(self.width_m * self.height_m, 2)

    def __post_init__(self):
        super().__post_init__()
        
        from types import SimpleNamespace
        def dict_to_ns(d):
            if isinstance(d, dict): return SimpleNamespace(**d)
            return d

        if self.mechanical and isinstance(self.mechanical, dict): self.mechanical = dict_to_ns(self.mechanical)
        if self.environmental and isinstance(self.environmental, dict): self.environmental = dict_to_ns(self.environmental)


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
    
    def __post_init__(self):
        super().__post_init__()
        
        from types import SimpleNamespace
        def dict_to_ns(d):
            if isinstance(d, dict): return SimpleNamespace(**d)
            return d

        if self.features and isinstance(self.features, dict): self.features = dict_to_ns(self.features)
        if self.interfaces and isinstance(self.interfaces, dict): self.interfaces = dict_to_ns(self.interfaces)


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
