#!/usr/bin/env python3
"""
Tariff Service Demo
===================
Demonstrates usage of the Swiss Tariff Service for electricity prices.

Run from oop-solar directory:
    python demo_tariff_service.py
"""

from tariff_service import TariffService, AddressLookup


def demo_test_services():
    """Demo 1: Test all API services."""
    print("\n" + "=" * 70)
    print("DEMO 1: Test API Services")
    print("=" * 70)
    
    service = TariffService()
    results = service.test_services()
    
    return results


def demo_address_lookup():
    """Demo 2: Address lookup and municipality info."""
    print("\n" + "=" * 70)
    print("DEMO 2: Address Lookup")
    print("=" * 70)
    
    lookup = AddressLookup()
    
    addresses = [
        "Bahnhofstrasse 10, Zürich",
        "Marktgasse 1, Bern",
        "Rue du Rhône 50, Genève",
    ]
    
    for address in addresses:
        print(f"\n🔍 Searching: {address}")
        results = lookup.search(address, limit=1)
        
        if results:
            print(f"   Found: {results[0]['label']}")
            municipality = lookup.get_municipality(results[0]['lat'], results[0]['lon'])
            if municipality:
                print(f"   Municipality: {municipality.name}")
                print(f"   BFS ID: {municipality.bfs_id}")
                print(f"   Canton: {municipality.canton}")
        else:
            print("   ❌ Not found")


def demo_consumption_prices():
    """Demo 3: Get consumption prices from ElCom."""
    print("\n" + "=" * 70)
    print("DEMO 3: Consumption Prices (ElCom)")
    print("=" * 70)
    
    service = TariffService()
    
    # Get prices for different municipalities
    municipalities = [
        ("261", "Zürich"),
        ("351", "Bern"),
        ("6621", "Genève"),
    ]
    
    print(f"\n{'Municipality':<15} {'Year':<6} {'Profile':<8} {'Total':<12} {'Energy':<12}")
    print("-" * 60)
    
    for bfs_id, name in municipalities:
        prices = service.get_consumption_prices(bfs_id, "2024", "H4")
        if prices:
            best = min(prices, key=lambda p: p.total_rp_kwh)
            energy = f"{best.energy_rp_kwh:.2f}" if best.energy_rp_kwh else "N/A"
            print(f"{name:<15} {'2024':<6} {'H4':<8} {best.total_rp_kwh:.2f} Rp/kWh  {energy} Rp/kWh")
        else:
            print(f"{name:<15} {'2024':<6} {'H4':<8} No data")


def demo_compare_profiles():
    """Demo 4: Compare prices for different household profiles."""
    print("\n" + "=" * 70)
    print("DEMO 4: Compare Household Profiles (Zürich 2024)")
    print("=" * 70)
    
    service = TariffService()
    
    profiles = {
        "H1": "1,600 kWh/yr (1-room apt)",
        "H4": "4,500 kWh/yr (typical)",
        "H6": "25,000 kWh/yr (heat pump)",
    }
    
    print(f"\n{'Profile':<8} {'Description':<30} {'Price':<15}")
    print("-" * 55)
    
    for profile, desc in profiles.items():
        prices = service.get_consumption_prices("261", "2024", profile)
        if prices:
            best = min(prices, key=lambda p: p.total_rp_kwh)
            print(f"{profile:<8} {desc:<30} {best.total_rp_kwh:.2f} Rp/kWh")


def demo_tariffs_for_address():
    """Demo 5: Get all tariffs for an address."""
    print("\n" + "=" * 70)
    print("DEMO 5: Complete Tariff Summary for Address")
    print("=" * 70)
    
    service = TariffService()
    
    address = "Bahnhofstrasse 10, Zürich"
    print(f"\n📍 Address: {address}")
    
    summary = service.get_tariffs_for_address(address, "2024", "H4")
    
    if summary:
        print(f"\n📊 Municipality: {summary.municipality.name} (BFS: {summary.municipality.bfs_id})")
        
        if summary.consumption_prices:
            best = summary.best_consumption_price
            print(f"\n⚡ Consumption (what you pay):")
            print(f"   Best: {best.total_rp_kwh:.2f} Rp/kWh = {best.total_chf_kwh:.4f} CHF/kWh")
            print(f"   Provider: {best.operator_name}")
        
        if summary.feedin_tariffs:
            best = summary.best_feedin_tariff
            print(f"\n🔋 Feed-in (what you receive):")
            print(f"   Best: {best.best_rate_rp_kwh:.2f} Rp/kWh")
            print(f"   Provider: {best.provider_name}")
        else:
            print(f"\n🔋 Feed-in: Not available (add VESE_API_KEY to .env)")
        
        # Export dictionary
        print(f"\n📤 Export dictionary:")
        export = summary.to_dict()
        for key, value in list(export.items())[:5]:  # First 5 items
            print(f"   {key}: {value}")
    else:
        print("   ❌ Could not get tariff summary")


def demo_year_comparison():
    """Demo 6: Compare prices across years."""
    print("\n" + "=" * 70)
    print("DEMO 6: Price Trend Over Years (Zürich H4)")
    print("=" * 70)
    
    service = TariffService()
    
    years = ["2020", "2021", "2022", "2023", "2024"]
    
    print(f"\n{'Year':<8} {'Total Price':<15} {'Change':<12}")
    print("-" * 40)
    
    prev_price = None
    for year in years:
        prices = service.get_consumption_prices("261", year, "H4")
        if prices:
            best = min(prices, key=lambda p: p.total_rp_kwh)
            if prev_price:
                change = best.total_rp_kwh - prev_price
                print(f"{year:<8} {best.total_rp_kwh:.2f} Rp/kWh      {change:+.2f} Rp/kWh")
            else:
                print(f"{year:<8} {best.total_rp_kwh:.2f} Rp/kWh      --")
            prev_price = best.total_rp_kwh
        else:
            print(f"{year:<8} No data")


def demo_quick_function():
    """Demo 7: Quick tariff lookup function."""
    print("\n" + "=" * 70)
    print("DEMO 7: Quick Tariff Lookup")
    print("=" * 70)
    
    from tariff_service import get_tariffs_quick
    
    result = get_tariffs_quick("Bundesplatz 1, Bern")
    
    if result:
        print(f"\nTariffs for {result['municipality_name']}:")
        print(f"  Consumption: {result['consumption_total_chf_kwh']:.4f} CHF/kWh")
    else:
        print("  Could not fetch tariffs")


def main():
    """Run all demos."""
    print("=" * 70)
    print("🇨🇭 SWISS TARIFF SERVICE - DEMO SUITE")
    print("=" * 70)
    
    demo_test_services()
    demo_address_lookup()
    demo_consumption_prices()
    demo_compare_profiles()
    demo_tariffs_for_address()
    demo_year_comparison()
    demo_quick_function()
    
    # New Demo for History by Address
    print("\n" + "=" * 70)
    print("DEMO 8: Historical Data by Address")
    print("=" * 70)
    
    address = "Laufen am Rheinfall 1 8447 Dachsen"
    print(f"\n📍 Getting history for: {address}")
    
    history = service.get_historical_data_for_address(address)
    
    if history:
        print(f"📊 Municipality: {history.municipality.name}")
        df = history.to_dataframe()
        print(df.to_string(index=False))
        
        # Calculate spread for latest year
        latest = df.iloc[-1]
        print(f"\nLatest Spread ({latest['Year']}): {latest['Spread_Rp_kWh']:.2f} Rp/kWh")
    else:
        print("❌ Could not fetch history")
    
    print("\n" + "=" * 70)
    print("✅ All demos completed!")
    print("=" * 70)


if __name__ == "__main__":
    main()
