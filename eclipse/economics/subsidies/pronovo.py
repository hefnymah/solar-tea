"""
Pronovo Subsidy Calculator
==========================

Swiss PV subsidy (EIV - One-time Remuneration) calculation service.

This module provides a professional OOP implementation for calculating Swiss solar
subsidies based on the official Pronovo tariff calculator.

Architecture:
    - PronovoSystemConfig: Immutable configuration for subsidy calculation
    - SubsidyResult: Immutable result with full breakdown
    - TariffRates: Tariff configuration with tiered rates
    - PronovoCalculator: Main calculation service

Example:
    >>> from eclipse.economics.subsidies import PronovoCalculator, PronovoSystemConfig
    >>> from eclipse.economics.enums import SystemCategory
    >>> 
    >>> calculator = PronovoCalculator()
    >>> config = PronovoSystemConfig(
    ...     capacity_kwp=10.0,
    ...     installation_type=SystemCategory.ATTACHED_ROOF
    ... )
    >>> result = calculator.calculate(config)
    >>> print(f"Total Subsidy: {result.total:,.2f} CHF")
    Total Subsidy: 3,600.00 CHF

References:
    - Official Calculator: https://pronovo.ch/de/services/tarifrechner/
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from enum import Enum, auto
from typing import Optional, Protocol

from eclipse.economics.enums import SystemCategory


# =============================================================================
# Constants
# =============================================================================

class TierThreshold:
    """Capacity thresholds for tiered rate calculation."""
    TIER_1_MAX = 30.0    # First 30 kWp
    TIER_2_MAX = 100.0   # 30-100 kWp
    # Tier 3: > 100 kWp (no upper limit)


class BonusThreshold:
    """Eligibility thresholds for bonus calculations."""
    TILT_ANGLE_MIN = 75.0       # Degrees - minimum for tilt bonus
    ALTITUDE_MIN = 1500.0       # Meters - minimum for altitude bonus
    PARKING_CAPACITY_MIN = 100.0  # kWp - minimum for parking bonus


# =============================================================================
# Installation Type Classification
# =============================================================================

class InstallationClass(Enum):
    """Installation classification for rate selection."""
    STANDARD = auto()      # Attached/Freestanding - standard rates
    INTEGRATED = auto()    # Building-integrated - premium rates
    FULL_FEED_IN = auto()  # No self-consumption - HEIV rates
    
    @classmethod
    def from_config(cls, config: 'PronovoSystemConfig') -> 'InstallationClass':
        """Determine installation class from configuration."""
        if not config.has_self_consumption:
            return cls.FULL_FEED_IN
        
        if config.installation_type in (
            SystemCategory.INTEGRATED_ROOF,
            SystemCategory.INTEGRATED_FACADE
        ):
            return cls.INTEGRATED
        
        return cls.STANDARD


# =============================================================================
# Data Transfer Objects (Immutable)
# =============================================================================

@dataclass(frozen=True)
class PronovoSystemConfig:
    """
    Immutable configuration for Pronovo subsidy calculation.
    
    Attributes:
        capacity_kwp: System capacity in kilowatts peak
        installation_type: Mounting category from SystemCategory enum
        has_self_consumption: True for EIV (standard), False for HEIV (full feed-in)
        tilt_angle_degrees: Panel tilt angle for steep installation bonus
        altitude_meters: Installation altitude for high-altitude bonus
        parking_area_coverage: True if system covers parking area (>= 100 kWp)
    """
    capacity_kwp: float
    installation_type: SystemCategory = SystemCategory.ATTACHED_ROOF
    has_self_consumption: bool = True
    tilt_angle_degrees: Optional[float] = None
    altitude_meters: Optional[float] = None
    parking_area_coverage: bool = False
    
    def __post_init__(self) -> None:
        """Validate configuration values."""
        if self.capacity_kwp <= 0:
            raise ValueError("Capacity must be positive")
        if self.tilt_angle_degrees is not None and not (0 <= self.tilt_angle_degrees <= 90):
            raise ValueError("Tilt angle must be between 0 and 90 degrees")
        if self.altitude_meters is not None and self.altitude_meters < 0:
            raise ValueError("Altitude cannot be negative")


@dataclass(frozen=True)
class SubsidyResult:
    """
    Immutable result from subsidy calculation.
    
    Attributes:
        base_contribution: Tiered base subsidy amount (CHF)
        tilt_bonus: Bonus for steep installation >= 75 degrees (CHF)
        altitude_bonus: Bonus for high altitude >= 1500m (CHF)
        parking_bonus: Bonus for parking area coverage >= 100 kWp (CHF)
        total: Total subsidy amount (CHF)
        tariff_year: Applied tariff year
        installation_class: Classification used for rate selection
    """
    base_contribution: float
    tilt_bonus: float
    altitude_bonus: float
    parking_bonus: float
    total: float
    tariff_year: str
    installation_class: InstallationClass
    
    @property
    def has_bonuses(self) -> bool:
        """Check if any bonuses were applied."""
        return self.tilt_bonus > 0 or self.altitude_bonus > 0 or self.parking_bonus > 0
    
    @property
    def total_bonuses(self) -> float:
        """Sum of all bonus contributions."""
        return self.tilt_bonus + self.altitude_bonus + self.parking_bonus


# =============================================================================
# Tariff Configuration
# =============================================================================

@dataclass(frozen=True)
class TariffRates:
    """
    Immutable tariff rates for a specific period.
    
    All rates are in CHF per kWp with tiered structure:
        - Tier 1: First 30 kWp
        - Tier 2: 30-100 kWp  
        - Tier 3: > 100 kWp
    """
    year: str
    source_url: str
    
    # Standard rates (attached/freestanding)
    standard_tier1: float
    standard_tier2: float
    standard_tier3: float
    
    # Integrated rates (building-integrated) - premium
    integrated_tier1: float
    integrated_tier2: float
    integrated_tier3: float
    
    # Full feed-in rates (no self-consumption) - HEIV
    feed_in_tier1: float
    feed_in_tier2: float
    feed_in_tier3: float
    
    # Bonus rates
    tilt_bonus_standard: float
    tilt_bonus_integrated: float
    altitude_bonus: float
    parking_bonus: float
    
    def get_rates(self, installation_class: InstallationClass) -> tuple[float, float, float]:
        """Get tiered rates for the specified installation class."""
        if installation_class == InstallationClass.FULL_FEED_IN:
            return self.feed_in_tier1, self.feed_in_tier2, self.feed_in_tier3
        elif installation_class == InstallationClass.INTEGRATED:
            return self.integrated_tier1, self.integrated_tier2, self.integrated_tier3
        else:
            return self.standard_tier1, self.standard_tier2, self.standard_tier3
    
    def get_tilt_bonus_rate(self, installation_class: InstallationClass) -> float:
        """Get tilt bonus rate for the installation class."""
        if installation_class == InstallationClass.INTEGRATED:
            return self.tilt_bonus_integrated
        return self.tilt_bonus_standard


# =============================================================================
# Tariff Registry
# =============================================================================

class TariffRegistry:
    """Registry of available tariff configurations."""
    
    @staticmethod
    def get_2025() -> TariffRates:
        """
        Get 2025 tariff rates.
        
        Source: https://pronovo.ch/de/services/tarifrechner/
        Verified: December 2024
        """
        return TariffRates(
            year="2025",
            source_url="https://pronovo.ch/de/services/tarifrechner/",
            
            # Standard EIV (attached/freestanding)
            standard_tier1=360.0,
            standard_tier2=300.0,
            standard_tier3=280.0,
            
            # Integrated EIV (building-integrated)
            integrated_tier1=400.0,
            integrated_tier2=330.0,
            integrated_tier3=310.0,
            
            # HEIV (full feed-in)
            feed_in_tier1=450.0,
            feed_in_tier2=350.0,
            feed_in_tier3=250.0,
            
            # Bonus rates
            tilt_bonus_standard=200.0,
            tilt_bonus_integrated=400.0,
            altitude_bonus=100.0,
            parking_bonus=250.0
        )
    
    @staticmethod
    def get_latest() -> TariffRates:
        """Get the most recent tariff configuration."""
        return TariffRegistry.get_2025()


# =============================================================================
# Calculator Protocol (Interface)
# =============================================================================

class SubsidyCalculator(Protocol):
    """Protocol for subsidy calculation services."""
    
    def calculate(self, config: PronovoSystemConfig) -> SubsidyResult:
        """Calculate subsidy for the given configuration."""
        ...


# =============================================================================
# Core Calculator Implementation
# =============================================================================

class PronovoCalculator:
    """
    Professional calculator for Swiss Pronovo PV subsidies.
    
    Supports:
        - Standard EIV (with self-consumption)
        - HEIV (full feed-in, no self-consumption)
        - Integrated installation premium rates
        - Tilt angle bonus (>= 75 degrees)
        - Altitude bonus (>= 1500m)
        - Parking area bonus (>= 100 kWp)
    
    Example:
        >>> calculator = PronovoCalculator()
        >>> config = PronovoSystemConfig(capacity_kwp=50.0)
        >>> result = calculator.calculate(config)
        >>> print(f"Total: {result.total:,.2f} CHF")
        Total: 16,800.00 CHF
    """
    
    def __init__(self, tariff: Optional[TariffRates] = None) -> None:
        """
        Initialize calculator with tariff configuration.
        
        Args:
            tariff: Optional tariff rates. Defaults to latest rates.
        """
        self._tariff = tariff or TariffRegistry.get_latest()
    
    @property
    def tariff(self) -> TariffRates:
        """Get the current tariff configuration."""
        return self._tariff
    
    def calculate(self, config: PronovoSystemConfig) -> SubsidyResult:
        """
        Calculate EIV subsidy based on system configuration.
        
        Args:
            config: System configuration with capacity and options
            
        Returns:
            SubsidyResult with complete breakdown
        """
        installation_class = InstallationClass.from_config(config)
        
        # Calculate base contribution (tiered)
        base_contribution = self._calculate_tiered_contribution(
            capacity=config.capacity_kwp,
            installation_class=installation_class
        )
        
        # Calculate bonuses
        tilt_bonus = self._calculate_tilt_bonus(config, installation_class)
        altitude_bonus = self._calculate_altitude_bonus(config)
        parking_bonus = self._calculate_parking_bonus(config)
        
        # Calculate total
        total = base_contribution + tilt_bonus + altitude_bonus + parking_bonus
        
        return SubsidyResult(
            base_contribution=round(base_contribution, 2),
            tilt_bonus=round(tilt_bonus, 2),
            altitude_bonus=round(altitude_bonus, 2),
            parking_bonus=round(parking_bonus, 2),
            total=round(total, 2),
            tariff_year=self._tariff.year,
            installation_class=installation_class
        )
    
    def _calculate_tiered_contribution(
        self,
        capacity: float,
        installation_class: InstallationClass
    ) -> float:
        """Calculate tiered base contribution."""
        r1, r2, r3 = self._tariff.get_rates(installation_class)
        contribution = 0.0
        
        # Tier 1: 0-30 kWp
        tier1_amount = min(capacity, TierThreshold.TIER_1_MAX)
        contribution += tier1_amount * r1
        
        # Tier 2: 30-100 kWp
        if capacity > TierThreshold.TIER_1_MAX:
            tier2_amount = min(
                capacity - TierThreshold.TIER_1_MAX,
                TierThreshold.TIER_2_MAX - TierThreshold.TIER_1_MAX
            )
            contribution += tier2_amount * r2
        
        # Tier 3: > 100 kWp
        if capacity > TierThreshold.TIER_2_MAX:
            tier3_amount = capacity - TierThreshold.TIER_2_MAX
            contribution += tier3_amount * r3
        
        return contribution
    
    def _calculate_tilt_bonus(
        self,
        config: PronovoSystemConfig,
        installation_class: InstallationClass
    ) -> float:
        """Calculate tilt angle bonus for steep installations."""
        if config.tilt_angle_degrees is None:
            return 0.0
        
        if config.tilt_angle_degrees < BonusThreshold.TILT_ANGLE_MIN:
            return 0.0
        
        rate = self._tariff.get_tilt_bonus_rate(installation_class)
        return config.capacity_kwp * rate
    
    def _calculate_altitude_bonus(self, config: PronovoSystemConfig) -> float:
        """Calculate altitude bonus for high-altitude installations."""
        if config.altitude_meters is None:
            return 0.0
        
        if config.altitude_meters < BonusThreshold.ALTITUDE_MIN:
            return 0.0
        
        return config.capacity_kwp * self._tariff.altitude_bonus
    
    def _calculate_parking_bonus(self, config: PronovoSystemConfig) -> float:
        """Calculate parking area bonus for large parking installations."""
        if not config.parking_area_coverage:
            return 0.0
        
        if config.capacity_kwp < BonusThreshold.PARKING_CAPACITY_MIN:
            return 0.0
        
        return config.capacity_kwp * self._tariff.parking_bonus


# =============================================================================
# Convenience Function
# =============================================================================

def calculate_subsidy(
    capacity_kwp: float,
    category: SystemCategory = SystemCategory.ATTACHED_ROOF,
    has_self_consumption: bool = True,
    altitude_meters: Optional[float] = None,
    tilt_angle_degrees: Optional[float] = None,
    parking_area_coverage: bool = False
) -> SubsidyResult:
    """
    Convenience function for quick subsidy calculation.
    
    Args:
        capacity_kwp: System capacity in kilowatts peak
        category: System mounting category
        has_self_consumption: True for EIV, False for HEIV
        altitude_meters: Optional altitude for high-altitude bonus
        tilt_angle_degrees: Optional tilt angle for steep installation bonus
        parking_area_coverage: True if covering parking area
        
    Returns:
        SubsidyResult with breakdown and total
        
    Example:
        >>> result = calculate_subsidy(10.0)
        >>> print(f"Subsidy: {result.total:,.0f} CHF")
        Subsidy: 3,600 CHF
    """
    calculator = PronovoCalculator()
    config = PronovoSystemConfig(
        capacity_kwp=capacity_kwp,
        installation_type=category,
        has_self_consumption=has_self_consumption,
        altitude_meters=altitude_meters,
        tilt_angle_degrees=tilt_angle_degrees,
        parking_area_coverage=parking_area_coverage
    )
    return calculator.calculate(config)


# =============================================================================
# Backward Compatibility Aliases
# =============================================================================

# Legacy class name aliases
PronovoSubsidyService = PronovoCalculator
TariffConfiguration = TariffRates
