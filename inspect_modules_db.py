
import pandas as pd
import os

def inspect():
    data_dir = os.path.join(os.path.dirname(__file__), 'data')
    mod_path = os.path.join(data_dir, 'SandiaMod.csv')
    
    if not os.path.exists(mod_path):
        print(f"File not found: {mod_path}")
        return

    print(f"Loading {mod_path}...")
    modules = pd.read_csv(mod_path, index_col=0)
    
    print("\n--- Modules DataFrame Info ---")
    print(f"Shape: {modules.shape}")
    print("\nColumns:")
    print(modules.columns.tolist())
    
    print("\nSample Index (first 5):")
    print(modules.index[:5].tolist())
    
    # Try to identify potential manufacturer column
    # Often encoded in the name or a specific column (e.g. 'Manufacturer')
    # If not present, we might need to parse the index.
    
    print("\nSample Row 0:")
    print(modules.iloc[0])

if __name__ == "__main__":
    inspect()
