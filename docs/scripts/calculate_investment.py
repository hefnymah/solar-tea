"""
Investment and Capital Structure Calculator
===========================================
Calculates investment costs and capital structure for PV systems.
Replicates Excel 'Eingaben' sheet Rows 85-97.
"""

from dataclasses import dataclass
from typing import Optional
from pronovo_subsidy_service import PronovoSubsidyService, SystemSpecs, InstallationType
import numpy_financial as nf

@dataclass
class InvestmentInput:
    """Input parameters for Investment Calculation."""
    
    # Required for automated cost calculation
    system_capacity_kwp: float = 0.0  # Excel: 'Anlagenleistung'
    
    # Optional Overrides
    investment_amount_chf: Optional[float] = None  # Excel: 'Investitionssumme PVA' (Row 86)
    
    # Additional Costs
    zev_investment_cost_chf: float = 0.0  # Excel: 'Investitionskosten ZEV' (Row 87)
    other_expenses_chf: float = 0.0  # Excel: 'Sonstige Aufwände PVA' (Row 88)
    
    # Building Envelope (Integrated Systems)
    building_envelope_value_chf_per_m2: float = 0.0  # Excel: 'Wert Funktion Gebäudehülle' (Row 89)
    pv_area_m2: float = 0.0  # Required for building envelope deduction calculation
    
    # VAT Configuration
    is_vat_taxable: bool = True  # Excel: '_MWStPflicht'
    vat_rate_percent: float = 7.7  # Excel: '_MWStSatz'
    
    # Subsidies & Bonuses (for Net Investment)
    one_time_payment_eiv_chf: float = 0.0  # Excel: 'Einmalvergütung'. If 0, auto-calculated.
    facade_bonus_chf: float = 0.0  # Excel: 'Fassadenbonus'
    height_bonus_chf: float = 0.0  # Excel: 'Höhenbonus'
    parking_bonus_chf: float = 0.0  # Excel: 'Parkflächenbonus'
    other_subsidies_chf: float = 0.0  # Excel: 'direkteFörderung'
    tax_savings_chf: float = 0.0  # Excel: 'Steuereinsparung'
    
    # Capital Structure Inputs
    debt_capital_1_chf: float = 0.0  # Excel: 'Fremdkapital 1'
    debt_capital_1_rate_percent: float = 0.0
    debt_capital_1_term_years: int = 0
    
    debt_capital_2_chf: float = 0.0  # Excel: 'Fremdkapital 2'
    debt_capital_2_rate_percent: float = 0.0
    debt_capital_2_term_years: int = 0


@dataclass
class InvestmentResult:
    """Output results for Investment Calculation."""
    
    # Gross Components
    investment_amount_pv_chf: float  # Excel: 'Investitionssumme PVA'
    zev_investment_cost_chf: float  # Excel: 'Investitionskosten ZEV'
    other_expenses_chf: float  # Excel: 'Sonstige Aufwände PVA'
    building_envelope_deduction_chf: float  # Excel: 'Abzug Funktion Gebäudehülle' (Row 90)
    
    # VAT
    vat_amount_chf: float  # Excel: 'MWSt. Investitionskosten' (Row 91)
    vat_input_tax_credit_chf: float  # Excel: 'Vorsteuerabzug Investitionskosten' (Implicit)
    
    # Net Calculations
    relevant_investment_cost_chf: float  # Excel: 'relevante Investitionskosten PVA' (Row 92)
    total_subsidies_chf: float  # Sum of all subsidies
    net_investment_chf: float  # Excel: 'Investition netto PVA' (Row 93)
    
    # Capital Structure
    equity_capital_chf: float  # Excel: 'Eigenkapital PVA' (Row 95)
    debt_capital_1_chf: float  # Excel: 'Fremdkapital 1 PVA'
    debt_capital_2_chf: float  # Excel: 'Fremdkapital 2 PVA'
    total_capital_chf: float   # Validation check (Equity + Debt)
    
    # Debt Service (Calculated via numpy_financial)
    debt_1_annual_payment_chf: float
    debt_2_annual_payment_chf: float
    total_annual_debt_service_chf: float


@dataclass
class BatteryInvestmentInput:
    """Input parameters for Battery Investment (Rows 99-108)."""
    
    battery_capacity_kwh: float = 0.0
    
    # Cost Parameters
    battery_price_per_kwh: float = 700.0  # Excel Default
    battery_investment_cost_chf: Optional[float] = None  # Excel: 'Investitionssumme Batterie' (Row 100)
    other_battery_expenses_chf: float = 0.0  # Excel: 'Sonstige Aufwände Batterie' (Row 101)
    emergency_power_value_chf: float = 0.0  # Excel: 'Wert Funktion Notstrom' (Row 102) - Deduction
    
    # VAT (Usually same as PV)
    is_vat_taxable: bool = True
    vat_rate_percent: float = 7.7
    
    # Financials
    battery_subsidy_chf: float = 0.0  # Excel: 'Förderung Batterie' (Implicit in formula C105)
    
    # Capital Structure
    debt_capital_chf: float = 0.0  # Excel: 'Fremdkapital Batterie'
    debt_rate_percent: float = 0.0
    debt_term_years: int = 0


@dataclass
class BatteryInvestmentResult:
    """Output results for Battery Investment."""
    
    gross_investment_chf: float
    emergency_power_deduction_chf: float  # Excel: 'Abzug Funktion Notstrom' (Row 102 calculated)
    
    vat_amount_chf: float
    vat_input_tax_credit_chf: float
    
    relevant_investment_cost_chf: float  # Excel: 'relevante Investitionskosten Batterie' (Row 104)
    net_investment_chf: float  # Excel: 'Investition netto Batterie' (Row 105)
    
    equity_capital_chf: float  # Excel: 'Eigenkapital Batterie' (Row 107)
    debt_capital_chf: float
    
    annual_debt_service_chf: float


class InvestmentCalculator:
    """
    Calculates Investment & Capital Structure logic (Excel Rows 85-97 PV & 99-108 Battery).
    Integrated with PronovoSubsidyService for automatic EIV estimation.
    Uses numpy_financial for annuity calculations.
    """
    
    def __init__(self):
        self.subsidy_service = PronovoSubsidyService()
    
    def _calculate_tiered_investment_cost(self, capacity_kwp: float) -> float:
        """
        Calculates default investment cost based on Excel I86 tiered formula.
        """
        if capacity_kwp <= 0:
            return 0.0
        elif capacity_kwp < 10:
            return 2034.0 * capacity_kwp + 6191.0
        elif capacity_kwp < 30:
            return 1177.0 * capacity_kwp + 14762.0
        elif capacity_kwp < 100:
            return 1464.0 * capacity_kwp + 6148.0
        else:
            # >= 100
            return 758.0 * capacity_kwp + 76754.0

    def _calculate_annuity(self, principal: float, rate_percent: float, term_years: int) -> float:
        """Calculates annual payment (PMT). Returns positive value."""
        if principal <= 0 or term_years <= 0:
            return 0.0
        if rate_percent == 0:
            return principal / term_years
            
        rate = rate_percent / 100.0
        # nf.pmt returns negative for payment, we return positive magnitude
        pmt = nf.pmt(rate, term_years, principal)
        return abs(pmt)

    def calculate(self, inputs: InvestmentInput) -> InvestmentResult:
        """
        Performs the full investment calculation for PV System.
        """
        
        # 1. Base Investment Cost (Row 86)
        if inputs.investment_amount_chf is not None:
            invest_pv = inputs.investment_amount_chf
        else:
            invest_pv = self._calculate_tiered_investment_cost(inputs.system_capacity_kwp)
            
        # 2. Building Envelope Deduction (Row 90)
        # Formula: - Area * Cost/m2
        deduction_envelope = 0.0
        if inputs.building_envelope_value_chf_per_m2 > 0 and inputs.pv_area_m2 > 0:
            deduction_envelope = -(inputs.pv_area_m2 * inputs.building_envelope_value_chf_per_m2)
            
        # 3. VAT Calculation (Row 91)
        # Base for VAT = InvestPV + ZEV + Other + Deduction
        base_for_vat = (
            invest_pv + 
            inputs.zev_investment_cost_chf + 
            inputs.other_expenses_chf + 
            deduction_envelope
        )
        
        vat_amount = 0.0
        if inputs.is_vat_taxable:
            vat_amount = base_for_vat * (inputs.vat_rate_percent / 100.0)
            
        # VAT Input Tax Credit (Vorsteuerabzug)
        # Usually equals VAT amount if taxable business
        vat_input_credit = vat_amount if inputs.is_vat_taxable else 0.0
        
        # 4. Relevant Investment Costs (Row 92)
        # Formula: Base (excl VAT) + VAT Input Credit
        # Note: If taxable, you pay VAT but get it back as credit, so net cash impact logic.
        # Check Excel C92: Sum of components + Vorsteuerabzug.
        # Actually in Excel C92 = Sum(Costs) + Vorsteuerabzug. 
        # C91 is VAT payable. Vorsteuerabzug is usually treated as a credit.
        relevant_costs = base_for_vat + vat_input_credit
        
        # 5. Net Investment (Row 93)
        # Auto-calculate EIV if not provided
        eiv = inputs.one_time_payment_eiv_chf
        if eiv == 0.0 and inputs.system_capacity_kwp > 0:
            # Create a basic spec for estimation (Assuming ANGEBAUT/Attached as standard default in absence of specific data)
            # You might want to expose installation_type in inputs later.
            spec = SystemSpecs(
                capacity_kwp=inputs.system_capacity_kwp,
                installation_type=InstallationType.ANGEBAUT 
            )
            eiv_result = self.subsidy_service.calculate_eiv(spec)
            eiv = eiv_result.total_subsidy

        # Formula: Relevant Costs - Subsidies
        total_subsidies = (
            eiv +
            inputs.facade_bonus_chf +
            inputs.height_bonus_chf + 
            inputs.parking_bonus_chf +
            inputs.other_subsidies_chf +
            inputs.tax_savings_chf
        )
        
        net_investment = max(0.0, relevant_costs - total_subsidies)
        
        # 6. Capital Structure (Row 95-97)
        # Equity = Net Investment - Debt1 - Debt2
        # Excel ensures Debt doesn't exceed Net Investment
        debt1 = max(0.0, min(inputs.debt_capital_1_chf, net_investment))
        
        remaining_for_debt2 = net_investment - debt1
        debt2 = max(0.0, min(inputs.debt_capital_2_chf, remaining_for_debt2))
        
        equity = max(0.0, net_investment - debt1 - debt2)
        
        total_capital = equity + debt1 + debt2
        
        # 7. Debt Service Calculation (Annuity)
        debt1_pmt = self._calculate_annuity(debt1, inputs.debt_capital_1_rate_percent, inputs.debt_capital_1_term_years)
        debt2_pmt = self._calculate_annuity(debt2, inputs.debt_capital_2_rate_percent, inputs.debt_capital_2_term_years)
        
        return InvestmentResult(
            investment_amount_pv_chf          =invest_pv,
            zev_investment_cost_chf           =inputs.zev_investment_cost_chf,
            other_expenses_chf                =inputs.other_expenses_chf,
            building_envelope_deduction_chf   =deduction_envelope,
            vat_amount_chf                    =vat_amount,
            vat_input_tax_credit_chf          =vat_input_credit,
            relevant_investment_cost_chf      =relevant_costs,
            total_subsidies_chf               =total_subsidies,
            net_investment_chf                =net_investment,
            equity_capital_chf                =equity,
            debt_capital_1_chf                =debt1,
            debt_capital_2_chf                =debt2,
            total_capital_chf                 =total_capital,
            debt_1_annual_payment_chf         =debt1_pmt,
            debt_2_annual_payment_chf         =debt2_pmt,
            total_annual_debt_service_chf     =debt1_pmt + debt2_pmt
        )

    def calculate_battery(self, inputs: BatteryInvestmentInput) -> BatteryInvestmentResult:
        """
        Performs battery investment calculation (Rows 99-108).
        """
        # 1. Gross Investment (Row 100)
        # If not provided, calculate using default price/kWh
        gross_invest = inputs.battery_investment_cost_chf
        if gross_invest is None:
            gross_invest = inputs.battery_capacity_kwh * inputs.battery_price_per_kwh
            
        # 2. Emergency Power Deduction (Row 102)
        # Excel Formula: If Value > 0, return -Value (Cost Deduction)
        # This is because "sowieso" costs for emergency power are deducted from economy calculation
        deduction_emergency = 0.0
        if inputs.emergency_power_value_chf > 0:
            deduction_emergency = -inputs.emergency_power_value_chf
            
        # 3. VAT (Row 103)
        # Base = Gross + Other + Deduction
        base_for_vat = (
            gross_invest +
            inputs.other_battery_expenses_chf +
            deduction_emergency
        )
        
        vat_amount = 0.0
        if inputs.is_vat_taxable:
            vat_amount = base_for_vat * (inputs.vat_rate_percent / 100.0)
            
        vat_input_credit = vat_amount if inputs.is_vat_taxable else 0.0
        
        # 4. Relevant Investment (Row 104)
        # Base (excl VAT) + Input Credit
        relevant_costs = base_for_vat + vat_input_credit
        
        # 5. Net Investment (Row 105)
        # Relevant - Subsidy
        net_investment = max(0.0, relevant_costs - inputs.battery_subsidy_chf)
        
        # 6. Capital Structure (Row 107-108)
        debt = max(0.0, min(inputs.debt_capital_chf, net_investment))
        equity = max(0.0, net_investment - debt)
        
        # 7. Debt Service
        debt_pmt = self._calculate_annuity(debt, inputs.debt_rate_percent, inputs.debt_term_years)
        
        return BatteryInvestmentResult(
            gross_investment_chf              =gross_invest,
            emergency_power_deduction_chf     =deduction_emergency,
            vat_amount_chf                    =vat_amount,
            vat_input_tax_credit_chf          =vat_input_credit,
            relevant_investment_cost_chf      =relevant_costs,
            net_investment_chf                =net_investment,
            equity_capital_chf                =equity,
            debt_capital_chf                  =debt,
            annual_debt_service_chf           =debt_pmt
        )
