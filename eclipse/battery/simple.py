"""
Simple Battery Simulator
========================
Fast, heuristic-based battery simulation using basic energy balance.
Good for initial sizing and quick estimates.
"""

import pandas as pd
import numpy as np
from typing import Optional

from eclipse.battery.simulator import BatterySimulator
from eclipse.config.equipment_models import MockBattery


class SimpleBatterySimulator(BatterySimulator):
    """
    Simple battery simulator using basic energy balance.
    
    Uses a fixed round-trip efficiency model without detailed
    physics (no voltage curves, thermal effects, etc.).
    
    Pros:
        - Fast execution
        - No external dependencies (pure Python)
        - Good for initial sizing estimates
        
    Cons:
        - Less accurate than PySAM
        - No degradation modeling
        - No thermal effects
    """
    
    def __init__(self, battery: MockBattery, efficiency: Optional[float] = None):
        """
        Initialize the simple simulator.
        
        Args:
            battery: MockBattery configuration object
            efficiency: Override round-trip efficiency (default: from battery.performance)
        """
        super().__init__(battery)
        
        # Get efficiency from config or use default
        if efficiency is not None:
            self.efficiency = efficiency
        elif battery.performance and 'round_trip_efficiency' in battery.performance:
            self.efficiency = battery.performance['round_trip_efficiency']
        else:
            self.efficiency = 0.95  # Default 95%
    
    def simulate(
        self, 
        load_kw: pd.Series, 
        pv_kw: pd.Series,
        system_kwh: Optional[float] = None,
        system_kw: Optional[float] = None
    ) -> pd.DataFrame:
        """
        Run simple battery simulation.
        
        Args:
            load_kw: Load profile in kW
            pv_kw: PV generation profile in kW
            system_kwh: Override for capacity (default: battery.nominal_energy_kwh)
            system_kw: Override for power limit (default: battery.max_discharge_power_kw)
            
        Returns:
            DataFrame with simulation results
        """
        # Resolve capacity and power
        capacity_kwh = system_kwh if system_kwh is not None else self.battery.nominal_energy_kwh
        max_power_kw = system_kw if system_kw is not None else self.battery.max_discharge_power_kw
        
        # SOC limits (as fractions)
        min_soc_frac = self.battery.min_soc / 100.0
        max_soc_frac = self.battery.max_soc / 100.0
        
        # Initial SOC (start full)
        initial_soc_kwh = capacity_kwh * max_soc_frac
        
        # Align inputs
        df = pd.DataFrame({'load': load_kw.fillna(0), 'pv': pv_kw.fillna(0)})
        
        # Calculate excess energy (Positive = can charge, Negative = need discharge)
        df['excess_kw'] = df['pv'] - df['load']
        
        # Initialize state
        soc_kwh = initial_soc_kwh
        soc_log = []
        battery_power_log = []  # Positive = Discharge, Negative = Charge
        grid_import_log = []
        grid_export_log = []
        
        min_energy_kwh = capacity_kwh * min_soc_frac
        max_energy_kwh = capacity_kwh * max_soc_frac
        
        # Calculate timestep in hours (infer from index if possible)
        if len(df) > 1 and hasattr(df.index, 'freq') and df.index.freq is not None:
            # Use pd.Timedelta to avoid deprecation warning
            dt_hours = pd.Timedelta(df.index.freq).total_seconds() / 3600
        elif len(df) > 1:
            dt_hours = (df.index[1] - df.index[0]).total_seconds() / 3600
        else:
            dt_hours = 0.25  # Default 15 minutes
        
        for excess in df['excess_kw']:
            # Convert power (kW) to energy for this timestep (kWh)
            excess_energy_kwh = excess * dt_hours
            
            if excess_energy_kwh < 0:
                # Deficit: Need to discharge battery
                deficit_kwh = -excess_energy_kwh
                
                # Limit by power (convert power limit to energy for this timestep)
                max_discharge_kwh = max_power_kw * dt_hours
                discharge_request_kwh = min(deficit_kwh, max_discharge_kwh)
                
                # Energy available for discharge (accounting for efficiency)
                available_energy_kwh = (soc_kwh - min_energy_kwh) * self.efficiency
                
                # Actual discharge
                actual_discharge_kwh = min(discharge_request_kwh, available_energy_kwh)
                
                # Update SOC (energy removed from battery)
                energy_removed_kwh = actual_discharge_kwh / self.efficiency
                soc_kwh = max(min_energy_kwh, soc_kwh - energy_removed_kwh)
                
                # Grid import for remaining deficit
                grid_import_kwh = deficit_kwh - actual_discharge_kwh
                grid_export_kwh = 0.0
                
                # Convert back to power for logging (kW)
                battery_power_kw = actual_discharge_kwh / dt_hours  # Positive = Discharge
                grid_import_kw = grid_import_kwh / dt_hours
                grid_export_kw = 0.0
                
                battery_power_log.append(battery_power_kw)
                
            else:
                # Excess: Can charge battery
                excess_kwh = excess_energy_kwh
                
                # Limit by power (convert power limit to energy for this timestep)
                max_charge_kwh = max_power_kw * dt_hours
                charge_request_kwh = min(excess_kwh, max_charge_kwh)
                
                # Energy room for charging (accounting for efficiency)
                room_kwh = (max_energy_kwh - soc_kwh) / self.efficiency
                
                # Actual charge
                actual_charge_kwh = min(charge_request_kwh, room_kwh)
                
                # Update SOC (energy added to battery, with losses)
                energy_stored_kwh = actual_charge_kwh * self.efficiency
                soc_kwh = min(max_energy_kwh, soc_kwh + energy_stored_kwh)
                
                # Grid export for remaining excess
                grid_export_kwh = excess_kwh - actual_charge_kwh
                grid_import_kwh = 0.0
                
                # Convert back to power for logging (kW)
                battery_power_kw = -actual_charge_kwh / dt_hours  # Negative = Charge
                grid_import_kw = 0.0
                grid_export_kw = grid_export_kwh / dt_hours
                
                battery_power_log.append(battery_power_kw)
            
            # Convert SOC to percentage
            soc_pct = (soc_kwh / capacity_kwh) * 100.0
            soc_log.append(soc_pct)
            grid_import_log.append(grid_import_kw)
            grid_export_log.append(grid_export_kw)
        
        # Build results DataFrame
        df['soc'] = soc_log
        df['battery_power'] = battery_power_log
        df['grid_import'] = grid_import_log
        df['grid_export'] = grid_export_log
        df['grid_power'] = df['grid_import'] - df['grid_export']
        
        # Store metadata for downstream use (e.g., by BatteryPlotter)
        df.attrs['battery_kwh'] = capacity_kwh
        
        return df
