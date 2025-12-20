
"""
Example 07: Consumption Analysis (Batch Processing)
===================================================
This script analyzes all consumption data files found in data/consumption/
and generates comparative reports for each.
"""

import sys
import os
import glob

# Ensure root is in path
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from eclipse.consumption.analyzer import ConsumptionAnalyzer

def main():
    print("=== Consumption Analysis Batch Processor ===\n")
    
    # 1. Find Data Files
    data_dir = os.path.join(os.path.dirname(__file__), '..', 'data', 'consumption')
    csv_files = glob.glob(os.path.join(data_dir, "*.csv"))
    
    if not csv_files:
        print(f"No CSV files found in {data_dir}")
        return

    print(f"Found {len(csv_files)} files to analyze:")
    for f in csv_files:
        print(f" - {os.path.basename(f)}")
    print("-" * 40)

    # 2. Process Each File
    output_base_dir = os.path.join(os.path.dirname(__file__), 'outputs', 'consumption_analysis')
    
    for file_path in csv_files:
        filename = os.path.basename(file_path)
        name_no_ext = os.path.splitext(filename)[0]
        
        print(f"\nProcessing: {filename}...")
        
        # Create output subdirectory for this file to avoid collision
        file_output_dir = os.path.join(output_base_dir, name_no_ext)
        
        analyzer = ConsumptionAnalyzer(output_dir=file_output_dir)
        
        # Example: Customize seasonal representative weeks
        # User defined weeks (Month, Day)
        analyzer.seasonal_weeks_config = {
            'Winter': (1, 15),  # Jan 15 (Default)
            'Spring': (5, 1),   # May 1  (Custom)
            'Summer': (6, 20),  # Jul 20 (Custom)
            'Autumn': (11, 1)   # Nov 1  (Custom)
        }
        
        if analyzer.load_data(file_path):
            analyzer.analyze()
            analyzer.plot_all(filename_prefix=name_no_ext)
            print(f"   [OK] Analysis complete. Plots saved to: {file_output_dir}")
        else:
            print(f"   [FAILED] Could not process {filename}")

if __name__ == "__main__":
    main()
