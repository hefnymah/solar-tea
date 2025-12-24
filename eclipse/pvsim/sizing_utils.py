"""
Sizing Utilities
=================
Utility functions and classes for PV system sizing analysis.

This module provides reusable tools for:
- Generating test sizes for what-if scenarios
- Running scenario comparisons
- Calculating optimal configurations

Author: Eclipse Framework
"""

from __future__ import annotations
from typing import List, Optional, TYPE_CHECKING
from dataclasses import dataclass

if TYPE_CHECKING:
    from eclipse.pvsim.system_sizer import PVSystemSizer, SizingResult


@dataclass
class ScenarioResult:
    """Result of a single sizing scenario simulation."""
    size_kwp: float
    result: 'SizingResult'
    
    @property
    def annual_generation_kwh(self) -> float:
        return self.result.annual_generation_kwh
    
    @property
    def self_sufficiency_pct(self) -> float:
        return self.result.self_sufficiency_pct
    
    @property
    def self_consumption_pct(self) -> float:
        return self.result.self_consumption_pct
    
    @property
    def grid_import_kwh(self) -> float:
        return self.result.annual_grid_import_kwh
    
    @property
    def grid_export_kwh(self) -> float:
        return self.result.annual_grid_export_kwh


class SizingUtilities:
    """
    Utilities for PV system sizing analysis and what-if scenarios.
    
    Provides static methods for:
    - Generating test sizes based on roof capacity
    - Running batch scenario simulations
    - Finding optimal system sizes
    
    Example:
        >>> sizes = SizingUtilities.generate_test_sizes(max_kwp=50.0)
        >>> print(sizes)  # [12.5, 25.0, 37.5, 50.0]
        
        >>> results = SizingUtilities.run_scenarios(sizer, sizes)
        >>> for r in results:
        ...     print(f"{r.size_kwp:.1f} kWp → {r.self_sufficiency_pct:.1f}%")
    """
    
    @staticmethod
    def generate_test_sizes(
        max_kwp: float,
        percentages: List[float] = None,
        min_kwp: float = 1.0
    ) -> List[float]:
        """
        Generate test sizes as percentages of maximum capacity.
        
        Args:
            max_kwp: Maximum PV capacity in kWp
            percentages: List of percentages to test (default: [0.25, 0.50, 0.75, 1.0])
            min_kwp: Minimum size to test (default: 1.0 kWp)
            
        Returns:
            List of sizes in kWp to test
            
        Example:
            >>> SizingUtilities.generate_test_sizes(100.0)
            [25.0, 50.0, 75.0, 100.0]
            
            >>> SizingUtilities.generate_test_sizes(8.0, percentages=[0.5, 1.0])
            [4.0, 8.0]
        """
        if percentages is None:
            percentages = [0.25, 0.50, 0.75, 1.0]
        
        # Generate sizes, ensuring minimum threshold
        sizes = [max(min_kwp, max_kwp * p) for p in percentages]
        
        # Remove duplicates (can happen if max_kwp is small) and sort
        sizes = sorted(set(sizes))
        
        return sizes
    
    @staticmethod
    def generate_sizes_with_step(
        max_kwp: float,
        step_kwp: float = 5.0,
        min_kwp: float = 2.5
    ) -> List[float]:
        """
        Generate test sizes with fixed step increments.
        
        Useful for detailed analysis of larger roofs.
        
        Args:
            max_kwp: Maximum PV capacity in kWp
            step_kwp: Step size between tests (default: 5.0 kWp)
            min_kwp: Minimum size to test (default: 2.5 kWp)
            
        Returns:
            List of sizes in kWp to test
            
        Example:
            >>> SizingUtilities.generate_sizes_with_step(20.0, step_kwp=5.0)
            [5.0, 10.0, 15.0, 20.0]
        """
        import numpy as np
        
        start = max(min_kwp, step_kwp)
        sizes = list(np.arange(start, max_kwp + step_kwp, step_kwp))
        
        # Ensure max_kwp is included
        if sizes[-1] != max_kwp:
            sizes[-1] = max_kwp
        
        return sizes
    
    @staticmethod
    def run_scenarios(
        sizer: 'PVSystemSizer',
        sizes: List[float],
        battery_kwh: float = 0.0
    ) -> List[ScenarioResult]:
        """
        Run simulations for multiple system sizes.
        
        Args:
            sizer: PVSystemSizer instance
            sizes: List of PV sizes in kWp to test
            battery_kwh: Battery capacity (default: 0.0)
            
        Returns:
            List of ScenarioResult objects with simulation results
            
        Example:
            >>> sizer = PVSystemSizer(data, location, roof)
            >>> sizes = [5.0, 10.0, 15.0]
            >>> results = SizingUtilities.run_scenarios(sizer, sizes)
        """
        results = []
        for size in sizes:
            result = sizer.simulate(pv_kwp=size, battery_kwh=battery_kwh)
            results.append(ScenarioResult(size_kwp=size, result=result))
        return results
    
    @staticmethod
    def find_optimal_for_self_sufficiency(
        sizer: 'PVSystemSizer',
        target_pct: float,
        max_kwp: float,
        tolerance: float = 1.0,
        max_iterations: int = 20
    ) -> Optional[ScenarioResult]:
        """
        Find the optimal system size for a target self-sufficiency percentage.
        
        Uses binary search to efficiently find the size.
        
        Args:
            sizer: PVSystemSizer instance
            target_pct: Target self-sufficiency percentage (e.g., 70.0)
            max_kwp: Maximum PV capacity constraint
            tolerance: Acceptable deviation from target (default: 1.0%)
            max_iterations: Maximum search iterations (default: 20)
            
        Returns:
            ScenarioResult for optimal size, or None if target is unachievable
            
        Example:
            >>> result = SizingUtilities.find_optimal_for_self_sufficiency(
            ...     sizer, target_pct=80.0, max_kwp=50.0
            ... )
            >>> print(f"Optimal: {result.size_kwp:.1f} kWp")
        """
        low = 0.5  # Minimum practical size
        high = max_kwp
        best_result = None
        
        for _ in range(max_iterations):
            mid = (low + high) / 2
            result = sizer.simulate(pv_kwp=mid, battery_kwh=0.0)
            current_pct = result.self_sufficiency_pct
            
            if abs(current_pct - target_pct) <= tolerance:
                return ScenarioResult(size_kwp=mid, result=result)
            
            if current_pct < target_pct:
                low = mid
                best_result = ScenarioResult(size_kwp=mid, result=result)
            else:
                high = mid
                best_result = ScenarioResult(size_kwp=mid, result=result)
        
        return best_result
