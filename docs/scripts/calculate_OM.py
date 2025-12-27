"""
Operating and Maintenance (O&M) Costs Calculator - OOP Refactored Version

Replicates Excel 'Eingaben' sheet Operating and Maintenance Costs section:
- PV System O&M: Rows 110-126
- Battery O&M: Rows 128-131

This module uses a clean OOP design with separated input parameter classes
for easy integration with other system components.
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, Any, Optional, List


# =============================================================================
# ENUMERATIONS
# =============================================================================

class CalculationMethod(Enum):
    """O&M calculation method options (Excel row 111)."""
    PRICE_PER_KWH = "Preis pro kWh"
    MAINTENANCE_SCHEDULE = "Wartungstabelle"


class InstallationCategory(Enum):
    """Installation category affects maintenance intervals."""
    DACH_INTEGRIERT = "Dach integriert"
    DACH_ANGEBAUT = "Dach angebaut"
    FASSADE_INTEGRIERT = "Fassade integriert"
    FASSADE_ANGEBAUT = "Fassade angebaut"
    KOMBINIERT = "kombiniert"
    FREISTEHEND = "freistehend"

    @property
    def is_facade(self) -> bool:
        """Check if installation is facade-mounted (affects intervals)."""
        return self in (
            InstallationCategory.FASSADE_INTEGRIERT,
            InstallationCategory.FASSADE_ANGEBAUT
        )


class BatteryTechnology(Enum):
    """Battery technology types with associated replacement costs."""
    LITHIUM_LFP = ("Lithium-Ionen LFP", 800.0)
    LITHIUM_NMC = ("Lithium-Ionen NMC", 900.0)
    LITHIUM_NCA = ("Lithium-Ionen NCA", 950.0)
    LITHIUM_LTO = ("Lithium-Ionen LTO", 1200.0)
    SODIUM_ION = ("Natrium-Ionen", 600.0)
    LEAD_ACID_AGM = ("Blei-Säure AGM", 300.0)

    def __init__(self, label: str, cost_per_kwh: float):
        self.label = label
        self.cost_per_kwh = cost_per_kwh


# =============================================================================
# INPUT PARAMETER CLASSES
# =============================================================================

@dataclass
class PVSystemParameters:
    """
    Input parameters for PV system O&M calculations.
    
    These parameters are typically passed from investment/sizing calculations.
    """
    capacity_kwp: float = 0.0
    investment_chf: float = 0.0
    pv_area_m2: float = 0.0
    category: InstallationCategory = InstallationCategory.DACH_ANGEBAUT
    lifetime_years: int = 30
    specific_yield_kwh_kwp: float = 1000.0
    degradation_percent: float = 0.4


@dataclass
class BatteryParameters:
    """
    Input parameters for battery O&M calculations.
    
    These parameters are typically passed from battery sizing calculations.
    """
    capacity_kwh: float = 0.0
    investment_chf: float = 0.0
    technology: BatteryTechnology = BatteryTechnology.LITHIUM_LFP
    lifetime_years: int = 15
    # Annual energy throughput (kWh/year) - for Row 131 calculation
    # If not provided, defaults to ~200 cycles/year × capacity
    annual_throughput_kwh: Optional[float] = None
    
    def get_annual_throughput(self) -> float:
        """Get annual battery throughput in kWh."""
        if self.annual_throughput_kwh is not None:
            return self.annual_throughput_kwh
        # Default: ~185 cycles per year (matches Excel typical assumptions)
        return self.capacity_kwh * 185


@dataclass
class OMOverrides:
    """
    Optional overrides for individual O&M cost items.
    
    If provided, these values override the calculated defaults.
    Use None to use calculated defaults.
    """
    # PV overrides (Excel column B inputs)
    inspection_cost: Optional[float] = None
    audit_cost: Optional[float] = None
    monitoring_cost: Optional[float] = None
    administration_cost: Optional[float] = None
    data_connection_cost: Optional[float] = None
    insurance_cost: Optional[float] = None
    repair_cost: Optional[float] = None
    cleaning_cost: Optional[float] = None
    vegetation_cost: Optional[float] = None
    transformer_cost: Optional[float] = None
    rent_cost: Optional[float] = None
    inverter_cost: Optional[float] = None
    
    # Battery overrides
    battery_maintenance_cost: Optional[float] = None
    battery_replacement_cost: Optional[float] = None
    
    # For "Preis pro kWh" method
    specific_cost_chf_kwh: Optional[float] = None


# =============================================================================
# RESULT CLASSES
# =============================================================================

@dataclass
class MaintenanceItem:
    """Represents a single maintenance cost item from the schedule."""
    name: str
    name_de: str
    excel_row: int
    cost_per_occurrence: float
    interval_years: float
    total_over_lifetime: float = 0.0
    is_replacement: bool = False  # If True, initial item is included in investment

    def calculate_total(self, lifetime_years: int) -> float:
        """
        Calculate total cost over system lifetime.
        
        For regular items: occurrences = floor(lifetime / interval)
        For replacement items (is_replacement=True): initial is in investment,
            so we subtract 1 from occurrences.
        """
        if self.interval_years <= 0 or lifetime_years <= 0:
            return 0.0
        occurrences = int(lifetime_years / self.interval_years)
        if self.is_replacement:
            # Initial item is included in investment cost
            occurrences = max(0, occurrences - 1)
        self.total_over_lifetime = occurrences * self.cost_per_occurrence
        return self.total_over_lifetime


@dataclass
class PVMaintenanceResult:
    """Result of PV system O&M calculation."""
    calculation_method: str
    specific_cost_chf_kwh: float
    items: List[MaintenanceItem] = field(default_factory=list)
    total_annual_cost: float = 0.0
    total_lifetime_cost: float = 0.0
    average_cost_chf_kwh: float = 0.0

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for Excel export."""
        result = {
            'berechnungsart': self.calculation_method,
            'spez_unterhaltskosten': round(self.specific_cost_chf_kwh, 4),
            'total_annual_cost': round(self.total_annual_cost, 2),
            'total_lifetime_cost': round(self.total_lifetime_cost, 2),
            'durchschnittliche_kosten': round(self.average_cost_chf_kwh, 4),
        }
        for item in self.items:
            key = item.name.lower().replace(' ', '_')
            result[f'{key}_cost'] = round(item.cost_per_occurrence, 2)
            result[f'{key}_interval'] = item.interval_years
            result[f'{key}_total'] = round(item.total_over_lifetime, 2)
        return result


@dataclass
class BatteryMaintenanceResult:
    """Result of battery O&M calculation."""
    annual_maintenance_cost: float = 0.0
    replacement_cost: float = 0.0
    specific_cost_chf_kwh: float = 0.0
    total_lifetime_cost: float = 0.0

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for Excel export."""
        return {
            'unterhaltskosten_batteriespeicher': round(self.annual_maintenance_cost, 2),
            'ersatz_batteriespeicher': round(self.replacement_cost, 2),
            'durchschnittliche_kosten_batterie': round(self.specific_cost_chf_kwh, 4),
            'total_lifetime_cost_battery': round(self.total_lifetime_cost, 2),
        }


@dataclass
class CombinedOMResult:
    """Combined PV and Battery O&M results."""
    pv_result: PVMaintenanceResult
    battery_result: Optional[BatteryMaintenanceResult] = None
    combined_lifetime_cost: float = 0.0
    combined_annual_cost: float = 0.0

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for Excel export."""
        result = self.pv_result.to_dict()
        if self.battery_result:
            result.update(self.battery_result.to_dict())
        result['combined_lifetime_cost'] = round(self.combined_lifetime_cost, 2)
        result['combined_annual_cost'] = round(self.combined_annual_cost, 2)
        return result


# =============================================================================
# CALCULATOR CLASSES
# =============================================================================

class PVOMCalculator:
    """
    PV System Operating and Maintenance Costs Calculator.
    
    Replicates Excel 'Eingaben' Rows 110-126.
    
    Excel Formulas (Column I):
        - I114: Inspection = 800 + 0.002 × Investment
        - I116: Monitoring = 60 + Capacity × 2
        - I117: Administration = 90 + Capacity × 2
        - I118: Data connection = 10 × 12 = 120 CHF/year
        - I119: Insurance = Investment × 0.0032
        - I120: Repair = 1200 + 0.001 × Investment
        - I121: Cleaning = 1000 + 3 × PV_Area
        - I125: Inverter = 500 + 150 × Capacity
    """

    def __init__(self, params: PVSystemParameters):
        """Initialize with PV system parameters."""
        self.params = params

    # -------------------------------------------------------------------------
    # Default Cost Formulas (Excel Column I)
    # -------------------------------------------------------------------------

    def calc_inspection_cost(self) -> float:
        """I114: 800 + 0.002 × Investment"""
        if self.params.investment_chf <= 0:
            return 0.0
        return 800.0 + 0.002 * self.params.investment_chf

    def calc_inspection_interval(self) -> int:
        """J114: Facade = 3 years, Other = 5 years"""
        return 3 if self.params.category.is_facade else 5

    def calc_monitoring_cost(self) -> float:
        """I116: 60 + Capacity × 2"""
        if self.params.capacity_kwp <= 0:
            return 0.0
        return 60.0 + self.params.capacity_kwp * 2.0

    def calc_administration_cost(self) -> float:
        """I117: 90 + Capacity × 2"""
        if self.params.capacity_kwp <= 0:
            return 0.0
        return 90.0 + self.params.capacity_kwp * 2.0

    def calc_data_connection_cost(self) -> float:
        """I118: 10 × 12 = 120 CHF/year"""
        return 120.0

    def calc_insurance_cost(self) -> float:
        """I119: Investment × 0.0032"""
        if self.params.investment_chf <= 0:
            return 0.0
        return self.params.investment_chf * 0.0032

    def calc_repair_cost(self) -> float:
        """I120: 1200 + 0.001 × Investment"""
        if self.params.investment_chf <= 0:
            return 0.0
        return 1200.0 + 0.001 * self.params.investment_chf

    def calc_repair_interval(self) -> int:
        """J120: Facade = 3 years, Other = 8 years"""
        return 3 if self.params.category.is_facade else 8

    def calc_cleaning_cost(self) -> float:
        """I121: 1000 + 3 × PV_Area"""
        if self.params.pv_area_m2 <= 0:
            return 0.0
        return 1000.0 + 3.0 * self.params.pv_area_m2

    def calc_cleaning_interval(self) -> int:
        """J121: Facade = 3 years, Other = 8 years"""
        return 3 if self.params.category.is_facade else 8

    def calc_inverter_cost(self) -> float:
        """I125: 500 + 150 × Capacity"""
        if self.params.capacity_kwp <= 0:
            return 0.0
        return 500.0 + 150.0 * self.params.capacity_kwp

    def calc_inverter_interval(self) -> float:
        """
        Inverter replacement interval.
        
        Inverters typically last 15 years. For a 30-year system:
        - Initial inverter at Year 0 (included in investment)
        - 1st replacement at Year 15
        - System ends at Year 30 (no replacement needed)
        
        Returns fixed 15-year interval.
        """
        return 15.0

    def calc_specific_cost_by_capacity(self) -> float:
        """J112: Tiered specific cost by capacity."""
        cap = self.params.capacity_kwp
        if cap <= 0:
            return 0.0
        elif cap < 100:
            return 0.03
        elif cap < 1000:
            return round(0.03 - (cap - 100) * 0.01 / 900, 4)
        else:
            return 0.02

    # -------------------------------------------------------------------------
    # Main Calculation
    # -------------------------------------------------------------------------

    def calculate(
        self,
        method: CalculationMethod = CalculationMethod.MAINTENANCE_SCHEDULE,
        overrides: Optional[OMOverrides] = None
    ) -> PVMaintenanceResult:
        """
        Calculate PV system O&M costs.
        
        Args:
            method: Calculation method (PRICE_PER_KWH or MAINTENANCE_SCHEDULE)
            overrides: Optional overrides for individual cost items
            
        Returns:
            PVMaintenanceResult with all calculated costs
        """
        overrides = overrides or OMOverrides()
        result = PVMaintenanceResult(
            calculation_method=method.value,
            specific_cost_chf_kwh=0.0,
        )

        if method == CalculationMethod.PRICE_PER_KWH:
            return self._calculate_price_per_kwh(result, overrides)
        else:
            return self._calculate_maintenance_schedule(result, overrides)

    def _calculate_price_per_kwh(
        self, result: PVMaintenanceResult, overrides: OMOverrides
    ) -> PVMaintenanceResult:
        """Calculate using simple price per kWh method."""
        if overrides.specific_cost_chf_kwh is not None:
            result.specific_cost_chf_kwh = overrides.specific_cost_chf_kwh
        else:
            result.specific_cost_chf_kwh = self.calc_specific_cost_by_capacity()

        annual_production = self.params.capacity_kwp * self.params.specific_yield_kwh_kwp
        result.total_annual_cost = annual_production * result.specific_cost_chf_kwh
        result.total_lifetime_cost = result.total_annual_cost * self.params.lifetime_years
        result.average_cost_chf_kwh = result.specific_cost_chf_kwh
        return result

    def _calculate_maintenance_schedule(
        self, result: PVMaintenanceResult, overrides: OMOverrides
    ) -> PVMaintenanceResult:
        """Calculate using detailed maintenance schedule."""
        items = [
            MaintenanceItem(
                name="inspection", name_de="Kontrollgänge", excel_row=114,
                cost_per_occurrence=overrides.inspection_cost or self.calc_inspection_cost(),
                interval_years=self.calc_inspection_interval(),
            ),
            MaintenanceItem(
                name="audit", name_de="Audits/Sicherheitsnachweise", excel_row=115,
                cost_per_occurrence=overrides.audit_cost or 0.0,
                interval_years=20,
            ),
            MaintenanceItem(
                name="monitoring", name_de="Überwachung", excel_row=116,
                cost_per_occurrence=overrides.monitoring_cost or self.calc_monitoring_cost(),
                interval_years=1,
            ),
            MaintenanceItem(
                name="administration", name_de="Administration", excel_row=117,
                cost_per_occurrence=overrides.administration_cost or self.calc_administration_cost(),
                interval_years=1,
            ),
            MaintenanceItem(
                name="data_connection", name_de="Datenverbindung", excel_row=118,
                cost_per_occurrence=overrides.data_connection_cost or self.calc_data_connection_cost(),
                interval_years=1,
            ),
            MaintenanceItem(
                name="insurance", name_de="Versicherung", excel_row=119,
                cost_per_occurrence=overrides.insurance_cost or self.calc_insurance_cost(),
                interval_years=1,
            ),
            MaintenanceItem(
                name="repair", name_de="Reparaturen", excel_row=120,
                cost_per_occurrence=overrides.repair_cost or self.calc_repair_cost(),
                interval_years=self.calc_repair_interval(),
            ),
            MaintenanceItem(
                name="cleaning", name_de="Reinigung Anlage", excel_row=121,
                cost_per_occurrence=overrides.cleaning_cost or self.calc_cleaning_cost(),
                interval_years=self.calc_cleaning_interval(),
            ),
            MaintenanceItem(
                name="vegetation", name_de="Grünbewuchs Pflege", excel_row=122,
                cost_per_occurrence=overrides.vegetation_cost or 0.0,
                interval_years=1,
            ),
            MaintenanceItem(
                name="transformer", name_de="Transformator", excel_row=123,
                cost_per_occurrence=overrides.transformer_cost or 0.0,
                interval_years=1,
            ),
            MaintenanceItem(
                name="rent", name_de="Dach-/Raummiete", excel_row=124,
                cost_per_occurrence=overrides.rent_cost or 0.0,
                interval_years=1,
            ),
            MaintenanceItem(
                name="inverter", name_de="Wechselrichteraustausch", excel_row=125,
                cost_per_occurrence=overrides.inverter_cost or self.calc_inverter_cost(),
                interval_years=self.calc_inverter_interval(),
                is_replacement=True,  # Initial inverter is in investment
            ),
        ]

        for item in items:
            item.calculate_total(self.params.lifetime_years)

        result.items = items
        result.total_lifetime_cost = sum(item.total_over_lifetime for item in items)

        # Annual cost: sum of annual items + amortized periodic items
        annual_items = [i for i in items if i.interval_years == 1]
        result.total_annual_cost = sum(i.cost_per_occurrence for i in annual_items)
        result.total_annual_cost += result.total_lifetime_cost / self.params.lifetime_years

        # Average cost per kWh (Row 126)
        degradation_factor = 1.0 - (self.params.degradation_percent / 100.0 * self.params.lifetime_years / 2.0)
        total_energy_kwh = (
            self.params.capacity_kwp *
            self.params.specific_yield_kwh_kwp *
            self.params.lifetime_years *
            degradation_factor
        )

        if total_energy_kwh > 0:
            result.average_cost_chf_kwh = result.total_lifetime_cost / total_energy_kwh
            result.specific_cost_chf_kwh = result.average_cost_chf_kwh

        return result


class BatteryOMCalculator:
    """
    Battery Operating and Maintenance Costs Calculator.
    
    Replicates Excel 'Eingaben' Rows 128-131.
    
    Excel Formulas:
        - I129: Battery maintenance (default 0)
        - I130: Ersatz = Investment × 0.7
    """

    def __init__(self, params: BatteryParameters, pv_params: PVSystemParameters):
        """Initialize with battery and PV system parameters."""
        self.params = params
        self.pv_params = pv_params

    def calc_maintenance_cost(self) -> float:
        """Calculate annual battery maintenance cost."""
        # Excel defaults to 0, but we support capacity-based calculation
        if self.params.capacity_kwh <= 0:
            return 0.0
        return self.params.capacity_kwh * 5.0  # 5 CHF/kWh/year

    def calc_replacement_cost_excel(self) -> float:
        """I130: Investment × 0.7 (Excel formula)"""
        if self.params.investment_chf <= 0:
            return 0.0
        return self.params.investment_chf * 0.7

    def calc_replacement_cost_technology(self) -> float:
        """Alternative: Capacity × Cost_per_kWh (technology-based)"""
        if self.params.capacity_kwh <= 0:
            return 0.0
        return self.params.capacity_kwh * self.params.technology.cost_per_kwh

    def calculate(
        self,
        overrides: Optional[OMOverrides] = None,
        use_excel_replacement_formula: bool = True
    ) -> BatteryMaintenanceResult:
        """
        Calculate battery O&M costs.
        
        Args:
            overrides: Optional overrides for cost items
            use_excel_replacement_formula: If True, use Excel formula (70% of investment).
                                           If False, use technology-based calculation.
            
        Returns:
            BatteryMaintenanceResult with calculated costs
        """
        if self.params.capacity_kwh <= 0:
            return BatteryMaintenanceResult()

        overrides = overrides or OMOverrides()
        result = BatteryMaintenanceResult()

        # Annual maintenance (Row 129)
        if overrides.battery_maintenance_cost is not None:
            result.annual_maintenance_cost = overrides.battery_maintenance_cost
        else:
            result.annual_maintenance_cost = self.calc_maintenance_cost()

        # Replacement cost (Row 130)
        if overrides.battery_replacement_cost is not None:
            result.replacement_cost = overrides.battery_replacement_cost
        elif use_excel_replacement_formula:
            result.replacement_cost = self.calc_replacement_cost_excel()
        else:
            result.replacement_cost = self.calc_replacement_cost_technology()

        # Number of replacements over PV system lifetime
        pv_lifetime = self.pv_params.lifetime_years
        num_replacements = max(0, int(pv_lifetime / self.params.lifetime_years) - 1)

        # Total lifetime cost
        result.total_lifetime_cost = (
            result.annual_maintenance_cost * pv_lifetime +
            result.replacement_cost * num_replacements
        )

        # Specific cost per kWh (Row 131)
        # Excel uses battery throughput (_Durchschnittlicher_Speichermenge), not PV energy
        annual_throughput = self.params.get_annual_throughput()
        pv_lifetime = self.pv_params.lifetime_years
        
        if annual_throughput > 0:
            # Total battery throughput over PV system lifetime
            # Account for battery degradation (simplified: average over lifetime)
            total_battery_throughput = annual_throughput * pv_lifetime
            if total_battery_throughput > 0:
                result.specific_cost_chf_kwh = result.total_lifetime_cost / total_battery_throughput

        return result


class OMCalculator:
    """
    Combined Operating and Maintenance Calculator.
    
    Facade class that orchestrates PV and Battery O&M calculations.
    """

    def __init__(
        self,
        pv_params: PVSystemParameters,
        battery_params: Optional[BatteryParameters] = None
    ):
        """
        Initialize with system parameters.
        
        Args:
            pv_params: PV system parameters
            battery_params: Optional battery parameters
        """
        self.pv_params = pv_params
        self.battery_params = battery_params
        self.pv_calculator = PVOMCalculator(pv_params)
        self.battery_calculator = (
            BatteryOMCalculator(battery_params, pv_params)
            if battery_params else None
        )

    def calculate(
        self,
        method: CalculationMethod = CalculationMethod.MAINTENANCE_SCHEDULE,
        overrides: Optional[OMOverrides] = None,
        use_excel_battery_formula: bool = True
    ) -> CombinedOMResult:
        """
        Calculate combined O&M costs.
        
        Args:
            method: PV calculation method
            overrides: Optional overrides for cost items
            use_excel_battery_formula: Use Excel's 70% investment formula for battery
            
        Returns:
            CombinedOMResult with all calculated costs
        """
        pv_result = self.pv_calculator.calculate(method, overrides)

        battery_result = None
        if self.battery_calculator:
            battery_result = self.battery_calculator.calculate(overrides, use_excel_battery_formula)

        combined_lifetime = pv_result.total_lifetime_cost
        combined_annual = pv_result.total_annual_cost

        if battery_result:
            combined_lifetime += battery_result.total_lifetime_cost
            combined_annual += battery_result.annual_maintenance_cost

        return CombinedOMResult(
            pv_result=pv_result,
            battery_result=battery_result,
            combined_lifetime_cost=combined_lifetime,
            combined_annual_cost=combined_annual,
        )

    def print_summary(self, result: CombinedOMResult) -> None:
        """Print a summary of the O&M calculation results."""
        print("=" * 70)
        print("OPERATING AND MAINTENANCE COSTS SUMMARY")
        print("=" * 70)
        
        print("\n--- PV System O&M ---")
        print(f"Method: {result.pv_result.calculation_method}")
        print(f"Annual Cost: {result.pv_result.total_annual_cost:,.2f} CHF")
        print(f"Lifetime Cost: {result.pv_result.total_lifetime_cost:,.2f} CHF")
        print(f"Specific Cost: {result.pv_result.specific_cost_chf_kwh:.4f} CHF/kWh")

        if result.pv_result.items:
            print("\nMaintenance Items:")
            for item in result.pv_result.items:
                if item.cost_per_occurrence > 0:
                    print(f"  {item.name_de}: {item.cost_per_occurrence:,.2f} CHF "
                          f"(every {item.interval_years} years) = {item.total_over_lifetime:,.2f} CHF total")

        if result.battery_result:
            print("\n--- Battery O&M ---")
            print(f"Annual Maintenance: {result.battery_result.annual_maintenance_cost:,.2f} CHF")
            print(f"Replacement Cost: {result.battery_result.replacement_cost:,.2f} CHF")
            print(f"Lifetime Cost: {result.battery_result.total_lifetime_cost:,.2f} CHF")
            print(f"Specific Cost: {result.battery_result.specific_cost_chf_kwh:.4f} CHF/kWh")

        print("\n--- Combined Totals ---")
        print(f"Combined Annual Cost: {result.combined_annual_cost:,.2f} CHF")
        print(f"Combined Lifetime Cost: {result.combined_lifetime_cost:,.2f} CHF")
        print("=" * 70)


# =============================================================================
# EXAMPLE USAGE / TESTING
# =============================================================================

if __name__ == "__main__":
    # Example: Create input parameters
    pv_params = PVSystemParameters(
        capacity_kwp=50.0,
        investment_chf=75000.0,
        pv_area_m2=300.0,
        category=InstallationCategory.DACH_ANGEBAUT,
        lifetime_years=30,
        specific_yield_kwh_kwp=950.0,
        degradation_percent=0.4,
    )

    battery_params = BatteryParameters(
        capacity_kwh=20.0,
        investment_chf=16000.0,
        technology=BatteryTechnology.LITHIUM_LFP,
        lifetime_years=15,
    )

    # Create calculator
    calculator = OMCalculator(pv_params, battery_params)

    # Calculate O&M costs
    result = calculator.calculate(
        method=CalculationMethod.MAINTENANCE_SCHEDULE,
        use_excel_battery_formula=True,
    )

    # Print summary
    calculator.print_summary(result)

    # Export to dictionary
    print("\n--- Export Dictionary ---")
    export = result.to_dict()
    for key, value in export.items():
        print(f"  {key}: {value}")
