#!/usr/bin/env python3
"""
ZEV Calculator Demo
===================
Demonstrates usage of the ZEV (Eigenverbrauchsgemeinschaft) Calculator.

Run from oop-solar directory:
    python demo_calculate_zev.py
"""

from calculate_zev import ZEVCalculator, ZEVParameters


def demo_basic_zev():
    """Demo 1: Basic ZEV calculation with default tariffs."""
    print("\n" + "=" * 70)
    print("DEMO 1: Basic ZEV Calculation")
    print("=" * 70)
    
    params = ZEVParameters(
        zev_enabled=True,
        annual_production_kwh=90000,  # 90 kWp × 1000 kWh/kWp
        capacity_kwp=90.0,
        specific_yield_kwh_kwp=1000.0,
        annual_consumption_kwh=80000,
        peak_reduction_percent=10.0,
        accounting_cost_per_kwh=0.01,  # 1 Rp/kWh
        base_cost_per_participant_month=8.0,  # 8 CHF/month
    )
    
    calculator = ZEVCalculator()
    result = calculator.calculate(params)
    result.print_summary()


def demo_with_address():
    """Demo 2: ZEV calculation with real tariffs from address lookup."""
    print("\n" + "=" * 70)
    print("DEMO 2: ZEV with Real Tariffs (Address Lookup)")
    print("=" * 70)
    
    params = ZEVParameters(
        zev_enabled=True,
        annual_production_kwh=50000,
        capacity_kwp=50.0,
        annual_consumption_kwh=45000,
        peak_reduction_percent=5.0,
        accounting_cost_per_kwh=0.015,
    )
    
    calculator = ZEVCalculator()
    
    # Try different Swiss addresses
    addresses = [
        "Bahnhofstrasse 10, Zürich",
        "Marktgasse 1, Bern",
    ]
    
    for address in addresses:
        print(f"\n--- {address} ---")
        result = calculator.calculate_with_address(params, address)
        print(f"Electricity Tariff: {result.electricity_tariff_chf_kwh:.4f} CHF/kWh")
        print(f"ZEV Revenue: {result.zev_revenue_chf:,.2f} CHF/year")
        print(f"Net Benefit: {result.net_benefit_chf:,.2f} CHF/year")


def demo_no_zev():
    """Demo 3: Compare with and without ZEV."""
    print("\n" + "=" * 70)
    print("DEMO 3: Comparison - With vs Without ZEV")
    print("=" * 70)
    
    base_params = {
        'annual_production_kwh': 30000,
        'capacity_kwp': 30.0,
        'annual_consumption_kwh': 25000,
    }
    
    calculator = ZEVCalculator()
    
    # Without ZEV
    params_no_zev = ZEVParameters(zev_enabled=False, **base_params)
    result_no_zev = calculator.calculate(params_no_zev)
    
    # With ZEV
    params_zev = ZEVParameters(
        zev_enabled=True,
        peak_reduction_percent=10.0,
        accounting_cost_per_kwh=0.01,
        **base_params
    )
    result_zev = calculator.calculate(params_zev)
    
    print(f"\n{'Metric':<35} {'Without ZEV':>15} {'With ZEV':>15}")
    print("-" * 70)
    print(f"{'Self-consumption %':<35} {'0.0':>15} {result_zev.self_consumption_percent:>15.1f}")
    print(f"{'ZEV Revenue (CHF/year)':<35} {'0.00':>15} {result_zev.zev_revenue_chf:>15,.2f}")
    print(f"{'Power Savings (CHF/year)':<35} {'0.00':>15} {result_zev.power_savings_chf:>15,.2f}")
    print(f"{'ZEV Costs (CHF/year)':<35} {'0.00':>15} {result_zev.total_zev_costs_chf:>15,.2f}")
    print(f"{'Net Benefit (CHF/year)':<35} {'0.00':>15} {result_zev.net_benefit_chf:>15,.2f}")


def demo_custom_self_consumption():
    """Demo 4: Override automatic self-consumption calculation."""
    print("\n" + "=" * 70)
    print("DEMO 4: Custom Self-Consumption Override")
    print("=" * 70)
    
    calculator = ZEVCalculator()
    
    # With automatic calculation
    params_auto = ZEVParameters(
        zev_enabled=True,
        annual_production_kwh=100000,
        capacity_kwp=100.0,
        annual_consumption_kwh=120000,
    )
    result_auto = calculator.calculate(params_auto)
    
    # With manual override (e.g., based on detailed simulation)
    params_manual = ZEVParameters(
        zev_enabled=True,
        annual_production_kwh=100000,
        capacity_kwp=100.0,
        annual_consumption_kwh=120000,
        self_consumption_percent=45.0,  # Override with exact value
    )
    result_manual = calculator.calculate(params_manual)
    
    print(f"\nAutomatic self-consumption: {result_auto.self_consumption_percent:.1f}%")
    print(f"Manual override: {result_manual.self_consumption_percent:.1f}%")
    print(f"\nRevenue difference: {result_manual.zev_revenue_chf - result_auto.zev_revenue_chf:+,.2f} CHF/year")


def demo_export_dict():
    """Demo 5: Export results to dictionary (for JSON/API)."""
    print("\n" + "=" * 70)
    print("DEMO 5: Export to Dictionary")
    print("=" * 70)
    
    params = ZEVParameters(
        zev_enabled=True,
        annual_production_kwh=60000,
        annual_consumption_kwh=50000,
        capacity_kwp=60.0,
    )
    
    calculator = ZEVCalculator()
    result = calculator.calculate(params)
    
    export = result.to_dict()
    print("\nExported dictionary:")
    for key, value in export.items():
        print(f"  {key}: {value}")


def main():
    """Run all demos."""
    print("=" * 70)
    print("🏘️  ZEV CALCULATOR - DEMO SUITE")
    print("=" * 70)
    
    demo_basic_zev()
    demo_with_address()
    demo_no_zev()
    demo_custom_self_consumption()
    demo_export_dict()
    
    print("\n" + "=" * 70)
    print("✅ All demos completed!")
    print("=" * 70)


if __name__ == "__main__":
    main()
