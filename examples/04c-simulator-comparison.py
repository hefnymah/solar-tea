"""
Example: Simulator Comparison (PySAM vs Simple)
=================================================
Compares the two battery simulator backends in terms of:
1. Execution time
2. Results accuracy
3. Self-sufficiency/consumption metrics
"""

import sys
import time
from pathlib import Path
import pandas as pd

# Ensure project root is in path
try:
    project_root = Path(__file__).parent.parent
except NameError:
    project_root = Path.cwd()
sys.path.insert(0, str(project_root))

from eclipse.battery import BatterySizer
from eclipse.synthetic import generate_scenario

# ==========================================
# Configuration
# ==========================================
PV_SIZE_KWP = 100.0
DAILY_LOAD_KWH = 250.0
TARGET_SOC_MAX = 90.0
MIN_SOC = 10.0

print("=" * 70)
print("SIMULATOR COMPARISON: PySAM vs Simple")
print("=" * 70)

# ==========================================
# Generate Test Data
# ==========================================
print("\n>>> Generating annual scenario...")
load_kw, pv_kw = generate_scenario(
    start_date='2024-01-01',
    days=365,
    daily_load=DAILY_LOAD_KWH,
    pv_size_kwp=PV_SIZE_KWP,
    freq='15min',
    profile_type='residential',
    include_anomalies=True
)
print(f"    Data points: {len(load_kw)}")

# ==========================================
# Test: Simple Simulator
# ==========================================
print("\n>>> Testing SIMPLE simulator...")
sizer_simple = BatterySizer(
    pv_kwp=PV_SIZE_KWP,
    daily_load_kwh=DAILY_LOAD_KWH,
    max_soc=TARGET_SOC_MAX,
    min_soc=MIN_SOC,
    simulator='simple'
)

start_time = time.time()
result_simple = sizer_simple.recommend(load_kw, pv_kw, target='optimal')
time_simple = time.time() - start_time

print(f"    Time: {time_simple:.2f}s")
print(f"    Recommended: {result_simple.recommended_kwh} kWh")
print(f"    Self-Sufficiency: {result_simple.self_sufficiency_pct:.1f}%")
print(f"    Self-Consumption: {result_simple.self_consumption_pct:.1f}%")

# ==========================================
# Test: PySAM Simulator
# ==========================================
print("\n>>> Testing PYSAM simulator...")
sizer_pysam = BatterySizer(
    pv_kwp=PV_SIZE_KWP,
    daily_load_kwh=DAILY_LOAD_KWH,
    max_soc=TARGET_SOC_MAX,
    min_soc=MIN_SOC,
    simulator='pysam'
)

start_time = time.time()
result_pysam = sizer_pysam.recommend(load_kw, pv_kw, target='optimal')
time_pysam = time.time() - start_time

print(f"    Time: {time_pysam:.2f}s")
print(f"    Recommended: {result_pysam.recommended_kwh} kWh")
print(f"    Self-Sufficiency: {result_pysam.self_sufficiency_pct:.1f}%")
print(f"    Self-Consumption: {result_pysam.self_consumption_pct:.1f}%")

# ==========================================
# Comparison Summary
# ==========================================
print("\n" + "=" * 70)
print("COMPARISON SUMMARY")
print("=" * 70)

print(f"\n{'Metric':<25} {'Simple':<15} {'PySAM':<15} {'Difference':<15}")
print("-" * 70)
print(f"{'Execution Time (s)':<25} {time_simple:<15.2f} {time_pysam:<15.2f} {time_pysam/time_simple:.1f}x slower")
print(f"{'Recommended Size (kWh)':<25} {result_simple.recommended_kwh:<15.1f} {result_pysam.recommended_kwh:<15.1f} {result_pysam.recommended_kwh - result_simple.recommended_kwh:+.1f}")
print(f"{'Self-Sufficiency (%)':<25} {result_simple.self_sufficiency_pct:<15.1f} {result_pysam.self_sufficiency_pct:<15.1f} {result_pysam.self_sufficiency_pct - result_simple.self_sufficiency_pct:+.1f}")
print(f"{'Self-Consumption (%)':<25} {result_simple.self_consumption_pct:<15.1f} {result_pysam.self_consumption_pct:<15.1f} {result_pysam.self_consumption_pct - result_simple.self_consumption_pct:+.1f}")
print(f"{'Grid Import (kWh/yr)':<25} {result_simple.grid_import_kwh:<15.0f} {result_pysam.grid_import_kwh:<15.0f} {result_pysam.grid_import_kwh - result_simple.grid_import_kwh:+.0f}")
print(f"{'Grid Export (kWh/yr)':<25} {result_simple.grid_export_kwh:<15.0f} {result_pysam.grid_export_kwh:<15.0f} {result_pysam.grid_export_kwh - result_simple.grid_export_kwh:+.0f}")

print("\n" + "=" * 70)
print("CONCLUSION")
print("=" * 70)
speedup = time_pysam / time_simple if time_simple > 0 else 1
if result_simple.recommended_kwh == result_pysam.recommended_kwh:
    print(f"✅ Both simulators recommend the SAME battery size!")
    print(f"   Simple is {speedup:.1f}x faster - use it for quick sizing sweeps.")
else:
    print(f"⚠️  Different recommendations: Simple={result_simple.recommended_kwh}kWh, PySAM={result_pysam.recommended_kwh}kWh")
    print(f"   PySAM is more accurate but {speedup:.1f}x slower.")
    print(f"   Recommendation: Use Simple for exploration, PySAM for final verification.")

print("\nDone.")
