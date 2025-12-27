#!/usr/bin/env python3
"""
Swiss Tariff Service (OOP Version)
==================================
A service for fetching Swiss electricity tariffs:
- Consumption prices from ElCom SPARQL API (what user pays utility)
- Feed-in tariffs from VESE PVTarif API (what utility pays producer)

Supports address-based lookup for real market prices.

Usage:
    from tariff_service import TariffService, AddressLookup
    
    # Initialize service (API key from .env file)
    service = TariffService()
    
    # Look up address
    address_info = AddressLookup().search("Bahnhofstrasse 10, Zürich")
    
    # Get tariffs
    tariffs = service.get_tariffs_for_municipality(address_info.bfs_id)

Requirements:
    pip install requests python-dotenv pandas
"""

import os
from dataclasses import dataclass, field
from typing import Optional, List, Dict, Any
from datetime import datetime
import requests



# =============================================================================
# CONFIGURATION
# =============================================================================

# API Configuration
VESE_API_KEY = "2wfwveqs85n4thbykk44uj3ewf2nwdhsoukmb2j0"
VESE_BASE_URL = "https://opendata.vese.ch/pvtarif/api/getData"
GEO_API = "https://api3.geo.admin.ch/rest/services/api"
ELCOM_SPARQL = "https://ld.admin.ch/query"

# Available years for historical data
AVAILABLE_YEARS = ['2018', '2019', '2020', '2021', '2022', '2023', '2024', '2025']

# Household profiles for ElCom
HOUSEHOLD_PROFILES = {
    "H1": "1,600 kWh/yr (1-room apartment)",
    "H2": "2,500 kWh/yr (2-room apartment)",
    "H3": "4,500 kWh/yr (4-room apartment)",
    "H4": "4,500 kWh/yr + cooking (typical household)",
    "H5": "7,500 kWh/yr (5-room house)",
    "H6": "25,000 kWh/yr (house with heat pump)",
    "H7": "13,000 kWh/yr (house with heat pump, no warm water)",
    "H8": "7,500 kWh/yr (house with cooking, heat pump)",
}


# =============================================================================
# DATA CLASSES
# =============================================================================

@dataclass
class MunicipalityInfo:
    """Information about a Swiss municipality."""
    bfs_id: str
    name: str
    canton: str
    lat: Optional[float] = None
    lon: Optional[float] = None


@dataclass
class EnergyProvider:
    """Information about an energy provider (EVU)."""
    elcom_id: str
    name: str
    additional_info: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ConsumptionPrice:
    """Electricity consumption price breakdown."""
    operator_name: str
    total_rp_kwh: float  # Total price in Rappen/kWh
    energy_rp_kwh: Optional[float] = None  # Energy component
    grid_rp_kwh: Optional[float] = None  # Grid usage
    fee_rp_kwh: Optional[float] = None  # Fees
    levy_rp_kwh: Optional[float] = None  # Aid fee (KEV)
    year: str = ""
    profile: str = ""
    
    @property
    def total_chf_kwh(self) -> float:
        """Total price in CHF/kWh."""
        return self.total_rp_kwh / 100
    
    @property
    def energy_chf_kwh(self) -> Optional[float]:
        """Energy component in CHF/kWh."""
        return self.energy_rp_kwh / 100 if self.energy_rp_kwh else None


@dataclass
class FeedInTariff:
    """Feed-in tariff for solar producers."""
    provider_name: str
    energy_rp_kwh: Optional[float] = None  # Base energy rate
    peak_ht_rp_kwh: Optional[float] = None  # Peak rate (High Tariff)
    offpeak_nt_rp_kwh: Optional[float] = None  # Off-peak rate (Low Tariff)
    eco_bonus_rp_kwh: Optional[float] = None  # Green certificate (HKN)
    year: str = ""
    
    @property
    def energy_chf_kwh(self) -> Optional[float]:
        """Energy rate in CHF/kWh."""
        return self.energy_rp_kwh / 100 if self.energy_rp_kwh else None
    
    @property
    def best_rate_rp_kwh(self) -> float:
        """Best available rate in Rappen/kWh."""
        rates = [r for r in [self.energy_rp_kwh, self.peak_ht_rp_kwh] if r]
        return max(rates) if rates else 0.0


@dataclass
class TariffSummary:
    """Combined tariff summary for a location."""
    municipality: MunicipalityInfo
    consumption_prices: List[ConsumptionPrice] = field(default_factory=list)
    feedin_tariffs: List[FeedInTariff] = field(default_factory=list)
    year: str = ""
    
    @property
    def best_consumption_price(self) -> Optional[ConsumptionPrice]:
        """Lowest consumption price."""
        if not self.consumption_prices:
            return None
        return min(self.consumption_prices, key=lambda p: p.total_rp_kwh)
    
    @property
    def best_feedin_tariff(self) -> Optional[FeedInTariff]:
        """Highest feed-in tariff."""
        if not self.feedin_tariffs:
            return None
        return max(self.feedin_tariffs, key=lambda t: t.best_rate_rp_kwh)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for ZEV integration."""
        cons = self.best_consumption_price
        feedin = self.best_feedin_tariff
        
        return {
            'municipality_name': self.municipality.name,
            'bfs_id': self.municipality.bfs_id,
            'year': self.year,
            # Consumption (what ZEV members pay to utility without PV)
            'consumption_total_rp_kwh': cons.total_rp_kwh if cons else None,
            'consumption_energy_rp_kwh': cons.energy_rp_kwh if cons else None,
            'consumption_total_chf_kwh': cons.total_chf_kwh if cons else None,
            # Feed-in (what utility pays for excess solar)
            'feedin_energy_rp_kwh': feedin.energy_rp_kwh if feedin else None,
            'feedin_peak_rp_kwh': feedin.peak_ht_rp_kwh if feedin else None,
            'feedin_energy_chf_kwh': feedin.energy_chf_kwh if feedin else None,
            # Spread (utility margin)
            'spread_rp_kwh': (cons.energy_rp_kwh - feedin.energy_rp_kwh) if cons and feedin and cons.energy_rp_kwh and feedin.energy_rp_kwh else None,
        }


@dataclass
class HistoricalData:
    """Historical tariff data for multiple years."""
    municipality: MunicipalityInfo
    years: List[str] = field(default_factory=list)
    consumption_total: List[Optional[float]] = field(default_factory=list)
    consumption_energy: List[Optional[float]] = field(default_factory=list)
    feedin_energy: List[Optional[float]] = field(default_factory=list)
    feedin_ht: List[Optional[float]] = field(default_factory=list)
    
    def to_dataframe(self):
        """Convert to pandas DataFrame."""
        import pandas as pd
        
        df = pd.DataFrame({
            'Year': self.years,
            'Consumption_Total_Rp_kWh': self.consumption_total,
            'Consumption_Energy_Rp_kWh': self.consumption_energy,
            'Feedin_Energy_Rp_kWh': self.feedin_energy,
            'Feedin_Peak_HT_Rp_kWh': self.feedin_ht,
        })
        
        # Calculate spread
        df['Spread_Rp_kWh'] = df['Consumption_Energy_Rp_kWh'] - df['Feedin_Energy_Rp_kWh']
        df.attrs['municipality'] = self.municipality.name
        
        return df


# =============================================================================
# ADDRESS LOOKUP SERVICE
# =============================================================================

class AddressLookup:
    """Service for looking up Swiss addresses and municipalities."""
    
    def __init__(self):
        self.geo_api = GEO_API
    
    def search(self, query: str, limit: int = 5) -> List[Dict[str, Any]]:
        """
        Search for Swiss addresses.
        
        Args:
            query: Address search string
            limit: Maximum results to return
            
        Returns:
            List of address results with coordinates
        """
        url = f"{self.geo_api}/SearchServer"
        params = {
            "searchText": query,
            "type": "locations",
            "origins": "address",
            "limit": limit
        }
        
        try:
            response = requests.get(url, params=params, timeout=10)
            if response.status_code == 200:
                data = response.json()
                results = []
                for r in data.get("results", []):
                    attrs = r.get("attrs", {})
                    results.append({
                        "label": attrs.get("label", "").replace("<b>", "").replace("</b>", ""),
                        "lat": attrs.get("lat"),
                        "lon": attrs.get("lon"),
                        "detail": attrs.get("detail", ""),
                    })
                return results
        except Exception as e:
            print(f"Address search error: {e}")
        return []
    
    def get_municipality(self, lat: float, lon: float) -> Optional[MunicipalityInfo]:
        """
        Get municipality from coordinates.
        
        Args:
            lat: Latitude (WGS84)
            lon: Longitude (WGS84)
            
        Returns:
            MunicipalityInfo or None
        """
        url = f"{self.geo_api}/MapServer/identify"
        params = {
            "geometry": f"{lon},{lat}",
            "geometryType": "esriGeometryPoint",
            "sr": 4326,
            "layers": "all:ch.swisstopo.swissboundaries3d-gemeinde-flaeche.fill",
            "tolerance": 0,
            "returnGeometry": "false"
        }
        
        try:
            response = requests.get(url, params=params, timeout=10)
            if response.status_code == 200:
                data = response.json()
                results = data.get("results", [])
                if results:
                    current = next(
                        (r for r in results if r.get("attributes", {}).get("is_current_jahr")),
                        results[0]
                    )
                    attrs = current.get("attributes", {})
                    return MunicipalityInfo(
                        bfs_id=str(attrs.get("gde_nr", "")),
                        name=attrs.get("gemname", ""),
                        canton=attrs.get("kanton", ""),
                        lat=lat,
                        lon=lon,
                    )
        except Exception as e:
            print(f"Municipality lookup error: {e}")
        return None
    
    def lookup_address(self, address: str) -> Optional[MunicipalityInfo]:
        """
        Full address lookup: search -> get municipality.
        
        Args:
            address: Swiss address string
            
        Returns:
            MunicipalityInfo or None
        """
        results = self.search(address, limit=1)
        if not results:
            return None
        
        first = results[0]
        return self.get_municipality(first["lat"], first["lon"])


# =============================================================================
# TARIFF SERVICE
# =============================================================================

class TariffService:
    """
    Service for fetching Swiss electricity tariffs.
    
    Provides:
    - Consumption prices from ElCom (what users pay)
    - Feed-in tariffs from VESE/PVTarif (what producers receive)
    - Historical data for trend analysis
    """
    
    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize tariff service.
        
        Args:
            api_key: VESE API key (optional, will try .env if not provided)
        """
        self.api_key = api_key or VESE_API_KEY
        self.address_lookup = AddressLookup()
    
    @property
    def has_feedin_api(self) -> bool:
        """Check if feed-in API is available."""
        return bool(self.api_key)
    
    def test_api_key(self, verbose: bool = True) -> bool:
        """
        Test if the VESE API key is valid and working.
        
        Args:
            verbose: Print status messages
            
        Returns:
            True if API key is valid, False otherwise
        """
        if not self.api_key:
            if verbose:
                print("❌ No VESE API key configured")
                print("   Add VESE_API_KEY=your_key to .env file")
            return False
        
        # Test with a known municipality (Zürich, BFS 261)
        url = f"{VESE_BASE_URL}/muni"
        params = {"idofs": "261", "licenseKey": self.api_key}
        
        try:
            response = requests.get(url, params=params, timeout=10)
            if response.status_code == 200:
                data = response.json()
                if data.get("valid"):
                    if verbose:
                        print("✅ VESE API key is valid and working")
                        evus = data.get("evus", [])
                        if evus:
                            print(f"   Found {len(evus)} provider(s) for test municipality")
                    return True
                else:
                    if verbose:
                        print("❌ VESE API returned invalid response")
                        print(f"   Response: {data}")
                    return False
            elif response.status_code == 401:
                if verbose:
                    print("❌ VESE API key is invalid (401 Unauthorized)")
                return False
            elif response.status_code == 403:
                if verbose:
                    print("❌ VESE API key is forbidden (403)")
                return False
            else:
                if verbose:
                    print(f"❌ VESE API returned status {response.status_code}")
                return False
        except requests.exceptions.Timeout:
            if verbose:
                print("⚠️  VESE API timeout - service may be slow or down")
            return False
        except requests.exceptions.ConnectionError:
            if verbose:
                print("⚠️  Could not connect to VESE API - check your internet connection")
            return False
        except Exception as e:
            if verbose:
                print(f"❌ VESE API error: {e}")
            return False
    
    def test_services(self, verbose: bool = True) -> Dict[str, bool]:
        """
        Test all API services.
        
        Args:
            verbose: Print status messages
            
        Returns:
            Dictionary with service status
        """
        results = {
            "geo_admin": False,
            "elcom": False,
            "vese": False,
        }
        
        if verbose:
            print("=" * 50)
            print("🔧 TESTING API SERVICES")
            print("=" * 50)
        
        # Test geo.admin.ch
        if verbose:
            print("\n1. Testing geo.admin.ch (Address Lookup)...")
        try:
            addresses = self.address_lookup.search("Zürich", limit=1)
            if addresses:
                results["geo_admin"] = True
                if verbose:
                    print("   ✅ geo.admin.ch is working")
            else:
                if verbose:
                    print("   ⚠️  geo.admin.ch returned no results")
        except Exception as e:
            if verbose:
                print(f"   ❌ geo.admin.ch error: {e}")
        
        # Test ElCom SPARQL
        if verbose:
            print("\n2. Testing ElCom SPARQL (Consumption Prices)...")
        try:
            prices = self.get_consumption_prices("261", "2024", "H4")
            if prices:
                results["elcom"] = True
                if verbose:
                    print(f"   ✅ ElCom is working ({len(prices)} price(s) found)")
            else:
                if verbose:
                    print("   ⚠️  ElCom returned no prices")
        except Exception as e:
            if verbose:
                print(f"   ❌ ElCom error: {e}")
        
        # Test VESE
        if verbose:
            print("\n3. Testing VESE/PVTarif (Feed-In Tariffs)...")
        results["vese"] = self.test_api_key(verbose=verbose)
        
        if verbose:
            print("\n" + "=" * 50)
            working = sum(results.values())
            print(f"Summary: {working}/3 services working")
            if not results["vese"]:
                print("⚠️  Feed-in tariffs unavailable - will use defaults")
            print("=" * 50)
        
        return results
    
    # -------------------------------------------------------------------------
    # Energy Providers (EVU)
    # -------------------------------------------------------------------------
    
    def get_providers(self, bfs_id: str) -> List[EnergyProvider]:
        """
        Get energy providers for a municipality.
        
        Args:
            bfs_id: Municipality BFS ID
            
        Returns:
            List of EnergyProvider objects
        """
        if not self.api_key:
            return []
        
        url = f"{VESE_BASE_URL}/muni"
        params = {"idofs": bfs_id, "licenseKey": self.api_key}
        
        try:
            response = requests.get(url, params=params, timeout=10)
            if response.status_code == 200:
                data = response.json()
                if data.get("valid"):
                    return [
                        EnergyProvider(
                            elcom_id=str(evu.get("nrElcom", "")),
                            name=evu.get("Name", "Unknown"),
                            additional_info=evu,
                        )
                        for evu in data.get("evus", [])
                    ]
        except Exception as e:
            print(f"Provider lookup error: {e}")
        return []
    
    # -------------------------------------------------------------------------
    # Consumption Prices (ElCom)
    # -------------------------------------------------------------------------
    
    def get_consumption_prices(
        self,
        bfs_id: str,
        year: str = "2024",
        profile: str = "H4"
    ) -> List[ConsumptionPrice]:
        """
        Get electricity consumption prices from ElCom.
        
        Args:
            bfs_id: Municipality BFS ID
            year: Year (e.g., "2024")
            profile: Household profile (H1-H8)
            
        Returns:
            List of ConsumptionPrice objects
        """
        sparql_query = f"""
        PREFIX cube: <https://cube.link/>
        PREFIX schema: <http://schema.org/>
        PREFIX elcom: <https://energy.ld.admin.ch/elcom/electricityprice/dimension/>
        
        SELECT ?obs ?total ?energy ?gridusage ?fee ?levy ?operatorName
        WHERE {{
            ?obs a cube:Observation .
            FILTER(STRSTARTS(STR(?obs), "https://energy.ld.admin.ch/elcom/electricityprice/observation/{bfs_id}-"))
            FILTER(CONTAINS(STR(?obs), "-{profile}-"))
            FILTER(CONTAINS(STR(?obs), "-{year}"))
            
            ?obs elcom:total ?total .
            
            OPTIONAL {{ ?obs elcom:energy ?energy }}
            OPTIONAL {{ ?obs elcom:gridusage ?gridusage }}
            OPTIONAL {{ ?obs elcom:charge ?fee }}
            OPTIONAL {{ ?obs elcom:aidfee ?levy }}
            OPTIONAL {{ 
                ?obs elcom:operator ?operator .
                ?operator schema:name ?operatorName .
            }}
        }}
        ORDER BY ?total
        LIMIT 5
        """
        
        try:
            response = requests.post(
                ELCOM_SPARQL,
                data={"query": sparql_query},
                headers={
                    "Accept": "application/sparql-results+json",
                    "Content-Type": "application/x-www-form-urlencoded"
                },
                timeout=30
            )
            
            if response.status_code == 200:
                data = response.json()
                bindings = data.get("results", {}).get("bindings", [])
                
                results = []
                for binding in bindings:
                    obs_id = binding.get("obs", {}).get("value", "")
                    operator_from_id = obs_id.split("/")[-1].split("-")[1] if obs_id else "Unknown"
                    
                    results.append(ConsumptionPrice(
                        operator_name=binding.get("operatorName", {}).get("value", f"Operator {operator_from_id}"),
                        total_rp_kwh=float(binding.get("total", {}).get("value", 0)),
                        energy_rp_kwh=float(binding.get("energy", {}).get("value", 0)) if binding.get("energy") else None,
                        grid_rp_kwh=float(binding.get("gridusage", {}).get("value", 0)) if binding.get("gridusage") else None,
                        fee_rp_kwh=float(binding.get("fee", {}).get("value", 0)) if binding.get("fee") else None,
                        levy_rp_kwh=float(binding.get("levy", {}).get("value", 0)) if binding.get("levy") else None,
                        year=year,
                        profile=profile,
                    ))
                return results
        except Exception as e:
            print(f"ElCom API error: {e}")
        return []
    
    # -------------------------------------------------------------------------
    # Feed-In Tariffs (VESE)
    # -------------------------------------------------------------------------
    
    def get_feedin_tariff(
        self,
        provider_id: str,
        year: str = "24"
    ) -> Optional[FeedInTariff]:
        """
        Get feed-in tariff from VESE API.
        
        Args:
            provider_id: EVU/ElCom ID
            year: Short year (e.g., "24" for 2024)
            
        Returns:
            FeedInTariff or None
        """
        if not self.api_key:
            return None
        
        url = f"{VESE_BASE_URL}/evu"
        params = {"evuId": provider_id, "year": year, "licenseKey": self.api_key}
        
        try:
            response = requests.get(url, params=params, timeout=10)
            if response.status_code == 200:
                data = response.json()
                if data.get("valid"):
                    return FeedInTariff(
                        provider_name=data.get("nomEw", "Unknown"),
                        energy_rp_kwh=float(data.get("energy1", 0)) if data.get("energy1") else None,
                        peak_ht_rp_kwh=float(data.get("energy1_ht", 0)) if data.get("energy1_ht") else None,
                        offpeak_nt_rp_kwh=float(data.get("energy1_nt", 0)) if data.get("energy1_nt") else None,
                        eco_bonus_rp_kwh=float(data.get("eco1", 0)) if data.get("eco1") else None,
                        year=f"20{year}",
                    )
        except Exception as e:
            print(f"VESE API error: {e}")
        return None
    
    # -------------------------------------------------------------------------
    # Combined Tariff Lookup
    # -------------------------------------------------------------------------
    
    def get_tariffs_for_address(
        self,
        address: str,
        year: str = "2024",
        profile: str = "H4"
    ) -> Optional[TariffSummary]:
        """
        Get all tariffs for a Swiss address.
        
        Args:
            address: Swiss address string
            year: Year for tariffs
            profile: Household profile
            
        Returns:
            TariffSummary or None
        """
        # Look up address
        municipality = self.address_lookup.lookup_address(address)
        if not municipality:
            print(f"Could not find address: {address}")
            return None
        
        return self.get_tariffs_for_municipality(municipality, year, profile)
    
    def get_tariffs_for_municipality(
        self,
        municipality: MunicipalityInfo,
        year: str = "2024",
        profile: str = "H4"
    ) -> TariffSummary:
        """
        Get all tariffs for a municipality.
        
        Args:
            municipality: MunicipalityInfo object
            year: Year for tariffs
            profile: Household profile
            
        Returns:
            TariffSummary
        """
        summary = TariffSummary(
            municipality=municipality,
            year=year,
        )
        
        # Get consumption prices
        summary.consumption_prices = self.get_consumption_prices(
            municipality.bfs_id, year, profile
        )
        
        # Get providers and feed-in tariffs
        if self.has_feedin_api:
            providers = self.get_providers(municipality.bfs_id)
            short_year = year[-2:]  # "2024" -> "24"
            
            for provider in providers:
                tariff = self.get_feedin_tariff(provider.elcom_id, short_year)
                if tariff:
                    summary.feedin_tariffs.append(tariff)
        
        return summary
    
    # -------------------------------------------------------------------------
    # Historical Data
    # -------------------------------------------------------------------------
    
    def get_historical_data(
        self,
        municipality: MunicipalityInfo,
        provider_id: Optional[str] = None,
        profile: str = "H4",
        years: Optional[List[str]] = None
    ) -> HistoricalData:
        """
        Fetch historical tariff data.
        
        Args:
            municipality: MunicipalityInfo object
            provider_id: EVU ID for feed-in tariffs (optional)
            profile: Household profile
            years: Years to fetch (default: 2018-2024)
            
        Returns:
            HistoricalData object
        """
        years = years or AVAILABLE_YEARS
        
        data = HistoricalData(municipality=municipality)
        
        for year in years:
            data.years.append(year)
            
            # Consumption prices
            cons = self.get_consumption_prices(municipality.bfs_id, year, profile)
            if cons:
                best = min(cons, key=lambda p: p.total_rp_kwh)
                data.consumption_total.append(best.total_rp_kwh)
                data.consumption_energy.append(best.energy_rp_kwh)
            else:
                data.consumption_total.append(None)
                data.consumption_energy.append(None)
            
            # Feed-in tariffs
            if provider_id and self.has_feedin_api:
                short_year = year[-2:]
                feedin = self.get_feedin_tariff(provider_id, short_year)
                if feedin:
                    data.feedin_energy.append(feedin.energy_rp_kwh)
                    data.feedin_ht.append(feedin.peak_ht_rp_kwh)
                else:
                    data.feedin_energy.append(None)
                    data.feedin_ht.append(None)
            else:
                data.feedin_energy.append(None)
                data.feedin_ht.append(None)
        
        return data

    def get_historical_data_for_address(
        self,
        address: str,
        profile: str = "H4",
        years: Optional[List[str]] = None
    ) -> Optional[HistoricalData]:
        """
        Fetch historical tariff data for a specific address.
        
        Args:
            address: Swiss address string
            profile: Household profile
            years: Years to fetch
            
        Returns:
            HistoricalData object or None
        """
        # Look up address
        municipality = self.address_lookup.lookup_address(address)
        if not municipality:
            print(f"Could not find address: {address}")
            return None
            
        # Find provider
        provider_id = None
        if self.has_feedin_api:
            providers = self.get_providers(municipality.bfs_id)
            if providers:
                # Use the first provider found
                provider_id = providers[0].elcom_id
                
        return self.get_historical_data(municipality, provider_id, profile, years)


# =============================================================================
# CONVENIENCE FUNCTIONS
# =============================================================================

def get_tariffs_quick(address: str, year: str = "2024") -> Optional[Dict[str, Any]]:
    """
    Quick function to get tariffs for an address.
    
    Args:
        address: Swiss address
        year: Year for tariffs
        
    Returns:
        Dictionary with tariff info or None
    """
    service = TariffService()
    summary = service.get_tariffs_for_address(address, year)
    return summary.to_dict() if summary else None


# =============================================================================
# DEMO
# =============================================================================

if __name__ == "__main__":
    print("=" * 60)
    print("🇨🇭 SWISS TARIFF SERVICE - DEMO")
    print("=" * 60)
    
    service = TariffService()
    
    # Check API key
    if service.has_feedin_api:
        print("✅ VESE API key found")
    else:
        print("⚠️  No VESE API key - feed-in tariffs unavailable")
        print("   Add VESE_API_KEY to .env file to enable")
    
    # Demo address lookup
    print("\n--- Address Lookup ---")
    address = "Bahnhofstrasse 10, Zürich"
    municipality = service.address_lookup.lookup_address(address)
    
    if municipality:
        print(f"Address: {address}")
        print(f"Municipality: {municipality.name} (BFS: {municipality.bfs_id})")
        print(f"Canton: {municipality.canton}")
        
        # Get tariffs
        print("\n--- Tariff Summary (2024) ---")
        summary = service.get_tariffs_for_municipality(municipality)
        
        if summary.consumption_prices:
            best = summary.best_consumption_price
            print(f"\nConsumption (what you pay):")
            print(f"  Best price: {best.total_rp_kwh:.2f} Rp/kWh ({best.operator_name})")
            print(f"  Energy component: {best.energy_rp_kwh:.2f} Rp/kWh")
        
        if summary.feedin_tariffs:
            best = summary.best_feedin_tariff
            print(f"\nFeed-in (what you receive):")
            print(f"  Best rate: {best.best_rate_rp_kwh:.2f} Rp/kWh ({best.provider_name})")
        
        # Export for ZEV
        print("\n--- Export for ZEV Integration ---")
        export = summary.to_dict()
        for key, value in export.items():
            print(f"  {key}: {value}")
    else:
        print(f"Could not find: {address}")
    
    print("\n" + "=" * 60)
