#!/usr/bin/env python3
"""
Interactive Tariff History
==========================
Recursively ask for an address, fetch historical tariff data (consumption and feed-in),
and display it in a formatted table.

Usage:
    python interactive_tariff_history.py
"""

import sys
import pandas as pd
from tariff_service import TariffService

def main():
    print("=" * 70)
    print("🇨🇭 INTERACTIVE TARIFF HISTORY EXPLORER")
    print("=" * 70)
    print("Type 'exit', 'quit', or press Ctrl+C to stop.\n")

    service = TariffService()
    
    # Check if API key is loaded
    if service.has_feedin_api:
        print("✅ VESE API Key detected. Feed-in tariffs will be included.")
    else:
        print("⚠️  No VESE API Key found. Feed-in tariffs will be missing.")

    while True:
        try:
            address = input("\n📍 Enter Swiss address: ").strip()
        except KeyboardInterrupt:
            print("\nExiting...")
            break
            
        if address.lower() in ('exit', 'quit'):
            break
            
        if not address:
            continue

        print(f"   Searching for details on: '{address}'...")
        
        try:
            history = service.get_historical_data_for_address(address)
            
            if history:
                print(f"\n✅ Municipality: {history.municipality.name} (BFS: {history.municipality.bfs_id})")
                print(f"   Canton: {history.municipality.canton}")
                
                # Convert to DataFrame for display
                df = history.to_dataframe()
                
                # Format for better reading
                # Keep only relevant columns if others are empty? 
                # But to_dataframe structure is fixed.
                
                print("\n📊 Historical Data (Rp/kWh):")
                print("-" * 75)
                # Using to_string to print the whole table nicely
                print(df.to_string(index=False, float_format=lambda x: "{:.2f}".format(x) if pd.notnull(x) else "-"))
                print("-" * 75)
                
                # Summary of latest year
                latest = df.iloc[-1]
                print(f"\n🔍 Latest Snapshot ({latest['Year']}):")
                
                cons_price = latest['Consumption_Total_Rp_kWh']
                print(f"   🔌 You Pay (Consumption):     {cons_price:.2f} Rp/kWh" if pd.notnull(cons_price) else "   🔌 You Pay (Consumption):     -")
                
                feed_price = latest['Feedin_Energy_Rp_kWh']
                print(f"   ☀️  You Receive (Feed-in):     {feed_price:.2f} Rp/kWh" if pd.notnull(feed_price) else "   ☀️  You Receive (Feed-in):     -")
                
                spread = latest['Spread_Rp_kWh']
                if pd.notnull(spread):
                    print(f"   💰 Utility Margin (Spread):   {spread:.2f} Rp/kWh")
                
            else:
                print("❌ Could not find tariff data for this address.")
                
        except Exception as e:
            print(f"❌ Error: {e}")

    print("\nGoodbye!")

if __name__ == "__main__":
    main()
