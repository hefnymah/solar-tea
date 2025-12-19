
import os
import sys

# Ensure project root is in path
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from src.config.equipments.modules import Jinko400, Longi550, Trina550

def main():
    print("=== Module Access & Degradation Example ===\n")
    
    # 1. Direct Import Usage
    module = Trina550
    print(f"Selected Module: {module.name}")
    
    # 2. Dot Notation Access (Performance)
    # Instead of module.performance['efficiency']
    print(f"Efficiency: {module.performance.efficiency}%")
    
    # 3. Dot Notation Access (Economics)
    print(f"Price: {module.economics.price_per_unit} {module.economics.currency}")
    
    # 4. Alias Access
    print(f"Annual Degradation: {module.degradation_yearly}%")

    # 5. Get Degradation at a specific year
    print(f"Degradation at Year 5: {module.get_degradation_at_year(5)}%")

    # 6. get power parameters
    print(f"Power: {module.power_watts} W")
    print(f"Cells in Series: {module.model_params['Cells_in_Series']}")
    print(f"Parallel Strings: {module.model_params['Parallel_Strings']}")
    print(f"Width: {module.width_m} m")
    print(f"Height: {module.height_m} m")
    print(f"Area: {module.area_m2} m^2")
    print(f"Weight: {module.mechanical.weight} kg")
    print(f"Frame Material: {module.mechanical.frame_material}")
    print(f"Front Glass: {module.mechanical.front_glass}")
    print(f"Back Glass: {module.mechanical.back_glass}")
    print(f"Backsheet: {module.mechanical.backsheet}")
    print(f"Junction Box: {module.mechanical.junction_box}")
    print(f"Max System Voltage: {module.performance.max_system_voltage} V")
    print(f"Max Series Fuse: {module.performance.max_series_fuse} A")
    print(f"Nominal Operating Cell Temperature: {module.performance.nominal_operating_cell_temperature} °C")
    print(f"Temperature Coefficient Power: {module.performance.temperature_coefficient_power} %/°C")
    print(f"Max Wind Load: {module.environmental.max_wind_load} N")
    print(f"Max Snow Load: {module.environmental.max_snow_load} N")
    print(f"Operating Temperature Range: {module.environmental.operating_temperature_range}")
    print(f"Humidity: {module.environmental.humidity}")
    print(f"Hail Resistance: {module.environmental.hail_resistance}")
    print(f"IEC: {module.certifications.iec}")
    print(f"UL: {module.certifications.ul}")
    print(f"CE: {module.certifications.ce}")
    print(f"ISO: {module.certifications.iso}")
    print(f"Product Warranty Years: {module.warranty.product_warranty_years}")
    print(f"Performance Warranty Years: {module.warranty.performance_warranty_years}")
    print(f"Performance Guarantee Year 1: {module.warranty.performance_guarantee_year_1}%")
    print(f"Performance Guarantee Year 25: {module.warranty.performance_guarantee_year_25}%")
    print(f"Performance Guarantee Year 30: {module.warranty.performance_guarantee_year_30}%")
    print(f"Linear Degradation: {module.warranty.linear_degradation}")
    print(f"Price Per Unit: {module.economics.price_per_unit} {module.economics.currency}")
    print(f"Min Order Quantity: {module.economics.min_order_quantity}")
    print(f"Price Per Watt: {module.economics.price_per_watt}")
    
    
    
    print("\n------------------------------")
    
    module2 = Jinko400
    print(f"Module: {module2.name}")
    print(f"Efficiency: {module2.performance.efficiency}%")
    print(f"Annual Degradation: {module2.degradation_yearly}%")

if __name__ == "__main__":
    main()
