#!/usr/bin/env python3
"""
Demo: Operating and Maintenance (O&M) Costs Calculator

This demo shows how to use the calculate_OM module to calculate
O&M costs for PV systems and battery storage.
"""

from calculate_OM import (
    PVSystemParameters,
    BatteryParameters,
    OMOverrides,
    OMCalculator,
    CalculationMethod,
    InstallationCategory,
    BatteryTechnology,
)


def demo_basic():
    """Basic demo: Calculate O&M for a residential PV system."""
    print("\n" + "=" * 70)
    print("DEMO 1: Basic Residential PV System (90 kWp)")
    print("=" * 70)

    # Define PV system parameters
    pv_params = PVSystemParameters(
        capacity_kwp=90.0,          # 10 kWp system
        investment_chf=137908.0,     # 20,000 CHF investment
        pv_area_m2=375.0,            # 60 m² PV area
        category=InstallationCategory.DACH_ANGEBAUT,
        lifetime_years=30,
        specific_yield_kwh_kwp=950.0,
        degradation_percent=0.4,
    )

    # Create calculator (no battery)
    calculator = OMCalculator(pv_params)

    # Calculate using maintenance schedule method
    result = calculator.calculate(method=CalculationMethod.MAINTENANCE_SCHEDULE)

    # Print results
    calculator.print_summary(result)

    return result


def demo_with_battery():
    """Demo with PV system and battery storage."""
    print("\n" + "=" * 70)
    print("DEMO 2: Commercial PV System (100 kWp) with Battery (50 kWh)")
    print("=" * 70)

    # PV system parameters
    pv_params = PVSystemParameters(
        capacity_kwp=100.0,
        investment_chf=150000.0,
        pv_area_m2=600.0,
        category=InstallationCategory.DACH_ANGEBAUT,
        lifetime_years=30,
        specific_yield_kwh_kwp=1000.0,
        degradation_percent=0.4,
    )

    # Battery parameters
    battery_params = BatteryParameters(
        capacity_kwh=90.0,
        investment_chf=63000.0,
        technology=BatteryTechnology.LITHIUM_LFP,
        lifetime_years=15,
    )

    # Create calculator
    calculator = OMCalculator(pv_params, battery_params)

    # Calculate
    result = calculator.calculate(
        method=CalculationMethod.MAINTENANCE_SCHEDULE,
        use_excel_battery_formula=True,  # Use Excel's 70% investment formula
    )

    calculator.print_summary(result)

    return result


def demo_price_per_kwh():
    """Demo using simple price-per-kWh calculation method."""
    print("\n" + "=" * 70)
    print("DEMO 3: Simple Price-per-kWh Method")
    print("=" * 70)

    pv_params = PVSystemParameters(
        capacity_kwp=50.0,
        investment_chf=75000.0,
        lifetime_years=25,
        specific_yield_kwh_kwp=900.0,
    )

    calculator = OMCalculator(pv_params)

    # Use simple price-per-kWh method
    result = calculator.calculate(method=CalculationMethod.PRICE_PER_KWH)

    calculator.print_summary(result)

    return result


def demo_with_overrides():
    """Demo with custom overrides for specific cost items."""
    print("\n" + "=" * 70)
    print("DEMO 4: Custom Overrides (User-Provided Values)")
    print("=" * 70)

    pv_params = PVSystemParameters(
        capacity_kwp=75.0,
        investment_chf=112500.0,
        pv_area_m2=450.0,
        category=InstallationCategory.FASSADE_ANGEBAUT,  # Facade installation
        lifetime_years=30,
    )

    # Custom overrides (simulating user input in Excel column B)
    overrides = OMOverrides(
        inspection_cost=1500.0,      # Override inspection cost
        insurance_cost=500.0,        # Override insurance
        cleaning_cost=2500.0,        # Override cleaning
        rent_cost=3000.0,            # Add roof rent (0 by default)
    )

    calculator = OMCalculator(pv_params)
    result = calculator.calculate(
        method=CalculationMethod.MAINTENANCE_SCHEDULE,
        overrides=overrides,
    )

    calculator.print_summary(result)

    return result


def demo_different_battery_tech():
    """Demo comparing different battery technologies."""
    print("\n" + "=" * 70)
    print("DEMO 5: Battery Technology Comparison")
    print("=" * 70)

    pv_params = PVSystemParameters(
        capacity_kwp=50.0,
        investment_chf=75000.0,
        lifetime_years=30,
    )

    technologies = [
        BatteryTechnology.LITHIUM_LFP,
        BatteryTechnology.LITHIUM_NMC,
        BatteryTechnology.SODIUM_ION,
        BatteryTechnology.LEAD_ACID_AGM,
    ]

    print(f"\nComparing 30 kWh battery with different technologies:")
    print(f"{'Technology':<25} {'Replacement Cost':<20} {'Lifetime Cost':<15}")
    print("-" * 60)

    for tech in technologies:
        battery_params = BatteryParameters(
            capacity_kwh=30.0,
            investment_chf=30.0 * tech.cost_per_kwh,  # Investment based on tech cost
            technology=tech,
            lifetime_years=15,
        )

        calculator = OMCalculator(pv_params, battery_params)
        result = calculator.calculate(use_excel_battery_formula=False)  # Use tech-based

        print(f"{tech.label:<25} "
              f"{result.battery_result.replacement_cost:>15,.0f} CHF  "
              f"{result.battery_result.total_lifetime_cost:>10,.0f} CHF")


def demo_export_to_dict():
    """Demo exporting results to dictionary for further processing."""
    print("\n" + "=" * 70)
    print("DEMO 6: Export Results to Dictionary")
    print("=" * 70)

    pv_params = PVSystemParameters(
        capacity_kwp=25.0,
        investment_chf=37500.0,
        pv_area_m2=150.0,
    )

    battery_params = BatteryParameters(
        capacity_kwh=15.0,
        investment_chf=12000.0,
    )

    calculator = OMCalculator(pv_params, battery_params)
    result = calculator.calculate()

    # Export to dictionary
    export = result.to_dict()

    print("\nExported Dictionary (for JSON/API output):")
    print("-" * 50)
    for key, value in export.items():
        print(f"  {key}: {value}")


def main():
    """Run all demos."""
    print("\n" + "=" * 70)
    print("O&M CALCULATOR - DEMO SUITE")
    print("=" * 70)

    # Run all demos
    demo_basic()
    demo_with_battery()
    demo_price_per_kwh()
    demo_with_overrides()
    demo_different_battery_tech()
    demo_export_to_dict()

    print("\n" + "=" * 70)
    print("ALL DEMOS COMPLETED SUCCESSFULLY")
    print("=" * 70)


if __name__ == "__main__":
    main()
