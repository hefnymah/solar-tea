
import os
import sys

# Ensure project root is in path
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from src.config.equipments.modules import MODULE_DB

def main():
    print("=== Solar Module Degradation Example ===\n")
    
    # 1. Select a Module
    module = MODULE_DB[0] # Jinko
    print(f"Selected Module: {module.name}")
    print(f"Warranty: {module.warranty['product_warranty_years']} Year Product, {module.warranty['performance_warranty_years']} Year Performance")
    
    # 2. Get Annual Degradation Rate
    # This property is calculated automatically from the warranty data
    annual_rate = module.annual_degradation_rate
    print(f"Annual Degradation Rate: {annual_rate}% per year")
    
    # 3. Calculate Performance over Time
    print("\nProjected Performance:")
    print("-" * 30)
    print(f"{'Year':<10} | {'Degradation':<15} | {'Remaining Power':<15}")
    print("-" * 30)
    
    years_to_check = [1, 5, 10, 15, 20, 25]
    if module.warranty.get('performance_warranty_years', 25) >= 30:
        years_to_check.append(30)
        
    for year in years_to_check:
        deg_percent = module.get_degradation_at_year(year)
        remaining_percent = 100.0 - deg_percent
        
        # Calculate actual watts remaining
        # Note: This is simplified. Real world p_mp also depends on irradiance/temp degradation, 
        # but this is the "Health" of the module relative to nameplate.
        remaining_watts = module.power_watts * (remaining_percent / 100.0)
        
        print(f"{year:<10} | {deg_percent:>5.2f}%          | {remaining_watts:>6.1f} W ({remaining_percent:.1f}%)")
        
    print("-" * 30)

if __name__ == "__main__":
    main()
