
import os
import sys

# Ensure project root is in path
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from src.config.equipments.modules import Jinko400, Longi550

def main():
    print("=== Simplified Module Access Example ===\n")
    
    # 1. Direct Import Usage
    module = Jinko400
    print(f"Module: {module.name}")
    
    # 2. Dot Notation Access (Performance)
    # Instead of module.performance['efficiency']
    print(f"Efficiency: {module.performance.efficiency}%")
    
    # 3. Dot Notation Access (Economics)
    print(f"Price: {module.economics.price_per_unit} {module.economics.currency}")
    
    # 4. Alias Access
    print(f"Annual Degradation: {module.degradation_yearly}%")
    
    print("\n------------------------------")
    
    module2 = Longi550
    print(f"Module: {module2.name}")
    print(f"Efficiency: {module2.performance.efficiency}%")
    print(f"Annual Degradation: {module2.degradation_yearly}%")

if __name__ == "__main__":
    main()
