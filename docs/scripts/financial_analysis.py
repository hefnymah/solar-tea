"""
Financial Analysis Module for Solar PV Techno-Economic Assessment.

This module provides a Reaktoro-inspired OOP architecture for financial analysis
of solar PV systems with optional battery storage.

Architecture:
- PVSystem: Technical PV system configuration
- BatterySystem: Battery storage configuration
- InvestmentModel: Investment and financing structure
- TariffModel: Electricity tariffs with inflation
- MaintenanceSchedule: Periodic maintenance costs
- YearlyState: Annual calculation state
- CashFlowAnalyzer: Core analysis engine
- FinancialAnalysis: Main orchestrator class
"""

from __future__ import annotations
import math
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Dict, Optional, List, Any
import pandas as pd
import numpy as np
import numpy_financial as nf


# =============================================================================
# Base Classes and Interfaces
# =============================================================================

class SystemComponent(ABC):
    """Base class for all system components."""
    
    @abstractmethod
    def validate(self) -> bool:
        """Validate component configuration."""
        pass


@dataclass
class YearlyState:
    """
    Immutable state container for a single year's calculations.
    
    This class encapsulates all calculated values for one year,
    enabling clean data flow between calculation stages.
    """
    year: int
    
    # Flags
    is_within_lifetime: bool = True
    is_within_battery_life: bool = False
    is_battery_renewal_year: bool = False
    is_remuneration_payout_year: bool = False
    is_debt_1_active: bool = False
    is_debt_2_active: bool = False
    is_battery_debt_active: bool = False
    
    # Performance
    pv_degradation: float = 1.0
    energy_yield_kwh: float = 0.0
    battery_degradation: float = 1.0
    battery_capacity_kwh: float = 0.0
    energy_from_storage_kwh: float = 0.0
    storage_losses_kwh: float = 0.0
    
    # Tariffs (inflated)
    feed_in_tariff: float = 0.0
    leg_tariff: float = 0.0
    self_consumption_tariff: float = 0.0
    performance_tariff: float = 0.0
    
    # Revenues
    feed_in_revenue: float = 0.0
    leg_revenue: float = 0.0
    self_consumption_revenue: float = 0.0
    performance_revenue: float = 0.0
    zev_billing_revenue: float = 0.0
    battery_self_consumption_revenue: float = 0.0
    battery_performance_revenue: float = 0.0
    battery_charging_cost: float = 0.0
    
    # Costs
    maintenance_cost: float = 0.0
    battery_maintenance_cost: float = 0.0
    vat_cost: float = 0.0
    vat_input_credit: float = 0.0
    vat_battery_credit: float = 0.0
    
    # Financing
    remuneration_payout: float = 0.0
    equity_annuity: float = 0.0
    debt_1_annuity: float = 0.0
    debt_2_annuity: float = 0.0
    battery_equity_annuity: float = 0.0
    battery_debt_annuity: float = 0.0
    
    # Cash flows
    cash_flow_pv: float = 0.0
    cash_flow_with_battery: float = 0.0
    cash_flow_battery_only: float = 0.0
    
    # NPV
    npv_pv: float = 0.0
    npv_with_battery: float = 0.0
    npv_battery_only: float = 0.0
    cumulative_npv_pv: float = 0.0
    cumulative_npv_with_battery: float = 0.0
    cumulative_npv_battery_only: float = 0.0
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert state to dictionary for DataFrame."""
        return {
            'year': self.year,
            'energy_yield_kwh': self.energy_yield_kwh,
            'pv_degradation_factor': self.pv_degradation,
            'battery_capacity_kwh': self.battery_capacity_kwh,
            'cash_flow_net_chf': self.cash_flow_pv,
            'cash_flow_net_with_battery_chf': self.cash_flow_with_battery,
            'cash_flow_battery_only_chf': self.cash_flow_battery_only,
            'cumulative_npv_chf': self.cumulative_npv_pv,
            'cumulative_npv_with_battery_chf': self.cumulative_npv_with_battery,
            'cumulative_npv_battery_only_chf': self.cumulative_npv_battery_only,
            'npv_cash_flow_net_chf': self.npv_pv,
            'npv_cash_flow_net_with_battery_chf': self.npv_with_battery,
            'npv_cash_flow_battery_only_chf': self.npv_battery_only,
        }


# =============================================================================
# Domain Models
# =============================================================================

@dataclass
class PVSystem(SystemComponent):
    """
    PV system technical specification.
    
    Example:
        pv = PVSystem(capacity_kwp=40, yield_kwh_kwp=1000)
        print(pv.annual_yield())  # 40000
    """
    capacity_kwp: float = 0.0
    yield_kwh_kwp: float = 1000.0
    lifetime_years: int = 30
    degradation_rate: float = 0.004
    
    def validate(self) -> bool:
        return self.capacity_kwp >= 0 and self.lifetime_years > 0
    
    def annual_yield(self) -> float:
        """Initial annual energy yield in kWh."""
        return self.capacity_kwp * self.yield_kwh_kwp
    
    def degradation_factor(self, year: int) -> float:
        """Degradation factor for given year (1-indexed)."""
        if year <= 0:
            return 1.0
        return max(0.0, 1.0 - self.degradation_rate * (year - 1))
    
    def energy_yield(self, year: int) -> float:
        """Energy yield in kWh for given year."""
        return self.annual_yield() * self.degradation_factor(year)


@dataclass
class BatterySystem(SystemComponent):
    """
    Battery storage system specification.
    
    Example:
        battery = BatterySystem(capacity_kwh=40, lifetime_years=16)
        print(battery.is_enabled())  # True
    """
    capacity_kwh: float = 0.0
    lifetime_years: int = 15
    degradation_rate: float = 0.01333
    efficiency: float = 0.85
    self_consumption_boost_pct: float = 20.0
    replacement_cost: float = 0.0
    
    def validate(self) -> bool:
        return self.capacity_kwh >= 0 and self.lifetime_years > 0
    
    def is_enabled(self) -> bool:
        """Check if battery is configured."""
        return self.capacity_kwh > 0
    
    def degradation_factor(self, year: int) -> float:
        """Degradation factor within current lifecycle."""
        if year <= 0 or not self.is_enabled():
            return 1.0
        years_in_period = ((year - 1) % self.lifetime_years) + 1
        return max(0.0, 1.0 - self.degradation_rate * (years_in_period - 1))
    
    def effective_capacity(self, year: int) -> float:
        """Effective capacity considering degradation."""
        return self.capacity_kwh * self.degradation_factor(year)
    
    def storage_loss_rate(self) -> float:
        """Energy lost during storage cycle."""
        return 1.0 - self.efficiency


@dataclass  
class InvestmentModel(SystemComponent):
    """
    Investment and financing structure.
    
    Supports equity capital and up to two debt instruments for PV,
    plus separate financing for battery.
    """
    # PV Investment
    pv_cost: float = 0.0
    pv_equity: float = 0.0
    pv_equity_rate: float = 0.0
    pv_debt_1: float = 0.0
    pv_debt_1_rate: float = 0.0
    pv_debt_1_term: int = 15
    pv_debt_2: float = 0.0
    pv_debt_2_rate: float = 0.0
    pv_debt_2_term: int = 15
    
    # Battery Investment
    battery_cost: float = 0.0
    battery_equity: float = 0.0
    battery_equity_rate: float = 0.0
    battery_debt: float = 0.0
    battery_debt_rate: float = 0.0
    battery_debt_term: int = 15
    
    # Subsidies
    direct_subsidy: float = 0.0
    tax_savings: float = 0.0
    battery_subsidy: float = 0.0
    one_time_remuneration: float = 0.0
    facade_bonus: float = 0.0
    altitude_bonus: float = 0.0
    remuneration_delay_years: int = 1
    
    def validate(self) -> bool:
        return self.pv_cost >= 0
    
    def total_investment(self) -> float:
        """Total investment cost."""
        return self.pv_cost + self.battery_cost
    
    def total_subsidies(self) -> float:
        """Total subsidies received."""
        return self.direct_subsidy + self.tax_savings + self.battery_subsidy
    
    def net_investment(self) -> float:
        """Net investment after subsidies."""
        return self.total_investment() - self.total_subsidies()
    
    def initial_pv_outflow(self) -> float:
        """Year 0 PV cash outflow (equity portion)."""
        return self.pv_cost - self.direct_subsidy - self.tax_savings - self.pv_debt_1 - self.pv_debt_2
    
    def initial_battery_outflow(self) -> float:
        """Year 0 battery cash outflow."""
        return self.battery_cost - self.battery_subsidy - self.battery_debt
    
    def remuneration_total(self) -> float:
        """Total one-time remuneration."""
        return self.one_time_remuneration + self.facade_bonus + self.altitude_bonus


@dataclass
class TariffModel(SystemComponent):
    """
    Electricity tariffs with inflation tracking.
    
    Handles feed-in tariffs, self-consumption savings,
    and ZEV community billing.
    """
    feed_in_energy: float = 0.05
    feed_in_hkn: float = 0.03
    leg_tariff: float = 0.0967
    self_consumption: float = 0.232
    performance_zev: float = 1.5
    admin_fee_zev: float = 0.02
    basic_cost_zev_month: float = 20.0
    inflation_rate: float = 0.005
    
    # Distribution percentages
    self_consumption_pct: float = 35.0
    leg_share_pct: float = 20.0
    peak_reduction_pv_pct: float = 60.0
    peak_reduction_battery_pct: float = 30.0
    num_consumers: int = 12
    
    # VAT
    vat_rate: float = 0.081
    vat_liable: bool = True
    
    def validate(self) -> bool:
        return (self.self_consumption_pct + self.leg_share_pct) <= 100
    
    def feed_in_total(self) -> float:
        """Total feed-in tariff (energy + HKN)."""
        return self.feed_in_energy + self.feed_in_hkn
    
    def feed_in_share_pct(self) -> float:
        """Percentage of energy fed into grid."""
        return 100.0 - self.self_consumption_pct - self.leg_share_pct
    
    def with_inflation(self, years: int) -> TariffModel:
        """Return tariffs inflated by given years."""
        factor = (1 + self.inflation_rate) ** years
        return TariffModel(
            feed_in_energy=self.feed_in_energy * factor,
            feed_in_hkn=self.feed_in_hkn * factor,
            leg_tariff=self.leg_tariff * factor,
            self_consumption=self.self_consumption * factor,
            performance_zev=self.performance_zev * factor,
            admin_fee_zev=self.admin_fee_zev * factor,
            basic_cost_zev_month=self.basic_cost_zev_month * factor,
            inflation_rate=self.inflation_rate,
            self_consumption_pct=self.self_consumption_pct,
            leg_share_pct=self.leg_share_pct,
            peak_reduction_pv_pct=self.peak_reduction_pv_pct,
            peak_reduction_battery_pct=self.peak_reduction_battery_pct,
            num_consumers=self.num_consumers,
            vat_rate=self.vat_rate,
            vat_liable=self.vat_liable,
        )


@dataclass
class MaintenanceSchedule(SystemComponent):
    """
    Maintenance cost schedule with periodic costs.
    
    Each cost item has a value and frequency.
    """
    base_cost: float = 929.0  # 800 + 0.002 * investment
    base_frequency: int = 5
    component_cost: float = 329.0
    component_frequency: int = 3
    monitoring_cost: float = 140.0
    administration_cost: float = 170.0
    data_connection_cost: float = 120.0
    insurance_cost: float = 207.0
    repairs_cost: float = 1265.0
    repairs_frequency: int = 8
    cleaning_cost: float = 1500.0
    cleaning_frequency: int = 8
    inverter_cost: float = 6500.0
    inverter_frequency: int = 16
    battery_replacement_cost: float = 0.0
    battery_replacement_frequency: int = 16
    
    # Calculation method
    use_kwh_price: bool = False
    kwh_price: float = 0.035
    
    def validate(self) -> bool:
        return self.base_frequency > 0
    
    @classmethod
    def from_investment(cls, investment: float) -> MaintenanceSchedule:
        """Create schedule based on investment amount."""
        return cls(base_cost=800 + 0.002 * investment)
    
    def annual_cost(self, year: int, energy_kwh: float = 0.0) -> float:
        """Calculate maintenance cost for given year."""
        if year <= 0:
            return 0.0
        
        if self.use_kwh_price:
            return energy_kwh * self.kwh_price
        
        total = 0.0
        
        # Periodic costs
        if year % self.base_frequency == 0:
            total += self.base_cost
        if year % self.component_frequency == 0:
            total += self.component_cost
        if year % self.repairs_frequency == 0:
            total += self.repairs_cost
        if year % self.cleaning_frequency == 0:
            total += self.cleaning_cost
        if year % self.inverter_frequency == 0:
            total += self.inverter_cost
        
        # Annual costs
        total += self.monitoring_cost
        total += self.administration_cost
        total += self.data_connection_cost
        total += self.insurance_cost
        
        return total
    
    def battery_cost(self, year: int) -> float:
        """Battery maintenance/replacement cost for given year."""
        if year <= 0 or self.battery_replacement_cost == 0:
            return 0.0
        if year % self.battery_replacement_frequency == 0:
            return self.battery_replacement_cost
        return 0.0


# =============================================================================
# Calculation Engines
# =============================================================================

class AnnuityCalculator:
    """Static methods for annuity calculations."""
    
    @staticmethod
    def payment(rate: float, periods: int, principal: float) -> float:
        """Calculate annuity payment (PMT function)."""
        if periods <= 0 or principal == 0:
            return 0.0
        if rate == 0:
            return -principal / periods
        return nf.pmt(rate, periods, principal)
    
    @staticmethod
    def equity_annuity(rate: float, lifetime: int, equity: float,
                       eiv_capital: float = 0.0, eiv_period: int = 1) -> float:
        """Calculate equity cost including EIV interest."""
        base_annuity = AnnuityCalculator.payment(rate, lifetime, equity)
        
        if eiv_capital > 0 and eiv_period > 0:
            eiv_pmt = AnnuityCalculator.payment(rate, eiv_period, eiv_capital)
            eiv_linear = eiv_capital / eiv_period
            return base_annuity + eiv_pmt + eiv_linear
        
        return base_annuity


class RevenueCalculator:
    """Calculate revenues from energy sales and savings."""
    
    def __init__(self, pv: PVSystem, tariffs: TariffModel):
        self.pv = pv
        self.tariffs = tariffs
    
    def sum_performance_peaks(self) -> float:
        """Calculate sum of monthly performance peaks."""
        annual_yield = self.pv.annual_yield()
        return (annual_yield / (365 * 24)) * 10 * 12
    
    def calculate(self, state: YearlyState, tariffs: TariffModel) -> Dict[str, float]:
        """Calculate all revenues for a year."""
        energy = state.energy_yield_kwh
        peaks = self.sum_performance_peaks()
        
        # Feed-in revenue
        feed_in_pct = tariffs.feed_in_share_pct() / 100
        feed_in_revenue = energy * feed_in_pct * tariffs.feed_in_total()
        
        # LEG revenue
        leg_revenue = energy * (tariffs.leg_share_pct / 100) * tariffs.leg_tariff
        
        # Self-consumption savings
        sc_revenue = energy * (tariffs.self_consumption_pct / 100) * tariffs.self_consumption
        
        # Performance savings
        perf_revenue = peaks * (tariffs.peak_reduction_pv_pct / 100) * state.pv_degradation * tariffs.performance_zev
        
        # ZEV billing
        variable_fee = energy * (tariffs.self_consumption_pct / 100) * tariffs.admin_fee_zev
        fixed_fee = tariffs.basic_cost_zev_month * tariffs.num_consumers * 12
        zev_revenue = variable_fee + fixed_fee
        
        return {
            'feed_in': feed_in_revenue,
            'leg': leg_revenue,
            'self_consumption': sc_revenue,
            'performance': perf_revenue,
            'zev_billing': zev_revenue,
        }


class CashFlowCalculator:
    """Calculate cash flows for different scenarios."""
    
    def __init__(self, investment: InvestmentModel, tariffs: TariffModel):
        self.investment = investment
        self.tariffs = tariffs
    
    def year_zero_pv(self) -> float:
        """Year 0 cash flow for PV only."""
        return -self.investment.initial_pv_outflow()
    
    def year_zero_total(self) -> float:
        """Year 0 cash flow including battery."""
        return -(self.investment.initial_pv_outflow() + self.investment.initial_battery_outflow())
    
    def year_zero_battery(self) -> float:
        """Year 0 cash flow for battery only."""
        return -self.investment.initial_battery_outflow()
    
    def pv_cash_flow(self, state: YearlyState) -> float:
        """Annual PV cash flow."""
        return (state.feed_in_revenue +
                state.leg_revenue +
                state.self_consumption_revenue +
                state.performance_revenue +
                state.zev_billing_revenue -
                state.maintenance_cost +
                state.vat_cost +
                state.vat_input_credit +
                state.remuneration_payout +
                state.debt_1_annuity +
                state.debt_2_annuity)
    
    def battery_incremental_cash_flow(self, state: YearlyState) -> float:
        """Additional cash flow from battery."""
        return (state.battery_self_consumption_revenue +
                state.battery_performance_revenue +
                state.battery_charging_cost -
                state.battery_maintenance_cost +
                state.vat_battery_credit +
                state.battery_debt_annuity)
    
    def discount_factor(self, year: int) -> float:
        """NPV discount factor."""
        rate = self.investment.pv_equity_rate
        return (1 + rate) ** (-year)


# =============================================================================
# Main Orchestrator
# =============================================================================

@dataclass
class FinancialAnalysisResult:
    """
    Results from financial analysis.
    
    Provides access to summary metrics and detailed yearly data.
    """
    total_investment: float
    total_subsidies: float
    net_investment: float
    payback_pv: Optional[int]
    payback_with_battery: Optional[int]
    payback_battery_only: Optional[int]
    npv_pv: float
    npv_with_battery: float
    npv_battery_only: float
    yearly_data: pd.DataFrame
    
    # Aliases for backward compatibility
    @property
    def total_investment_chf(self) -> float:
        return self.total_investment
    
    @property
    def net_investment_chf(self) -> float:
        return self.net_investment
    
    @property
    def payback_year_pv_only(self) -> Optional[int]:
        return self.payback_pv
    
    @property
    def payback_year_with_battery(self) -> Optional[int]:
        return self.payback_with_battery
    
    @property
    def npv_30_year_pv_only_chf(self) -> float:
        return self.npv_pv
    
    @property
    def npv_30_year_with_battery_chf(self) -> float:
        return self.npv_with_battery


class FinancialAnalysis:
    """
    Main financial analysis orchestrator.
    
    Coordinates all calculation components to produce comprehensive
    techno-economic analysis results.
    
    Example:
        pv = PVSystem(capacity_kwp=40, yield_kwh_kwp=1000)
        investment = InvestmentModel(pv_cost=64708, pv_equity=64708)
        
        analysis = FinancialAnalysis(pv, investment)
        result = analysis.calculate()
        
        print(f"Payback: {result.payback_pv} years")
        print(f"NPV: {result.npv_pv:,.0f} CHF")
    """
    
    def __init__(self,
                 pv: PVSystem,
                 investment: InvestmentModel,
                 battery: Optional[BatterySystem] = None,
                 tariffs: Optional[TariffModel] = None,
                 maintenance: Optional[MaintenanceSchedule] = None):
        """
        Initialize financial analysis.
        
        Args:
            pv: PV system specification
            investment: Investment and financing structure
            battery: Optional battery storage
            tariffs: Electricity tariffs (defaults provided)
            maintenance: Maintenance schedule (defaults provided)
        """
        self.pv = pv
        self.investment = investment
        self.battery = battery or BatterySystem()
        self.tariffs = tariffs or TariffModel()
        self.maintenance = maintenance or MaintenanceSchedule.from_investment(investment.pv_cost)
        
        # Initialize calculators
        self._revenue_calc = RevenueCalculator(pv, self.tariffs)
        self._cf_calc = CashFlowCalculator(investment, self.tariffs)
    
    def calculate(self) -> FinancialAnalysisResult:
        """
        Execute complete financial analysis.
        
        Returns:
            FinancialAnalysisResult with metrics and yearly data
        """
        states = self._calculate_all_years()
        df = pd.DataFrame([s.to_dict() for s in states])
        
        # Find payback years
        payback_pv = self._find_payback(states, 'cumulative_npv_pv')
        payback_bat = self._find_payback(states, 'cumulative_npv_with_battery')
        payback_bat_only = self._find_payback(states, 'cumulative_npv_battery_only')
        
        final = states[-1]
        
        return FinancialAnalysisResult(
            total_investment=self.investment.total_investment(),
            total_subsidies=self.investment.total_subsidies(),
            net_investment=self.investment.net_investment(),
            payback_pv=payback_pv,
            payback_with_battery=payback_bat,
            payback_battery_only=payback_bat_only,
            npv_pv=final.cumulative_npv_pv,
            npv_with_battery=final.cumulative_npv_with_battery,
            npv_battery_only=final.cumulative_npv_battery_only,
            yearly_data=df
        )
    
    def _calculate_all_years(self) -> List[YearlyState]:
        """Calculate states for all years."""
        states = []
        
        for year in range(self.pv.lifetime_years + 1):
            state = self._calculate_year(year, states)
            states.append(state)
        
        return states
    
    def _calculate_year(self, year: int, prev_states: List[YearlyState]) -> YearlyState:
        """Calculate state for single year."""
        inv = self.investment
        bat = self.battery
        
        # Get inflated tariffs
        tariffs = self.tariffs.with_inflation(max(0, year - 1))
        
        # Initialize state
        state = YearlyState(year=year)
        
        if year == 0:
            # Year 0: Initial investment
            state.cash_flow_pv = self._cf_calc.year_zero_pv()
            state.cash_flow_with_battery = self._cf_calc.year_zero_total()
            state.cash_flow_battery_only = self._cf_calc.year_zero_battery()
            state.npv_pv = state.cash_flow_pv
            state.npv_with_battery = state.cash_flow_with_battery
            state.npv_battery_only = state.cash_flow_battery_only
            # Cumulative NPV at year 0 equals the year 0 NPV
            state.cumulative_npv_pv = state.npv_pv
            state.cumulative_npv_with_battery = state.npv_with_battery
            state.cumulative_npv_battery_only = state.npv_battery_only
            return state
        
        prev = prev_states[-1]
        
        # Flags
        state.is_within_lifetime = year <= self.pv.lifetime_years
        state.is_within_battery_life = year <= bat.lifetime_years
        state.is_battery_renewal_year = bat.is_enabled() and year <= self.pv.lifetime_years
        state.is_remuneration_payout_year = year == inv.remuneration_delay_years
        state.is_debt_1_active = year <= inv.pv_debt_1_term
        state.is_debt_2_active = year <= inv.pv_debt_2_term
        state.is_battery_debt_active = year <= inv.battery_debt_term
        
        # Performance
        state.pv_degradation = self.pv.degradation_factor(year)
        state.energy_yield_kwh = self.pv.energy_yield(year)
        state.battery_degradation = bat.degradation_factor(year)
        state.battery_capacity_kwh = bat.effective_capacity(year)
        
        # Storage calculations
        if bat.is_enabled():
            ev_boost = bat.self_consumption_boost_pct * state.battery_degradation / 100
            stored = ev_boost * state.energy_yield_kwh
            state.storage_losses_kwh = stored * bat.storage_loss_rate()
            state.energy_from_storage_kwh = stored - state.storage_losses_kwh
        
        # Tariffs
        state.feed_in_tariff = tariffs.feed_in_total()
        state.leg_tariff = tariffs.leg_tariff
        state.self_consumption_tariff = tariffs.self_consumption
        state.performance_tariff = tariffs.performance_zev
        
        # Revenues
        revenues = self._revenue_calc.calculate(state, tariffs)
        state.feed_in_revenue = revenues['feed_in']
        state.leg_revenue = revenues['leg']
        state.self_consumption_revenue = revenues['self_consumption']
        state.performance_revenue = revenues['performance']
        state.zev_billing_revenue = revenues['zev_billing']
        
        # Battery revenues
        if state.is_battery_renewal_year:
            state.battery_self_consumption_revenue = state.energy_from_storage_kwh * tariffs.self_consumption
            peaks = self._revenue_calc.sum_performance_peaks()
            state.battery_performance_revenue = peaks * (tariffs.peak_reduction_battery_pct / 100) * state.battery_degradation * tariffs.performance_zev
            state.battery_charging_cost = -state.storage_losses_kwh / (1 - bat.storage_loss_rate()) * tariffs.feed_in_total()
        
        # Maintenance
        inflation_factor = (1 + self.tariffs.inflation_rate) ** (year - 1)
        state.maintenance_cost = self.maintenance.annual_cost(year, state.energy_yield_kwh) * inflation_factor
        state.battery_maintenance_cost = self.maintenance.battery_cost(year) * inflation_factor
        
        # VAT
        if tariffs.vat_liable:
            state.vat_cost = -state.feed_in_revenue * tariffs.vat_rate
            state.vat_input_credit = state.maintenance_cost * tariffs.vat_rate
            state.vat_battery_credit = state.battery_maintenance_cost * tariffs.vat_rate
        
        # Financing
        if state.is_remuneration_payout_year:
            state.remuneration_payout = inv.remuneration_total()
        
        state.equity_annuity = AnnuityCalculator.payment(inv.pv_equity_rate, self.pv.lifetime_years, inv.pv_equity)
        
        if state.is_debt_1_active:
            state.debt_1_annuity = AnnuityCalculator.payment(inv.pv_debt_1_rate, inv.pv_debt_1_term, inv.pv_debt_1)
        if state.is_debt_2_active:
            state.debt_2_annuity = AnnuityCalculator.payment(inv.pv_debt_2_rate, inv.pv_debt_2_term, inv.pv_debt_2)
        if state.is_within_battery_life:
            state.battery_equity_annuity = AnnuityCalculator.payment(inv.battery_equity_rate, bat.lifetime_years, inv.battery_equity)
        if state.is_battery_debt_active and state.is_within_battery_life:
            state.battery_debt_annuity = AnnuityCalculator.payment(inv.battery_debt_rate, inv.battery_debt_term, inv.battery_debt)
        
        # Cash flows
        state.cash_flow_pv = self._cf_calc.pv_cash_flow(state)
        state.cash_flow_with_battery = state.cash_flow_pv + self._cf_calc.battery_incremental_cash_flow(state)
        if state.is_battery_renewal_year:
            state.cash_flow_battery_only = self._cf_calc.battery_incremental_cash_flow(state)
        
        # NPV
        df = self._cf_calc.discount_factor(year)
        state.npv_pv = state.cash_flow_pv * df
        state.npv_with_battery = state.cash_flow_with_battery * df
        state.npv_battery_only = state.cash_flow_battery_only * df if state.is_battery_renewal_year else 0
        
        # Cumulative NPV
        state.cumulative_npv_pv = prev.cumulative_npv_pv + state.npv_pv if year > 0 else state.npv_pv
        state.cumulative_npv_with_battery = prev.cumulative_npv_with_battery + state.npv_with_battery if year > 0 else state.npv_with_battery
        
        prev_bat_npv = prev.cumulative_npv_battery_only if prev.cumulative_npv_battery_only else prev.npv_battery_only
        state.cumulative_npv_battery_only = prev_bat_npv + state.npv_battery_only
        
        return state
    
    def _find_payback(self, states: List[YearlyState], attr: str) -> Optional[int]:
        """Find first year where cumulative NPV becomes non-negative."""
        for i, state in enumerate(states):
            if i == 0:
                continue
            current = getattr(state, attr, 0)
            prev = getattr(states[i-1], attr, 0)
            if prev < 0 and current >= 0:
                return state.year
        return None


# =============================================================================
# Backward Compatibility Layer
# =============================================================================

# Import Pydantic for backward compatibility with old API
from pydantic import BaseModel, Field

class FinancialAnalysisConfig(BaseModel):
    """
    Configuration for financial analysis - backward compatible interface.
    
    This class maintains the original flat configuration interface
    for backward compatibility while internally using the new OOP structure.
    """
    
    # System parameters
    lifetime_years: int = Field(default=30, ge=1, le=50)
    battery_lifetime_years: int = Field(default=15, ge=1, le=30)
    initial_battery_capacity_kwh: float = Field(default=0.0, ge=0)
    initial_energy_yield_kwh: float = Field(default=0.0, ge=0)
    pv_degradation_rate: float = Field(default=0.004, ge=0, le=0.05)
    battery_degradation_rate: float = Field(default=0.01333, ge=0, le=0.1)
    storage_loss_rate: float = Field(default=0.15, ge=0, le=0.5)
    self_consumption_increase_with_battery_pct: float = Field(default=20.0, ge=0, le=100)
    
    # Investment
    relevant_investment_costs_pv_chf: float = Field(default=0.0, ge=0)
    relevant_investment_costs_battery_chf: float = Field(default=0.0, ge=0)
    direct_subsidy_chf: float = Field(default=0.0, ge=0)
    tax_savings_chf: float = Field(default=0.0, ge=0)
    battery_subsidy_chf: float = Field(default=0.0, ge=0)
    one_time_remuneration_chf: float = Field(default=0.0, ge=0)
    facade_bonus_chf: float = Field(default=0.0, ge=0)
    altitude_bonus_chf: float = Field(default=0.0, ge=0)
    payment_delay_years: int = Field(default=1, ge=0, le=10)
    
    # Financing
    equity_interest_rate_pct: float = Field(default=0.0, ge=0, le=20)
    equity_capital_pv_chf: float = Field(default=0.0, ge=0)
    equity_interest_rate_battery_pct: float = Field(default=0.0, ge=0, le=20)
    equity_capital_battery_chf: float = Field(default=0.0, ge=0)
    eiv_payment_period_years: int = Field(default=1, ge=1, le=30)
    debt_1_interest_rate_pct: float = Field(default=0.0, ge=0, le=20)
    debt_1_term_years: int = Field(default=15, ge=1, le=30)
    debt_1_amount_chf: float = Field(default=0.0, ge=0)
    debt_2_interest_rate_pct: float = Field(default=0.0, ge=0, le=20)
    debt_2_term_years: int = Field(default=15, ge=1, le=30)
    debt_2_amount_chf: float = Field(default=0.0, ge=0)
    battery_debt_interest_rate_pct: float = Field(default=0.0, ge=0, le=20)
    battery_debt_term_years: int = Field(default=15, ge=1, le=30)
    battery_debt_amount_chf: float = Field(default=0.0, ge=0)
    
    # Tariffs
    acceptance_energy_tariff_chf_kwh: float = Field(default=0.05, ge=0)
    hkn_tariff_chf_kwh: float = Field(default=0.03, ge=0)
    leg_tariff_chf_kwh: float = Field(default=0.0967, ge=0)
    saved_withdrawal_tariff_chf_kwh: float = Field(default=0.232, ge=0)
    performance_tariff_zev_chf_kw_month: float = Field(default=1.5, ge=0)
    inflation_rate_pct: float = Field(default=0.5, ge=0, le=20)
    self_consumption_rate_pct: float = Field(default=35.0, ge=0, le=100)
    leg_share_pct: float = Field(default=20.0, ge=0, le=100)
    reduction_performance_peaks_pct: float = Field(default=60.0, ge=0, le=100)
    reduction_performance_peaks_battery_pct: float = Field(default=30.0, ge=0, le=100)
    admin_fee_zev_chf_kwh: float = Field(default=0.02, ge=0)
    basic_cost_zev_chf_month: float = Field(default=20.0, ge=0)
    number_of_consumers: int = Field(default=12, ge=0)
    
    # Maintenance
    system_power_kwp: float = Field(default=20.0, ge=0)
    investment_sum_chf: float = Field(default=64708.0, ge=0)
    maintenance_calculation_method: str = Field(default="table")
    specific_maintenance_cost_chf_kwh: float = Field(default=0.035, ge=0)
    maintenance_frequency_years: int = Field(default=5, ge=1)
    component_maintenance_cost_chf: float = Field(default=329.0, ge=0)
    component_maintenance_frequency_years: int = Field(default=3, ge=1)
    monitoring_cost_chf: float = Field(default=140.0, ge=0)
    monitoring_frequency_years: int = Field(default=1, ge=1)
    administration_cost_chf: float = Field(default=170.0, ge=0)
    administration_frequency_years: int = Field(default=1, ge=1)
    data_connection_cost_chf: float = Field(default=120.0, ge=0)
    data_connection_frequency_years: int = Field(default=1, ge=1)
    insurance_cost_chf: float = Field(default=207.0, ge=0)
    insurance_frequency_years: int = Field(default=1, ge=1)
    repairs_cost_chf: float = Field(default=1265.0, ge=0)
    repairs_frequency_years: int = Field(default=8, ge=1)
    cleaning_cost_chf: float = Field(default=1500.0, ge=0)
    cleaning_frequency_years: int = Field(default=8, ge=1)
    inverter_replacement_cost_chf: float = Field(default=6500.0, ge=0)
    inverter_replacement_frequency_years: int = Field(default=16, ge=1)
    battery_replacement_cost_chf: float = Field(default=0.0, ge=0)
    battery_replacement_frequency_years: int = Field(default=16, ge=1)
    
    # VAT
    vat_obligation: str = Field(default="liable")
    vat_rate_pct: float = Field(default=8.1, ge=0, le=30)
    
    @property
    def has_battery(self) -> bool:
        return self.initial_battery_capacity_kwh > 0


class FinancialAnalysisResults(BaseModel):
    """Backward compatible results container."""
    total_investment_chf: float
    total_subsidies_chf: float
    net_investment_chf: float
    payback_year_pv_only: Optional[int] = None
    payback_year_with_battery: Optional[int] = None
    payback_year_battery_only: Optional[int] = None
    npv_30_year_pv_only_chf: float
    npv_30_year_with_battery_chf: float
    npv_30_year_battery_only_chf: float
    irr_pv_only_pct: Optional[float] = None
    irr_with_battery_pct: Optional[float] = None
    yearly_data: pd.DataFrame
    
    class Config:
        arbitrary_types_allowed = True


class FinancialAnalyzer:
    """
    Backward compatible analyzer interface.
    
    Wraps the new OOP classes for compatibility with existing code.
    """
    
    def __init__(self, config: FinancialAnalysisConfig):
        self.config = config
        self._analysis = self._build_analysis()
    
    def _build_analysis(self) -> FinancialAnalysis:
        """Convert config to OOP structure."""
        cfg = self.config
        
        # Calculate capacity from yield
        capacity = cfg.system_power_kwp
        if capacity == 0 and cfg.initial_energy_yield_kwh > 0:
            capacity = cfg.initial_energy_yield_kwh / 1000  # Assume 1000 kWh/kWp
        
        pv = PVSystem(
            capacity_kwp=capacity,
            yield_kwh_kwp=cfg.initial_energy_yield_kwh / capacity if capacity > 0 else 1000,
            lifetime_years=cfg.lifetime_years,
            degradation_rate=cfg.pv_degradation_rate
        )
        
        battery = BatterySystem(
            capacity_kwh=cfg.initial_battery_capacity_kwh,
            lifetime_years=cfg.battery_lifetime_years,
            degradation_rate=cfg.battery_degradation_rate,
            efficiency=1.0 - cfg.storage_loss_rate,
            self_consumption_boost_pct=cfg.self_consumption_increase_with_battery_pct,
            replacement_cost=cfg.battery_replacement_cost_chf
        )
        
        investment = InvestmentModel(
            pv_cost=cfg.relevant_investment_costs_pv_chf,
            pv_equity=cfg.equity_capital_pv_chf,
            pv_equity_rate=cfg.equity_interest_rate_pct / 100,
            pv_debt_1=cfg.debt_1_amount_chf,
            pv_debt_1_rate=cfg.debt_1_interest_rate_pct / 100,
            pv_debt_1_term=cfg.debt_1_term_years,
            pv_debt_2=cfg.debt_2_amount_chf,
            pv_debt_2_rate=cfg.debt_2_interest_rate_pct / 100,
            pv_debt_2_term=cfg.debt_2_term_years,
            battery_cost=cfg.relevant_investment_costs_battery_chf,
            battery_equity=cfg.equity_capital_battery_chf,
            battery_equity_rate=cfg.equity_interest_rate_battery_pct / 100,
            battery_debt=cfg.battery_debt_amount_chf,
            battery_debt_rate=cfg.battery_debt_interest_rate_pct / 100,
            battery_debt_term=cfg.battery_debt_term_years,
            direct_subsidy=cfg.direct_subsidy_chf,
            tax_savings=cfg.tax_savings_chf,
            battery_subsidy=cfg.battery_subsidy_chf,
            one_time_remuneration=cfg.one_time_remuneration_chf,
            facade_bonus=cfg.facade_bonus_chf,
            altitude_bonus=cfg.altitude_bonus_chf,
            remuneration_delay_years=cfg.payment_delay_years
        )
        
        tariffs = TariffModel(
            feed_in_energy=cfg.acceptance_energy_tariff_chf_kwh,
            feed_in_hkn=cfg.hkn_tariff_chf_kwh,
            leg_tariff=cfg.leg_tariff_chf_kwh,
            self_consumption=cfg.saved_withdrawal_tariff_chf_kwh,
            performance_zev=cfg.performance_tariff_zev_chf_kw_month,
            admin_fee_zev=cfg.admin_fee_zev_chf_kwh,
            basic_cost_zev_month=cfg.basic_cost_zev_chf_month,
            inflation_rate=cfg.inflation_rate_pct / 100,
            self_consumption_pct=cfg.self_consumption_rate_pct,
            leg_share_pct=cfg.leg_share_pct,
            peak_reduction_pv_pct=cfg.reduction_performance_peaks_pct,
            peak_reduction_battery_pct=cfg.reduction_performance_peaks_battery_pct,
            num_consumers=cfg.number_of_consumers,
            vat_rate=cfg.vat_rate_pct / 100,
            vat_liable=cfg.vat_obligation == "liable"
        )
        
        maintenance = MaintenanceSchedule(
            base_cost=800 + 0.002 * cfg.investment_sum_chf,
            base_frequency=cfg.maintenance_frequency_years,
            component_cost=cfg.component_maintenance_cost_chf,
            component_frequency=cfg.component_maintenance_frequency_years,
            monitoring_cost=cfg.monitoring_cost_chf,
            administration_cost=cfg.administration_cost_chf,
            data_connection_cost=cfg.data_connection_cost_chf,
            insurance_cost=cfg.insurance_cost_chf,
            repairs_cost=cfg.repairs_cost_chf,
            repairs_frequency=cfg.repairs_frequency_years,
            cleaning_cost=cfg.cleaning_cost_chf,
            cleaning_frequency=cfg.cleaning_frequency_years,
            inverter_cost=cfg.inverter_replacement_cost_chf,
            inverter_frequency=cfg.inverter_replacement_frequency_years,
            battery_replacement_cost=cfg.battery_replacement_cost_chf,
            battery_replacement_frequency=cfg.battery_replacement_frequency_years,
            use_kwh_price=cfg.maintenance_calculation_method == "kwh_price",
            kwh_price=cfg.specific_maintenance_cost_chf_kwh
        )
        
        return FinancialAnalysis(pv, investment, battery, tariffs, maintenance)
    
    def calculate(self) -> FinancialAnalysisResults:
        """Execute analysis and return backward-compatible results."""
        result = self._analysis.calculate()
        
        return FinancialAnalysisResults(
            total_investment_chf=result.total_investment,
            total_subsidies_chf=result.total_subsidies,
            net_investment_chf=result.net_investment,
            payback_year_pv_only=result.payback_pv,
            payback_year_with_battery=result.payback_with_battery,
            payback_year_battery_only=result.payback_battery_only,
            npv_30_year_pv_only_chf=result.npv_pv,
            npv_30_year_with_battery_chf=result.npv_with_battery,
            npv_30_year_battery_only_chf=result.npv_battery_only,
            yearly_data=result.yearly_data
        )
