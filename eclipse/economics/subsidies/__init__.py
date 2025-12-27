"""
Economics Subsidies Package
===========================

Subsidy calculation services for different markets.

Available:
    - PronovoCalculator: Swiss PV subsidy calculator (main service)
    - PronovoSystemConfig: Input configuration for calculation
    - SubsidyResult: Output result with breakdown
    - TariffRates: Tariff configuration
    - calculate_subsidy: Convenience function
    
Backward Compatible:
    - PronovoSubsidyService: Alias for PronovoCalculator
    - TariffConfiguration: Alias for TariffRates
"""

from eclipse.economics.subsidies.pronovo import (
    # Core classes
    PronovoCalculator,
    PronovoSystemConfig,
    SubsidyResult,
    TariffRates,
    TariffRegistry,
    InstallationClass,
    
    # Convenience
    calculate_subsidy,
    
    # Backward compatibility
    PronovoSubsidyService,
    TariffConfiguration,
)

__all__ = [
    # Core
    'PronovoCalculator',
    'PronovoSystemConfig',
    'SubsidyResult',
    'TariffRates',
    'TariffRegistry',
    'InstallationClass',
    'calculate_subsidy',
    
    # Legacy aliases
    'PronovoSubsidyService',
    'TariffConfiguration',
]
