"""
Objective Functions
===================
Defines objective functions used by optimizers.

Objective functions encapsulate the evaluation logic and can be
composed or customized without modifying the optimizer.
"""

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, Optional

if TYPE_CHECKING:
    from eclipse.pvsim.system_sizer import PVSystemSizer


class ObjectiveFunction(ABC):
    """
    Abstract base class for objective functions.
    
    Objective functions evaluate a (pv_kwp, battery_kwh) configuration
    and return a scalar value. By convention, optimizers minimize the
    objective, so use negative values for maximization problems.
    """
    
    @abstractmethod
    def evaluate(self, pv_kwp: float, battery_kwh: float) -> float:
        """
        Evaluate the objective for given configuration.
        
        Args:
            pv_kwp: PV system size in kWp.
            battery_kwh: Battery size in kWh.
            
        Returns:
            Objective value (lower is better for minimization).
        """
        pass
    
    @property
    @abstractmethod
    def name(self) -> str:
        """Human-readable name of the objective."""
        pass
    
    @property
    def is_minimization(self) -> bool:
        """Whether this objective should be minimized (True) or maximized (False)."""
        return True


class SelfSufficiencyObjective(ObjectiveFunction):
    """
    Maximize self-sufficiency percentage.
    
    Self-sufficiency = (consumption - grid_import) / consumption × 100
    
    Returns negative value since optimizers minimize.
    """
    
    def __init__(self, simulator: 'PVSystemSizer'):
        """
        Initialize with a PV system simulator.
        
        Args:
            simulator: PVSystemSizer instance for running simulations.
        """
        self._simulator = simulator
    
    def evaluate(self, pv_kwp: float, battery_kwh: float) -> float:
        """Evaluate self-sufficiency (returns negative for maximization)."""
        result = self._simulator.simulate(pv_kwp, battery_kwh)
        return -result.self_sufficiency_pct  # Negative for maximization
    
    @property
    def name(self) -> str:
        return "Self-Sufficiency"
    
    @property
    def is_minimization(self) -> bool:
        return False  # We actually want to maximize


class SelfConsumptionObjective(ObjectiveFunction):
    """
    Maximize self-consumption percentage.
    
    Self-consumption = self_consumed / pv_generation × 100
    
    Returns negative value since optimizers minimize.
    """
    
    def __init__(self, simulator: 'PVSystemSizer'):
        self._simulator = simulator
    
    def evaluate(self, pv_kwp: float, battery_kwh: float) -> float:
        result = self._simulator.simulate(pv_kwp, battery_kwh)
        return -result.self_consumption_pct
    
    @property
    def name(self) -> str:
        return "Self-Consumption"
    
    @property
    def is_minimization(self) -> bool:
        return False


class GridImportObjective(ObjectiveFunction):
    """
    Minimize annual grid import.
    """
    
    def __init__(self, simulator: 'PVSystemSizer'):
        self._simulator = simulator
    
    def evaluate(self, pv_kwp: float, battery_kwh: float) -> float:
        result = self._simulator.simulate(pv_kwp, battery_kwh)
        return result.annual_grid_import_kwh
    
    @property
    def name(self) -> str:
        return "Grid Import"


class CombinedObjective(ObjectiveFunction):
    """
    Weighted combination of multiple objectives.
    
    Useful for simple multi-objective optimization without Pareto.
    """
    
    def __init__(
        self,
        objectives: list[ObjectiveFunction],
        weights: Optional[list[float]] = None
    ):
        self._objectives = objectives
        self._weights = weights or [1.0] * len(objectives)
        
        if len(self._weights) != len(self._objectives):
            raise ValueError("Number of weights must match number of objectives")
    
    def evaluate(self, pv_kwp: float, battery_kwh: float) -> float:
        total = 0.0
        for obj, weight in zip(self._objectives, self._weights):
            total += weight * obj.evaluate(pv_kwp, battery_kwh)
        return total
    
    @property
    def name(self) -> str:
        names = [obj.name for obj in self._objectives]
        return f"Combined({', '.join(names)})"
