
from eclipse.config.equipment_models import MockInverter


# ====================================
# SMA SunnyBoy 5.0
# ====================================
_SMA_SunnyBoy_5_0 = MockInverter(
    name="SMA_SunnyBoy_5.0", 
    max_ac_power=5000, 
    mppt_low_v=175, mppt_high_v=500, 
    max_input_voltage=600, max_input_current=15,
    
    # Extended Specs
    dimensions={
        "width": 435, "height": 470, "depth": 176, "weight": 16.0
    },
    features={
        "topology": "Transformerless",
        "cooling": "Convection",
        "display": "No display (Web UI)",
        "protection_rating": "IP65"
    },
    interfaces={
        "wifi": True,
        "ethernet": True,
        "communication": "Modbus, Speedwire, Webconnect"
    },
    certifications={
         "safety": "IEC 62109-1/2",
         "grid": "VDE-AR-N 4105, EN 50549-1"
    },
    warranty={
        "standard_years": 5,
        "extension_options": [10, 15, 20]
    },
    economics={
        "price_per_unit": 1250.00,
        "currency": "EUR",
        "price_per_watt": 0.25
    }
)

# ====================================
# Huawei SUN2000 10KTL
# ====================================
_Huawei_SUN2000_10KTL = MockInverter(
    name="Huawei_SUN2000_10KTL", 
    max_ac_power=10000, 
    mppt_low_v=160, mppt_high_v=950, 
    max_input_voltage=1100, max_input_current=13.5,
    
    dimensions={
        "width": 525, "height": 470, "depth": 262, "weight": 17.0
    },
    features={
        "topology": "Transformerless",
        "cooling": "Natural Convection",
        "hybird_ready": True,
        "protection_rating": "IP65"
    },
    interfaces={
        "wifi": True, # Dongle
        "ethernet": True, # Dongle
        "communication": "RS485, WLAN/FE"
    },
    certifications={
         "safety": "IEC 62109-1/2",
         "grid": "EN 50549-1, VDE-AR-N 4105"
    },
    warranty={
        "standard_years": 10
    },
    economics={
        "price_per_unit": 1600.00,
        "currency": "EUR",
        "price_per_watt": 0.16
    }
)

# ====================================
# Fronius Symo Gen24 10.0
# ====================================
_Fronius_Symo_Gen24_10_0 = MockInverter(
    name="Fronius_Symo_Gen24_10.0", 
    max_ac_power=10000, 
    mppt_low_v=80, mppt_high_v=1000, 
    max_input_voltage=1000, max_input_current=25,
    
    dimensions={
        "width": 529, "height": 594, "depth": 180, "weight": 23.4
    },
    features={
        "topology": "Transformerless",
        "cooling": "Active Cooling",
        "backup_power": "PV Point (Basic) / Full Backup (Optional)",
        "protection_rating": "IP66"
    },
    interfaces={
        "wifi": True,
        "ethernet": True,
        "communication": "Modbus TCP, JSON API"
    },
    certifications={
         "safety": "IEC 62109-1/2",
         "grid": "VDE-AR-N 4105, TOR Erzeuger"
    },
    warranty={
        "standard_years": 5,
        "extension_free_years": 2 # With registration
    },
    economics={
        "price_per_unit": 2400.00,
        "currency": "EUR",
        "price_per_watt": 0.24
    }
)

# ====================================
# GoodWe GW5000 ES Hybrid
# ====================================
_GoodWe_GW5000_ES_Hybrid = MockInverter(
    name="GoodWe_GW5000_ES_Hybrid", 
    max_ac_power=5000, 
    mppt_low_v=120, mppt_high_v=550, 
    max_input_voltage=600, max_input_current=13,
    
    dimensions={
        "width": 516, "height": 440, "depth": 184, "weight": 21.5
    },
    features={
        "topology": "Transformerless",
        "cooling": "Natural Convection",
        "battery_support": "Low Voltage (48V)",
        "protection_rating": "IP65"
    },
    interfaces={
        "wifi": True,
        "app_monitoring": True
    },
    certifications={
         "safety": "IEC 62109-1/2",
         "grid": "EN 50549-1"
    },
    warranty={
        "standard_years": 10
    },
    economics={
        "price_per_unit": 1100.00,
        "currency": "EUR",
        "price_per_watt": 0.22
    }
)

# ====================================
# Enphase IQ 8M
# ====================================
_Enphase_IQ8M = MockInverter(
    name="Enphase_IQ8M", 
    max_ac_power=325, 
    mppt_low_v=30, mppt_high_v=45, 
    max_input_voltage=60, max_input_current=12,
    
    dimensions={
        "width": 175, "height": 212, "depth": 30, "weight": 1.1
    },
    features={
        "topology": "Microinverter",
        "cooling": "Natural Convection",
        "module_level_optimization": True,
        "protection_rating": "IP67"
    },
    interfaces={
        "communication": "Power Line Communication (PLC)"
    },
    certifications={
         "safety": "UL 1741, IEC 62109",
         "grid": "IEEE 1547, VDE-AR-N 4105"
    },
    warranty={
        "standard_years": 25
    },
    economics={
        "price_per_unit": 145.00,
        "currency": "EUR",
        "price_per_watt": 0.45
    }
)

INVERTER_DB = [
    _SMA_SunnyBoy_5_0,
    _Huawei_SUN2000_10KTL,
    _Fronius_Symo_Gen24_10_0,
    _GoodWe_GW5000_ES_Hybrid,
    _Enphase_IQ8M,
]

DEFAULT_INVERTER = _SMA_SunnyBoy_5_0

# ==============================================================================
# Helper Methods (Module-Level Access)
# Usage:
#   from eclipse.config.equipments import inverters
#   inv = inverters.default()
#   inv = inverters.SMA_SunnyBoy_5_0()
# ==============================================================================

def get_all():
    """Return list of all available inverters."""
    return INVERTER_DB

def list_options():
    """Print available inverter models to console."""
    print("Available Inverters:")
    for i in INVERTER_DB:
        print(f" - {i.name} ({i.max_ac_power} W)")
        
def get(name: str):
    """Get an inverter by name (case-insensitive)."""
    for i in INVERTER_DB:
        if i.name.lower() == name.lower():
            return i
    raise ValueError(f"Inverter '{name}' not found. options: {[i.name for i in INVERTER_DB]}")

def default():
    """Return the default inverter."""
    return DEFAULT_INVERTER

# Factory wrappers for specific models
def SMA_SunnyBoy_5_0(): return _SMA_SunnyBoy_5_0
def Huawei_SUN2000_10KTL(): return _Huawei_SUN2000_10KTL
def Fronius_Symo_Gen24_10_0(): return _Fronius_Symo_Gen24_10_0
def GoodWe_GW5000_ES_Hybrid(): return _GoodWe_GW5000_ES_Hybrid
def Enphase_IQ8M(): return _Enphase_IQ8M

