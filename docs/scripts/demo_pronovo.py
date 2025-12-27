#!/usr/bin/env python3
"""
Interactive Pronovo Playground
==============================
Run this script to interactively test the Pronovo Subsidy Service
and verify results against the online calculator.

Usage:
    python3 materials/eingaben_replicators/play_with_pronovo.py
"""

import sys
import os

# Add current directory to path so we can import the service
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from pronovo_subsidy_service import PronovoSubsidyService, SystemSpecs, InstallationType

def get_float_input(prompt: str, default: float = 0.0) -> float:
    try:
        user_input = input(f"{prompt} [{default}]: ").strip()
        if not user_input:
            return default
        return float(user_input)
    except ValueError:
        print("Invalid number, using default.")
        return default

def get_bool_input(prompt: str, default: bool = False) -> bool:
    default_str = "y" if default else "n"
    user_input = input(f"{prompt} (y/n) [{default_str}]: ").lower().strip()
    if not user_input:
        return default
    return user_input.startswith('y')

def main():
    print("🇨🇭 Pronovo Subsidy Playground (2025 Rules)")
    print("==========================================")
    print("Press Ctrl+C to exit.\n")
    
    service = PronovoSubsidyService()
    
    while True:
        try:
            print("\n--- New Calculation ---")
            
            # 1. Capacity
            cap = get_float_input("System Capacity (kWp)", 10.0)
            if cap <= 0:
                print("Capacity must be positive.")
                continue
                
            # 2. Installation Type (Simplified)
            print("Installation Type: 1=Angebaute (Attached), 2=Integriert (Integrated), 3=Freistehend")
            type_choice = input("Select Type [1]: ").strip()
            if type_choice == "2":
                inst_type = InstallationType.INTEGRIERT
            elif type_choice == "3":
                inst_type = InstallationType.FREISTEHEND
            else:
                inst_type = InstallationType.ANGEBAUT
            
            # 3. Self Consumption
            # Default to Yes (Standard EIV)
            has_consumption = get_bool_input("Has Self-Consumption? (Standard EIV)", True)
            
            # 4. Bonuses
            ask_bonuses = get_bool_input("Configure Bonuses? (Tilt/Height/Parking)", False)
            
            tilt_angle = 0.0
            altitude = 0.0
            parking_cov = False
            
            if ask_bonuses:
                tilt_angle = get_float_input("  Tilt Angle (degrees)", 0.0)
                altitude = get_float_input("  Altitude (meters)", 400.0)
                parking_cov = get_bool_input("  Parking Area Coverage (>100kWp)?", False)
            
            # Create Specs
            specs = SystemSpecs(
                capacity_kwp=cap,
                installation_type=inst_type,
                has_self_consumption=has_consumption,
                tilt_angle_degrees=tilt_angle,
                altitude_meters=altitude,
                parking_area_coverage=parking_cov
            )
            
            # Calculate
            result = service.calculate_eiv(specs)
            
            # Display Result
            print("\n📊 Results for {:.2f} kWp ({})".format(cap, "Standard" if has_consumption else "HEIV"))
            print("-" * 40)
            print(f"Base Contribution: {result.base_contribution:10,.2f} CHF")
            
            if result.tilt_bonus > 0:
                print(f"Tilt Bonus:        {result.tilt_bonus:10,.2f} CHF (Angle: {tilt_angle}°)")
            if result.height_bonus > 0:
                print(f"Height Bonus:      {result.height_bonus:10,.2f} CHF (Alt: {altitude}m)")
            if result.parking_bonus > 0:
                print(f"Parking Bonus:     {result.parking_bonus:10,.2f} CHF")
            
            print("-" * 40)
            print(f"TOTAL SUBSIDY:     {result.total_subsidy:10,.2f} CHF")
            print("=" * 40)
            
        except KeyboardInterrupt:
            print("\n\nGoodbye!")
            break
        except Exception as e:
            print(f"\nError: {e}")

if __name__ == "__main__":
    main()
#%%