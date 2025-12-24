
from eclipse.config.equipment_models import MockBattery

# ====================================
# PySAM Test Battery
# ====================================
# ====================================
# PySAM Test Battery
# ====================================
_PySAM_Test_Battery = MockBattery(
    name="PySAM_Test_Battery",
    # ... args ...
    nominal_energy_kwh=10.0,
    nominal_voltage_v=500,
    max_charge_power_kw=5.0,
    max_discharge_power_kw=5.0,
    min_soc=20.0,
    max_soc=95.0,
    initial_soc=95.0,
    chem=1,
    v_nom_cell=3.6, v_max_cell=4.1, v_min_cell=3.0, q_full_cell=3.0, resistance=0.01,
    v_exp=4.05, q_exp=0.05, q_nom=3.0, v_nom_curve=3.6, c_rate=1.0,
    model_params={
        "life_model": 0, "calendar_choice": 0,
        "cycling_matrix": [[0, 0, 100], [50, 5000, 90], [100, 5000, 80]],
        "mass": 500, "surface_area": 2.0, "Cp": 1000, "h": 20, "T_room_init": 20,
        "cap_vs_temp": [[-10, 60], [0, 80], [25, 100], [40, 100]],
        "loss_choice": 0, "monthly_charge_loss": [0]*12, "monthly_discharge_loss": [0]*12, "monthly_idle_loss": [0]*12
    },
    dimensions={"width": 1000, "height": 1000, "depth": 500, "weight": 500.0},
    performance={"round_trip_efficiency": 0.95, "depth_of_discharge": 1.0, "chemistry": "Li-ion (NMC)"},
    certifications={}, warranty={"standard_years": 10}, economics={"price_per_unit": 5000}
)

# ====================================
# Tesla Powerwall 2
# ====================================
_Tesla_Powerwall_2 = MockBattery(
    name="Tesla_Powerwall_2",
    nominal_energy_kwh=13.5,
    nominal_voltage_v=50, 
    max_charge_power_kw=5.0,
    max_discharge_power_kw=5.0,
    min_soc=10.0,
    max_soc=100.0,
    v_exp=4.05, q_exp=0.05, q_nom=3.0, v_nom_curve=3.6, c_rate=1.0,
    dimensions={"width": 753, "height": 1150, "depth": 147, "weight": 114.0},
    performance={"round_trip_efficiency": 0.90, "depth_of_discharge": 1.0, "warranty_cycles": 0},
    certifications={"safety": "UL 1642, UL 1741, IEC 62619", "grid": "IEEE 1547, VDE-AR-N 4105"},
    warranty={"standard_years": 10, "retention": 0.70},
    economics={"price_per_unit": 9500.00, "currency": "EUR", "price_per_kwh": 703.70}
)


BATTERY_DB = [
    _PySAM_Test_Battery,
    _Tesla_Powerwall_2,
]

DEFAULT_BATTERY = _PySAM_Test_Battery

# ==============================================================================
# Helper Methods (Module-Level Access)
# Usage:
#   from eclipse.config.equipments import batteries
#   bat = batteries.default()
#   bat = batteries.Tesla_Powerwall_2()
# ==============================================================================

def get_all():
    """Return list of all available batteries."""
    return BATTERY_DB

def list_options():
    """Print available battery models to console."""
    print("Available Batteries:")
    for b in BATTERY_DB:
        print(f" - {b.name} ({b.nominal_energy_kwh} kWh)")
        
def get(name: str):
    """Get a battery by name (case-insensitive)."""
    for b in BATTERY_DB:
        if b.name.lower() == name.lower():
            return b
    raise ValueError(f"Battery '{name}' not found. options: {[b.name for b in BATTERY_DB]}")

def default():
    """Return the default battery."""
    return DEFAULT_BATTERY

# Factory functions exposing public API
def PySAM_Test_Battery(): return _PySAM_Test_Battery
def Tesla_Powerwall_2(): return _Tesla_Powerwall_2
