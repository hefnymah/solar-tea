
"""
Local Energy Community (LEG) Calculator
=======================================
Calculates parameters for "Lokale Elektrizitätsgemeinschaft" (LEG).
Replicates Excel 'Eingaben' sheet rows 55-66.
"""

from typing import Dict, Any, Optional
from dataclasses import dataclass

@dataclass
class LEGInput:
    """Input parameters for LEG calculation."""
    is_leg_active: bool = False  # Excel: 'LEG' (Row 56)
    annual_production_kwh: float = 0.0  # Excel: 'Jahresenergieertrag'
    
    # Optional overrides
    share_percent: Optional[float] = None  # Excel: 'Anteil Solarstrom an LEG in %' (Row 58)
    tariff_incl_accounting_chf: Optional[float] = None  # Excel: 'PV-Stromtarif LEG inkl. Abrechnung' (Row 60)
    accounting_cost_chf: Optional[float] = 0.015  # Excel: 'Abrechnungskosten LEG' (Row 61)
    operating_cost_total_chf: Optional[float] = None  # Excel: 'Betriebskosten LEG' (Row 66)
    
    # Metadata
    grid_level: str = 'NE 7'  # Excel: 'Nutzung der Netzebenen' (Row 57)
    
    # Dynamic Pricing Inputs
    grid_electricity_price_chf_per_kwh: Optional[float] = None  # External grid tariff (overrides 0.29 default)
    
    # For automated cost calculation (Row 65 logic)
    cost_factor_chf_per_kwh: Optional[float] = None  # Excel: Cell D65 (Hidden factor)
    system_capacity_kwp: Optional[float] = None  # Excel: 'Anlagenleistung'
    specific_yield_kwh_kwp: Optional[float] = None  # Excel: 'spez. Jahresenergieertrag'

    # Dependencies for validation
    self_consumption_percent: float = 0.0  # Excel: 'Eigennutzungsgrad'
    battery_increase_percent: float = 0.0  # Excel: 'Erhöhung Eigennutzungsgrad Speicher'


@dataclass
class LEGResult:
    """Output results for LEG calculation."""
    is_active: bool
    share_percent: float  # Excel: 'Anteil Solarstrom an LEG in %'
    share_kwh: float  # Excel: 'Anteil Solarstrom an LEG in kWh'
    tariff_incl_accounting: float  # Excel: 'PV-Stromtarif LEG inkl. Abrechnung'
    tariff_excl_accounting: float  # Excel: 'PV-Stromtarif LEG exkl. Abrechnung'
    accounting_cost: float  # Excel: 'Abrechnungskosten LEG'
    operating_cost_total: float  # Excel: 'Betriebskosten LEG' (Annual)
    revenue_chf: float  # Calculated Annual Revenue
    net_benefit_chf: float  # Annual Revenue - Annual Operating Costs
    max_possible_share: float  # Calculated physical limit
    grid_level: str
    base_electricity_price: float # The base price used for calculation


class LocalEnergyCommunityCalculator:
    """
    Calculates financial metrics for a Local Energy Community (LEG / Lokale Elektrizitätsgemeinschaft).
    """
    
    # Default Reference Values (Excel Column I)
    DEFAULT_ACCOUNTING_COST = 0.015  # CHF/kWh
    DEFAULT_TARIFF_FACTOR = 1.0 / 3.0  # 1/3 of Base Tariff
    BASE_TARIFF = 0.29  # CHF/kWh (Reference)

    def _calculate_default_tariff(self, base_price: Optional[float] = None) -> float:
        """
        Calculate default tariff (Excel I60 logic).
        Formula: Base Price * 1/3
        """
        price = base_price if base_price is not None else self.BASE_TARIFF
        return price * self.DEFAULT_TARIFF_FACTOR

    def _calculate_max_share(self, self_consumption: float, battery_increase: float) -> float:
        """
        Calculate maximum possible LEG share (Excel L58).
        Limit = 100% - Self Consumption - Battery Increase
        """
        return max(0.0, 100.0 - self_consumption - battery_increase)

    def calculate(self, inputs: LEGInput) -> LEGResult:
        """
        Perform the full LEG calculation.
        
        Args:
            inputs: LEGInput object containing all necessary parameters.
            
        Returns:
            LEGResult object with calculated metrics.
        """
        # 1. Determine Costs & Tariffs
        accounting_cost = inputs.accounting_cost_chf if inputs.accounting_cost_chf is not None else self.DEFAULT_ACCOUNTING_COST
        
        tariff_incl = inputs.tariff_incl_accounting_chf
        
        # Determine base price used (for reporting)
        base_price_used = inputs.grid_electricity_price_chf_per_kwh if inputs.grid_electricity_price_chf_per_kwh is not None else self.BASE_TARIFF

        if tariff_incl is None:
            tariff_incl = self._calculate_default_tariff(inputs.grid_electricity_price_chf_per_kwh)
            
        # Excel I62: Tariff Excl = Tariff Incl - Accounting Cost
        tariff_excl = tariff_incl - accounting_cost
        
        # 2. Handle Inactive State
        if not inputs.is_leg_active:
            return LEGResult(
                is_active=False,
                share_percent=0.0,
                share_kwh=0.0,
                tariff_incl_accounting=tariff_incl,
                tariff_excl_accounting=tariff_excl,
                accounting_cost=accounting_cost,
                operating_cost_total=0.0,
                revenue_chf=0.0,
                net_benefit_chf=0.0,
                max_possible_share=100.0,
                grid_level=inputs.grid_level,
                base_electricity_price=base_price_used
            )

        # 3. Calculate Effective Share
        # Excel L58: Physical limit validation
        max_share = self._calculate_max_share(inputs.self_consumption_percent, inputs.battery_increase_percent)
        
        # Excel I58 Logic: Use Max Share if input is None, otherwise clamp input to max
        raw_share = inputs.share_percent if inputs.share_percent is not None else max_share
        effective_share = min(raw_share, max_share)
        
        # 4. Calculate Energy Volume (kWh)
        # Excel C59: Production * Share / 100
        share_kwh = inputs.annual_production_kwh * (effective_share / 100.0)
        
        # 5. Calculate Operating Costs
        # Excel H65/H66 Logic:
        # If explicit cost provided (row 66 override), use it.
        # Else if D65 factor exists: Factor * Share% * Capacity * SpecificYield
        op_cost = 0.0
        if inputs.operating_cost_total_chf is not None:
            op_cost = inputs.operating_cost_total_chf
        elif (inputs.cost_factor_chf_per_kwh and 
              inputs.system_capacity_kwp and 
              inputs.specific_yield_kwh_kwp):
            # Reconstruct annual production from system data for cost calc consistency with Excel H65
            # (Though conceptually same as annual_production_kwh)
            calc_production = inputs.system_capacity_kwp * inputs.specific_yield_kwh_kwp
            op_cost = inputs.cost_factor_chf_per_kwh * (effective_share / 100.0) * calc_production
            
        # 6. Calculate Financials
        revenue = share_kwh * tariff_excl
        net_benefit = revenue - op_cost
        
        return LEGResult(
            is_active=True,
            share_percent=effective_share,
            share_kwh=share_kwh,
            tariff_incl_accounting=tariff_incl,
            tariff_excl_accounting=tariff_excl,
            accounting_cost=accounting_cost,
            operating_cost_total=op_cost,
            revenue_chf=revenue,
            net_benefit_chf=net_benefit,
            max_possible_share=max_share,
            grid_level=inputs.grid_level,
            base_electricity_price=base_price_used
        )
