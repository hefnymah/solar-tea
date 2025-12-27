from enum import Enum, auto
from typing import Literal

class MaintenanceCostType(Enum):
    """How maintenance costs are calculated."""
    PRICE_PER_KWH       = auto()       # Cost proportional to energy generated
    MAINTENANCE_TABLE   = auto()       # Fixed schedule from lookup table

class VATCompliance(Enum):
    """VAT registration status affecting subsidy calculations."""
    VAT_LIABLE          = auto()       # Can reclaim VAT on equipment
    NOT_VAT_LIABLE      = auto()       # Standard residential (no VAT reclaim)

class BatteryChemistry(Enum):
    """Battery cell chemistry types with different characteristics."""
    LITHIUM_LFP         = "LFP"        # Lithium Iron Phosphate (long life, safe)
    LITHIUM_NMC         = "NMC"        # Nickel Manganese Cobalt (high density)
    LITHIUM_NCA         = "NCA"        # Nickel Cobalt Aluminum (Tesla-style)
    LITHIUM_LTO         = "LTO"        # Lithium Titanate (fast charge, long life)
    SODIUM_ION          = "Na-ion"     # Sodium-ion (emerging, low cost)

class SystemCategory(Enum):
    """PV mounting category per Swiss Pronovo classification."""
    INTEGRATED_ROOF     = "integrated_roof"    # Roof-integrated
    ATTACHED_ROOF       = "attached_roof"      # Roof-attached
    INTEGRATED_FACADE   = "integrated_facade"  # Facade-integrated
    ATTACHED_FACADE     = "attached_facade"    # Facade-attached
    COMBINED            = "combined"           # Combined roof and facade
    FREE_STANDING       = "free_standing"      # Free-standing