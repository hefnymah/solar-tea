
import os
import sys
import dataclasses
from pprint import pprint

# Ensure project root is in path
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

# Import from specific module file as requested
from src.config.equipments.modules import module

def print_module_details(module_obj):
    print(f"=== Default Module Details: {module_obj.name} ===\n")
    
    # 1. Top Level Attributes
    print("--- General Specifications ---")
    print(f"Power: {module_obj.power_watts} W")
    print(f"Dimensions: {module_obj.width_m}m x {module_obj.height_m}m")
    print(f"Area: {module_obj.area_m2} m²")
    print(f"Electrical: Vmpp={module_obj.vmpp}V, Impp={module_obj.impp}A, Voc={module_obj.voc}V, Isc={module_obj.isc}A")
    print("\n")

    # 2. Iterate over nested SimpleNamespace objects (Performance, Mechanical, etc.)
    # The __post_init__ converted these from dicts to SimpleNamespace
    
    categories = ['performance', 'mechanical', 'environmental', 'certifications', 'warranty', 'economics']
    
    for cat in categories:
        print(f"--- {cat.capitalize()} ---")
        obj = getattr(module_obj, cat, None)
        
        if obj:
            # Check if it's a SimpleNamespace or Dict (just in case)
            if hasattr(obj, '__dict__'):
                # It's a SimpleNamespace or Object
                items = vars(obj).items()
            elif isinstance(obj, dict):
                items = obj.items()
            else:
                items = []
                
            for key, value in items:
                # Clean up key display
                clean_key = key.replace('_', ' ').title()
                print(f"{clean_key}: {value}")
        else:
            print("N/A")
        print("")

    # 3. Calculated degradations
    print("--- Calculated Degradation ---")
    print(f"Annual Degradation Rate: {module_obj.degradation_yearly}%")
    print(f"Degradation at Year 10: {module_obj.get_degradation_at_year(10)}%")
    print(f"Degradation at Year 25: {module_obj.get_degradation_at_year(25)}%")

def main():
    # Usage is simple: just use module
    print_module_details(module)

if __name__ == "__main__":
    main()
