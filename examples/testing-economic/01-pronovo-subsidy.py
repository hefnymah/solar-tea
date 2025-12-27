#!/usr/bin/env python3
"""
Example 06: Pronovo Subsidy Calculation
=======================================
Demonstrates Swiss PV subsidy calculation using the Pronovo service.

This example shows:
- Basic subsidy calculation for different system sizes
- Integrated vs Attached installation type comparison
- HEIV (Volleinspeisung) vs Standard EIV rates
- Alpine systems with bonuses (tilt, altitude)

Reference: https://pronovo.ch/de/services/tarifrechner/
"""


import sys
import os
from pathlib import Path
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

# Ensure project root is in path
try:
    project_root = Path(__file__).parent.parent
except NameError:
    project_root = Path.cwd()
sys.path.insert(0, str(project_root))

from eclipse.economics.subsidies import (
    PronovoSubsidyService,
    PronovoSystemConfig,
    SubsidyResult,
    calculate_subsidy,
)
from eclipse.economics.enums import SystemCategory


def print_pronovo_result(config: PronovoSystemConfig, result: SubsidyResult):
    """
    Print Pronovo subsidy calculation with input parameters and output breakdown.
    Matches official Pronovo website format with all items shown (even if None/False).
    """
    # Input parameters (matching Pronovo website)
    print("\n    INPUT PARAMETERS:")
    print(f"    ├─ Capacity (Leistung in kWp):                  {config.capacity_kwp:.1f} kWp")
    print(f"    ├─ Installation Type (Art des Anlagenbaues):    {config.installation_type.value}")
    print(f"    ├─ Tilt Angle ≥75° (Neigungswinkel):            {config.tilt_angle_degrees if config.tilt_angle_degrees else 'None'}")
    print(f"    ├─ Altitude ≥1500m (Höhenbonus):                {config.altitude_meters if config.altitude_meters else 'None'}")
    print(f"    ├─ Parking Area Bonus (Parkflächenbonus):       {config.parking_area_coverage}")
    print(f"    └─ No Self-Consumption (kein Eigenverbrauch):   {not config.has_self_consumption}")
    
    # Output breakdown (matching Pronovo calculator)
    print("\n    SUBSIDY BREAKDOWN (Vergütungsdetails):")
    print(f"    ├─ Base Contribution (Leistungsbeitrag):       {result.base_contribution:>10,.2f} CHF")
    print(f"    ├─ Tilt Angle Bonus (Neigungswinkelbonus):     {result.tilt_bonus:>10,.2f} CHF")
    print(f"    ├─ Altitude Bonus (Höhenbonus):                {result.height_bonus:>10,.2f} CHF")
    print(f"    ├─ Parking Area Bonus (Parkflächenbonus):      {result.parking_bonus:>10,.2f} CHF")
    print(f"    └─ Total Subsidy (Förderbeitrag):              {result.total_subsidy:>10,.2f} CHF")


print("=" * 70)
print("PRONOVO SUBSIDY CALCULATOR - SWISS PV SUBSIDIES 2025")
print("=" * 70)

# Initialize service with default 2025 rates
service = PronovoSubsidyService()

#%%
# =========================================================================
# SCENARIO 1: Standard Residential System (10 kWp)
# =========================================================================
print("\n>>> SCENARIO 1: Standard Residential System (10 kWp)")
print("-" * 50)

config_10 = PronovoSystemConfig(
    capacity_kwp=10.0,
    installation_type=SystemCategory.ATTACHED_ROOF,
    has_self_consumption=True,
    tilt_angle_degrees=75.0,
    altitude_meters=1600.0,
    parking_area_coverage=True
)
result_10 = service.calculate(config_10)
print_pronovo_result(config_10, result_10)

#%%
# =========================================================================
# SCENARIO 2: Commercial System (50 kWp)
# =========================================================================
print("\n>>> SCENARIO 2: Commercial System (50 kWp)")
print("-" * 50)

config_50 = PronovoSystemConfig(
    capacity_kwp=50.0,
    installation_type=SystemCategory.ATTACHED_ROOF
)
result_50 = service.calculate(config_50)
print_pronovo_result(config_50, result_50)

#%%
# =========================================================================
# SCENARIO 3: Integrated vs Attached (70 kWp)
# =========================================================================
print("\n>>> SCENARIO 3: Integrated vs Attached (70 kWp)")
print("-" * 50)

config_attached = PronovoSystemConfig(
    capacity_kwp=70.0,
    installation_type=SystemCategory.ATTACHED_ROOF
)
result_attached = service.calculate(config_attached)

config_integrated = PronovoSystemConfig(
    capacity_kwp=70.0,
    installation_type=SystemCategory.INTEGRATED_ROOF
)
result_integrated = service.calculate(config_integrated)

print("    >>> ATTACHED (Aufdach):")
print_pronovo_result(config_attached, result_attached)
print("\n    >>> INTEGRATED (Indach):")
print_pronovo_result(config_integrated, result_integrated)
print(f"\n    ➜ Integrated Premium: +{result_integrated.total_subsidy - result_attached.total_subsidy:,.2f} CHF")

#%%
# =========================================================================
# SCENARIO 4: Large System with Parking Bonus (100 kWp)
# =========================================================================
print("\n>>> SCENARIO 4: Large System with Parking Bonus (100 kWp)")
print("-" * 50)

config_100 = PronovoSystemConfig(
    capacity_kwp=100.0,
    installation_type=SystemCategory.FREE_STANDING,
    parking_area_coverage=True
)
result_100 = service.calculate(config_100)
print_pronovo_result(config_100, result_100)

#%%
# =========================================================================
# SCENARIO 5: Alpine Installation (25 kWp with bonuses)
# =========================================================================
print("\n>>> SCENARIO 5: Alpine Installation (25 kWp)")
print("-" * 50)

config_alpine = PronovoSystemConfig(
    capacity_kwp=25.0,
    installation_type=SystemCategory.INTEGRATED_ROOF,
    altitude_meters=1600.0,
    tilt_angle_degrees=80.0
)
result_alpine = service.calculate(config_alpine)
print_pronovo_result(config_alpine, result_alpine)

#%%
# =========================================================================
# SCENARIO 6: HEIV vs Standard EIV (10 kWp)
# =========================================================================
print("\n>>> SCENARIO 6: HEIV vs Standard EIV (10 kWp)")
print("-" * 50)

config_eiv = PronovoSystemConfig(capacity_kwp=10.0, has_self_consumption=True)
result_eiv = service.calculate(config_eiv)

config_heiv = PronovoSystemConfig(capacity_kwp=10.0, has_self_consumption=False)
result_heiv = service.calculate(config_heiv)

print("    >>> Standard EIV (with self-consumption):")
print_pronovo_result(config_eiv, result_eiv)
print("\n    >>> HEIV (Volleinspeisung):")
print_pronovo_result(config_heiv, result_heiv)
print(f"\n    ➜ HEIV Premium: +{result_heiv.total_subsidy - result_eiv.total_subsidy:,.2f} CHF")

print("\n" + "=" * 70)
print("Done. Source: Pronovo 2025 Tariff Rates")
print("=" * 70)

