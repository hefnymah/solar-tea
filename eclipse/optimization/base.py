"""
Optimization Base Classes
=========================
Abstract base class and common interfaces for all optimizers.

This module defines the contract that all optimization algorithms must follow,
enabling the Strategy pattern for swappable optimizers.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Optional, Callable, Any, TYPE_CHECKING
import pandas as pd

if TYPE_CHECKING:
    from eclipse.pvsim.results import SizingResult


@dataclass(frozen=True)
class OptimizationBounds:
    """
    Defines the search space for optimization.
    
    Attributes:
        pv_min_kwp: Minimum PV system size in kWp.
        pv_max_kwp: Maximum PV system size in kWp (often from roof constraint).
        battery_min_kwh: Minimum battery size in kWh (default: 0).
        battery_max_kwh: Maximum battery size in kWh.
        pv_step_kwp: PV size increment for grid-based methods.
        battery_step_kwh: Battery size increment for grid-based methods.
    """
    pv_min_kwp: float = 0.5
    pv_max_kwp: float = 20.0
    battery_min_kwh: float = 0.0
    battery_max_kwh: float = 30.0
    pv_step_kwp: float = 0.5
    battery_step_kwh: float = 2.5


@dataclass
class OptimizationResult:
    """
    Result of an optimization run.
    
    Attributes:
        optimal_pv_kwp: Recommended PV system size in kWp.
        optimal_battery_kwh: Recommended battery size in kWh.
        objective_value: Final value of the objective function.
        achieved_target: Whether the optimization target was achieved.
        metrics: Dictionary of performance metrics.
        iterations: Number of iterations/evaluations performed.
        converged: Whether the optimizer converged.
        sizing_result: Full SizingResult for the optimal configuration.
        all_evaluations: DataFrame of all tested configurations (optional).
        recommendation: Human-readable recommendation string.
    """
    optimal_pv_kwp: float
    optimal_battery_kwh: float
    objective_value: float
    achieved_target: bool
    metrics: dict = field(default_factory=dict)
    iterations: int = 0
    converged: bool = True
    sizing_result: Optional['SizingResult'] = None
    all_evaluations: Optional[pd.DataFrame] = None
    recommendation: str = ""
    
    def __str__(self) -> str:
        return (
            f"OptimizationResult(\n"
            f"  PV: {self.optimal_pv_kwp} kWp\n"
            f"  Battery: {self.optimal_battery_kwh} kWh\n"
            f"  Objective: {self.objective_value:.2f}\n"
            f"  Target Achieved: {self.achieved_target}\n"
            f"  Iterations: {self.iterations}\n"
            f")"
        )


class Optimizer(ABC):
    """
    Abstract base class for all optimization algorithms.
    
    Subclasses must implement the `optimize` method. This enables the
    Strategy pattern where different algorithms can be swapped without
    changing the calling code.
    
    Example:
        optimizer = SweepOptimizer(pv_step=0.5, battery_step=2.5)
        result = optimizer.optimize(
            objective=objective_function,
            bounds=OptimizationBounds(pv_max_kwp=10.0),
            target_value=80.0
        )
    """
    
    @abstractmethod
    def optimize(
        self,
        objective: Callable[[float, float], float],
        bounds: OptimizationBounds,
        target_value: Optional[float] = None,
        constraints: Optional[dict] = None,
        verbose: bool = True
    ) -> OptimizationResult:
        """
        Run optimization and return the best solution.
        
        Args:
            objective: Callable that takes (pv_kwp, battery_kwh) and returns
                      the objective value to minimize (use negative for maximize).
            bounds: Search space bounds for PV and battery sizes.
            target_value: Optional target value for the objective (e.g., 80% SS).
            constraints: Optional dictionary of additional constraints.
            verbose: If True, print progress information.
            
        Returns:
            OptimizationResult with optimal configuration and metrics.
        """
        pass
    
    @property
    @abstractmethod
    def name(self) -> str:
        """Human-readable name of the optimizer."""
        pass
    
    @property
    def supports_multi_objective(self) -> bool:
        """Whether this optimizer supports multi-objective optimization."""
        return False


class MultiObjectiveOptimizer(Optimizer):
    """
    Abstract base class for multi-objective optimizers.
    
    Extends Optimizer to support Pareto-optimal solutions.
    """
    
    @property
    def supports_multi_objective(self) -> bool:
        return True
    
    @abstractmethod
    def optimize_multi(
        self,
        objectives: list[Callable[[float, float], float]],
        bounds: OptimizationBounds,
        constraints: Optional[dict] = None,
        verbose: bool = True
    ) -> list[OptimizationResult]:
        """
        Run multi-objective optimization.
        
        Args:
            objectives: List of objective functions to minimize.
            bounds: Search space bounds.
            constraints: Optional constraints.
            verbose: If True, print progress information.
            
        Returns:
            List of OptimizationResult representing Pareto front.
        """
        pass
