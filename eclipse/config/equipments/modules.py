
from eclipse.config.equipment_models import MockModule

# Mock Database (User Customizable)
# Enriched with full specs from manufacturer datasheets (via JSON extraction)

# ====================================
# Jinko JKM400M 54HL4 B
# ====================================
Jinko400 = MockModule(
    name="Jinko_JKM400M_54HL4_B",
    power_watts=400.0,
    width_m=1.048, # 1048 mm
    height_m=2.108, # 2108 mm
    vmpp=41.7,
    impp=9.59,
    voc=49.8,
    isc=10.04,
    
    # Generic Model Params
    model_params={
        "pdc0": 400.0,
        "gamma_pdc": -0.004,
        "alpha_sc": 0.0005,
        "beta_oc": -0.0023,
        "Cells_in_Series": 72,
        "Parallel_Strings": 1
    },
    
    Notes="High efficiency monocrystalline module. 25-year linear power warranty.",
    
    # Nested Data Containers
    dimensions={
        "length": 2108, "width": 1048, "thickness": 35, "area": 2.21
    },
    performance={
        "efficiency": 18.1,
        "efficiency_range": "18.0-18.2%",
        "temperature_coefficient_power": -0.37,
        "nominal_operating_cell_temperature": 45,
        "max_system_voltage": 1500,
        "max_series_fuse": 20,
        "bifacial_factor": None  # Not bifacial
    },
    mechanical={
        "weight": 22.5,
        "frame_material": "aluminum",
        "front_glass": "3.2mm tempered glass",
        "back_glass": None, # Standard backsheet
        "backsheet": "TPT (Tedlar-PET-Tedlar)",
        "junction_box": "IP67 rated"
    },
    environmental={
        "max_wind_load": 2400,
        "max_snow_load": 5400,
        "operating_temperature_range": "-40 to +85°C",
        "humidity": "≤85%",
        "hail_resistance": "IEC 61215 certified"
    },
    certifications={
        "iec": "IEC 61215, IEC 61730",
        "ul": "UL 1703",
        "ce": "CE marked",
        "iso": "ISO 9001:2015, ISO 14001:2015",
        "tuv": None
    },
    warranty={
        "product_warranty_years": 12,
        "performance_warranty_years": 25,
        "performance_guarantee_year_1": 98,
        "performance_guarantee_year_25": 84.8,
        "performance_guarantee_year_30": None, # 25 year warranty
        "linear_degradation": True
    },
    economics={
        "price_per_unit": 110.00,
        "currency": "EUR",
        "min_order_quantity": 30,
        "price_per_watt": 0.275
    }
)

# ====================================
# Longi LR5 72HTH 550M
# ====================================
Longi550 = MockModule(
    name="Longi_LR5_72HTH_550M",
    power_watts=550.0,
    width_m=1.134, # 1134 mm
    height_m=2.278, # 2278 mm
    vmpp=41.7,
    impp=13.19,
    voc=49.8,
    isc=13.85,
    
    model_params={
        "pdc0": 550.0,
        "gamma_pdc": -0.004,
        "alpha_sc": 0.0005,
        "beta_oc": -0.0023,
        "Cells_in_Series": 72,
        "Parallel_Strings": 1
    },
    
    Notes="High power density module. Excellent for maximizing energy per m2.",
    
    dimensions={
        "length": 2278, "width": 1134, "thickness": 35, "area": 2.58
    },
    performance={
        "efficiency": 21.3,
        "efficiency_range": "21.2-21.4%",
        "temperature_coefficient_power": -0.37,
        "nominal_operating_cell_temperature": 45,
        "max_system_voltage": 1500,
        "max_series_fuse": 25,
        "bifacial_factor": None
    },
    mechanical={
        "weight": 28.5,
        "frame_material": "aluminum",
        "front_glass": "3.2mm tempered glass",
        "back_glass": None,
        "backsheet": "TPT",
        "junction_box": "IP67 rated"
    },
    environmental={
        "max_wind_load": 2400,
        "max_snow_load": 5400,
        "operating_temperature_range": "-40 to +85°C",
        "humidity": "≤85%",
        "hail_resistance": "IEC 61215 certified"
    },
    certifications={
        "iec": "IEC 61215, IEC 61730",
        "ce": "CE",
        "tuv": "TÜV",
        "ul": None,
        "iso": None
    },
    warranty={  # Estimated from notes
            "product_warranty_years": 12,
            "performance_warranty_years": 30,
            "performance_guarantee_year_1": 99.0,
            "performance_guarantee_year_25": None, # Will be interpolated
            "performance_guarantee_year_30": 87.4,
            "linear_degradation": True
    },
    economics={
        "price_per_unit": 155.00,
        "currency": "EUR",
        "min_order_quantity": 30,
        "price_per_watt": 0.28
    }
)

# ====================================
# Trina TSM DEG21C 20 550
# ====================================
Trina550 = MockModule(
    name="Trina_TSM_DEG21C_20_550",
    power_watts=550.0,
    width_m=1.096, # 1096 mm
    height_m=2.384, # 2384 mm
    vmpp=41.7,
    impp=13.19,
    voc=49.8,
    isc=13.85,
    
    model_params={
        "pdc0": 550.0,
        "gamma_pdc": -0.004,
        "alpha_sc": 0.0005,
        "beta_oc": -0.0023,
        "Cells_in_Series": 72,
        "Parallel_Strings": 1
    },
    
    Notes="Bifacial glass-glass module. Can generate power from both sides.",
    
    dimensions={
            "length": 2384, "width": 1096, "thickness": 40, "area": 2.61
    },
    performance={
        "efficiency": 21.0,
        "efficiency_range": "20.9-21.1%",
        "temperature_coefficient_power": -0.37,
        "nominal_operating_cell_temperature": 45,
        "max_system_voltage": 1500,
        "max_series_fuse": 25,
        "bifacial_factor": 0.7
    },
    mechanical={
        "weight": 32.0,
        "frame_material": "aluminum",
        "front_glass": "3.2mm tempered glass",
        "back_glass": "3.2mm tempered glass",
        "backsheet": None, # Glass-glass module
        "junction_box": "IP67 rated"
    },
    environmental={
            "max_wind_load": 2400,
            "max_snow_load": 5400,
            "operating_temperature_range": "-40 to +85°C",
            "humidity": "≤85%",
            "hail_resistance": "IEC 61215 certified"
        },
    certifications={
        "iec": "IEC 61215, IEC 61730",
        "ce": "CE",
        "tuv": "TÜV",
        "ul": None,
        "iso": None
    },
        warranty={
            "product_warranty_years": 12,
            "performance_warranty_years": 30,
            "performance_guarantee_year_1": 99.0,
            "performance_guarantee_year_25": None, # Will be interpolated
            "performance_guarantee_year_30": 87.4, # 87.4% at year 30
            "linear_degradation": True
        },
        economics={
        "price_per_unit": 170.00,
        "currency": "EUR",
        "min_order_quantity": 30,
        "price_per_watt": 0.31
    }
)

MODULE_DB = [
    Jinko400,
    Longi550,
    Trina550,
]

DEFAULT_MODULE = Trina550
module = DEFAULT_MODULE
