"""
Commercial Battery Equipment Catalog
=====================================
Database of modular battery systems with commercial specifications.

This module contains COMMERCIAL EQUIPMENT data (brand, model, pricing, stacking rules).
For physics simulation parameters, see: eclipse/battery/defaults.py
"""

from dataclasses import dataclass
from typing import List, Optional, Tuple
from enum import Enum


class BatteryChemistry(Enum):
    """Battery cell chemistry types."""
    LFP = "LFP"    # Lithium Iron Phosphate (safe, long cycle life)
    NMC = "NMC"    # Nickel Manganese Cobalt (higher energy density)
    LTO = "LTO"    # Lithium Titanate (ultra-fast charging)


@dataclass(frozen=True)
class ModularBatterySpec:
    """
    Specification for a modular/stackable battery system.
    
    Represents ONE MODULE that can be stacked in towers (columns).
    Multiple towers can be installed in parallel.
    
    Example:
        Huawei LUNA2000: 5 kWh per module, max 6 modules/tower, max 2 towers
        → Possible capacities: 5, 10, 15, 20, 25, 30, 35, 40, 45, 50, 55, 60 kWh
    """
    # Identity
    brand: str                      # "Huawei", "BYD", "Sonnen", "Tesla"
    model: str                      # "LUNA2000-5-S0", "HVS-5.1"
    
    # Per-Module Electrical Specs
    capacity_kwh: float             # Energy per module (5.0, 5.1, 13.5)
    power_kw: float                 # Continuous power per module
    chemistry: BatteryChemistry     # LFP, NMC
    round_trip_efficiency: float    # 0.95-0.97
    
    # Stacking Constraints
    max_modules_per_tower: int      # Vertical stack limit (6, 5, 3)
    max_towers: int                 # Parallel tower limit (2, 4, 16)
    min_modules: int = 1            # Minimum modules required (some need 2+)
    
    # Physical
    weight_kg: float = 0.0          # Per-module weight
    dimensions_mm: Optional[Tuple[int, int, int]] = None  # (W, H, D)
    
    # Economics (Swiss Market 2025)
    price_per_kwh_chf: float = 0.0  # CHF per kWh
    warranty_years: int = 10        # Standard warranty period
    
    # ════════════════════════════════════════════════════════════════════════
    # COMPUTED PROPERTIES
    # ════════════════════════════════════════════════════════════════════════
    
    @property
    def max_system_capacity_kwh(self) -> float:
        """Maximum possible capacity with full stacking."""
        return self.capacity_kwh * self.max_modules_per_tower * self.max_towers
    
    @property
    def price_per_module_chf(self) -> float:
        """Cost of one module."""
        return self.capacity_kwh * self.price_per_kwh_chf
    
    def available_capacities(self) -> List[float]:
        """
        List all possible discrete capacity configurations.
        
        Returns:
            Sorted list of achievable capacities in kWh.
        """
        capacities = set()
        for towers in range(1, self.max_towers + 1):
            for modules in range(self.min_modules, self.max_modules_per_tower + 1):
                cap = self.capacity_kwh * modules * towers
                capacities.add(round(cap, 2))
        return sorted(capacities)
    
    def __str__(self) -> str:
        return f"{self.brand} {self.model} ({self.capacity_kwh} kWh/module)"


# ════════════════════════════════════════════════════════════════════════════
# COMMERCIAL BATTERY CATALOG (2025 Swiss Market)
# ════════════════════════════════════════════════════════════════════════════

# --- HUAWEI ---
_Huawei_LUNA2000 = ModularBatterySpec(
    brand="Huawei",
    model="LUNA2000-5-S0",
    capacity_kwh=5.0,
    power_kw=2.5,
    chemistry=BatteryChemistry.LFP,
    round_trip_efficiency=0.96,
    max_modules_per_tower=6,
    max_towers=2,
    min_modules=1,
    weight_kg=62.0,
    dimensions_mm=(670, 600, 150),
    price_per_kwh_chf=650,
    warranty_years=10
)

# --- BYD ---
_BYD_HVS = ModularBatterySpec(
    brand="BYD",
    model="HVS-5.1",
    capacity_kwh=5.1,
    power_kw=2.5,
    chemistry=BatteryChemistry.LFP,
    round_trip_efficiency=0.95,
    max_modules_per_tower=5,
    max_towers=4,
    min_modules=2,  # BYD HVS requires minimum 2 modules
    weight_kg=45.0,
    dimensions_mm=(585, 520, 295),
    price_per_kwh_chf=600,
    warranty_years=10
)

_BYD_HVM = ModularBatterySpec(
    brand="BYD",
    model="HVM-2.76",
    capacity_kwh=2.76,
    power_kw=1.3,
    chemistry=BatteryChemistry.LFP,
    round_trip_efficiency=0.95,
    max_modules_per_tower=8,
    max_towers=16,  # Commercial-scale: up to 16 towers
    min_modules=3,  # BYD HVM requires minimum 3 modules
    weight_kg=26.0,
    dimensions_mm=(585, 130, 415),
    price_per_kwh_chf=550,  # Volume discount for large systems
    warranty_years=10
)

# --- SONNEN ---
_Sonnen_Eco = ModularBatterySpec(
    brand="Sonnen",
    model="Eco-5",
    capacity_kwh=5.0,
    power_kw=2.25,
    chemistry=BatteryChemistry.LFP,
    round_trip_efficiency=0.94,
    max_modules_per_tower=4,
    max_towers=2,
    min_modules=1,
    weight_kg=55.0,
    dimensions_mm=(690, 880, 220),
    price_per_kwh_chf=900,  # Premium brand
    warranty_years=10
)

# --- TESLA ---
_Tesla_Powerwall3 = ModularBatterySpec(
    brand="Tesla",
    model="Powerwall3",
    capacity_kwh=13.5,
    power_kw=11.5,
    chemistry=BatteryChemistry.NMC,
    round_trip_efficiency=0.97,
    max_modules_per_tower=3,
    max_towers=2,
    min_modules=1,
    weight_kg=130.0,
    dimensions_mm=(1098, 1380, 168),
    price_per_kwh_chf=850,
    warranty_years=10
)


# ════════════════════════════════════════════════════════════════════════════
# CATALOG & HELPER FUNCTIONS
# ════════════════════════════════════════════════════════════════════════════

BATTERY_CATALOG: List[ModularBatterySpec] = [
    _Huawei_LUNA2000,
    _BYD_HVS,
    _BYD_HVM,
    _Sonnen_Eco,
    _Tesla_Powerwall3,
]

DEFAULT_COMMERCIAL_SPEC = _BYD_HVS


def get_all() -> List[ModularBatterySpec]:
    """Return all available battery specs."""
    return BATTERY_CATALOG


def get_by_brand(brand: str) -> List[ModularBatterySpec]:
    """Filter batteries by brand name (case-insensitive)."""
    return [b for b in BATTERY_CATALOG if b.brand.lower() == brand.lower()]


def get(model_name: str) -> ModularBatterySpec:
    """
    Get battery by model name (case-insensitive).
    
    Raises:
        ValueError: If model not found.
    """
    for b in BATTERY_CATALOG:
        if b.model.lower() == model_name.lower():
            return b
    available = [b.model for b in BATTERY_CATALOG]
    raise ValueError(f"Battery '{model_name}' not found. Available: {available}")


def default_spec() -> ModularBatterySpec:
    """Return the default commercial battery spec (BYD HVS) for CAPEX calculations."""
    return DEFAULT_COMMERCIAL_SPEC


def default():
    """
    Return a simulation-ready MockBattery for PySAM/Simple simulators.
    
    Usage:
        from eclipse.config.equipments import batteries
        battery = batteries.default()
        simulator = PySAMBatterySimulator(battery)
        results = simulator.simulate(load, pv, system_kwh=13.5)
    """
    from eclipse.battery.defaults import DEFAULT_PYSAM_BATTERY
    return DEFAULT_PYSAM_BATTERY


def list_options() -> None:
    """Print available battery options to console."""
    print("Available Modular Batteries:")
    print("-" * 60)
    for b in BATTERY_CATALOG:
        max_cap = b.max_system_capacity_kwh
        print(f"  {b.brand:10} {b.model:20} {b.capacity_kwh:5.1f} kWh/mod  "
              f"(max {max_cap:.0f} kWh)")


# ════════════════════════════════════════════════════════════════════════════
# FACTORY FUNCTIONS (For convenient imports)
# ════════════════════════════════════════════════════════════════════════════

def Huawei_LUNA2000() -> ModularBatterySpec:
    return _Huawei_LUNA2000

def BYD_HVS() -> ModularBatterySpec:
    return _BYD_HVS

def BYD_HVM() -> ModularBatterySpec:
    return _BYD_HVM

def Sonnen_Eco() -> ModularBatterySpec:
    return _Sonnen_Eco

def Tesla_Powerwall3() -> ModularBatterySpec:
    return _Tesla_Powerwall3

