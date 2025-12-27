from dataclasses import dataclass, field
from typing import Optional, Dict
from .enums import (
    MaintenanceCostType, VATCompliance, 
    BatteryChemistry, SystemCategory
)
@dataclass(frozen=True)
class MaintenanceConfig:
    """Maintenance cost configuration."""
    cost_type: MaintenanceCostType
    # For PRICE_PER_KWH mode
    cost_per_kwh_chf: float = 0.02  # CHF per kWh generated
    # For MAINTENANCE_TABLE mode (years -> annual cost CHF)
    maintenance_schedule: Dict[int, float] = field(default_factory=dict)
@dataclass(frozen=True)
class BatterySpecification:
    """Battery economic parameters."""
    chemistry: BatteryChemistry
    capacity_kwh: float
    # Chemistry-specific defaults can be loaded from registry
    cost_per_kwh_chf: Optional[float] = None  # None = use registry default
    cycle_life: Optional[int] = None
    round_trip_efficiency: float = 0.95
@dataclass(frozen=True)
class SystemSpecification:
    """PV system installation specification."""
    category: SystemCategory
    capacity_kwp: float
    # Category affects subsidy rates (Pronovo)
    cost_per_kwp_chf: Optional[float] = None  # None = use registry default
@dataclass(frozen=True)
class EconomicsConfig:
    """
    Master configuration for economic analysis.
    
    Example:
        config = EconomicsConfig(
            vat_compliance=VATCompliance.NOT_VAT_LIABLE,
            maintenance=MaintenanceConfig(
                cost_type=MaintenanceCostType.PRICE_PER_KWH,
                cost_per_kwh_chf=0.025
            ),
            battery=BatterySpecification(
                chemistry=BatteryChemistry.LITHIUM_LFP,
                capacity_kwh=10.0
            ),
            system=SystemSpecification(
                category=SystemCategory.ATTACHED_ROOF,
                capacity_kwp=8.5
            )
        )
    """
    vat_compliance: VATCompliance
    maintenance: MaintenanceConfig
    battery: Optional[BatterySpecification] = None
    system: Optional[SystemSpecification] = None