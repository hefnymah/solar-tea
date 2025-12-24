#!/usr/bin/env python3
"""
Example: EnergySizer Usage
==========================

This script demonstrates how to use the EnergySizer class for PV system sizing.

Run from the project root:
    python examples/00-energy-sizer.py
"""

import sys
import os
from pathlib import Path

# Add eclipse module to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from eclipse.pvsim.kwp_sizer import kWpSizer, EnergyProfile, kWpSizingResult, size_pv_kwp

#%%
# Handle both script and interactive execution
try:
    project_root = Path(__file__).parent.parent
except NameError:
    project_root = Path.cwd()
sys.path.insert(0, str(project_root))

output_dir = project_root / "examples" / "outputs" / "example-01"
os.makedirs(output_dir, exist_ok=True)
#%%
print("=" * 60)
print("kWpSizer Usage Examples")
print("=" * 60)

#%%------------------------------------------------------------------------
# Example 1: Basic usage - PSH estimated from latitude
# -------------------------------------------------------------------------
print("\n--- Example 1: Basic Usage (PSH Estimated from Latitude) ---")

# Initialize sizer for Zurich - PSH will be auto-estimated from latitude
sizer = kWpSizer(
    latitude=47.3769,
    longitude=8.5417
    # peak_sun_hours not provided - will be estimated automatically
)

# Size from daily consumption (30 kWh/day)
# Default self-sufficiency is 80% (covers 80% of consumption from PV)
self_sufficiency = 0.80
result = sizer.size_from_daily(30, self_sufficiency=self_sufficiency)

print(f"Location: ({sizer.latitude}, {sizer.longitude})")
print(f"Peak Sun Hours (estimated): {sizer.peak_sun_hours} h/day")
print(f"Daily Consumption: 30 kWh")
print(f"Target Self-Sufficiency: {self_sufficiency:.0%} (PV covers {self_sufficiency:.0%} of load)")
print(f"Recommended Size: {result.recommended_kwp} kWp")
print(f"Specific Yield: {result.specific_yield} kWh/kWp/year")
print(f"Est. Annual Generation: {result.estimated_annual_generation} kWh")

#%%------------------------------------------------------------------------
# Example 2: Using EnergyProfile for more control
# -------------------------------------------------------------------------
print("\n--- Example 2: Using EnergyProfile ---")

# Create a detailed energy profile
profile = EnergyProfile(
    daily_kwh=25,
    peak_demand_kw=5.0  # Optional: max instantaneous demand
)

print(f"Profile: {profile.daily_kwh} kWh/day, {profile.annual_kwh} kWh/year")

# Size with custom self-sufficiency target (90%)
result = sizer.size_system(profile, self_sufficiency=0.9)

print(f"Target Self-Sufficiency: 90%")
print(f"Recommended: {result.recommended_kwp} kWp")
print(f"Annual Generation: {result.estimated_annual_generation} kWh")

#%%------------------------------------------------------------------------
# Example 3: Auto-estimate PSH from latitude
# -------------------------------------------------------------------------

print("\n--- Example 3: Auto-Estimate PSH from Latitude ---")

# Don't provide PSH - let it be estimated from latitude
sizer_madrid = kWpSizer(latitude=40.4168, longitude=-3.7038)

print(f"Madrid: lat={sizer_madrid.latitude}")
print(f"Estimated PSH: {sizer_madrid.peak_sun_hours} h/day")

result_madrid = sizer_madrid.size_from_daily(30)
print(f"Recommended for 30 kWh/day: {result_madrid.recommended_kwp} kWp")

#%%------------------------------------------------------------------------
# Example 4: Calculate required kWp for 100% offset
# -------------------------------------------------------------------------
print("\n--- Example 4: Required kWp for Full Offset ---")

annual_consumption = 12000  # kWh/year
required = sizer.required_kwp_for_offset(annual_consumption, offset_target=1.0)

print(f"Annual Consumption: {annual_consumption} kWh")
print(f"Required for 100% offset: {required} kWp")

# 80% offset
required_80 = sizer.required_kwp_for_offset(annual_consumption, offset_target=0.8)
print(f"Required for 80% offset: {required_80} kWp")

#%%------------------------------------------------------------------------
# Example 5: Estimate generation for a given system size
# -------------------------------------------------------------------------
print("\n--- Example 5: Estimate Generation ---")

system_size = 10.0  # kWp
gen = sizer.estimate_generation(system_size)

print(f"System Size: {system_size} kWp")
print(f"Estimated Annual Generation: {gen:.0f} kWh")

#%%------------------------------------------------------------------------
# Example 6: Using the helper function
# -------------------------------------------------------------------------
print("\n--- Example 6: Helper Function (size_pv_kwp) ---")

# Quick sizing without creating class instances
kwp1 = size_pv_kwp(daily_kwh=30, latitude=47.38, longitude=8.54, peak_sun_hours=3.8)
kwp2 = size_pv_kwp(daily_kwh=15, latitude=47.38, longitude=8.54, peak_sun_hours=3.8, self_sufficiency=0.9)

print(f"30 kWh/day, 80% SS: {kwp1} kWp")
print(f"15 kWh/day, 90% SS: {kwp2} kWp")

#%%------------------------------------------------------------------------
# Example 7: Full SizingResult object
# -------------------------------------------------------------------------
print("\n--- Example 7: Full SizingResult Output ---")

result_full = sizer.size_from_annual(10950)  # ~30 kWh/day
print(result_full)  # Uses __str__ for formatted output

#%%------------------------------------------------------------------------
# Example 8: Advanced PVGIS-based sizing (uses real irradiance data)
# -------------------------------------------------------------------------
print("\n--- Example 8: Advanced PVGIS Sizing (Real Data from API) ---")

# This fetches real TMY data from PVGIS and simulates a 1kWp reference system
# to get accurate specific yield for the exact location
print("Fetching real irradiance data from PVGIS...")

try:
    result_pvgis = sizer.size_from_daily_pvgis(
        daily_kwh=30,
        self_sufficiency=0.80,
        tilt=30.0,           # Module tilt angle
        azimuth=180.0,       # South-facing
        performance_ratio=0.85
    )
    
    print(f"Location: ({result_pvgis.latitude}, {result_pvgis.longitude})")
    print(f"Specific Yield (from simulation): {result_pvgis.specific_yield} kWh/kWp/year")
    print(f"Equivalent PSH: {result_pvgis.peak_sun_hours} h/day")
    print(f"Recommended Size: {result_pvgis.recommended_kwp} kWp")
    print(f"Est. Annual Generation: {result_pvgis.estimated_annual_generation} kWh")
    
    # Compare simple vs PVGIS
    print("\n  Comparison: Simple Estimate vs PVGIS:")
    print(f"    Simple: {result.recommended_kwp} kWp (PSH={sizer.peak_sun_hours})")
    print(f"    PVGIS:  {result_pvgis.recommended_kwp} kWp (Yield={result_pvgis.specific_yield})")
except RuntimeError as e:
    print(f"PVGIS fetch failed: {e}")
    print("(This requires internet connection)")

print("\n" + "=" * 60)
print("Examples Complete!")
print("=" * 60)


