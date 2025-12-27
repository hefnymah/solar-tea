#!/usr/bin/env python3
"""
ZEV (Eigenverbrauchsgemeinschaft) Calculator - OOP Version
==========================================================
Calculates ZEV (Energy Community) parameters and related costs/revenues.

Replicates Excel 'Eingaben' sheet rows 41-53:
- Row 41: ZEV oder vZEV (JA/NEIN)
- Row 42: Anzahl separat gemessene Teilnehmer ZEV
- Row 44: Reduktion der Leistungsspitzen pro Jahr
- Row 45: Eigenverbrauchsanteil ZEV (%)
- Row 46: Eigenverbrauchsanteil ZEV (kWh)
- Row 47: PV-Stromtarif ZEV / ersetzter Bezugstarif
- Row 48: Leistungstarif ZEV
- Row 50: Abrechnungskosten ZEV (pro kWh)
- Row 51: Grundkosten Abrechnung ZEV pro Teilnehmer
- Row 53: Betriebskosten ZEV

Integration with TariffService for real market prices based on address.

Usage:
    from calculate_zev_oop import ZEVCalculator, ZEVParameters
    from tariff_service import TariffService
    
    # With manual tariffs
    params = ZEVParameters(
        zev_enabled=True,
        annual_production_kwh=90000,
        annual_consumption_kwh=50000,
    )
    calculator = ZEVCalculator()
    result = calculator.calculate(params)
    
    # With real tariffs from address lookup
    result = calculator.calculate_with_address(params, "Bahnhofstrasse 10, Zürich")
"""

from dataclasses import dataclass, field
from typing import Optional, Dict, Any, List
from enum import Enum


# =============================================================================
# DATA CLASSES
# =============================================================================

@dataclass
class ZEVParameters:
    """
    Input parameters for ZEV calculations.
    
    Maps to Excel rows 41-53 inputs.
    """
    # Row 41: ZEV enabled?
    zev_enabled: bool = False
    
    # PV System parameters (from PV sizing)
    annual_production_kwh: float = 0.0  # Annual PV production
    capacity_kwp: float = 0.0  # PV capacity (for self-consumption formula)
    specific_yield_kwh_kwp: float = 1000.0  # Specific yield
    
    # Consumption parameters
    annual_consumption_kwh: float = 0.0  # Total consumption (Gesamtverbrauch)
    
    # Row 42: Number of participants (optional, auto-calculated if None)
    num_participants: Optional[int] = None
    
    # Row 44: Peak power reduction (%)
    peak_reduction_percent: float = 0.0
    
    # Row 45: Self-consumption percentage (optional, auto-calculated if None)
    self_consumption_percent: Optional[float] = None
    
    # Row 47: Electricity tariff for ZEV members (CHF/kWh)
    # If None, calculated from consumption price × 0.8 - accounting costs
    electricity_tariff_chf_kwh: Optional[float] = None
    
    # Row 48: Power tariff (CHF/kW/month)
    # If None, defaults based on consumption threshold
    power_tariff_chf_kw_month: Optional[float] = None
    
    # Row 50: Accounting costs per kWh (CHF/kWh)
    accounting_cost_per_kwh: float = 0.0
    
    # Row 51: Base accounting cost per participant per month (CHF)
    base_cost_per_participant_month: float = 8.0
    
    # Row 53: Operating costs (CHF/year)
    operating_costs_chf_year: float = 0.0
    
    # Monthly peak power (kW) - for power savings calculation
    monthly_peak_power_kw: Optional[float] = None
    
    # PV degradation factor (for year-by-year calculations)
    degradation_factor: float = 1.0


@dataclass
class ZEVResult:
    """
    Result of ZEV calculations.
    
    Contains both input echoes and calculated values.
    """
    # Status
    zev_enabled: bool = False
    
    # Row 42: Participants (calculated or input)
    num_participants: int = 0
    
    # Row 45-46: Self-consumption
    self_consumption_percent: float = 0.0
    self_consumption_kwh: float = 0.0
    
    # Row 44: Peak reduction
    peak_reduction_percent: float = 0.0
    
    # Row 47: Electricity tariff used
    electricity_tariff_chf_kwh: float = 0.0
    
    # Row 48: Power tariff used
    power_tariff_chf_kw_month: float = 0.0
    
    # Row 50: Accounting cost per kWh
    accounting_cost_per_kwh: float = 0.0
    
    # Row 51: Base cost per participant
    base_cost_per_participant_month: float = 0.0
    
    # Row 53: Operating costs
    operating_costs_chf_year: float = 0.0
    
    # Calculated revenues
    zev_revenue_chf: float = 0.0  # Self-consumption × tariff
    power_savings_chf: float = 0.0  # Peak reduction savings
    
    # Calculated costs
    accounting_costs_chf: float = 0.0  # Total accounting costs
    total_zev_costs_chf: float = 0.0  # Accounting + operating
    
    # Net benefit
    net_benefit_chf: float = 0.0  # Revenue + savings - costs
    
    # Metadata
    tariff_source: str = "default"  # "default", "address_lookup", "manual"
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for export."""
        return {
            'zev_oder_vzev': 'JA' if self.zev_enabled else 'NEIN',
            'anzahl_teilnehmer_zev': self.num_participants,
            'eigenverbrauchsanteil_prozent': round(self.self_consumption_percent, 2),
            'eigenverbrauchsanteil_kwh': round(self.self_consumption_kwh, 2),
            'reduktion_leistungsspitzen_prozent': round(self.peak_reduction_percent, 2),
            'pv_stromtarif_zev_chf_kwh': round(self.electricity_tariff_chf_kwh, 4),
            'leistungstarif_zev_chf_kw_month': round(self.power_tariff_chf_kw_month, 2),
            'abrechnungskosten_chf_kwh': round(self.accounting_cost_per_kwh, 4),
            'grundkosten_pro_teilnehmer_chf_month': round(self.base_cost_per_participant_month, 2),
            'betriebskosten_chf_year': round(self.operating_costs_chf_year, 2),
            'zev_einnahmen_chf': round(self.zev_revenue_chf, 2),
            'leistungseinsparung_chf': round(self.power_savings_chf, 2),
            'abrechnungskosten_total_chf': round(self.accounting_costs_chf, 2),
            'total_zev_kosten_chf': round(self.total_zev_costs_chf, 2),
            'netto_zev_nutzen_chf': round(self.net_benefit_chf, 2),
            'tariff_source': self.tariff_source,
        }
    
    def print_summary(self):
        """Print a summary of ZEV results."""
        print("=" * 60)
        print("ZEV CALCULATION RESULTS")
        print("=" * 60)
        print(f"\nStatus: {'ZEV aktiv' if self.zev_enabled else 'Kein ZEV'}")
        
        if not self.zev_enabled:
            print("No ZEV calculations performed.")
            return
        
        print(f"\n--- Configuration ---")
        print(f"  Participants: {self.num_participants}")
        print(f"  Self-consumption: {self.self_consumption_percent:.1f}% ({self.self_consumption_kwh:,.0f} kWh)")
        print(f"  Peak reduction: {self.peak_reduction_percent:.1f}%")
        
        print(f"\n--- Tariffs ---")
        print(f"  Electricity: {self.electricity_tariff_chf_kwh:.4f} CHF/kWh")
        print(f"  Power: {self.power_tariff_chf_kw_month:.2f} CHF/kW/month")
        print(f"  Accounting: {self.accounting_cost_per_kwh:.4f} CHF/kWh")
        print(f"  Source: {self.tariff_source}")
        
        print(f"\n--- Annual Financial Summary ---")
        print(f"  ZEV Revenue: +{self.zev_revenue_chf:,.2f} CHF")
        print(f"  Power Savings: +{self.power_savings_chf:,.2f} CHF")
        print(f"  Accounting Costs: -{self.accounting_costs_chf:,.2f} CHF")
        print(f"  Operating Costs: -{self.operating_costs_chf_year:,.2f} CHF")
        print(f"  ---")
        print(f"  Net Benefit: {self.net_benefit_chf:,.2f} CHF/year")
        print("=" * 60)


# =============================================================================
# ZEV CALCULATOR
# =============================================================================

class ZEVCalculator:
    """
    ZEV (Eigenverbrauchsgemeinschaft) Calculator.
    
    Calculates ZEV parameters and financial benefits based on Excel formulas.
    Supports integration with TariffService for real market prices.
    """
    
    # Default base electricity price (Excel default: 0.29 CHF/kWh)
    DEFAULT_ELECTRICITY_PRICE = 0.29
    
    # ZEV discount factor (80% of retail price)
    ZEV_DISCOUNT_FACTOR = 0.8
    
    # Default power tariff thresholds
    HIGH_CONSUMPTION_THRESHOLD = 50000  # kWh/year
    HIGH_CONSUMPTION_POWER_TARIFF = 10.0  # CHF/kW/month
    LOW_CONSUMPTION_POWER_TARIFF = 1.5  # CHF/kW/month
    
    # Self-consumption formula coefficients (Excel I45)
    SC_COEFFICIENT = 320.67
    SC_EXPONENT = -0.492
    
    def __init__(self):
        """Initialize ZEV calculator."""
        self._tariff_service = None
    
    @property
    def tariff_service(self):
        """Lazy load tariff service."""
        if self._tariff_service is None:
            try:
                from tariff_service import TariffService
                self._tariff_service = TariffService()
            except ImportError:
                self._tariff_service = None
        return self._tariff_service
    
    # -------------------------------------------------------------------------
    # Default Calculations (Excel Column I formulas)
    # -------------------------------------------------------------------------
    
    def calc_default_self_consumption(
        self,
        capacity_kwp: float,
        specific_yield: float,
        consumption_kwh: float
    ) -> float:
        """
        Calculate default self-consumption percentage (Excel I45).
        
        Formula: 320.67 × (Production/Consumption × 100) ^ -0.492
        
        Args:
            capacity_kwp: PV system capacity in kWp
            specific_yield: Specific yield in kWh/kWp
            consumption_kwh: Annual consumption in kWh
            
        Returns:
            Self-consumption percentage (0-100%)
        """
        if capacity_kwp <= 0 or specific_yield <= 0 or consumption_kwh <= 0:
            return 0.0
        
        production = capacity_kwp * specific_yield
        ratio_percent = (production / consumption_kwh) * 100.0
        
        if ratio_percent <= 0:
            return 0.0
        
        try:
            sc_percent = self.SC_COEFFICIENT * (ratio_percent ** self.SC_EXPONENT)
            return max(0.0, min(100.0, sc_percent))
        except (ValueError, OverflowError):
            return 0.0
    
    def calc_default_participants(self, consumption_kwh: float) -> int:
        """
        Calculate default number of participants (Excel I42).
        
        Formula: ROUNDDOWN(Consumption / 5000, 0)
        Assumes ~5,000 kWh per participant per year.
        
        Args:
            consumption_kwh: Annual consumption in kWh
            
        Returns:
            Number of participants
        """
        if consumption_kwh <= 0:
            return 0
        return int(consumption_kwh / 5000)
    
    def calc_default_electricity_tariff(
        self,
        zev_enabled: bool,
        base_price_chf_kwh: float = None,
        accounting_cost_chf_kwh: float = 0.0
    ) -> float:
        """
        Calculate default ZEV electricity tariff (Excel I47).
        
        Formula:
        - No ZEV: 0.29 CHF/kWh (retail price)
        - ZEV: 0.29 × 0.8 - accounting_costs = 0.232 - accounting_costs
        
        Args:
            zev_enabled: Whether ZEV is active
            base_price_chf_kwh: Base electricity price (default: 0.29)
            accounting_cost_chf_kwh: Accounting costs per kWh
            
        Returns:
            Electricity tariff in CHF/kWh
        """
        base = base_price_chf_kwh or self.DEFAULT_ELECTRICITY_PRICE
        
        if not zev_enabled:
            return base
        
        return base * self.ZEV_DISCOUNT_FACTOR - accounting_cost_chf_kwh
    
    def calc_default_power_tariff(self, consumption_kwh: float) -> float:
        """
        Calculate default power tariff (Excel I48).
        
        Formula: IF(consumption > 50000, 10, 1.5)
        
        Args:
            consumption_kwh: Annual consumption in kWh
            
        Returns:
            Power tariff in CHF/kW/month
        """
        if consumption_kwh > self.HIGH_CONSUMPTION_THRESHOLD:
            return self.HIGH_CONSUMPTION_POWER_TARIFF
        return self.LOW_CONSUMPTION_POWER_TARIFF
    
    def calc_default_peak_power(self, consumption_kwh: float) -> float:
        """
        Calculate default sum of monthly peak power (Excel I38).
        
        Formula: consumption / (365 × 24) × 10 × 12
        
        Args:
            consumption_kwh: Annual consumption in kWh
            
        Returns:
            Sum of monthly peak power in kW
        """
        hours_per_year = 365 * 24
        average_power = consumption_kwh / hours_per_year
        peak_factor = 10.0
        return average_power * peak_factor * 12
    
    # -------------------------------------------------------------------------
    # Component Calculations
    # -------------------------------------------------------------------------
    
    def calc_self_consumption_kwh(
        self,
        production_kwh: float,
        self_consumption_percent: float
    ) -> float:
        """Calculate self-consumption in kWh (Row 46)."""
        return production_kwh * (self_consumption_percent / 100.0)
    
    def calc_zev_revenue(
        self,
        self_consumption_kwh: float,
        tariff_chf_kwh: float
    ) -> float:
        """Calculate ZEV revenue from self-consumption."""
        return self_consumption_kwh * tariff_chf_kwh
    
    def calc_power_savings(
        self,
        peak_power_kw: float,
        reduction_percent: float,
        power_tariff: float,
        degradation_factor: float = 1.0
    ) -> float:
        """
        Calculate annual power cost savings.
        
        Formula: peak × reduction% × degradation × tariff × 12 months
        """
        reduced_peak = peak_power_kw * (reduction_percent / 100.0)
        monthly_savings = reduced_peak * power_tariff * degradation_factor
        return monthly_savings * 12
    
    def calc_accounting_costs(
        self,
        self_consumption_kwh: float,
        cost_per_kwh: float,
        num_participants: int,
        base_cost_per_participant: float
    ) -> float:
        """
        Calculate total ZEV accounting costs.
        
        Formula: (energy × cost/kWh) + (base_cost × participants × 12)
        """
        energy_costs = self_consumption_kwh * cost_per_kwh
        base_costs = base_cost_per_participant * num_participants * 12
        return energy_costs + base_costs
    
    # -------------------------------------------------------------------------
    # Main Calculation
    # -------------------------------------------------------------------------
    
    def calculate(
        self,
        params: ZEVParameters,
        real_consumption_price_chf_kwh: Optional[float] = None
    ) -> ZEVResult:
        """
        Calculate ZEV data based on input parameters.
        
        Args:
            params: ZEVParameters with all input values
            real_consumption_price_chf_kwh: Optional real consumption price from tariff lookup
            
        Returns:
            ZEVResult with all calculated values
        """
        result = ZEVResult()
        result.zev_enabled = params.zev_enabled
        
        if not params.zev_enabled:
            # ZEV not active - return empty result
            result.tariff_source = "none"
            return result
        
        # Determine self-consumption percentage (Row 45)
        if params.self_consumption_percent is not None:
            result.self_consumption_percent = params.self_consumption_percent
        else:
            result.self_consumption_percent = self.calc_default_self_consumption(
                params.capacity_kwp,
                params.specific_yield_kwh_kwp,
                params.annual_consumption_kwh
            )
        
        # Calculate self-consumption in kWh (Row 46)
        result.self_consumption_kwh = self.calc_self_consumption_kwh(
            params.annual_production_kwh,
            result.self_consumption_percent
        )
        
        # Determine number of participants (Row 42)
        if params.num_participants is not None:
            result.num_participants = params.num_participants
        else:
            result.num_participants = self.calc_default_participants(
                params.annual_consumption_kwh
            )
        
        # Peak reduction (Row 44)
        result.peak_reduction_percent = params.peak_reduction_percent
        
        # Accounting costs (Row 50-51)
        result.accounting_cost_per_kwh = params.accounting_cost_per_kwh
        result.base_cost_per_participant_month = params.base_cost_per_participant_month
        
        # Determine electricity tariff (Row 47)
        if params.electricity_tariff_chf_kwh is not None:
            result.electricity_tariff_chf_kwh = params.electricity_tariff_chf_kwh
            result.tariff_source = "manual"
        elif real_consumption_price_chf_kwh is not None:
            # Use real market price with ZEV discount
            result.electricity_tariff_chf_kwh = (
                real_consumption_price_chf_kwh * self.ZEV_DISCOUNT_FACTOR 
                - params.accounting_cost_per_kwh
            )
            result.tariff_source = "address_lookup"
        else:
            result.electricity_tariff_chf_kwh = self.calc_default_electricity_tariff(
                True,
                self.DEFAULT_ELECTRICITY_PRICE,
                params.accounting_cost_per_kwh
            )
            result.tariff_source = "default"
        
        # Determine power tariff (Row 48)
        if params.power_tariff_chf_kw_month is not None:
            result.power_tariff_chf_kw_month = params.power_tariff_chf_kw_month
        else:
            result.power_tariff_chf_kw_month = self.calc_default_power_tariff(
                params.annual_consumption_kwh
            )
        
        # Operating costs (Row 53)
        result.operating_costs_chf_year = params.operating_costs_chf_year
        
        # Calculate ZEV revenue
        result.zev_revenue_chf = self.calc_zev_revenue(
            result.self_consumption_kwh,
            result.electricity_tariff_chf_kwh
        )
        
        # Calculate power savings
        peak_power = params.monthly_peak_power_kw or self.calc_default_peak_power(
            params.annual_consumption_kwh
        )
        result.power_savings_chf = self.calc_power_savings(
            peak_power,
            result.peak_reduction_percent,
            result.power_tariff_chf_kw_month,
            params.degradation_factor
        )
        
        # Calculate accounting costs
        result.accounting_costs_chf = self.calc_accounting_costs(
            result.self_consumption_kwh,
            result.accounting_cost_per_kwh,
            result.num_participants,
            result.base_cost_per_participant_month
        )
        
        # Total ZEV costs
        result.total_zev_costs_chf = (
            result.accounting_costs_chf + result.operating_costs_chf_year
        )
        
        # Net benefit
        result.net_benefit_chf = (
            result.zev_revenue_chf +
            result.power_savings_chf -
            result.total_zev_costs_chf
        )
        
        return result
    
    def calculate_with_address(
        self,
        params: ZEVParameters,
        address: str,
        year: str = "2024",
        profile: str = "H4"
    ) -> ZEVResult:
        """
        Calculate ZEV data using real tariffs from address lookup.
        
        If the tariff service is unavailable or fails, automatically falls back
        to default tariffs with a warning message.
        
        Args:
            params: ZEVParameters with input values
            address: Swiss address for tariff lookup
            year: Year for tariff data
            profile: Household profile (H1-H8)
            
        Returns:
            ZEVResult with real market tariffs (or defaults if service unavailable)
        """
        real_price = None
        
        try:
            if self.tariff_service:
                summary = self.tariff_service.get_tariffs_for_address(address, year, profile)
                if summary and summary.best_consumption_price:
                    # Use TOTAL price (what members would pay to utility without ZEV)
                    price = summary.best_consumption_price
                    real_price = price.total_chf_kwh  # Full electricity cost
                    print(f"✅ Using real tariff for {summary.municipality.name}: {real_price:.4f} CHF/kWh (total)")
                else:
                    print(f"⚠️  No tariff data found for '{address}'")
        except Exception as e:
            print(f"⚠️  Tariff service error: {e}")
        
        if real_price is None:
            print("ℹ️  Using default tariff (0.29 CHF/kWh) - tariff service unavailable or failed")
        
        return self.calculate(params, real_price)


# =============================================================================
# DEMO
# =============================================================================

if __name__ == "__main__":
    print("=" * 60)
    print("🏘️ ZEV CALCULATOR - DEMO")
    print("=" * 60)
    
    # Example: 90 kWp system with ZEV
    params = ZEVParameters(
        zev_enabled=True,
        annual_production_kwh=90000,  # 90 kWp × 1000 kWh/kWp
        capacity_kwp=90.0,
        specific_yield_kwh_kwp=1000.0,
        annual_consumption_kwh=80000,  # Total building consumption
        peak_reduction_percent=10.0,  # 10% peak shaving
        accounting_cost_per_kwh=0.01,  # 1 Rp/kWh
        base_cost_per_participant_month=8.0,  # 8 CHF/month/participant
    )
    
    calculator = ZEVCalculator()
    
    # Calculate with defaults
    print("\n--- With Default Tariffs ---")
    result = calculator.calculate(params)
    result.print_summary()
    
    # Try with address lookup (if tariff service available)
    print("\n--- With Address Lookup ---")
    try:
        result_with_address = calculator.calculate_with_address(
            params,
            "Bahnhofstrasse 10, Zürich"
        )
        result_with_address.print_summary()
    except Exception as e:
        print(f"Address lookup failed: {e}")
    
    # Export to dict
    print("\n--- Export to Dict ---")
    export = result.to_dict()
    for key, value in export.items():
        print(f"  {key}: {value}")
