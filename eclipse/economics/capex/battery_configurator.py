"""
Battery Configurator
====================
Translates target battery capacity into optimal commercial configurations.

Given a target (e.g., 12.5 kWh), finds the minimal configuration that meets
or exceeds the target from available modular battery systems.
"""

from dataclasses import dataclass
from typing import List, Optional
import math

from eclipse.config.equipments.batteries import (
    ModularBatterySpec,
    BATTERY_CATALOG,
    DEFAULT_COMMERCIAL_SPEC
)


@dataclass(frozen=True)
class BatteryConfiguration:
    """
    Concrete configuration for a battery installation.
    
    Represents the actual commercial quote with specific module/tower counts.
    """
    spec: ModularBatterySpec
    modules_per_tower: int
    tower_count: int
    
    @property
    def total_modules(self) -> int:
        """Total number of battery modules."""
        return self.modules_per_tower * self.tower_count
    
    @property
    def total_capacity_kwh(self) -> float:
        """Total system capacity in kWh."""
        return self.spec.capacity_kwh * self.total_modules
    
    @property
    def total_power_kw(self) -> float:
        """Total continuous power in kW."""
        return self.spec.power_kw * self.total_modules
    
    @property
    def base_cost_chf(self) -> float:
        """Base cost without margin (CHF)."""
        return self.spec.price_per_module_chf * self.total_modules
    
    @property
    def total_weight_kg(self) -> float:
        """Total weight of all modules."""
        return self.spec.weight_kg * self.total_modules
    
    @property
    def oversizing_pct(self) -> float:
        """How much larger than minimum required (for display)."""
        # This is set by the configurator based on target
        return getattr(self, '_oversizing_pct', 0.0)
    
    def __str__(self) -> str:
        tower_str = f"{self.tower_count} tower{'s' if self.tower_count > 1 else ''}"
        return (f"{self.spec.brand} {self.spec.model}: "
                f"{self.total_modules}× modules ({tower_str}) = "
                f"{self.total_capacity_kwh:.1f} kWh")


@dataclass(frozen=True)
class BatteryCapexResult:
    """
    CAPEX breakdown for a battery configuration.
    """
    configuration: BatteryConfiguration
    base_cost_chf: float
    margin_amount_chf: float
    total_cost_chf: float
    target_kwh: float
    
    @property
    def oversizing_kwh(self) -> float:
        """How much capacity exceeds target."""
        return self.configuration.total_capacity_kwh - self.target_kwh
    
    @property
    def cost_per_kwh_effective(self) -> float:
        """Effective cost per kWh including margin."""
        if self.configuration.total_capacity_kwh > 0:
            return self.total_cost_chf / self.configuration.total_capacity_kwh
        return 0.0


class BatteryConfigurator:
    """
    Translates target capacity into optimal commercial configurations.
    
    Algorithm:
    1. Filter specs that CAN reach target capacity
    2. For each: find MINIMAL module/tower combo >= target
    3. Score by cost efficiency (lower cost/kWh = better)
    4. Return ranked recommendations
    
    Example:
        configurator = BatteryConfigurator()
        configs = configurator.recommend(target_kwh=12.5, top_n=3)
        for cfg in configs:
            print(f"{cfg} - CHF {cfg.base_cost_chf:,.0f}")
    """
    
    def __init__(self, catalog: List[ModularBatterySpec] = None):
        """
        Initialize with battery catalog.
        
        Args:
            catalog: List of available battery specs. Defaults to BATTERY_CATALOG.
        """
        self.catalog = catalog if catalog is not None else BATTERY_CATALOG
    
    def find_configuration(
        self,
        target_kwh: float,
        spec: ModularBatterySpec
    ) -> Optional[BatteryConfiguration]:
        """
        Find the minimal configuration for a specific battery spec.
        
        Args:
            target_kwh: Desired capacity in kWh.
            spec: The battery spec to configure.
            
        Returns:
            BatteryConfiguration if achievable, None if target exceeds max capacity.
        """
        if target_kwh <= 0:
            # Return minimum configuration
            return BatteryConfiguration(
                spec=spec,
                modules_per_tower=spec.min_modules,
                tower_count=1
            )
        
        # Check if target is achievable
        if target_kwh > spec.max_system_capacity_kwh:
            return None
        
        # Find minimal configuration
        # Strategy: Try fewest towers first, then fewest modules
        best_config = None
        best_capacity = float('inf')
        
        for towers in range(1, spec.max_towers + 1):
            for modules in range(spec.min_modules, spec.max_modules_per_tower + 1):
                capacity = spec.capacity_kwh * modules * towers
                
                if capacity >= target_kwh and capacity < best_capacity:
                    best_capacity = capacity
                    best_config = BatteryConfiguration(
                        spec=spec,
                        modules_per_tower=modules,
                        tower_count=towers
                    )
        
        return best_config
    
    def recommend(
        self,
        target_kwh: float,
        preferred_brand: Optional[str] = None,
        max_budget_chf: Optional[float] = None,
        top_n: int = 3
    ) -> List[BatteryConfiguration]:
        """
        Return top N cost-efficient configurations for target capacity.
        
        Args:
            target_kwh: Desired capacity in kWh.
            preferred_brand: Optional brand filter (case-insensitive).
            max_budget_chf: Optional maximum budget constraint.
            top_n: Number of recommendations to return.
            
        Returns:
            List of BatteryConfiguration sorted by cost efficiency.
        """
        candidates = []
        
        # Filter catalog
        specs = self.catalog
        if preferred_brand:
            specs = [s for s in specs if s.brand.lower() == preferred_brand.lower()]
        
        for spec in specs:
            config = self.find_configuration(target_kwh, spec)
            if config is None:
                continue
            
            # Apply budget filter
            if max_budget_chf and config.base_cost_chf > max_budget_chf:
                continue
            
            # Calculate score (lower = better)
            # Score = cost_per_kwh + oversizing_penalty
            cost_per_kwh = config.base_cost_chf / config.total_capacity_kwh
            oversizing = config.total_capacity_kwh - target_kwh
            oversizing_penalty = (oversizing / target_kwh) * 50  # 50 CHF penalty per % oversizing
            
            score = cost_per_kwh + oversizing_penalty
            
            candidates.append((config, score))
        
        # Sort by score (lower = better)
        candidates.sort(key=lambda x: x[1])
        
        return [cfg for cfg, _ in candidates[:top_n]]
    
    def calculate_capex(
        self,
        target_kwh: float,
        spec: ModularBatterySpec = None,
        margin_pct: float = 0.0
    ) -> Optional[BatteryCapexResult]:
        """
        Calculate CAPEX for a battery configuration.
        
        Args:
            target_kwh: Desired capacity in kWh.
            spec: Specific battery spec, or None to auto-select best.
            margin_pct: Profit margin as decimal (e.g., 0.20 for 20%).
            
        Returns:
            BatteryCapexResult with cost breakdown.
        """
        if spec:
            config = self.find_configuration(target_kwh, spec)
        else:
            recommendations = self.recommend(target_kwh, top_n=1)
            config = recommendations[0] if recommendations else None
        
        if config is None:
            return None
        
        base_cost = config.base_cost_chf
        margin = base_cost * margin_pct
        total = base_cost + margin
        
        return BatteryCapexResult(
            configuration=config,
            base_cost_chf=base_cost,
            margin_amount_chf=margin,
            total_cost_chf=total,
            target_kwh=target_kwh
        )
