"""
Sweep Optimizer
===============
Grid-based sweep optimization for PV and battery sizing.

This is the default optimizer that systematically evaluates configurations
on a grid of PV and battery sizes with physics-based constraints.
"""

from typing import Callable, Optional
import pandas as pd
import numpy as np

from eclipse.optimization.base import (
    Optimizer,
    OptimizationResult,
    OptimizationBounds,
)


class SweepOptimizer(Optimizer):
    """
    Grid sweep optimization with physics-based battery constraints.
    
    Tests combinations of PV and battery sizes on a configurable grid,
    applying physics-based limits to battery sizing based on PV capacity.
    
    Features:
    - Physics-based battery limits (max = daily_pv × storage_days)
    - Diminishing returns detection
    - Early stopping when target achieved
    - Two priority modes: 'performance' and 'economy'
    
    Example:
        optimizer = SweepOptimizer(max_storage_days=2.0)
        result = optimizer.optimize(
            objective=lambda pv, bat: -simulate(pv, bat).self_sufficiency,
            bounds=OptimizationBounds(pv_max_kwp=10.0),
            target_value=-80.0  # Negative because we minimize
        )
    """
    
    def __init__(
        self,
        max_storage_days: float = 2.0,
        priority: str = 'performance',
        diminishing_returns_threshold: float = 1.0
    ):
        """
        Initialize sweep optimizer.
        
        Args:
            max_storage_days: Maximum battery storage as days of PV generation.
            priority: 'performance' (max objective) or 'economy' (min size).
            diminishing_returns_threshold: Stop battery increase when improvement
                                          falls below this percentage per kWh.
        """
        self.max_storage_days = max_storage_days
        self.priority = priority
        self.diminishing_returns_threshold = diminishing_returns_threshold
        
        if priority not in ['performance', 'economy']:
            raise ValueError(f"priority must be 'performance' or 'economy', got {priority}")
    
    @property
    def name(self) -> str:
        return f"SweepOptimizer({self.priority})"
    
    def optimize(
        self,
        objective: Callable[[float, float], float],
        bounds: OptimizationBounds,
        target_value: Optional[float] = None,
        constraints: Optional[dict] = None,
        verbose: bool = True
    ) -> OptimizationResult:
        """
        Run grid sweep optimization.
        
        Physics-based constraints are automatically applied:
        - Battery size limited by PV daily generation × max_storage_days
        - Early stopping on diminishing returns
        """
        constraints = constraints or {}
        daily_pv_factor = constraints.get('daily_pv_factor', 2.71)  # kWh/kWp/day avg
        
        # Generate PV sizes to test
        pv_sizes = self._generate_pv_grid(bounds)
        
        if verbose:
            print(f"\n{'='*70}")
            print(f"🔍 {self.name} - Grid Sweep Optimization")
            print(f"{'='*70}")
            print(f"PV range: {bounds.pv_min_kwp} - {bounds.pv_max_kwp} kWp")
            print(f"Battery max: {bounds.battery_max_kwh} kWh")
            print(f"Priority: {self.priority}")
            if target_value is not None:
                print(f"Target: {abs(target_value):.1f}")
            print()
        
        all_results = []
        best_result = None
        best_score = float('inf') if self.priority == 'economy' else float('-inf')
        iterations = 0
        
        for pv_kwp in pv_sizes:
            # Calculate physics-based battery limit for this PV size
            daily_pv = pv_kwp * daily_pv_factor
            max_useful_battery = min(
                daily_pv * self.max_storage_days,
                bounds.battery_max_kwh
            )
            
            # Generate battery sizes for this PV
            battery_sizes = self._generate_battery_grid(bounds, max_useful_battery)
            
            prev_obj = None
            for battery_kwh in battery_sizes:
                iterations += 1
                obj_value = objective(pv_kwp, battery_kwh)
                
                all_results.append({
                    'pv_kwp': pv_kwp,
                    'battery_kwh': battery_kwh,
                    'objective': obj_value,
                    'cost_proxy': pv_kwp * 10 + battery_kwh * 4
                })
                
                # Check diminishing returns
                if prev_obj is not None and battery_kwh > 0:
                    improvement = abs(obj_value - prev_obj)
                    if improvement < self.diminishing_returns_threshold:
                        break  # Stop increasing battery for this PV size
                
                prev_obj = obj_value
                
                # Scoring based on priority
                is_better = False
                if self.priority == 'performance':
                    score = obj_value
                    if score < best_score:  # Minimizing (negative SS)
                        is_better = True
                else:  # economy
                    if target_value is not None and obj_value <= target_value:
                        cost = pv_kwp * 10 + battery_kwh * 4
                        if cost < best_score:
                            is_better = True
                            score = cost
                    else:
                        score = obj_value
                
                if is_better:
                    best_score = score
                    best_result = {
                        'pv_kwp': pv_kwp,
                        'battery_kwh': battery_kwh,
                        'objective': obj_value
                    }
                
                if verbose and pv_kwp == pv_sizes[-1]:  # Print for last PV size
                    print(f"  PV: {pv_kwp:.1f} kWp + Battery: {battery_kwh:.1f} kWh → Obj: {obj_value:.2f}")
        
        # If no result found (economy mode, target not reached)
        if best_result is None:
            # Fall back to best objective value
            best_idx = min(range(len(all_results)), key=lambda i: all_results[i]['objective'])
            best_result = all_results[best_idx]
        
        achieved_target = target_value is not None and best_result['objective'] <= target_value
        
        if verbose:
            print(f"\n{'='*70}")
            print(f"✅ Optimization Complete")
            print(f"{'='*70}")
            print(f"Optimal PV: {best_result['pv_kwp']} kWp")
            print(f"Optimal Battery: {best_result['battery_kwh']} kWh")
            print(f"Objective: {best_result['objective']:.2f}")
            print(f"Iterations: {iterations}")
            if target_value is not None:
                print(f"Target Achieved: {'Yes ✅' if achieved_target else 'No ⚠️'}")
        
        return OptimizationResult(
            optimal_pv_kwp=best_result['pv_kwp'],
            optimal_battery_kwh=best_result['battery_kwh'],
            objective_value=best_result['objective'],
            achieved_target=achieved_target,
            iterations=iterations,
            converged=True,
            all_evaluations=pd.DataFrame(all_results),
            recommendation=self._generate_recommendation(best_result, achieved_target, target_value)
        )
    
    def _generate_pv_grid(self, bounds: OptimizationBounds) -> list[float]:
        """Generate list of PV sizes to test."""
        sizes = []
        pv = bounds.pv_min_kwp
        while pv <= bounds.pv_max_kwp:
            sizes.append(round(pv, 2))
            pv += bounds.pv_step_kwp
        if sizes[-1] < bounds.pv_max_kwp:
            sizes.append(round(bounds.pv_max_kwp, 2))
        return sizes
    
    def _generate_battery_grid(
        self,
        bounds: OptimizationBounds,
        max_useful: float
    ) -> list[float]:
        """Generate list of battery sizes to test for given PV."""
        sizes = [0.0]  # Always test no battery
        battery = bounds.battery_step_kwh
        while battery <= max_useful:
            sizes.append(round(battery, 1))
            battery += bounds.battery_step_kwh
        if sizes[-1] < max_useful:
            sizes.append(round(max_useful, 1))
        return sizes
    
    def _generate_recommendation(
        self,
        best: dict,
        achieved: bool,
        target: Optional[float]
    ) -> str:
        """Generate human-readable recommendation."""
        if achieved:
            return f"Target achieved with {best['pv_kwp']} kWp PV and {best['battery_kwh']} kWh battery."
        elif target is not None:
            return f"Target not achievable. Best configuration: {best['pv_kwp']} kWp PV + {best['battery_kwh']} kWh battery."
        else:
            return f"Optimal configuration: {best['pv_kwp']} kWp PV + {best['battery_kwh']} kWh battery."
