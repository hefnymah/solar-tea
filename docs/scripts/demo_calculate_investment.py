#!/usr/bin/env python3
"""
Investment Calculator Demo
==========================
Demonstrates the calculation of Investment & Capital Structure parameters.
Verifies logic against Excel 'Eingaben' sheet Rows 85-97.

Usage:
    python3 demo_calculate_investment.py
"""

from calculate_investment import InvestmentCalculator, InvestmentInput, BatteryInvestmentInput

def main():
    print("="*80)
    print("💰 INVESTMENT CALCULATOR DEMO")
    print("="*80)
    
    calculator = InvestmentCalculator()
    
    # CASE 1: Small System (Tier 1: <10 kWp)
    # 8 kWp -> Formula: 2034 * 8 + 6191 = 22,463 CHF
    print("\n🔹 CASE 1: Small System (8 kWp)")
    inputs1 = InvestmentInput(
        system_capacity_kwp=8.0,
        is_vat_taxable=True
    )
    res1 = calculator.calculate(inputs1)
    
    print(f"   Capacity: {inputs1.system_capacity_kwp} kWp")
    print(f"   Calculated Investment (Gross): {res1.investment_amount_pv_chf:,.2f} CHF (Expected: 22,463.00)")
    # VAT 7.7% of 22463 = 1729.65
    print(f"   VAT Amount (7.7%): {res1.vat_amount_chf:,.2f} CHF")
    print(f"   Relevant Cost (Gross + VAT Credit): {res1.relevant_investment_cost_chf:,.2f} CHF")
    print(f"   Net Investment: {res1.net_investment_chf:,.2f} CHF")
    
    
    # CASE 2: Medium System (Tier 2: 10-30 kWp)
    # 20 kWp -> Formula: 1177 * 20 + 14762 = 23,540 + 14,762 = 38,302 CHF
    print("\n🔹 CASE 2: Medium System (20 kWp)")
    inputs2 = InvestmentInput(
        system_capacity_kwp=20.0
    )
    res2 = calculator.calculate(inputs2)
    
    print(f"   Capacity: {inputs2.system_capacity_kwp} kWp")
    print(f"   Calculated Investment (Gross): {res2.investment_amount_pv_chf:,.2f} CHF (Expected: 38,302.00)")
    
    
    # CASE 3: Complex Scenario (Subsidies + Debt)
    # 100 kWp System
    # Inputs: EIV = 20,000, Debt1 = 50,000 (2.5%, 15y), Debt2 = 20,000 (3.0%, 10y)
    print("\n🔹 CASE 3: Large System (100 kWp) with Subsidies & Debt Repayment")
    inputs3 = InvestmentInput(
        system_capacity_kwp=100.0,
        one_time_payment_eiv_chf=20000.0,
        tax_savings_chf=5000.0,
        debt_capital_1_chf=50000.0,
        debt_capital_1_rate_percent=2.5,
        debt_capital_1_term_years=15,
        
        debt_capital_2_chf=20000.0,
        debt_capital_2_rate_percent=3.0,
        debt_capital_2_term_years=10
    )
    res3 = calculator.calculate(inputs3)
    
    # Formula check: 758 * 100 + 76754 = 152,554
    print(f"   Capacity: {inputs3.system_capacity_kwp} kWp")
    print(f"   Calculated Investment (Gross): {res3.investment_amount_pv_chf:,.2f} CHF")
    
    print(f"   Subsidies (EIV + Tax): {res3.total_subsidies_chf:,.2f} CHF")
    print(f"   Net Investment: {res3.net_investment_chf:,.2f} CHF")
    
    print(f"   Debt 1: {res3.debt_capital_1_chf:,.2f} CHF (@ 2.5%, 15y)")
    print(f"   👉 Annual Payment 1: {res3.debt_1_annual_payment_chf:,.2f} CHF")
    
    print(f"   Debt 2: {res3.debt_capital_2_chf:,.2f} CHF (@ 3.0%, 10y)")
    print(f"   👉 Annual Payment 2: {res3.debt_2_annual_payment_chf:,.2f} CHF")
    
    print(f"   => Equity: {res3.equity_capital_chf:,.2f} CHF")
    print(f"   Total Annual Debt Service: {res3.total_annual_debt_service_chf:,.2f} CHF")


    # CASE 4: Automatic Subsidy Calculation (Pronovo Service)
    # 15 kWp System, Attached (ANGEBAUT)
    # Expected EIV ~: Base + Performance.
    # Base <30kWp: 350 CHF
    # Performance <30kWp: 460 CHF/kWp * 15 = 6900 CHF
    # Total ~ 7250 CHF (approx depending on exact tariff year)
    print("\n🔹 CASE 4: Automatic Subsidy Calculation (15 kWp)")
    inputs4 = InvestmentInput(
        system_capacity_kwp=15.0,
        one_time_payment_eiv_chf=0.0 # Trigger auto-calc
    )
    res4 = calculator.calculate(inputs4)
    
    print(f"   Capacity: {inputs4.system_capacity_kwp} kWp")
    print(f"   EIV Input: {inputs4.one_time_payment_eiv_chf} CHF")
    print(f"   👉 Auto-Calculated Subsidies: {res4.total_subsidies_chf:,.2f} CHF")
    if res4.total_subsidies_chf > 0:
        print("   ✅ Automatic subsidy calculation active")
    else:
        print("   ❌ Automatic subsidy calculation failed")

    # CASE 5: Battery Investment
    print("\n🔹 CASE 5: Battery Investment (10 kWh)")
    # Default Cost = 10 * 700 = 7000
    # Emergency Power value = 500 (Deduction)
    # Subsidy = 1000
    # Debt = 3000 (@ 2.5%, 10y)
    battery_inputs = BatteryInvestmentInput(
        battery_capacity_kwh=10.0,
        emergency_power_value_chf=500.0,
        battery_subsidy_chf=1000.0,
        debt_capital_chf=3000.0,
        debt_rate_percent=2.5,
        debt_term_years=10,
        is_vat_taxable=True
    )
    
    bat_res = calculator.calculate_battery(battery_inputs)
    
    print(f"   Capacity: {battery_inputs.battery_capacity_kwh} kWh")
    print(f"   Gross Investment (calc): {bat_res.gross_investment_chf:,.2f} CHF (Expected: 7000)")
    print(f"   Emergency Power Deduction: {bat_res.emergency_power_deduction_chf:,.2f} CHF")
    
    # Base for VAT = 7000 - 500 (Deduction) = 6500
    # VAT = 6500 * 7.7% = 500.50
    # Relevant = 6500 + 500.50 = 7000.50
    print(f"   VAT Amount: {bat_res.vat_amount_chf:,.2f} CHF")
    
    # Net = Relevant (7000.50) - Subsidy (1000) = 6000.50 (Approx, pending validation)
    print(f"   Net Investment: {bat_res.net_investment_chf:,.2f} CHF")
    
    print(f"   Debt: {bat_res.debt_capital_chf:,.2f} CHF")
    print(f"   => Equity: {bat_res.equity_capital_chf:,.2f} CHF")
    print(f"   Annual Debt Service: {bat_res.annual_debt_service_chf:,.2f} CHF")


    print("\n" + "="*80)
    print("✅ Demo completed.")

if __name__ == "__main__":
    main()
