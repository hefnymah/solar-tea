
import pandas as pd
import numpy as np
from scipy.optimize import minimize_scalar

def simulate_battery(
    load_profile: pd.Series, 
    pv_production: pd.Series, 
    battery_kwh: float,
    efficiency: float = 0.95,
    min_soc: float = 0.2
) -> pd.DataFrame:
    """
    Simulates battery behavior over time.
    """
    # Ensure inputs are aligned
    df = pd.DataFrame({'load': load_profile, 'pv': pv_production}).fillna(0)
    
    # Basic Energy Balance
    df['excess_pv'] = (df['pv'] / 1000) - df['load'] # Assuming load in kW, PV in Watts -> now all in kW?
    # Actually let's assume inputs are consistently Watts or kW.
    # Standardize to kWh per hour step (average power)
    
    # Let's assume input Series are Watts, convert to kWh (if hourly data)
    df['excess_energy_kwh'] = (df['pv'] - df['load']) / 1000 # Watts -> kWh
    
    soc = [battery_kwh] # Start full
    grid_import = []
    grid_export = []
    
    battery_capacity_kwh = battery_kwh
    
    for excess in df['excess_energy_kwh']:
        current_soc = soc[-1]
        
        if excess > 0:
            # Charging
            charge_energy = excess * efficiency
            new_soc = min(battery_capacity_kwh, current_soc + charge_energy)
            export_energy = excess - ((new_soc - current_soc) / efficiency)
            import_energy = 0
        else:
            # Discharging
            deficit = -excess
            discharge_needed = deficit / efficiency
            available_energy = current_soc - (battery_capacity_kwh * min_soc)
            
            if available_energy >= discharge_needed:
                new_soc = current_soc - discharge_needed
                import_energy = 0
                export_energy = 0
            else:
                new_soc = battery_capacity_kwh * min_soc
                used_energy = available_energy
                import_energy = deficit - (used_energy * efficiency)
                export_energy = 0
        
        soc.append(new_soc)
        grid_import.append(import_energy)
        grid_export.append(export_energy)
        
    df['soc'] = soc[1:]
    df['grid_import'] = grid_import
    df['grid_export'] = grid_export
    
    return df

def optimize_battery_size(
    load_profile: pd.Series, 
    pv_production: pd.Series,
    target_autonomy_days: float = 1.0,
    daily_load_kwh: float = 10.0
) -> float:
    """
    Finds battery size to maximize self-sufficiency or meet simple heuristic.
    Here we implement the Perplexity suggestion: E_batt = E_day * N_aut / (DoD * efficiency)
    Or we can do a cost optimization. Let's do the heuristic first as a baseline specific target.
    """
    
    # Heuristic based on conversation
    dod = 0.8
    eff = 0.95
    suggested_size = (daily_load_kwh * target_autonomy_days) / (dod * eff)
    
    return suggested_size

def optimize_battery_cost(
    load_profile: pd.Series, 
    pv_production: pd.Series,
    battery_cost_per_kwh: float = 400,
    electricity_rate: float = 0.30
) -> float:
    """
    Uses optimization to find battery size that minimizes total cost (Battery CapEx + Grid OpEx)
    over one year.
    """
    
    def objective(batt_size):
        if batt_size < 0: return 1e9
        
        results = simulate_battery(load_profile, pv_production, batt_size)
        total_import = results['grid_import'].sum()
        
        capex = batt_size * battery_cost_per_kwh
        opex = total_import * electricity_rate
        
        return capex + opex

    res = minimize_scalar(objective, bounds=(0, 50), method='bounded')
    return res.x
