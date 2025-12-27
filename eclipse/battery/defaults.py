"""
Battery Physics Configuration
=============================
Default cell-level parameters for battery simulation engines (PySAM, Simple).

These are GENERIC physics parameters, not tied to specific commercial brands.
Commercial brand/model data lives in: eclipse/config/equipments/batteries.py
"""

from dataclasses import dataclass, field
from typing import List, Optional
from enum import Enum


class CellChemistry(Enum):
    """Battery cell chemistry types."""
    LEAD_ACID = 0
    LITHIUM_ION = 1


@dataclass
class CellPhysicsConfig:
    """
    Low-level cell parameters for physics-based battery simulation.
    
    Used by PySAM BatteryStateful to model voltage curves, thermal effects,
    and degradation behavior.
    """
    # Chemistry
    chemistry: CellChemistry = CellChemistry.LITHIUM_ION
    
    # Voltage Curve (Shepherd Model)
    v_nom_cell: float = 3.6       # Nominal cell voltage (V)
    v_max_cell: float = 4.1       # Maximum cell voltage (V)
    v_min_cell: float = 3.0       # Minimum cell voltage (V)
    q_full_cell: float = 3.0      # Full charge capacity (Ah)
    resistance: float = 0.01      # Internal resistance (Ohms)
    
    # Shepherd Parameters
    v_exp: float = 4.05           # Exponential zone voltage
    q_exp: float = 0.05           # Exponential zone capacity
    q_nom: float = 3.0            # Nominal capacity
    v_nom_curve: float = 3.6      # Nominal voltage on curve
    c_rate: float = 1.0           # C-rate for discharge curve
    
    # Life Model
    life_model: int = 0           # 0=None, 1=Capacity fade
    calendar_choice: int = 0      # 0=None, 1=Calendar aging
    cycling_matrix: List = field(default_factory=lambda: [
        [0, 0, 100],       # [DOD%, Cycles, Remaining Capacity%]
        [50, 5000, 90],
        [100, 5000, 80]
    ])
    
    # Thermal Properties
    mass_kg: float = 500.0
    surface_area_m2: float = 2.0
    specific_heat_j_kg_k: float = 1000.0
    heat_transfer_coeff: float = 20.0
    initial_temp_c: float = 20.0
    
    # Capacity vs Temperature: [[Temp_C, Capacity_%], ...]
    cap_vs_temp: List = field(default_factory=lambda: [
        [-20, 60],
        [0, 80],
        [25, 100],
        [40, 100]
    ])
    
    # Losses (monthly arrays for seasonal effects)
    loss_choice: int = 0
    monthly_charge_loss: List = field(default_factory=lambda: [0]*12)
    monthly_discharge_loss: List = field(default_factory=lambda: [0]*12)
    monthly_idle_loss: List = field(default_factory=lambda: [0]*12)


# ════════════════════════════════════════════════════════════════════════════
# PRE-CONFIGURED DEFAULTS BY CHEMISTRY
# ════════════════════════════════════════════════════════════════════════════

LFP_CELL_CONFIG = CellPhysicsConfig(
    chemistry=CellChemistry.LITHIUM_ION,
    v_nom_cell=3.2,       # LFP has lower nominal voltage
    v_max_cell=3.65,
    v_min_cell=2.5,
    v_exp=3.4,
    v_nom_curve=3.2,
    cycling_matrix=[
        [0, 0, 100],
        [80, 6000, 80],   # LFP: ~6000 cycles to 80% at 80% DOD
        [100, 4000, 80]
    ]
)

NMC_CELL_CONFIG = CellPhysicsConfig(
    chemistry=CellChemistry.LITHIUM_ION,
    v_nom_cell=3.6,
    v_max_cell=4.2,
    v_min_cell=3.0,
    v_exp=4.05,
    v_nom_curve=3.6,
    cycling_matrix=[
        [0, 0, 100],
        [80, 3000, 80],   # NMC: ~3000 cycles to 80% at 80% DOD
        [100, 2000, 80]
    ]
)

# Default for general use
DEFAULT_CELL_CONFIG = LFP_CELL_CONFIG


def get_physics_config(chemistry: str = "LFP") -> CellPhysicsConfig:
    """
    Get pre-configured physics parameters by chemistry type.
    
    Args:
        chemistry: "LFP" or "NMC"
        
    Returns:
        CellPhysicsConfig with appropriate defaults
    """
    chemistry = chemistry.upper()
    if chemistry == "LFP":
        return LFP_CELL_CONFIG
    elif chemistry == "NMC":
        return NMC_CELL_CONFIG
    else:
        return DEFAULT_CELL_CONFIG


# ════════════════════════════════════════════════════════════════════════════
# DEFAULT PYSAM BATTERY (Ready-to-use MockBattery)
# ════════════════════════════════════════════════════════════════════════════

from eclipse.config.equipment_models import MockBattery

DEFAULT_PYSAM_BATTERY = MockBattery(
    name="Default_PySAM_Battery",
    nominal_energy_kwh=10.0,  # Default 10 kWh (overrideable via system_kwh)
    nominal_voltage_v=400,
    max_charge_power_kw=5.0,
    max_discharge_power_kw=5.0,
    min_soc=10.0,
    max_soc=90.0,
    initial_soc=90.0,
    chem=1,  # Li-ion
    # Voltage model parameters
    v_nom_cell=3.6,
    v_max_cell=4.1,
    v_min_cell=3.0,
    q_full_cell=3.0,
    resistance=0.01,
    v_exp=4.05,
    q_exp=0.05,
    q_nom=3.0,
    v_nom_curve=3.6,
    c_rate=1.0,
    # PySAM model_params with valid cycling_matrix
    model_params={
        "life_model": 0,
        "calendar_choice": 0,
        "cycling_matrix": [
            [0, 0, 100],
            [50, 5000, 90],
            [100, 5000, 80]
        ],
        "mass": 500,
        "surface_area": 2.0,
        "Cp": 1000,
        "h": 20,
        "T_room_init": 20,
        "cap_vs_temp": [[-20, 60], [0, 80], [25, 100], [40, 100]],
        "loss_choice": 0,
        "monthly_charge_loss": [0]*12,
        "monthly_discharge_loss": [0]*12,
        "monthly_idle_loss": [0]*12
    },
    performance={'round_trip_efficiency': 0.95}
)


def get_pysam_battery(
    capacity_kwh: float = 10.0,
    power_kw: float = None,
    min_soc: float = 10.0,
    max_soc: float = 90.0,
    efficiency: float = 0.95
) -> MockBattery:
    """
    Create a MockBattery configured for PySAM simulation.
    
    Args:
        capacity_kwh: Battery capacity in kWh
        power_kw: Charge/discharge power limit (default: 0.5C rate)
        min_soc: Minimum SOC % (default: 10)
        max_soc: Maximum SOC % (default: 90)
        efficiency: Round-trip efficiency (default: 0.95)
        
    Returns:
        MockBattery ready for PySAMBatterySimulator
    """
    if power_kw is None:
        power_kw = capacity_kwh * 0.5  # 0.5C rate default
    
    return MockBattery(
        name=f"PySAM_Battery_{capacity_kwh}kWh",
        nominal_energy_kwh=capacity_kwh,
        nominal_voltage_v=400,
        max_charge_power_kw=power_kw,
        max_discharge_power_kw=power_kw,
        min_soc=min_soc,
        max_soc=max_soc,
        initial_soc=max_soc,
        chem=1,
        v_nom_cell=3.6,
        v_max_cell=4.1,
        v_min_cell=3.0,
        q_full_cell=3.0,
        resistance=0.01,
        v_exp=4.05,
        q_exp=0.05,
        q_nom=3.0,
        v_nom_curve=3.6,
        c_rate=1.0,
        model_params={
            "life_model": 0,
            "calendar_choice": 0,
            "cycling_matrix": [
                [0, 0, 100],
                [50, 5000, 90],
                [100, 5000, 80]
            ],
            "mass": 500,
            "surface_area": 2.0,
            "Cp": 1000,
            "h": 20,
            "T_room_init": 20,
            "cap_vs_temp": [[-20, 60], [0, 80], [25, 100], [40, 100]],
            "loss_choice": 0,
            "monthly_charge_loss": [0]*12,
            "monthly_discharge_loss": [0]*12,
            "monthly_idle_loss": [0]*12
        },
        performance={'round_trip_efficiency': efficiency}
    )
