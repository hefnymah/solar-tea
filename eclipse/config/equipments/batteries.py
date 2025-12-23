
from eclipse.config.equipment_models import MockBattery

# ====================================
# PySAM Test Battery
# ====================================
PySAM_Test_Battery = MockBattery(
    name="PySAM_Test_Battery",
    nominal_energy_kwh=10.0,        # PySAM: nominal_energy
    nominal_voltage_v=500,          # PySAM: nominal_voltage (Hardcoded was 500)
    max_charge_power_kw=5.0,
    max_discharge_power_kw=5.0,
    min_soc=20.0,                   # PySAM: minimum_SOC
    max_soc=95.0,                   # PySAM: maximum_SOC
    initial_soc=95.0,               # PySAM: initial_SOC
    chem=1,                         # PySAM: chem (1=Li-ion)
    
    # Cell Specs (Matching PySAM Defaults)
    v_nom_cell=3.6,                 # PySAM: Vnom_default
    v_max_cell=4.1,                 # PySAM: Vfull
    v_min_cell=3.0,                 # PySAM: Vcut
    q_full_cell=3.0,                # PySAM: Qfull
    resistance=0.01,                # PySAM: resistance
    
    # Shepherd Model (Matching PySAM Defaults)
    v_exp=4.05,                     # PySAM: Vexp
    q_exp=0.05,                     # PySAM: Qexp
    q_nom=3.0,                      # PySAM: Qnom
    v_nom_curve=3.6,                # PySAM: Vnom
    c_rate=1.0,                     # PySAM: C_rate
    
    # Extended PySAM Parameters (Physics/Thermal/Life)
    # Stored in model_params to avoid cluttering the main dataclass yet
    model_params={
        # Life Model
        "life_model": 0,           # 0=Calendar/Cycle
        "calendar_choice": 0,      # 0=None
        "cycling_matrix": [
            [0, 0, 100],
            [50, 5000, 90],
            [100, 5000, 80]
        ],
        
        # Thermal Model
        "mass": 500,               # kg
        "surface_area": 2.0,       # m2
        "Cp": 1000,                # Specific heat capacity J/kgK
        "h": 20,                   # Heat transfer coefficient W/m2K
        "T_room_init": 20,         # Room temperature C
        "cap_vs_temp": [
            [-10, 60],
            [0, 80],
            [25, 100],
            [40, 100]
        ],
        
        # Losses
        "loss_choice": 0,
        "monthly_charge_loss": [0]*12,
        "monthly_discharge_loss": [0]*12,
        "monthly_idle_loss": [0]*12
    },
    
    dimensions={
        "width": 1000, "height": 1000, "depth": 500, "weight": 500.0
    },
    performance={
        "round_trip_efficiency": 0.95,
        "depth_of_discharge": 1.0,
        "chemistry": "Li-ion (NMC)"
    },
    certifications={},
    warranty={"standard_years": 10},
    economics={"price_per_unit": 5000}
)

# ====================================
# Tesla Powerwall 2
# ====================================
Tesla_Powerwall_2 = MockBattery(
    name="Tesla_Powerwall_2",
    nominal_energy_kwh=13.5,
    nominal_voltage_v=50, 
    max_charge_power_kw=5.0,
    max_discharge_power_kw=5.0,
    min_soc=10.0,
    max_soc=100.0,
    v_exp=4.05, q_exp=0.05, q_nom=3.0, v_nom_curve=3.6, c_rate=1.0,
    
    # Extended Specs
    dimensions={
        "width": 753, "height": 1150, "depth": 147, "weight": 114.0
    },
    performance={
        "round_trip_efficiency": 0.90,
        "depth_of_discharge": 1.0,
        "warranty_cycles": 0 # Unlimited cycles depending on region
    },
    certifications={
        "safety": "UL 1642, UL 1741, IEC 62619",
        "grid": "IEEE 1547, VDE-AR-N 4105"
    },
    warranty={
        "standard_years": 10,
        "retention": 0.70 # 70% capacity
    },
    economics={
        "price_per_unit": 9500.00,
        "currency": "EUR",
        "price_per_kwh": 703.70
    }
)


BATTERY_DB = [
    PySAM_Test_Battery,
    Tesla_Powerwall_2,
]

DEFAULT_BATTERY = PySAM_Test_Battery
battery = DEFAULT_BATTERY