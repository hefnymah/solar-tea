
from src.config.equipment_models import MockBattery


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

BYD_Battery_Box_Premium_HVS_10_2 = MockBattery(
    name="BYD_Battery-Box_Premium_HVS_10.2",
    nominal_energy_kwh=10.2,
    nominal_voltage_v=400,
    max_charge_power_kw=10.2,
    max_discharge_power_kw=10.2,
    min_soc=5.0,
    max_soc=100.0,
    v_nom_cell=3.2, v_max_cell=3.65, v_min_cell=2.5,
    v_exp=3.5, q_exp=0.02, q_nom=2.8, v_nom_curve=3.2, c_rate=1.0,
    
    dimensions={
        "width": 585, "height": 1178, "depth": 298, "weight": 167.0
    },
    performance={
        "round_trip_efficiency": 0.96,
        "depth_of_discharge": 1.0,
        "chemistry": "LFP"
    },
    certifications={
        "safety": "VDE 2510-50, IEC 62619, CE",
        "transport": "UN38.3"
    },
    warranty={
        "standard_years": 10
    },
    economics={
        "price_per_unit": 6500.00,
        "currency": "EUR",
        "price_per_kwh": 637.25
    }
)

LG_Chem_RESU_10H = MockBattery(
    name="LG_Chem_RESU_10H",
    nominal_energy_kwh=9.8,
    nominal_voltage_v=400,
    max_charge_power_kw=5.0,
    max_discharge_power_kw=5.0,
    min_soc=5.0,
    max_soc=95.0,
    chem=1,
    
    dimensions={
        "width": 744, "height": 907, "depth": 206, "weight": 97.0
    },
    performance={
        "round_trip_efficiency": 0.95,
        "depth_of_discharge": 0.95,
        "chemistry": "NMC"
    },
    certifications={
        "safety": "UL1973, CE, IEC 62619"
    },
    warranty={
        "standard_years": 10,
        "retention": 0.60
    },
    economics={
        "price_per_unit": 5800.00,
        "currency": "EUR",
        "price_per_kwh": 591.84
    }
)

Generic_LeadAcid_10kWh = MockBattery(
    name="Generic_LeadAcid_10kWh",
    nominal_energy_kwh=10.0,
    nominal_voltage_v=48,
    max_charge_power_kw=2.0,
    max_discharge_power_kw=3.0,
    min_soc=40.0, # Lead Acid shouldn't go too deep
    max_soc=100.0,
    chem=0, # Lead Acid
    v_nom_cell=2.0, v_max_cell=2.4, v_min_cell=1.75,
    q10=100, q20=110, qn=100, tn=20, # Examples
    
    dimensions={
        "width": 600, "height": 800, "depth": 600, "weight": 400.0
    },
    performance={
        "round_trip_efficiency": 0.80,
        "depth_of_discharge": 0.50,
        "chemistry": "Lead-Acid (AGM/Gel)"
    },
    certifications={
        "safety": "Standard Industrial"
    },
    warranty={
        "standard_years": 2
    },
    economics={
        "price_per_unit": 2000.00,
        "currency": "EUR",
        "price_per_kwh": 200.00 # High effective cost due to lower DoD
    }
)

BATTERY_DB = [
    Tesla_Powerwall_2,
    BYD_Battery_Box_Premium_HVS_10_2,
    LG_Chem_RESU_10H,
    Generic_LeadAcid_10kWh
]

DEFAULT_BATTERY = Generic_LeadAcid_10kWh
battery = DEFAULT_BATTERY