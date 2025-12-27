#!/usr/bin/env python3
"""
LEG Calculator Demo
===================
Demonstrates the calculation of Lokale Elektrizitätsgemeinschaft (LEG) parameters.
Verifies logic against Excel 'Eingaben' sheet Rows 55-66.

Usage:
    python demo_calculate_leg.py
"""

from calculate_leg import LocalEnergyCommunityCalculator, LEGInput
from tariff_service import TariffService

def main():
    print("="*80)
    print("🏙️  LEG CALCULATOR DEMO (Refactored English API)")
    print("="*80)
    
    calculator = LocalEnergyCommunityCalculator()
    tariff_service = TariffService()
    
    # CASE 1: Default (LEG = NEIN)
    print("\n🔹 CASE 1: No LEG (Default)")
    # Defaults in LEGInput are is_leg_active=False
    inputs1 = LEGInput(is_leg_active=False)
    res1 = calculator.calculate(inputs1)
    
    print(f"   LEG Active: {res1.is_active}")
    print(f"   Revenue: {res1.revenue_chf} CHF")
    
    # CASE 2: LEG = JA, Default Parameters
    # Production: 10,000 kWh
    # Self-Consumption: 30%
    # Battery Increase: 0%
    # -> Max Share should be 70%
    print("\n🔹 CASE 2: LEG Active, Defaults")
    production = 10000
    sc_percent = 30.0
    
    inputs2 = LEGInput(
        is_leg_active=True,
        annual_production_kwh=production,
        self_consumption_percent=sc_percent
    )
    
    res2 = calculator.calculate(inputs2)
    
    print(f"   Input Production: {production} kWh")
    print(f"   Self-Consumption: {sc_percent}%")
    print(f"   👉 Max Share (Calc): {res2.max_possible_share}% (Expected: 70.0%)")
    print(f"   👉 Effective Share: {res2.share_percent}%")
    print(f"   👉 LEG Energy: {res2.share_kwh} kWh (Expected: 7000.0)")
    
    # Verify Tariff Defaults
    # Excel I60: 0.29 * 1/3 = 0.0966...
    print(f"   👉 Base Price (Default): {res2.base_electricity_price} CHF/kWh")
    print(f"   👉 Tariff (incl.): {res2.tariff_incl_accounting:.4f} CHF/kWh (Expected: ~0.0967)")
    print(f"   👉 Tariff (excl.): {res2.tariff_excl_accounting:.4f} CHF/kWh")
    
    
    # CASE 3: LEG = JA, Custom Operational Costs (Row 65 Logic)
    # Cost per kWh: 0.02 CHF/kWh (D65)
    # Capacity: 10 kWp
    # Specific Yield: 1000 kWh/kWp
    print("\n🔹 CASE 3: Custom Operating Costs (Row 65 Logic)")
    cost_factor = 0.02
    cap = 10.0
    yield_spec = 1000.0
    # Annual Prod = 10,000
    # Share = 50%
    
    inputs3 = LEGInput(
        is_leg_active=True,
        annual_production_kwh=cap*yield_spec,
        share_percent=50.0,
        cost_factor_chf_per_kwh=cost_factor,
        system_capacity_kwp=cap,
        specific_yield_kwh_kwp=yield_spec
    )
    
    res3 = calculator.calculate(inputs3)
    
    # Expected Cost: 0.02 * (50/100) * 10000 = 100 CHF
    print(f"   Cost Factor (D65): {cost_factor} CHF/kWh")
    print(f"   Share: 50%")
    print(f"   👉 Operating Cost: {res3.operating_cost_total:.2f} CHF (Expected: 100.00)")
    print(f"   Revenue: {res3.revenue_chf:.2f} CHF")
    print(f"   Net Benefit: {res3.net_benefit_chf:.2f} CHF")
    
    
    # CASE 4: Dynamic Tariff via API
    print("\n🔹 CASE 4: Dynamic Tariff (Real Data)")
    address = "Laufen am Rheinfall 1, 8447 Dachsen"
    print(f"   📍 Using address: {address}")
    
    # Fetch real tariff data
    try:
        tariff_data = tariff_service.get_tariffs_for_address(address, year="2025")
        if tariff_data and tariff_data.best_consumption_price:
            real_total_price = tariff_data.best_consumption_price.total_rp_kwh / 100.0
            print(f"   ✅ Fetched Real Grid Price: {real_total_price:.4f} CHF/kWh")
            
            inputs4 = LEGInput(
                is_leg_active=True,
                annual_production_kwh=10000,
                self_consumption_percent=30.0,
                grid_electricity_price_chf_per_kwh=real_total_price
            )
            
            res4 = calculator.calculate(inputs4)
            print(f"   👉 Base Price Used: {res4.base_electricity_price:.4f} CHF/kWh")
            # Should be real_total_price * 1/3
            expected_leg = real_total_price * (1/3)
            print(f"   👉 LEG Tariff (incl.): {res4.tariff_incl_accounting:.4f} CHF/kWh (Expected: ~{expected_leg:.4f})")
            
        else:
             print("   ⚠️  Could not fetch real tariff data. Skipping dynamic test.")
    except Exception as e:
        print(f"   ❌ Error fetching tariff: {e}")

    print("\n" + "="*80)
    print("✅ Demo completed.")

if __name__ == "__main__":
    main()
