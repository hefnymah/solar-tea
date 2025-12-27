"""
Battery Sizer
=============
OOP class for intelligent battery sizing based on multiple optimization targets:
1. Autonomy: Capacity needed for N days of grid independence.
2. Self-Sufficiency: Minimum size to achieve target % of load from PV+Battery.
3. Self-Consumption: Minimum size to use target % of PV locally.
"""

from dataclasses import dataclass
from typing import Optional, Tuple, Literal, List, Union
import pandas as pd
import numpy as np

from eclipse.battery.simple import SimpleBatterySimulator
from eclipse.battery.simple import SimpleBatterySimulator
try:
    from eclipse.battery.pysam import PySAMBatterySimulator
except ImportError:
    PySAMBatterySimulator = None

from eclipse.config.equipment_models import MockBattery
from eclipse.config.equipments import batteries


@dataclass
class SizingResult:
    """Result of battery sizing calculation."""
    recommended_kwh: float
    target_type: str
    target_value: float
    achieved_value: float
    chargeable_kwh: float
    autonomy_kwh: float
    self_sufficiency_pct: float
    self_consumption_pct: float
    grid_import_kwh: float
    grid_export_kwh: float
    is_target_achieved: bool


class BatterySizer:
    """
    Intelligent battery sizer with multiple optimization targets.
    
    Supports three sizing strategies:
    - 'autonomy': Size for N days of backup power.
    - 'self_sufficiency': Size to achieve target % of load from PV+Battery.
    - 'self_consumption': Size to use target % of PV locally.
    
    Example:
        >>> sizer = BatterySizer(pv_kwp=6.0, daily_load_kwh=15.0)
        >>> 
        >>> # Target 1 day autonomy
        >>> result = sizer.recommend(load_kw, pv_kw, target='autonomy', value=1.0)
        >>> 
        >>> # Target 80% self-sufficiency
        >>> result = sizer.recommend(load_kw, pv_kw, target='self_sufficiency', value=80.0)
        >>> 
        >>> # Compare multiple sizes
        >>> df = sizer.compare_sizes(load_kw, pv_kw, sizes=[5, 10, 15, 20, 25])
    """
    
    def __init__(
        self,
        pv_kwp: float,
        daily_load_kwh: float,
        max_soc: float = 90.0,
        min_soc: float = 10.0,
        efficiency: float = 0.95,
        chargeability_percentile: float = 0.80,
        simulator: Literal['simple', 'pysam'] = 'simple'
    ):
        """
        Initialize the battery sizer.
        
        Args:
            pv_kwp: PV system size in kWp
            daily_load_kwh: Average daily load in kWh
            max_soc: Maximum SOC target (default 90%)
            min_soc: Minimum SOC reserve (default 10%)
            efficiency: Round-trip efficiency for simulation (default 95%)
            chargeability_percentile: Percentile of excess PV days to use (default 80th)
            simulator: Simulation backend to use:
                - 'simple': Fast heuristic model (default, no external deps)
                - 'pysam': High-fidelity PySAM model (requires PySAM library)
        """
        self.pv_kwp = pv_kwp
        self.daily_load_kwh = daily_load_kwh
        self.max_soc = max_soc
        self.min_soc = min_soc
        self.efficiency = efficiency
        self.chargeability_percentile = chargeability_percentile
        self.simulator_type = simulator
        
        # Calculate SOC range fraction
        self.soc_range_fraction = (max_soc - min_soc) / 100.0
        
        # Create a mock battery for simulation
        self._mock_battery = MockBattery(
            name="SizerMock",
            nominal_energy_kwh=100.0,  # Will be overridden per simulation
            max_discharge_power_kw=50.0,
            max_charge_power_kw=50.0,
            min_soc=min_soc,
            max_soc=max_soc,
            performance={'round_trip_efficiency': efficiency}
        )
    
    def _simulate(self, load_kw: pd.Series, pv_kw: pd.Series, capacity_kwh: float) -> dict:
        """
        Run a quick simulation and return key metrics.
        
        Returns dict with: self_sufficiency, self_consumption, grid_import, grid_export
        """
        if capacity_kwh <= 0:
            # No battery case
            net = load_kw - pv_kw
            grid_import = net[net > 0].sum()
            grid_export = (-net[net < 0]).sum()
            total_load = load_kw.sum()
            total_pv = pv_kw.sum()
            
            self_suff = (1.0 - grid_import / total_load) * 100 if total_load > 0 else 100.0
            self_cons = ((total_pv - grid_export) / total_pv) * 100 if total_pv > 0 else 100.0
            
            return {
                'self_sufficiency': self_suff,
                'self_consumption': self_cons,
                'grid_import': grid_import,
                'grid_export': grid_export
            }
        
        # Run simulation with selected backend
        if self.simulator_type == 'pysam':
            if PySAMBatterySimulator is None:
                raise ImportError("PySAM not found. Cannot use 'pysam' simulator.")
            battery_model = batteries.default()
            sim = PySAMBatterySimulator(battery_model)
            # Auto-scale power limit based on capacity (0.5C rate = charge/discharge in 2 hours)
            # This ensures large batteries aren't bottlenecked by small power limits
            c_rate = 0.5  # Conservative C-rate
            auto_power_kw = capacity_kwh * c_rate
            results = sim.simulate(load_kw, pv_kw, system_kwh=capacity_kwh, 
                                   system_kw=auto_power_kw,
                                   max_soc=self.max_soc, min_soc=self.min_soc)
        else:
            sim = SimpleBatterySimulator(self._mock_battery, efficiency=self.efficiency)
            results = sim.simulate(load_kw, pv_kw, system_kwh=capacity_kwh)
        
        total_load = results['load'].sum()
        total_pv = results['pv'].sum()
        grid_import = results['grid_import'].sum()
        grid_export = results['grid_export'].sum()
        
        self_suff = (1.0 - grid_import / total_load) * 100 if total_load > 0 else 100.0
        self_cons = ((total_pv - grid_export) / total_pv) * 100 if total_pv > 0 else 100.0
        
        return {
            'self_sufficiency': self_suff,
            'self_consumption': self_cons,
            'grid_import': grid_import,
            'grid_export': grid_export
        }
    
    def calculate_chargeability(self, load_kw: pd.Series, pv_kw: pd.Series) -> Tuple[float, float]:
        """Calculate max capacity PV can reliably charge."""
        df = pd.DataFrame({'load': load_kw, 'pv': pv_kw})
        daily = df.resample('D').sum()
        daily['excess_pv'] = (daily['pv'] - daily['load']).clip(lower=0)
        chargeable_energy = daily['excess_pv'].quantile(self.chargeability_percentile)
        max_chargeable = chargeable_energy / self.soc_range_fraction
        return max_chargeable, chargeable_energy
    
    def calculate_autonomy(self, target_days: float) -> float:
        """Calculate capacity needed for N days autonomy."""
        required_effective = self.daily_load_kwh * target_days
        return required_effective / self.soc_range_fraction
    
    def compare_sizes(
        self, 
        load_kw: pd.Series, 
        pv_kw: pd.Series, 
        sizes: Optional[List[float]] = None,
        find_sweet_spot: bool = False
    ) -> pd.DataFrame:
        """
        Compare multiple battery sizes and return metrics for each.
        
        Args:
            load_kw: Load profile in kW
            pv_kw: PV generation profile in kW
            sizes: List of capacities to test. Options:
                - List[float]: Explicit list of sizes to test
                - 'auto' or None: Auto-generate based on system characteristics
            find_sweet_spot: If True, detect the optimal knee-point (best value)
            
        Returns:
            DataFrame with columns: capacity_kwh, self_sufficiency_pct, self_consumption_pct, 
                                    grid_import_kwh, grid_export_kwh
            If find_sweet_spot=True, adds 'is_sweet_spot' column
        """
        # Auto-generate sizes if not provided or 'auto'
        if sizes is None or sizes == 'auto':
            # Calculate system bounds
            chargeable_kwh, _ = self.calculate_chargeability(load_kw, pv_kw)
            
            # Upper bound: Max of (3x daily load) or (chargeable capacity + 50%)
            # These scale automatically with any system size
            upper_bound_load = self.daily_load_kwh * 3
            upper_bound_pv = chargeable_kwh * 1.5
            max_test = max(upper_bound_load, upper_bound_pv)  # No minimum - fully data-driven
            
            # Minimum practical size: 1 hour of average load (for very small systems)
            min_practical = self.daily_load_kwh / 24
            max_test = max(max_test, min_practical * 10)  # At least 10 hours of avg load
            
            # Generate ~12 evenly spaced test points, with smart step sizing
            num_points = 12
            step = max_test / num_points
            # Round step to a nice value (1, 2, 5, 10, 20, 50, 100, etc.)
            magnitude = 10 ** int(np.floor(np.log10(max(step, 0.1))))
            step = round(step / magnitude) * magnitude
            step = max(step, 1)  # At least 1 kWh steps
            
            sizes = [0] + list(np.arange(step, max_test + step, step))
            
            # Ensure we don't have too many points
            if len(sizes) > 15:
                sizes = [0] + list(np.linspace(step, max_test, 12))
        
        # Run simulations for each size
        results = []
        for cap in sizes:
            metrics = self._simulate(load_kw, pv_kw, cap)
            results.append({
                'capacity_kwh': cap,
                'self_sufficiency_pct': round(metrics['self_sufficiency'], 1),
                'self_consumption_pct': round(metrics['self_consumption'], 1),
                'grid_import_kwh': round(metrics['grid_import'], 0),
                'grid_export_kwh': round(metrics['grid_export'], 0)
            })
        
        df = pd.DataFrame(results)
        
        # Find sweet spot if requested
        if find_sweet_spot and len(df) > 2:
            # Calculate incremental benefit per kWh
            # Sweet spot = where adding more capacity gives diminishing returns
            df['delta_ss'] = df['self_sufficiency_pct'].diff()  # Improvement in SS
            df['delta_cap'] = df['capacity_kwh'].diff()  # Capacity increment
            df['efficiency'] = df['delta_ss'] / df['delta_cap'].replace(0, np.nan)  # %/kWh
            
            # Fill first row
            df.loc[0, 'efficiency'] = df.loc[1, 'efficiency'] if len(df) > 1 else 0
            
            # Sweet spot heuristics:
            # 1. If we reach 95%+ self-sufficiency, that's the cap
            # 2. Otherwise, find where efficiency drops below threshold (0.5%/kWh)
            # 3. Simple knee detection: largest efficiency drop
            
            sweet_spot_idx = 0
            
            # Calculate dynamic efficiency threshold based on system scale
            # For a 15 kWh/day system, 1%/kWh is good; for 250 kWh/day, 0.1%/kWh is good
            # Use: threshold = 10 / daily_load (inversely proportional to system size)
            eff_threshold = min(1.0, max(0.05, 10.0 / self.daily_load_kwh))
            
            # Check if we hit 95% self-sufficiency (universal practical limit)
            high_ss_rows = df[df['self_sufficiency_pct'] >= 95.0]
            if len(high_ss_rows) > 0:
                sweet_spot_idx = high_ss_rows.index[0]
            else:
                # Find knee point: where efficiency drops below dynamic threshold
                df['eff_change'] = df['efficiency'].diff()
                
                if len(df) > 2:
                    # Find the point where efficiency becomes < threshold
                    low_eff_rows = df[(df['efficiency'] < eff_threshold) & (df['capacity_kwh'] > 0)]
                    if len(low_eff_rows) > 0:
                        sweet_spot_idx = low_eff_rows.index[0] - 1
                        sweet_spot_idx = max(0, sweet_spot_idx)
                    else:
                        # If no low efficiency found, use second-to-last row
                        sweet_spot_idx = len(df) - 2
            
            df['is_sweet_spot'] = False
            df.loc[sweet_spot_idx, 'is_sweet_spot'] = True
            
            # Clean up intermediate columns
            df = df.drop(columns=['delta_ss', 'delta_cap', 'efficiency', 'eff_change'], errors='ignore')
        
        return df
    
    def recommend(
        self, 
        load_kw: pd.Series, 
        pv_kw: pd.Series, 
        target: Literal['autonomy', 'self_sufficiency', 'self_consumption', 'optimal'] = 'autonomy',
        value: float = 1.0
    ) -> SizingResult:
        """
        Recommend optimal battery capacity based on the selected target.
        
        Args:
            load_kw: Load profile in kW
            pv_kw: PV generation profile in kW
            target: Optimization target:
                - 'autonomy': Size for N days backup (value = days)
                - 'self_sufficiency': Size to achieve target % (value = percentage)
                - 'self_consumption': Size to use target % of PV (value = percentage)
            value: Target value (days for autonomy, percentage for others)
            
        Returns:
            SizingResult with all metrics and recommendation
        """
        # Get chargeability limit regardless of target
        chargeable_kwh, _ = self.calculate_chargeability(load_kw, pv_kw)
        autonomy_kwh = self.calculate_autonomy(1.0)  # Default 1 day for reference
        
        if target == 'autonomy':
            # Original logic: Compare chargeability vs autonomy needs
            autonomy_kwh = self.calculate_autonomy(value)
            
            if autonomy_kwh <= chargeable_kwh:
                recommended = autonomy_kwh
                is_achieved = True
            else:
                recommended = chargeable_kwh
                is_achieved = False
            
            recommended = round(recommended * 2) / 2
            metrics = self._simulate(load_kw, pv_kw, recommended)
            
            return SizingResult(
                recommended_kwh=recommended,
                target_type='autonomy',
                target_value=value,
                achieved_value=value if is_achieved else (recommended * self.soc_range_fraction / self.daily_load_kwh),
                chargeable_kwh=chargeable_kwh,
                autonomy_kwh=autonomy_kwh,
                self_sufficiency_pct=metrics['self_sufficiency'],
                self_consumption_pct=metrics['self_consumption'],
                grid_import_kwh=metrics['grid_import'],
                grid_export_kwh=metrics['grid_export'],
                is_target_achieved=is_achieved
            )
        
        elif target in ['self_sufficiency', 'self_consumption']:
            # Sweep to find minimum capacity that achieves target
            test_sizes = [0, 5, 10, 15, 20, 25, 30, 40, 50, 60, 80, 100]
            metric_key = 'self_sufficiency' if target == 'self_sufficiency' else 'self_consumption'
            
            recommended = None
            best_metrics = None
            
            for cap in test_sizes:
                metrics = self._simulate(load_kw, pv_kw, cap)
                achieved = metrics[metric_key]
                
                if achieved >= value:
                    recommended = cap
                    best_metrics = metrics
                    break
            
            # If target not achieved, use largest tested
            if recommended is None:
                recommended = test_sizes[-1]
                best_metrics = self._simulate(load_kw, pv_kw, recommended)
            
            is_achieved = best_metrics[metric_key] >= value
            
            return SizingResult(
                recommended_kwh=recommended,
                target_type=target,
                target_value=value,
                achieved_value=best_metrics[metric_key],
                chargeable_kwh=chargeable_kwh,
                autonomy_kwh=autonomy_kwh,
                self_sufficiency_pct=best_metrics['self_sufficiency'],
                self_consumption_pct=best_metrics['self_consumption'],
                grid_import_kwh=best_metrics['grid_import'],
                grid_export_kwh=best_metrics['grid_export'],
                is_target_achieved=is_achieved
            )
        
        elif target == 'optimal':
            # Find optimal size using marginal efficiency analysis
            # This finds where adding more capacity gives diminishing returns
            
            # Auto-scale test sizes based on daily load and chargeability
            upper_bound_load = self.daily_load_kwh * 3
            upper_bound_pv = chargeable_kwh * 1.5
            max_test = max(upper_bound_load, upper_bound_pv)
            
            # Minimum practical test range: at least 10 hours of avg load
            min_practical = self.daily_load_kwh / 24
            max_test = max(max_test, min_practical * 10)
            
            # Generate ~12 test points with smart step sizing
            num_points = 12
            step = max_test / num_points
            # Round step to a nice value (1, 2, 5, 10, 20, 50, 100, etc.)
            if step > 0.1:
                magnitude = 10 ** int(np.floor(np.log10(step)))
                step = round(step / magnitude) * magnitude
            step = max(step, 1)  # At least 1 kWh steps
            
            test_sizes = [0] + list(np.arange(step, max_test + step, step))
            
            results_list = []
            for cap in test_sizes:
                metrics = self._simulate(load_kw, pv_kw, cap)
                results_list.append({
                    'capacity': cap,
                    'ss': metrics['self_sufficiency'],
                    'sc': metrics['self_consumption'],
                    'import': metrics['grid_import'],
                    'export': metrics['grid_export']
                })
            
            # Calculate marginal efficiency (% self-sufficiency improvement per kWh)
            optimal_idx = 0
            best_metrics = None
            
            # Dynamic efficiency threshold: scales inversely with system size
            # For 15 kWh/day: threshold = 0.67%/kWh
            # For 250 kWh/day: threshold = 0.04%/kWh
            eff_threshold = min(1.0, max(0.02, 10.0 / self.daily_load_kwh))
            
            for i in range(1, len(results_list)):
                prev = results_list[i-1]
                curr = results_list[i]
                
                delta_ss = curr['ss'] - prev['ss']
                delta_cap = curr['capacity'] - prev['capacity']
                
                if delta_cap > 0:
                    efficiency = delta_ss / delta_cap  # %/kWh
                    
                    # Stop when efficiency drops below threshold
                    # OR when self-sufficiency >= 95%
                    if efficiency < eff_threshold or curr['ss'] >= 95.0:
                        optimal_idx = i - 1  # Use the previous size (before diminishing returns)
                        break
                    
                    optimal_idx = i
            
            # Ensure we don't return 0 if there's meaningful benefit to having a battery
            # Check if 5% improvement in self-sufficiency is achievable
            if optimal_idx == 0 and len(results_list) > 1:
                if results_list[1]['ss'] > results_list[0]['ss'] + 5:
                    optimal_idx = 1
            
            recommended = results_list[optimal_idx]['capacity']
            best_metrics = self._simulate(load_kw, pv_kw, recommended)
            
            return SizingResult(
                recommended_kwh=recommended,
                target_type='optimal',
                target_value=0,  # No target value for optimal
                achieved_value=best_metrics['self_sufficiency'],
                chargeable_kwh=chargeable_kwh,
                autonomy_kwh=autonomy_kwh,
                self_sufficiency_pct=best_metrics['self_sufficiency'],
                self_consumption_pct=best_metrics['self_consumption'],
                grid_import_kwh=best_metrics['grid_import'],
                grid_export_kwh=best_metrics['grid_export'],
                is_target_achieved=True  # Optimal is always "achieved"
            )
        
        else:
            raise ValueError(f"Unknown target: {target}. Use 'autonomy', 'self_sufficiency', 'self_consumption', or 'optimal'.")
    
    def summary(self, result: SizingResult) -> str:
        """Generate a formatted summary string of the sizing result."""
        if result.target_type == 'optimal':
            lines = [
                f"\n>>> Target: OPTIMAL (best value battery size)",
                f">>> RECOMMENDED BATTERY SIZE: {result.recommended_kwh} kWh",
                "",
                "Metrics at recommended size:",
                f"  Self-Sufficiency:  {result.self_sufficiency_pct:.1f}%",
                f"  Self-Consumption:  {result.self_consumption_pct:.1f}%",
                f"  Grid Import:       {result.grid_import_kwh:.0f} kWh/year",
                f"  Grid Export:       {result.grid_export_kwh:.0f} kWh/year",
                "",
                "✅ Optimal size found (best efficiency before diminishing returns)"
            ]
        else:
            lines = [
                f"\n>>> Target: {result.target_type.upper()} = {result.target_value}",
                f">>> RECOMMENDED BATTERY SIZE: {result.recommended_kwh} kWh",
                "",
                "Metrics at recommended size:",
                f"  Self-Sufficiency:  {result.self_sufficiency_pct:.1f}%",
                f"  Self-Consumption:  {result.self_consumption_pct:.1f}%",
                f"  Grid Import:       {result.grid_import_kwh:.0f} kWh/year",
                f"  Grid Export:       {result.grid_export_kwh:.0f} kWh/year",
                ""
            ]
            
            if result.is_target_achieved:
                lines.append(f"✅ Target achieved!")
            else:
                lines.append(f"⚠️  Target NOT fully achieved. Achieved: {result.achieved_value:.1f}")
                if result.target_type == 'autonomy':
                    lines.append(f"    PV ({self.pv_kwp} kWp) can only reliably charge {result.chargeable_kwh:.1f} kWh.")
        
        return "\n".join(lines)
