"""
Battery Simulator Base Class
============================
Abstract base class defining the common interface for all battery simulators.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Optional, List
import pandas as pd
import numpy as np

from src.config.equipment_models import MockBattery


class BatterySimulator(ABC):
    """
    Abstract base class for battery simulation.
    
    All simulators accept a MockBattery configuration object and provide
    a consistent interface for simulation and optimization.
    """
    
    def __init__(self, battery: MockBattery):
        """
        Initialize the simulator with a battery configuration.
        
        Args:
            battery: MockBattery configuration object with all specs.
        """
        self.battery = battery
    
    @abstractmethod
    def simulate(
        self, 
        load_kw: pd.Series, 
        pv_kw: pd.Series,
        system_kwh: Optional[float] = None,
        system_kw: Optional[float] = None
    ) -> pd.DataFrame:
        """
        Run battery simulation over the given time series.
        
        Args:
            load_kw: Load profile in kW (pandas Series with datetime index)
            pv_kw: PV generation profile in kW (pandas Series with datetime index)
            system_kwh: Override for total capacity (e.g., for multiple units)
            system_kw: Override for total power limit
            
        Returns:
            DataFrame with columns: load, pv, soc, battery_power, grid_import, grid_export
        """
        pass
    
    def calculate_self_sufficiency(self, results: pd.DataFrame) -> float:
        """
        Calculate self-sufficiency percentage from simulation results.
        
        Args:
            results: DataFrame from simulate()
            
        Returns:
            Self-sufficiency as a decimal (0.0 to 1.0)
        """
        total_load = results['load'].sum()
        if total_load == 0:
            return 1.0
        total_import = results['grid_import'].sum()
        return 1.0 - (total_import / total_load)
    
    def optimize_size(
        self, 
        load_kw: pd.Series, 
        pv_kw: pd.Series,
        target_ss: float = 1.0,
        capacity_range: Optional[List[float]] = None
    ) -> dict:
        """
        Find optimal battery capacity for a target self-sufficiency.
        
        Uses sweep-based optimization to find the minimum capacity
        that achieves the target self-sufficiency.
        
        Args:
            load_kw: Load profile in kW
            pv_kw: PV generation profile in kW
            target_ss: Target self-sufficiency (default 1.0 = 100%)
            capacity_range: List of capacities to test (default: 0 to 100 kWh)
            
        Returns:
            Dict with 'optimal_kwh', 'achieved_ss', 'results_df'
        """
        if capacity_range is None:
            capacity_range = [0, 5, 10, 15, 20, 30, 40, 50, 75, 100]
        
        best_result = None
        sweep_results = []
        
        for cap in capacity_range:
            if cap == 0:
                # No battery case
                net = load_kw - pv_kw
                grid_import = net[net > 0].sum()
                total_load = load_kw.sum()
                ss = 1.0 - (grid_import / total_load) if total_load > 0 else 1.0
                sweep_results.append({'capacity_kwh': cap, 'ss': ss, 'import_kwh': grid_import})
            else:
                results = self.simulate(load_kw, pv_kw, system_kwh=float(cap))
                ss = self.calculate_self_sufficiency(results)
                grid_import = results['grid_import'].sum()
                sweep_results.append({'capacity_kwh': cap, 'ss': ss, 'import_kwh': grid_import})
                
                # Check if we've reached target (with tolerance)
                if ss >= target_ss - 0.001 and best_result is None:
                    best_result = {
                        'optimal_kwh': cap,
                        'achieved_ss': ss,
                        'results_df': results
                    }
        
        # If target never reached, return largest capacity tested
        if best_result is None:
            last = sweep_results[-1]
            best_result = {
                'optimal_kwh': last['capacity_kwh'],
                'achieved_ss': last['ss'],
                'results_df': None  # Large cap, didn't store
            }
            
        best_result['sweep_results'] = pd.DataFrame(sweep_results)
        return best_result
    
    def optimize_cost(
        self,
        load_kw: pd.Series,
        pv_kw: pd.Series,
        capex_per_kwh: float = 400.0,
        electricity_rate: float = 0.30,
        capacity_range: Optional[List[float]] = None
    ) -> dict:
        """
        Find optimal battery capacity minimizing total cost (CapEx + OpEx).
        
        Args:
            load_kw: Load profile in kW
            pv_kw: PV generation profile in kW
            capex_per_kwh: Battery cost per kWh capacity (EUR/kWh)
            electricity_rate: Grid electricity price (EUR/kWh)
            capacity_range: List of capacities to test
            
        Returns:
            Dict with 'optimal_kwh', 'total_cost', 'capex', 'opex', 'sweep_results'
        """
        if capacity_range is None:
            capacity_range = list(range(0, 55, 5))  # 0 to 50 kWh in 5 kWh steps
        
        sweep_results = []
        best_cost = float('inf')
        best_result = None
        
        for cap in capacity_range:
            if cap == 0:
                net = load_kw - pv_kw
                grid_import = net[net > 0].sum()
            else:
                results = self.simulate(load_kw, pv_kw, system_kwh=float(cap))
                grid_import = results['grid_import'].sum()
            
            capex = cap * capex_per_kwh
            opex = grid_import * electricity_rate
            total = capex + opex
            
            sweep_results.append({
                'capacity_kwh': cap,
                'capex': capex,
                'opex': opex,
                'total_cost': total,
                'import_kwh': grid_import
            })
            
            if total < best_cost:
                best_cost = total
                best_result = {
                    'optimal_kwh': cap,
                    'total_cost': total,
                    'capex': capex,
                    'opex': opex
                }
        
        best_result['sweep_results'] = pd.DataFrame(sweep_results)
        return best_result
