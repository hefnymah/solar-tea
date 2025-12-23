
import os
import sys

# Ensure project root is in path
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

# Module
from eclipse.config.equipments.modules import module, Jinko400, Longi550, Trina550

# Inverter
from eclipse.config.equipments.inverters import inverter, SMA_SunnyBoy_5_0, Huawei_SUN2000_10KTL, GoodWe_GW5000_ES_Hybrid

# Battery
from eclipse.config.equipments.batteries import battery, PySAM_Test_Battery, Tesla_Powerwall_2

#%%

module = module
module.economics.price_per_unit

inverter = inverter
inverter.economics

battery = battery
battery.economics

#%%

# Print properties in a professional, Spyder-like table format
def print_spyder_style(obj, name="module"):
    import types
    
    print(f"Object: {name}")
    print("-" * 80)
    print(f"{'Name':<35} | {'Type':<20} | {'Value'}")
    print("-" * 80)
    
    # Get all properties (std dict + properties)
    # We'll use dir() but filter out private/magic methods
    keys = [k for k in dir(obj) if not k.startswith('_')]
    
    for key in sorted(keys):
        val = getattr(obj, key)
        val_type = type(val).__name__
        
        # Handle recursive display for SimpleNamespaces or dicts if needed
        # For this summary, we just show string representation
        val_str = str(val)
        if len(val_str) > 70:
            val_str = val_str[:67] + "..."
        
        print(f"{key:<35} | {val_type:<20} | {val_str}")
        
        # If it's a namespace, optionally show content indented (simple version)
        if isinstance(val, types.SimpleNamespace):
            for sub_k, sub_v in val.__dict__.items():
                 print(f"  .{sub_k:<32} | {type(sub_v).__name__:<20} | {sub_v}")

    print("-" * 80)
    print("\n")
    
#%%
print_spyder_style(module, "Selected Module")
print_spyder_style(inverter, "Selected Inverter") 
print_spyder_style(battery, "Selected Battery")

