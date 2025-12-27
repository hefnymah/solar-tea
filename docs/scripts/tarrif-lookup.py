#!/usr/bin/env python3
"""
PVTariff Lookup Script
Fetches PV feed-in tariff data for a Swiss address using the VESE pvtarif API.

Usage:
    python pvtarif_lookup.py "Bahnhofstrasse 1, 8001 Zürich"
    
Requirements:
    - requests library (pip install requests)
    - A valid VESE pvtarif API license key
"""

import requests
import sys
import json
from datetime import datetime


# Configuration - Replace with your actual API key from VESE
PVTARIF_API_KEY = "2wfwveqs85n4thbykk44uj3ewf2nwdhsoukmb2j0"  # Get your key at info@vese.ch

# API Endpoints
GEO_ADMIN_API = "https://api3.geo.admin.ch/rest/services/api/SearchServer"
PVTARIF_MUNI_API = "https://opendata.vese.ch/pvtarif/api/getData/muni"
PVTARIF_EVU_API = "https://opendata.vese.ch/pvtarif/api/getData/evu"


def geocode_address(address: str) -> dict:
    """
    Geocode a Swiss address using the geo.admin.ch API.
    Returns municipality information including BFS number (idofs).
    
    Uses a two-step process:
    1. Geocode the address to get coordinates
    2. Use identify API to get municipality info from coordinates
    """
    # Step 1: Geocode the address
    params = {
        "searchText": address,
        "type": "locations",
        "limit": 1,
        "sr": 4326  # WGS84 coordinate system
    }
    
    response = requests.get(GEO_ADMIN_API, params=params)
    response.raise_for_status()
    
    data = response.json()
    
    if not data.get("results"):
        raise ValueError(f"Could not find address: {address}")
    
    result = data["results"][0]
    attrs = result.get("attrs", {})
    
    lat = attrs.get("lat")
    lon = attrs.get("lon")
    label = attrs.get("label", "")
    
    if not lat or not lon:
        raise ValueError(f"Could not get coordinates for address: {address}")
    
    # Step 2: Use identify API to get municipality info from coordinates
    identify_url = "https://api3.geo.admin.ch/rest/services/api/MapServer/identify"
    identify_params = {
        "geometryType": "esriGeometryPoint",
        "geometry": f"{lon},{lat}",
        "sr": 4326,
        "layers": "all:ch.swisstopo.swissboundaries3d-gemeinde-flaeche.fill",
        "tolerance": 0,
        "returnGeometry": "false"
    }
    
    identify_response = requests.get(identify_url, params=identify_params)
    identify_response.raise_for_status()
    
    identify_data = identify_response.json()
    
    # Find the current year municipality entry
    municipality = ""
    bfs_number = None
    canton = ""
    
    for result in identify_data.get("results", []):
        attrs = result.get("attributes", {})
        # Look for current year entry (is_current_jahr = true)
        if attrs.get("is_current_jahr") == True:
            municipality = attrs.get("gemname", "")
            bfs_number = attrs.get("gde_nr")
            canton = attrs.get("kanton", "")
            break
    
    # Fallback: use the first result if no current year entry found
    if not bfs_number and identify_data.get("results"):
        first_result = identify_data["results"][0]
        attrs = first_result.get("attributes", {})
        municipality = attrs.get("gemname", "")
        bfs_number = attrs.get("gde_nr")
        canton = attrs.get("kanton", "")
    
    return {
        "label": label,
        "municipality": municipality,
        "bfs_number": bfs_number,
        "canton": canton,
        "lat": lat,
        "lon": lon
    }


def get_evus_for_municipality(bfs_number: int) -> list:
    """
    Get all energy utilities (EVUs) operating in a municipality.
    """
    params = {
        "idofs": str(bfs_number),
        "licenseKey": PVTARIF_API_KEY
    }
    
    response = requests.get(PVTARIF_MUNI_API, params=params)
    response.raise_for_status()
    
    data = response.json()
    
    if not data.get("valid"):
        raise ValueError(f"Invalid response from pvtarif API for municipality {bfs_number}")
    
    return data.get("evus", [])


def get_tariff_data(evu_id: str, year: str = None) -> dict:
    """
    Get tariff data for a specific EVU.
    
    Args:
        evu_id: ElCom number or UID of the EVU
        year: Two-digit year (e.g., "24" for 2024). Defaults to current year.
    """
    if year is None:
        year = str(datetime.now().year)[-2:]  # Get last 2 digits of current year
    
    params = {
        "evuId": evu_id,
        "year": year,
        "licenseKey": PVTARIF_API_KEY
    }
    
    response = requests.get(PVTARIF_EVU_API, params=params)
    response.raise_for_status()
    
    data = response.json()
    
    if not data.get("valid"):
        return None
    
    return data


def format_tariff_summary(tariff: dict) -> str:
    """
    Format tariff data into a readable summary.
    """
    if not tariff:
        return "  No tariff data available"
    
    lines = []
    lines.append(f"  Company: {tariff.get('nomEw', 'N/A')}")
    lines.append(f"  ElCom Number: {tariff.get('nrElcom', 'N/A')}")
    lines.append(f"  UID: {tariff.get('uid', 'N/A')}")
    lines.append(f"  Website: {tariff.get('link', 'N/A')}")
    
    # Feed-in tariffs
    energy1 = tariff.get('energy1', '')
    eco1 = tariff.get('eco1', '')
    if energy1:
        lines.append(f"\n  Feed-in Tariffs (Power Category 1):")
        lines.append(f"    Energy: {energy1} Rp/kWh")
        if eco1:
            lines.append(f"    HKN (Eco): {eco1} Rp/kWh")
        
        # High/Low tariff details
        if tariff.get('htnt') == 'y':
            lines.append(f"    High Tariff (HT): {tariff.get('energy1_ht', 'N/A')} Rp/kWh")
            lines.append(f"    Low Tariff (NT): {tariff.get('energy1_nt', 'N/A')} Rp/kWh")
    
    # Power category 2
    energy2 = tariff.get('energy2', '')
    if energy2:
        power2 = tariff.get('power2', '')
        lines.append(f"\n  Feed-in Tariffs (Power Category 2, >{power2} kVA):")
        lines.append(f"    Energy: {energy2} Rp/kWh")
    
    # Meter costs
    counter_cost = tariff.get('counterCost', '')
    load_curve = tariff.get('loadCurveCost', '')
    if counter_cost or load_curve:
        lines.append(f"\n  Meter Costs:")
        if counter_cost:
            lines.append(f"    Simple Meter: {counter_cost} CHF/month")
        if load_curve:
            lines.append(f"    Load Curve Measurement: {load_curve} CHF/month")
    
    return "\n".join(lines)


def lookup_pv_tariff(address: str, year: str = None) -> None:
    """
    Main function to lookup PV tariff for an address.
    """
    print(f"\n{'='*60}")
    print(f"PV Tariff Lookup for: {address}")
    print(f"{'='*60}\n")
    
    # Step 1: Geocode the address
    print("Step 1: Geocoding address...")
    try:
        location = geocode_address(address)
        print(f"  Found: {location['label']}")
        print(f"  Municipality: {location['municipality']} (BFS: {location['bfs_number']})")
        print(f"  Canton: {location['canton']}")
    except Exception as e:
        print(f"  Error: {e}")
        return
    
    if not location['bfs_number']:
        print("  Error: Could not determine BFS municipality number")
        return
    
    # Step 2: Get EVUs for the municipality
    print(f"\nStep 2: Finding energy utilities in {location['municipality']}...")
    try:
        evus = get_evus_for_municipality(location['bfs_number'])
        print(f"  Found {len(evus)} energy utility/utilities")
    except Exception as e:
        print(f"  Error: {e}")
        return
    
    if not evus:
        print("  No energy utilities found for this municipality")
        return
    
    # Step 3: Get tariff data for each EVU
    year_display = year if year else str(datetime.now().year)[-2:]
    print(f"\nStep 3: Fetching tariff data for year 20{year_display}...")
    
    for i, evu in enumerate(evus, 1):
        print(f"\n--- EVU {i}: {evu.get('Name', 'Unknown')} ---")
        print(f"  ElCom Number: {evu.get('nrElcom', 'N/A')}")
        print(f"  UID: {evu.get('uid', 'N/A')}")
        
        try:
            tariff = get_tariff_data(evu.get('nrElcom', ''), year)
            print(format_tariff_summary(tariff))
        except Exception as e:
            print(f"  Error fetching tariff: {e}")
    
    print(f"\n{'='*60}")
    print("Lookup complete!")
    print(f"{'='*60}\n")


def main():
    if len(sys.argv) < 2:
        print("Usage: python pvtarif_lookup.py <address> [year]")
        print("Example: python pvtarif_lookup.py \"Bahnhofstrasse 1, 8001 Zürich\"")
        print("Example with year: python pvtarif_lookup.py \"Bahnhofstrasse 1, 8001 Zürich\" 24")
        sys.exit(1)
    
    address = sys.argv[1]
    year = sys.argv[2] if len(sys.argv) > 2 else None
    
    if PVTARIF_API_KEY == "your_license_key_here":
        print("\n⚠️  WARNING: You need to set your VESE pvtarif API key!")
        print("   Request a free key at info@vese.ch")
        print("   Then update PVTARIF_API_KEY in this script.\n")
    
    lookup_pv_tariff(address, year)


if __name__ == "__main__":
    main()
