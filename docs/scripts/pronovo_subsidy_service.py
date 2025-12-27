"""
Pronovo Subsidy Service
=======================
A professional, object-oriented service for calculating Swiss PV subsidies (EIV and EVS).

Features:
- Dataclass-baesd DTOs for cleaner inputs and outputs
- Separation of tariff data and calculation logic
- Strategy pattern for different tariff years (extensible)
- Strict typing and docstrings
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, Optional, List
from datetime import datetime

# -----------------------------------------------------------------------------
# Enums and Types
# -----------------------------------------------------------------------------

class InstallationType(Enum):
    """PV installation types according to Pronovo classification."""
    INTEGRIERT = "Integriert"  # Integrated
    ANGEBAUT = "Angebaut"      # Mounted
    FREISTEHEND = "Freistehend" # Freestanding

@dataclass
class SystemSpecs:
    """
    Data Transfer Object (DTO) for PV System Specifications.
    Centralizes all technical parameters needed for calculations.
    """
    capacity_kwp: float
    installation_type: InstallationType = InstallationType.ANGEBAUT
    has_self_consumption: bool = True  # True = Eigenverbrauch (Standard EIV), False = Volleinspeisung (HEIV)
    
    # Optional parameters for bonuses
    tilt_angle_degrees: Optional[float] = None
    altitude_meters: Optional[float] = None
    parking_area_coverage: bool = False
    
    # Commissioning date (optional, for selecting tariff year)
    commissioning_date: Optional[str] = None

@dataclass
class SubsidyResult:
    """Result object for subsidy calculations."""
    base_contribution: float
    performance_contribution: float = 0.0
    tilt_bonus: float = 0.0
    height_bonus: float = 0.0
    parking_bonus: float = 0.0
    total_subsidy: float = 0.0
    
    # Metadata
    tariff_source: str = ""
    tariff_year: str = ""
    is_heiv: bool = False # High EIV applied?

# -----------------------------------------------------------------------------
# Tariff Configuration
# -----------------------------------------------------------------------------

@dataclass
class TariffConfiguration:
    """Holds tariff rates for a specific period."""
    year: str
    source_url: str
    
    # Base Rates (Standard EIV)
    base_rate_tier1: float # < 30 kWp
    base_rate_tier2: float # 30-100 kWp
    base_rate_tier3: float # > 100 kWp
    
    # Integrated Rates (Indach) - Higher for 2025
    integrated_rate_tier1: float # First 30 kWp
    integrated_rate_tier2: float # 30-100 kWp
    integrated_rate_tier3: float # > 100 kWp
    
    # HEIV Rates (Volleinspeisung)
    heiv_rate_tier1: float
    heiv_rate_tier2: float
    heiv_rate_tier3: float
    
    # Bonus Rates
    tilt_bonus_rate: float # if the tilt angle is above 75 degrees
    tilt_bonus_rate_integrated: float # Higher rate for integrated tilt
    height_bonus_rate: float # if the height is above 1500m
    parking_bonus_rate: float # if the parking area is above 50m2
    
    # Multipliers
    multipliers: Dict[InstallationType, float] = field(default_factory=lambda: {
        InstallationType.INTEGRIERT: 1.0,
        InstallationType.ANGEBAUT: 1.0,
        InstallationType.FREISTEHEND: 1.0,
    })

    @classmethod
    def get_2025(cls) -> 'TariffConfiguration':
        """Factory method for 2025 Tariff Rates (based on research & reverse engineering)."""
        
        return cls(
            year="2025",
            source_url="https://pronovo.ch/de/services/tarifrechner/",
            # Standard EIV (Attached/Aufdach/Freistehend)
            base_rate_tier1=360.0,   # First 30 kWp
            base_rate_tier2=300.0,   # Next 70 kWp
            base_rate_tier3=280.0,   # > 100 kWp
            
            # Integrated EIV (Indach) - Confirmed Research
            integrated_rate_tier1=400.0, # First 30 kWp
            integrated_rate_tier2=330.0, # Next 70 kWp
            integrated_rate_tier3=310.0, # > 100 kWp (Estimate based on +20-30 premium)
            
            # HEIV Rates (Volleinspeisung) - typically +10-20% higher
            heiv_rate_tier1=450.0,   # Estimate
            heiv_rate_tier2=350.0,   # Estimate
            heiv_rate_tier3=250.0,   # Estimate
            
            # Bonuses 2025
            tilt_bonus_rate=200.0,             # Attached/Freestanding
            tilt_bonus_rate_integrated=400.0,  # Integrated (Double)
            height_bonus_rate=100.0,
            parking_bonus_rate=250.0
        )
        
    @classmethod
    def get_2024_2025(cls) -> 'TariffConfiguration':
        """Legacy naming alias - redirects to 2025."""
        return cls.get_2025()

# -----------------------------------------------------------------------------
# Core Service
# -----------------------------------------------------------------------------

class PronovoSubsidyService:
    """
    Professional Service Class for calculating Pronovo subsidies.
    Uses dependency injection for tariff configuration.
    """
    
    def __init__(self, config: Optional[TariffConfiguration] = None):
        """
        Initialize service with specific tariff configuration.
        Defaults to latest known rates if none provided.
        """
        self.config = config or TariffConfiguration.get_2024_2025()
        
    def calculate_eiv(self, system: SystemSpecs) -> SubsidyResult:
        """
        Calculate EIV (One-time remuneration) based on system specs.
        """
        # Determine applicable rates (HEIV or Integrated or Standard)
        is_heiv = not system.has_self_consumption
        is_integrated = system.installation_type == InstallationType.INTEGRIERT
        
        if is_heiv:
            # HEIV Rates (Volleinspeisung)
            # Note: 2025 rules apply park bonus to HEIV too
            r1, r2, r3 = self.config.heiv_rate_tier1, self.config.heiv_rate_tier2, self.config.heiv_rate_tier3
        elif is_integrated:
            # Integrated Rates (Indach) - 2025 Rules
            r1, r2, r3 = self.config.integrated_rate_tier1, self.config.integrated_rate_tier2, self.config.integrated_rate_tier3
        else:
            # Standard Rates (Attached/Freestanding)
            r1, r2, r3 = self.config.base_rate_tier1, self.config.base_rate_tier2, self.config.base_rate_tier3
            
        multiplier = self.config.multipliers.get(system.installation_type, 1.0)
        
        # 1. Base Contribution Calculation (Tiered)
        cap = system.capacity_kwp
        base_contrib = 0.0
        
        # Tier 1: 0 - 30 kWp
        t1_amount = min(cap, 30.0)
        base_contrib += t1_amount * r1 * multiplier
        
        # Tier 2: 30 - 100 kWp
        if cap > 30.0:
            t2_amount = min(cap - 30.0, 70.0)
            base_contrib += t2_amount * r2 * multiplier
            
        # Tier 3: > 100 kWp
        if cap > 100.0:
            t3_amount = cap - 100.0
            base_contrib += t3_amount * r3 * multiplier
            
        # 2. Bonuses
        # Tilt Bonus (Neigungswinkel)
        tilt_bonus = 0.0
        if system.tilt_angle_degrees and system.tilt_angle_degrees >= 75.0:
            rate = self.config.tilt_bonus_rate_integrated if is_integrated else self.config.tilt_bonus_rate
            tilt_bonus = cap * rate
            
        # Height Bonus (Höhenbonus)
        height_bonus = 0.0
        if system.altitude_meters and system.altitude_meters >= 1500.0:
            height_bonus = cap * self.config.height_bonus_rate
            
        # Parking Bonus (Parkflächenbonus)
        # Rule (from 2025):
        # - Rate: 250 CHF/kWp
        # - Eligibility: Capacity >= 100 kWp (Large systems only)
        # - Condition: Permanent, previously unroofed parking area
        parking_bonus = 0.0
        if system.parking_area_coverage and cap >= 100.0:
            parking_bonus = cap * self.config.parking_bonus_rate
        
        # Note: Parking bonus and Tilt bonus rules might interact (some sources say mutually exclusive)
        # For now, we apply them independently as configured unless mutually exclusive logic is confirmed strict.
            
        # 3. Total
        total = base_contrib + tilt_bonus + height_bonus + parking_bonus
        
        return SubsidyResult(
            base_contribution=round(base_contrib, 2),
            tilt_bonus=round(tilt_bonus, 2),
            height_bonus=round(height_bonus, 2),
            parking_bonus=round(parking_bonus, 2),
            total_subsidy=round(total, 2),
            tariff_source=self.config.source_url,
            tariff_year=self.config.year,
            is_heiv=is_heiv
        )

# -----------------------------------------------------------------------------
# Demo / Main
# -----------------------------------------------------------------------------

def main():
    """Demonstrate the OOP usage."""
    print("="*60)
    print("Pronovo Subsidy Service (OOP Demo)")
    print("="*60)
    
    # Initialize Service
    service = PronovoSubsidyService()
    
    # 1. Standard System
    specs_standard = SystemSpecs(
        capacity_kwp=10.0,
        installation_type=InstallationType.ANGEBAUT,
        has_self_consumption=True
    )
    result_std = service.calculate_eiv(specs_standard)
    
    print(f"\nScenario 1: {specs_standard.capacity_kwp} kWp (Self-Consumption)")
    print("-" * 40)
    print(f"Base Contribution: {result_std.base_contribution:,.2f} CHF")
    print(f"Total Subsidy:     {result_std.total_subsidy:,.2f} CHF")
    
    
    # 2. Verification Case: 50 kWp (User Screenshot)
    # Expected: ~16,800 CHF
    specs_50 = SystemSpecs(capacity_kwp=50.0)
    result_50 = service.calculate_eiv(specs_50)
    print(f"\nVerification 1: 50.0 kWp System")
    print("-" * 40)
    print(f"Expected:        ~16,800.00 CHF")
    print(f"Calculated Base: {result_50.base_contribution:,.2f} CHF")
    print(f"Total Subsidy:   {result_50.total_subsidy:,.2f} CHF")
    
    # 3. Verification Case: 100 kWp (User Screenshot)
    # Expected: ~31,800 CHF (Base) + 25,000 CHF (Parking) = ~56,800 CHF
    specs_100 = SystemSpecs(
        capacity_kwp=100.0, 
        parking_area_coverage=True
    )
    result_100 = service.calculate_eiv(specs_100)
    print(f"\nVerification 2: 100.0 kWp System (with Parking Bonus)")
    print("-" * 40)
    print(f"Expected Base:   ~31,800.00 CHF")
    print(f"Calculated Base: {result_100.base_contribution:,.2f} CHF")
    print(f"Parking Bonus:   {result_100.parking_bonus:,.2f} CHF")
    print(f"Total Subsidy:   {result_100.total_subsidy:,.2f} CHF")

    # 4. Verification Case: 70 kWp Freestanding (User Bug Report)
    # Expected: ~22,800 CHF (previously 20,520)
    specs_70_free = SystemSpecs(
        capacity_kwp=70.0,
        installation_type=InstallationType.FREISTEHEND
    )
    result_70 = service.calculate_eiv(specs_70_free)
    print(f"\nVerification 3: 70.0 kWp Freestanding (User Bug Report)")
    print("-" * 40)
    print(f"Expected:        ~22,800.00 CHF")
    print(f"Calculated:      {result_70.total_subsidy:,.2f} CHF")

    # 5. Verification Case: 70 kWp Integrated (Indach)
    # Expected: 30 * 400 + 40 * 330 = 12,000 + 13,200 = 25,200 CHF (Higher than 22,800)
    specs_70_int = SystemSpecs(
        capacity_kwp=70.0,
        installation_type=InstallationType.INTEGRIERT
    )
    result_70_int = service.calculate_eiv(specs_70_int)
    print(f"\nVerification 4: 70.0 kWp Integrated (Indach 2025 Premium)")
    print("-" * 40)
    print(f"Expected:        ~25,200.00 CHF")
    print(f"Calculated:      {result_70_int.total_subsidy:,.2f} CHF")
    print(f"Premium vs Std:  +{result_70_int.total_subsidy - result_70.total_subsidy:,.2f} CHF")

    # 6. HEIV System
    specs_heiv = SystemSpecs(
        capacity_kwp=10.0,
        has_self_consumption=False # Triggers HEIV
    )
    result_heiv = service.calculate_eiv(specs_heiv)
    
    print(f"\nScenario 3: 10.0 kWp (Volleinspeisung/HEIV)")
    print("-" * 40)
    print(f"Base Contribution: {result_heiv.base_contribution:,.2f} CHF")
    print(f"Total Subsidy:     {result_heiv.total_subsidy:,.2f} CHF")
    
    # 3. Alpine System with Bonuses
    specs_alpine = SystemSpecs(
        capacity_kwp=25.0,
        installation_type=InstallationType.INTEGRIERT,
        altitude_meters=1600.0,
        tilt_angle_degrees=80.0
    )
    result_alpine = service.calculate_eiv(specs_alpine)
    
    print(f"\nScenario 3: 25 kWp Alpine System (Integrated + Bonuses)")
    print("-" * 40)
    print(f"Base:    {result_alpine.base_contribution:,.2f} CHF")
    print(f"Tilt:    {result_alpine.tilt_bonus:,.2f} CHF (>= 75°)")
    print(f"Height:  {result_alpine.height_bonus:,.2f} CHF (>= 1500m)")
    print(f"Total:   {result_alpine.total_subsidy:,.2f} CHF")

if __name__ == "__main__":
    main()
