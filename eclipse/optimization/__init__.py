"""
Optimization Module
===================
Abstract base classes and interfaces for optimization algorithms.

This module provides a pluggable optimization framework that separates
optimization logic from physics simulation.

Available Optimizers:
- SweepOptimizer: Grid-based sweep (default)
- JAYAOptimizer: JAYA algorithm (future)
- NSGAIIOptimizer: NSGA-II multi-objective (future)
- MILPOptimizer: Mixed-Integer Linear Programming (future)
"""

from eclipse.optimization.base import (
    Optimizer,
    OptimizationResult,
    OptimizationBounds,
)
from eclipse.optimization.objectives import (
    ObjectiveFunction,
    SelfSufficiencyObjective,
    SelfConsumptionObjective,
)
from eclipse.optimization.sweep import SweepOptimizer

__all__ = [
    # Base classes
    'Optimizer',
    'OptimizationResult',
    'OptimizationBounds',
    # Objective functions
    'ObjectiveFunction',
    'SelfSufficiencyObjective',
    'SelfConsumptionObjective',
    # Optimizers
    'SweepOptimizer',
]
