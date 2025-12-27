#!/usr/bin/env python3
"""
Feed-in Tariff Demo
===================
Demonstrates the calculation of feed-in tariffs using real VESE API data.
Replicates logic from Excel 'Eingaben' sheet rows 68-73.

Usage:
    python demo_calculate_feedin.py
"""

from calculate_feedin import FeedInTariffCalculator

def main():
    print("="*70)
    print("🔋 FEED-IN TARIFF CALCULATOR DEMO")
    print("="*70)
    
    calculator = FeedInTariffCalculator()
    
    # Example Parameters
    examples = [
        ("Laufen am Rheinfall 1, 8447 Dachsen", 12000, 35.0),
        ("Bahnhofstrasse 10, Zürich", 4500, 20.0),
    ]
    
    for address, prod, share in examples:
        print(f"\n📍 Address: {address}")
        print(f"⚡ Production: {prod} kWh | Export Share: {share}%")
        
        try:
            result = calculator.calculate(address, prod, share)
            
            print(f"🏢 Provider: {result['parameters']['provider']}")
            print("-" * 65)
            print(f"{'Row':<4} {'Label':<45} {'Value (CHF/kWh | % | kWh)':<25}")
            print("-" * 65)
            
            rows = result['rows']
            for row_num in [69, 70, 71, 72, 73]:
                data = rows[row_num]
                val_str = f"{data['value']:.4f}"
                print(f"{row_num:<4} {data['label']:<45} {val_str:<10} {data['unit']}")
                
        except Exception as e:
            print(f"❌ Error: {e}")
            
    print("\n" + "="*70)
    print("✅ Demo completed.")

if __name__ == "__main__":
    main()
