"""
PV System Sizing Module
=======================
High-quality OOP module for sizing PV systems based on consumption data.

Integrates with eclipse.consumption.ConsumptionData and uses pvlib for
accurate generation simulation.

Example Usage:
    from eclipse.consumption import ConsumptionData
    from eclipse.pvsim import PVSystemSizer, LocationConfig, RoofConfig
    
    data = ConsumptionData.load("consumption.csv")
    sizer = PVSystemSizer(
        consumption_data=data,
        location=LocationConfig(latitude=47.38, longitude=8.54),
        roof=RoofConfig(tilt=30, azimuth=180, max_area_m2=50)
    )
    
    result = sizer.size_for_self_sufficiency(target_percent=80)
    print(f"Recommended: {result.recommended_kwp} kWp")
    print(f"Self-sufficiency: {result.self_sufficiency_pct:.1f}%")
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional, Dict, Any, TYPE_CHECKING, Union
import pandas as pd
import numpy as np

import pvlib
from pvlib.location import Location
from pvlib.pvsystem import PVSystem
from pvlib.modelchain import ModelChain
from pvlib.temperature import TEMPERATURE_MODEL_PARAMETERS

if TYPE_CHECKING:
    from eclipse.consumption.data import ConsumptionData


# =============================================================================
# Roof Fitting Utilities
# =============================================================================

def suggest_module_layout(
    roof_width_m: float,
    roof_height_m: float,
    module_width_m: float,
    module_height_m: float,
    setback_m: float = 0.5
) -> tuple[str, int, float]:
    """
    Calculate optimal module layout for a rectangular roof.
    
    Args:
        roof_width_m: Roof width in meters.
        roof_height_m: Roof height in meters.
        module_width_m: Module width in meters.
        module_height_m: Module height in meters.
        setback_m: Safety setback from roof edges in meters (default: 0.5m).
        
    Returns:
        Tuple of (orientation, num_modules, total_area_m2):
        - orientation: 'Portrait' or 'Landscape'
        - num_modules: Maximum number of modules that fit
        - total_area_m2: Total area covered by modules
        
    Example:
        >>> orientation, count, area = suggest_module_layout(10, 6, 1.7, 1.0, 0.5)
        >>> print(f"{orientation}: {count} modules, {area:.1f} m²")
        Portrait: 30 modules, 51.0 m²
    """
    import math
    
    # Calculate usable area after setback
    usable_width = roof_width_m - (2 * setback_m)
    usable_height = roof_height_m - (2 * setback_m)
    
    if usable_width <= 0 or usable_height <= 0:
        return "Portrait", 0, 0.0
    
    # Portrait orientation (module in normal orientation)
    cols_p = math.floor(usable_width / module_width_m)
    rows_p = math.floor(usable_height / module_height_m)
    count_portrait = cols_p * rows_p
    
    # Landscape orientation (module rotated 90°)
    cols_l = math.floor(usable_width / module_height_m)
    rows_l = math.floor(usable_height / module_width_m)
    count_landscape = cols_l * rows_l
    
    # Choose orientation with more modules
    if count_landscape > count_portrait:
        num_modules = count_landscape
        orientation = "Landscape"
    else:
        num_modules = count_portrait
        orientation = "Portrait"
    
    # Calculate total area
    total_area_m2 = num_modules * (module_width_m * module_height_m)
    
    return orientation, num_modules, total_area_m2


@dataclass(frozen=True)
class LocationConfig:
    """
    Immutable location configuration for PV simulation.
    
    Attributes:
        latitude: Site latitude in decimal degrees.
        longitude: Site longitude in decimal degrees.
        altitude: Site altitude in meters (default: 400m).
        timezone: Timezone string (default: 'Europe/Zurich').
    """
    latitude: float
    longitude: float
    altitude: float = 400
    timezone: str = 'Europe/Zurich'
    
    def __post_init__(self):
        if not -90 <= self.latitude <= 90:
            raise ValueError(f"Latitude must be between -90 and 90, got {self.latitude}")
        if not -180 <= self.longitude <= 180:
            raise ValueError(f"Longitude must be between -180 and 180, got {self.longitude}")


@dataclass(frozen=True)
class RoofConfig:
    """
    Immutable roof configuration for PV system.
    
    Attributes:
        tilt: Roof tilt angle in degrees (0=horizontal, 90=vertical).
        azimuth: Azimuth angle in degrees (180=South, 90=East, 270=West).
        max_area_m2: Maximum available roof area in m² (optional).
        module_efficiency: Module efficiency (default: 0.20 = 20%).
        performance_ratio: System performance ratio accounting for losses (default: 0.75).
    """
    tilt: float
    azimuth: float
    max_area_m2: Optional[float] = None
    module_efficiency: float = 0.20
    performance_ratio: float = 0.75
    
    def __post_init__(self):
        if not 0 <= self.tilt <= 90:
            raise ValueError(f"Tilt must be between 0 and 90 degrees, got {self.tilt}")
        if not 0 <= self.azimuth <= 360:
            raise ValueError(f"Azimuth must be between 0 and 360 degrees, got {self.azimuth}")
        if self.max_area_m2 is not None and self.max_area_m2 <= 0:
            raise ValueError(f"max_area_m2 must be positive, got {self.max_area_m2}")
        if not 0 < self.module_efficiency <= 1:
            raise ValueError(f"module_efficiency must be between 0 and 1, got {self.module_efficiency}")
        if not 0 < self.performance_ratio <= 1:
            raise ValueError(f"performance_ratio must be between 0 and 1, got {self.performance_ratio}")
    
    @property
    def max_capacity_kwp(self) -> Optional[float]:
        """Maximum system capacity based on roof area (if specified)."""
        if self.max_area_m2 is None:
            return None
        return self.max_area_m2 * self.module_efficiency


@dataclass(frozen=True)
class BatteryConfig:
    """
    Battery configuration for energy storage.
    
    Two modes:
    1. Auto-size (default): Capacity determined by BatterySizer after PV simulation
    2. Manual: Specify capacity_kwh and power_kw explicitly
    
    Example:
        # Auto-size (recommended)
        battery = BatteryConfig(max_soc=90, min_soc=10, simulator='simple')
        
        # Manual
        battery = BatteryConfig(capacity_kwh=13.5, power_kw=5.0, max_soc=90, min_soc=10)
    
    Attributes:
        capacity_kwh: Battery capacity in kWh (None = auto-size).
        power_kw: Max charge/discharge power in kW (None = derive from capacity at 0.5C).
        efficiency: Round-trip efficiency (default: 0.95 = 95%).
        min_soc: Minimum state of charge percentage (default: 10%).
        max_soc: Maximum state of charge percentage (default: 90%).
        sizing_target: Target for auto-sizing: 'optimal', 'autonomy', 'self_sufficiency'.
        simulator: Simulator backend: 'simple' (fast) or 'pysam' (accurate).
    """
    # Manual mode (optional - None means auto-size)
    capacity_kwh: Optional[float] = None
    power_kw: Optional[float] = None
    
    # Common settings
    efficiency: float = 0.95
    min_soc: float = 10.0
    max_soc: float = 90.0
    
    # Auto-sizing settings
    sizing_target: str = 'optimal'
    simulator: str = 'simple'
    
    @property
    def auto_size(self) -> bool:
        """Returns True if capacity should be auto-determined."""
        return self.capacity_kwh is None
    
    def __post_init__(self):
        # Validate only if manual mode
        if self.capacity_kwh is not None and self.capacity_kwh <= 0:
            raise ValueError(f"capacity_kwh must be positive, got {self.capacity_kwh}")
        if self.power_kw is not None and self.power_kw <= 0:
            raise ValueError(f"power_kw must be positive, got {self.power_kw}")
        if not 0 < self.efficiency <= 1:
            raise ValueError(f"efficiency must be between 0 and 1, got {self.efficiency}")
        if not 0 <= self.min_soc < self.max_soc <= 100:
            raise ValueError(f"Invalid SOC range: min={self.min_soc}, max={self.max_soc}")
        if self.sizing_target not in ('optimal', 'autonomy', 'self_sufficiency', 'self_consumption'):
            raise ValueError(f"Invalid sizing_target: {self.sizing_target}")
        if self.simulator not in ('simple', 'pysam'):
            raise ValueError(f"Invalid simulator: {self.simulator}")


@dataclass(frozen=True)
class SizingResult:
    """
    Immutable result of a PV system sizing calculation.
    
    Contains comprehensive metrics for system performance and energy flows.
    
    Attributes:
        recommended_kwp: Recommended system size in kWp.
        annual_generation_kwh: Expected annual PV generation in kWh.
        annual_consumption_kwh: Total annual consumption in kWh.
        self_sufficiency_pct: Percentage of consumption covered by PV (0-100).
        self_consumption_pct: Percentage of PV generation used locally (0-100).
        annual_self_consumed_kwh: Energy consumed directly from PV.
        annual_grid_import_kwh: Energy imported from grid.
        annual_grid_export_kwh: Energy exported to grid.
        specific_yield_kwh_per_kwp: Annual yield per kWp installed.
        capacity_factor: Actual generation / theoretical maximum.
        monthly_profile: DataFrame with monthly breakdown.
        hourly_data: DataFrame with hourly PV and consumption data.
        constrained_by_roof: Whether sizing was limited by roof area.
    """
    recommended_kwp: float
    annual_generation_kwh: float
    annual_consumption_kwh: float
    self_sufficiency_pct: float
    self_consumption_pct: float
    annual_self_consumed_kwh: float
    annual_grid_import_kwh: float
    annual_grid_export_kwh: float
    specific_yield_kwh_per_kwp: float
    capacity_factor: float
    monthly_profile: pd.DataFrame
    hourly_data: pd.DataFrame
    constrained_by_roof: bool = False
    # Battery-specific metrics (optional)
    battery_enabled: bool = False
    battery_capacity_kwh: Optional[float] = None
    battery_soc_profile: Optional[pd.Series] = None
    battery_charge_kwh: Optional[float] = None
    battery_discharge_kwh: Optional[float] = None
    battery_cycles: Optional[float] = None
    
    def __str__(self) -> str:
        return (
            f"PV Sizing Result:\n"
            f"  System Size: {self.recommended_kwp:.2f} kWp\n"
            f"  Annual Generation: {self.annual_generation_kwh:.0f} kWh\n"
            f"  Annual Consumption: {self.annual_consumption_kwh:.0f} kWh\n"
            f"  Self-Sufficiency: {self.self_sufficiency_pct:.1f}%\n"
            f"  Self-Consumption: {self.self_consumption_pct:.1f}%\n"
            f"  Grid Import: {self.annual_grid_import_kwh:.0f} kWh\n"
            f"  Grid Export: {self.annual_grid_export_kwh:.0f} kWh\n"
            f"  Specific Yield: {self.specific_yield_kwh_per_kwp:.0f} kWh/kWp/year\n"
            + (f"  ⚠️  Limited by roof area\n" if self.constrained_by_roof else "")
        )
    
    def plot_monthly_comparison(
        self,
        output_path: Optional[str] = None,
        figsize: tuple = (12, 10),
        show_self_consumed: bool = True
    ) -> Optional[str]:
        """
        Plots monthly PV generation vs consumption comparison.
        
        Delegates to SizingResultPlotter for visualization.
        
        Args:
            output_path: Path to save figure. If None, displays interactively.
            figsize: Figure size (width, height) in inches.
            show_self_consumed: If True, shows self-consumed energy as overlay.
            
        Returns:
            Path to saved figure if output_path provided, else None.
        """
        from eclipse.plotting.pvsim_plotter import SizingResultPlotter
        plotter = SizingResultPlotter(self)
        return plotter.plot_monthly_comparison(output_path, figsize, show_self_consumed)
    
    def plot_seasonal_daily_production(
        self,
        output_path: Optional[str] = None,
        figsize: tuple = (14, 8)
    ) -> Optional[str]:
        """
        Plots typical daily PV production profiles for each season.
        
        Delegates to SizingResultPlotter for visualization.
        
        Args:
            output_path: Path to save figure. If None, displays interactively.
            figsize: Figure size (width, height) in inches.
            
        Returns:
            Path to saved figure if output_path provided, else None.
        """
        from eclipse.plotting.pvsim_plotter import SizingResultPlotter
        plotter = SizingResultPlotter(self)
        return plotter.plot_seasonal_daily_production(output_path, figsize)
    
    def plot_battery_soc(
        self,
        output_path: Optional[str] = None,
        figsize: tuple = (14, 6),
        days_to_show: int = 7
    ) -> Optional[str]:
        """
        Plots battery state of charge over time.
        
        Delegates to SizingResultPlotter for visualization.
        
        Args:
            output_path: Path to save figure. If None, displays interactively.
            figsize: Figure size (width, height) in inches.
            days_to_show: Number of days to display.
            
        Returns:
            Path to saved figure if output_path provided, else None.
        """
        from eclipse.plotting.pvsim_plotter import SizingResultPlotter
        plotter = SizingResultPlotter(self)
        return plotter.plot_battery_soc(output_path, figsize, days_to_show)


class SimulationAccessor:
    """
    Handles PV generation simulation using pvlib.
    
    Lazily evaluates simulation on first access to avoid redundant calculations.
    Caches results for subsequent queries.
    """
    
    def __init__(
        self,
        location: LocationConfig,
        roof: RoofConfig,
        consumption_data: 'ConsumptionData'
    ):
        """
        Initialize simulation accessor.
        
        Args:
            location: Location configuration.
            roof: Roof configuration.
            consumption_data: Consumption data for alignment.
        """
        self._location = location
        self._roof = roof
        self._consumption_data = consumption_data
        
        # Lazy-loaded simulation results
        self._simulated = False
        self._weather_data: Optional[pd.DataFrame] = None
        self._reference_generation_kwh: Optional[pd.Series] = None
        self._specific_yield: Optional[float] = None
    
    def _run_simulation(self) -> None:
        """Runs pvlib simulation for reference 1kWp system."""
        if self._simulated:
            return
        
        print("Running PV generation simulation with PVGIS data...")
        
        # 1. Fetch weather data from PVGIS (Generic TMY)
        try:
            weather, meta = pvlib.iotools.get_pvgis_tmy(
                self._location.latitude,
                self._location.longitude,
                map_variables=True
            )
        except Exception as e:
            raise RuntimeError(f"Failed to fetch PVGIS weather data: {e}")
        
        # 2. Align simulation to Consumption Data Index (Target Index)
        target_index = self._consumption_data.series.index
        print(f"DEBUG: Target index range: {target_index.min()} to {target_index.max()}")
        print(f"DEBUG: Target index tz: {target_index.tz}")
        
        # Shift TMY generic year to match target year(s)
        # We assume target index spans mainly one year (or we take the mode)
        target_year = int(pd.Series(target_index.year).mode()[0])
        print(f"DEBUG: Shifting TMY to year {target_year}")
        
        weather.index = weather.index.map(lambda t: t.replace(year=target_year))
        print(f"DEBUG: Weather index tz: {weather.index.tz}")
        
        # TIMEZONE NORMALIZATION: 
        # If target is naive and weather is aware, drop tz from weather (assuming aligned)
        # Or if target is aware, convert weather.
        if target_index.tz is None and weather.index.tz is not None:
             print("DEBUG: Dropping timezone from TMY to match naive target")
             weather.index = weather.index.tz_localize(None)
        elif target_index.tz is not None and weather.index.tz is None:
             print(f"DEBUG: Localizing TMY to {target_index.tz} to match target")
             weather.index = weather.index.tz_localize('UTC').tz_convert(target_index.tz)
             
        # 3. Resample/Interpolate Weather to match Target Index Resolution (e.g. 15-min)
        # This handles:
        #   - Resolution mismatch (Hourly -> 15min)
        #   - Leap Years (Interpolates Feb 29 if missing in TMY)
        #   - Timezones (Assuming target is localized, we match it)
        
        # Reindex checks for timestamps. Method='time' interpolates based on time distance.
        aligned_weather = weather.reindex(target_index).interpolate(method='time')
        print(f"DEBUG: Aligned weather shape: {aligned_weather.shape}")
        print(f"DEBUG: Aligned weather NaNs: {aligned_weather.isna().sum().sum()}")
        print(aligned_weather.head())
        
        # Fill any remaining NaNs (e.g. if TMY starts slightly later or ends earlier)
        aligned_weather = aligned_weather.bfill().ffill()
        
        # 4. Setup Simulation
        location = Location(
            self._location.latitude,
            self._location.longitude,
            self._location.timezone,
            self._location.altitude
        )
        temp_params = TEMPERATURE_MODEL_PARAMETERS['sapm']['open_rack_glass_glass']
        
        # Reference 1kWp system
        system = PVSystem(
            surface_tilt=self._roof.tilt,
            surface_azimuth=self._roof.azimuth,
            module_parameters={'pdc0': 1000, 'gamma_pdc': -0.004},
            inverter_parameters={'pdc0': 1000},
            temperature_model_parameters=temp_params
        )
        
        # 5. Run Model on ALIGNED weather
        mc = ModelChain(system, location, aoi_model='physical', spectral_model='no_loss')
        mc.run_model(aligned_weather)
        
        # 6. Extract AC Generation
        # Result index matches target_index exactly
        ref_ac_power_watts = mc.results.ac.fillna(0)
        
        # Convert Power (Watts) to Energy (kWh) per step
        # Ideally, we integrate power over time step.
        # Calculate step size in hours
        step_hours = pd.Series(target_index).diff().median().total_seconds() / 3600
        if pd.isna(step_hours) or step_hours == 0:
             step_hours = 1.0 # Default fallback
             
        ref_ac_kwh = (ref_ac_power_watts * step_hours) / 1000.0 * self._roof.performance_ratio
        
        # 7. Calculate Specific Yield (Annualized)
        total_gen = ref_ac_kwh.sum()
        # Scale to 365 days if target is substantially different? 
        # For now, assumes target index is ~1 year.
        specific_yield = total_gen
        
        # Cache results
        self._weather_data = aligned_weather
        self._reference_generation_kwh = ref_ac_kwh
        self._specific_yield = specific_yield
        self._simulated = True
        
        print(f"Simulation complete. Specific yield: {specific_yield:.0f} kWh/kWp/year (Resolution: {step_hours*60:.0f} min)")
    
    @property
    def specific_yield(self) -> float:
        """Annual specific yield in kWh/kWp/year."""
        self._run_simulation()
        return self._specific_yield
    
    @property
    def reference_1kwp(self) -> pd.Series:
        """Hourly generation for reference 1kWp system."""
        self._run_simulation()
        return self._reference_generation_kwh.copy()
    
    def scale_to_capacity(self, kwp: float) -> pd.Series:
        """
        Returns scaled generation for given capacity.
        
        Args:
            kwp: System capacity in kWp.
            
        Returns:
            Series with hourly generation aligned to consumption timestamps.
        """
        self._run_simulation()
        scaled = self._reference_generation_kwh * kwp
        scaled.name = 'PV_Generation_kWh'
        
        # Result is already aligned to consumption index by _run_simulation
        return scaled


class PVSystemSizer:
    """
    Main entry point for PV system sizing.
    
    Integrates consumption data with pvlib simulation to size systems
    based on self-sufficiency targets or other optimization criteria.
    
    Example:
        sizer = PVSystemSizer(
            consumption_data=data,
            location=LocationConfig(47.38, 8.54),
            roof=RoofConfig(tilt=30, azimuth=180, max_area_m2=50)
        )
        result = sizer.size_for_self_sufficiency(target_percent=80)
    """
    
    def __init__(
        self,
        consumption_data: 'ConsumptionData',
        location: LocationConfig,
        roof: RoofConfig,
        battery: Optional[BatteryConfig] = None
    ):
        """
        Initialize PV system sizer.
        
        Args:
            consumption_data: ConsumptionData object with hourly consumption.
            location: Location configuration.
            roof: Roof configuration.
            battery: Optional battery configuration for storage simulation.
                     If battery.auto_size=True, BatterySizer.recommend() is called
                     internally after PV simulation.
        """
        self._consumption_data = consumption_data
        self._location = location
        self._roof = roof
        
        # Handle battery=True shorthand
        if battery is True:
            self._battery = BatteryConfig()  # Use defaults with auto-sizing
        else:
            self._battery = battery
        
        # For backward compatibility
        self._battery_config = self._battery
        
        # Lazy-loaded simulation accessor
        self._simulation: Optional[SimulationAccessor] = None
    
    def simulate(self, pv_sizing: Union[str, float] = 'max_roof') -> 'SizingResult':
        """
        Run physics simulation for given PV and battery configuration.
        
        Args:
            pv_sizing: PV sizing mode:
                - 'max_roof': Use maximum roof capacity (default)
                - 'match_load': Size to match annual consumption
                - float: Explicit kWp value
            
        Returns:
            SizingResult with all performance metrics.
        """
        # Resolve PV size
        if isinstance(pv_sizing, str):
            if pv_sizing == 'max_roof':
                pv_kwp = self._roof.max_area_m2 * self._roof.module_efficiency
            elif pv_sizing == 'match_load':
                pv_kwp = self._calculate_kwp_for_load_match()
            else:
                raise ValueError(f"Unknown pv_sizing mode: {pv_sizing}. Use 'max_roof', 'match_load', or a float.")
        else:
            pv_kwp = float(pv_sizing)
        
        # If battery is configured with auto-sizing, run BatterySizer
        battery_kwh = 0.0
        if self._battery is not None:
            if self._battery.auto_size:
                # Run PV simulation first to get hourly data
                hourly_pv = self.simulation.scale_to_capacity(pv_kwp)
                hourly_load = self._consumption_data.hourly.series
                daily_load = self._consumption_data.daily.mean()
                
                # Import and use BatterySizer
                from eclipse.battery import BatterySizer
                
                battery_sizer = BatterySizer(
                    pv_kwp=pv_kwp,
                    daily_load_kwh=daily_load,
                    max_soc=self._battery.max_soc,
                    min_soc=self._battery.min_soc,
                    simulator=self._battery.simulator
                )
                
                sizing_result = battery_sizer.recommend(
                    load_kw=hourly_load,
                    pv_kw=hourly_pv,
                    target=self._battery.sizing_target
                )
                
                battery_kwh = sizing_result.recommended_kwh
                print(f"    🔋 Auto-sized battery: {battery_kwh:.1f} kWh ({self._battery.sizing_target})")
                
                # Create temp config with determined capacity for simulation
                temp_battery = BatteryConfig(
                    capacity_kwh=battery_kwh,
                    power_kw=battery_kwh * 0.5,  # 0.5C rate
                    efficiency=self._battery.efficiency,
                    min_soc=self._battery.min_soc,
                    max_soc=self._battery.max_soc
                )
                original = self._battery_config
                self._battery_config = temp_battery
                result = self._calculate_result(pv_kwp, constrained=False)
                self._battery_config = original
                return result
            else:
                # Manual mode - use specified capacity
                battery_kwh = self._battery.capacity_kwh
                return self._calculate_result(pv_kwp, constrained=False)
        else:
            # No battery
            return self._calculate_result(pv_kwp, constrained=False)
    
    def _calculate_kwp_for_load_match(self) -> float:
        """
        Calculate PV capacity needed to match annual consumption.
        
        Uses specific yield (kWh/kWp/year) from simulation to determine
        the system size that produces roughly equal to annual consumption.
        """
        annual_consumption = self._consumption_data.hourly.sum()
        
        # Get expected specific yield (kWh per kWp per year)
        # Use simulation accessor to get a reference 1 kWp yield
        reference_yield = self.simulation.scale_to_capacity(1.0).sum()  # kWh for 1 kWp
        
        if reference_yield > 0:
            return annual_consumption / reference_yield
        else:
            # Fallback: assume 1000 kWh/kWp/year
            return annual_consumption / 1000
    
    @property
    def simulation(self) -> SimulationAccessor:
        """Access to PV simulation results."""
        if self._simulation is None:
            self._simulation = SimulationAccessor(
                self._location,
                self._roof,
                self._consumption_data
            )
        return self._simulation
    
    @property
    def consumption_data(self) -> 'ConsumptionData':
        """Returns the consumption data."""
        return self._consumption_data
    
    @property
    def location(self) -> LocationConfig:
        """Returns the location configuration."""
        return self._location
    
    @property
    def roof(self) -> RoofConfig:
        """Returns the roof configuration."""
        return self._roof
    
    def size_for_self_sufficiency(
        self,
        target_percent: float,
        constrain_by_roof: bool = True
    ) -> SizingResult:
        """
        Sizes PV system to achieve target self-sufficiency percentage.
        
        Args:
            target_percent: Target self-sufficiency (0-100), percentage of 
                           consumption to be covered by PV.
            constrain_by_roof: If True, limits system size to available roof area.
            
        Returns:
            SizingResult with comprehensive metrics.
            
        Raises:
            ValueError: If target_percent is outside valid range.
        """
        if not 0 < target_percent <= 100:
            raise ValueError(f"target_percent must be between 0 and 100, got {target_percent}")
        
        # Calculate required capacity
        annual_consumption = self._consumption_data.hourly.sum()
        target_coverage_kwh = annual_consumption * (target_percent / 100.0)
        
        specific_yield = self.simulation.specific_yield
        required_kwp = target_coverage_kwh / specific_yield
        
        # Check roof constraint
        constrained = False
        if constrain_by_roof and self._roof.max_capacity_kwp is not None:
            if required_kwp > self._roof.max_capacity_kwp:
                required_kwp = self._roof.max_capacity_kwp
                constrained = True
        
        # Calculate result metrics
        return self._calculate_result(required_kwp, constrained)
    
    def size_for_full_offset(self, constrain_by_roof: bool = True) -> SizingResult:
        """
        Sizes system for 100% consumption offset.
        
        Args:
            constrain_by_roof: If True, limits to available roof area.
            
        Returns:
            SizingResult with 100% (or max possible) coverage.
        """
        return self.size_for_self_sufficiency(100.0, constrain_by_roof)
    
    def size_for_roof_area(self) -> SizingResult:
        """
        Sizes system to use maximum available roof area.
        
        Returns:
            SizingResult for maximum roof capacity.
            
        Raises:
            ValueError: If no roof area constraint is configured.
        """
        if self._roof.max_capacity_kwp is None:
            raise ValueError("No roof area constraint configured. Set max_area_m2 in RoofConfig.")
        
        return self._calculate_result(self._roof.max_capacity_kwp, constrained=False)
    
    def size_for_self_consumption(
        self,
        target_percent: float,
        constrain_by_roof: bool = True,
        max_iterations: int = 30
    ) -> SizingResult:
        """
        Sizes PV system to achieve target self-consumption percentage.
        
        Self-consumption = % of PV generation that is used locally (not exported).
        Uses iterative approach as relationship is non-linear.
        
        NOTE: Higher self-consumption requires SMALLER systems (less export).
        
        Args:
            target_percent: Target self-consumption (0-100), percentage of 
                           PV generation to be used locally.
            constrain_by_roof: If True, limits system size to available roof area.
            max_iterations: Maximum iterations for convergence (default: 30).
            
        Returns:
            SizingResult with self-consumption close to target.
            
        Raises:
            ValueError: If target_percent is outside valid range.
        """
        if not 0 < target_percent <= 100:
            raise ValueError(f"target_percent must be between 0 and 100, got {target_percent}")
        
        # Initial guess: smaller system for higher self-consumption
        # Start conservative
        annual_consumption = self._consumption_data.hourly.sum()
        kwp_min = 0.5  # Minimum realistic size
        kwp_max = self._roof.max_capacity_kwp if (constrain_by_roof and self._roof.max_capacity_kwp) else 20.0
        
        # Binary search for optimal size
        tolerance = 1.0  # Within 1% of target
        best_result = None
        best_error = float('inf')
        
        for iteration in range(max_iterations):
            kwp_guess = (kwp_min + kwp_max) / 2.0
            
            # Calculate result for current guess
            result = self._calculate_result(kwp_guess, constrained=False)
            
            error = result.self_consumption_pct - target_percent
            
            # Track best result
            if abs(error) < abs(best_error):
                best_error = error
                best_result = result
            
            # Check convergence
            if abs(error) < tolerance:
                return result
            
            # Adjust search range
            # Higher self-consumption needs SMALLER system (less PV to export)
            # Lower self-consumption needs LARGER system (more PV generation)
            if error > 0:  # Self-consumption too high, need bigger system
                kwp_min = kwp_guess
            else:  # Self-consumption too low, need smaller system
                kwp_max = kwp_guess
            
            # Prevent search range collapse
            if kwp_max - kwp_min < 0.01:
                break
        
        # Return best attempt
        return best_result if best_result else self._calculate_result(kwp_guess, constrained=constrain_by_roof)
    
    def optimize(
        self,
        target_metric: str,
        target_percent: float,
        constrain_by_roof: bool = True
    ) -> SizingResult:
        """
        Generic optimization method for either self-sufficiency or self-consumption.
        
        Args:
            target_metric: Either 'self_sufficiency' or 'self_consumption'.
            target_percent: Target percentage (0-100).
            constrain_by_roof: If True, limits to available roof area.
            
        Returns:
            SizingResult optimized for chosen metric.
            
        Raises:
            ValueError: If target_metric is invalid.
        """
        metric_map = {
            'self_sufficiency': self.size_for_self_sufficiency,
            'self_consumption': self.size_for_self_consumption,
            'autarchy': self.size_for_self_sufficiency,  # Alias
        }
        
        if target_metric.lower() not in metric_map:
            raise ValueError(
                f"target_metric must be one of {list(metric_map.keys())}, got '{target_metric}'"
            )
        
        method = metric_map[target_metric.lower()]
        return method(target_percent, constrain_by_roof)
    
    def optimize_battery_size(
        self,
        pv_kwp: float,
        target_self_sufficiency: float = 80.0,
        battery_sizes: Optional[list] = None,
        max_storage_days: float = 2.0
    ) -> dict:
        """
        Find optimal battery size for a given PV system with physics-based constraints.
        
        Uses sweep optimization with intelligent sizing limits based on PV capacity.
        Stops when diminishing returns detected (< 1% improvement per kWh added).
        
        Args:
            pv_kwp: PV system size in kWp.
            target_self_sufficiency: Target self-sufficiency percentage (0-100).
            battery_sizes: List of battery sizes to test in kWh (default: auto-calculated).
            max_storage_days: Maximum days of storage (default: 2.0 days).
            
        Returns:
            Dictionary with optimization results including:
            - 'optimal_kwh': Recommended battery size
            - 'achieved_ss': Self-sufficiency achieved
            - 'sweep_results': DataFrame with all tested sizes
            - 'recommendation': Sizing rationale
        """
        if not 0 < target_self_sufficiency <= 100:
            raise ValueError(f"target_self_sufficiency must be between 0 and 100, got {target_self_sufficiency}")
        
        # Calculate physics-based battery sizing limits
        annual_consumption = self._consumption_data.hourly.sum()
        daily_consumption = annual_consumption / 365
        daily_pv_generation = pv_kwp * self.simulation.specific_yield / 365
        
        # Maximum useful battery = PV daily generation × storage days
        # Can't charge more than what PV produces daily
        max_useful_battery = daily_pv_generation * max_storage_days
        
        # Also consider consumption-based limit (shouldn't exceed 1-2 days consumption)
        max_consumption_battery = daily_consumption * max_storage_days
        
        # Use the smaller of the two limits
        max_recommended = min(max_useful_battery, max_consumption_battery)
        
        print(f"\n🔋 Battery Sizing Analysis:")
        print(f"   Daily PV generation: {daily_pv_generation:.1f} kWh")
        print(f"   Daily consumption: {daily_consumption:.1f} kWh")
        print(f"   Max useful battery: {max_useful_battery:.1f} kWh ({max_storage_days} days PV)")
        print(f"   Recommended range: 0-{max_recommended:.1f} kWh\n")
        
        # Auto-generate battery sizes if not provided
        if battery_sizes is None:
            # Test from 0 to max_recommended in reasonable steps
            if max_recommended < 10:
                step = 1.0
            elif max_recommended < 20:
                step = 2.5
            else:
                step = 5.0
            
            battery_sizes = [0]
            size = step
            while size <= max_recommended:
                battery_sizes.append(size)
                size += step
            battery_sizes.append(max_recommended)  # Add upper limit
        else:
            # Filter provided sizes to max_recommended
            battery_sizes = [s for s in battery_sizes if s <= max_recommended * 1.2]  # Allow 20% over
        
        results = []
        best_result = None
        previous_ss = 0
        
        print(f"Optimizing battery size for {pv_kwp} kWp PV system...")
        print(f"Target self-sufficiency: {target_self_sufficiency}%\n")
        
        for bat_size in battery_sizes:
            if bat_size == 0:
                # No battery case
                temp_sizer = PVSystemSizer(
                    self._consumption_data,
                    self._location,
                    self._roof
                )
            else:
                # With battery
                bat_config = BatteryConfig(
                    capacity_kwh=bat_size,
                    power_kw=min(bat_size / 2, 10.0),  # C-rate of 0.5
                    efficiency=0.95
                )
                temp_sizer = PVSystemSizer(
                    self._consumption_data,
                    self._location,
                    self._roof,
                    battery_config=bat_config
                )
            
            # Calculate result for this PV size (fixed) with current battery
            result = temp_sizer._calculate_result(pv_kwp, constrained=False)
            
            improvement = result.self_sufficiency_pct - previous_ss
            
            results.append({
                'battery_kwh': bat_size,
                'self_sufficiency_pct': result.self_sufficiency_pct,
                'grid_import_kwh': result.annual_grid_import_kwh,
                'grid_export_kwh': result.annual_grid_export_kwh,
                'cycles_per_year': result.battery_cycles if result.battery_cycles else 0,
                'improvement_pct': improvement
            })
            
            # Check if target reached
            if result.self_sufficiency_pct >= target_self_sufficiency and best_result is None:
                best_result = {
                    'optimal_kwh': bat_size,
                    'achieved_ss': result.self_sufficiency_pct,
                    'result': result,
                    'recommendation': f'Target {target_self_sufficiency}% achieved with {bat_size} kWh battery'
                }
            
            # Check for diminishing returns (< 1% improvement per kWh added)
            if bat_size > 0 and improvement < 1.0 and improvement > 0:
                if best_result is None:
                    # Diminishing returns detected, use previous size
                    prev_size = results[-2]['battery_kwh'] if len(results) > 1 else 0
                    best_result = {
                        'optimal_kwh': prev_size if prev_size > 0 else bat_size,
                        'achieved_ss': previous_ss if prev_size > 0 else result.self_sufficiency_pct,
                        'result': result,
                        'recommendation': f'Stopped at {bat_size} kWh - diminishing returns detected (< 1%/kWh gain)'
                    }
                    break
            
            previous_ss = result.self_sufficiency_pct
        
        # If target never reached and no diminishing returns, recommend based on physics
        if best_result is None:
            # Use 50-75% of max_recommended as optimal
            optimal_size = round(max_recommended * 0.67, 1)
            
            # Find closest tested size
            closest_idx = min(range(len(results)), key=lambda i: abs(results[i]['battery_kwh'] - optimal_size))
            
            best_result = {
                'optimal_kwh': results[closest_idx]['battery_kwh'],
                'achieved_ss': results[closest_idx]['self_sufficiency_pct'],
                'result': None,
                'recommendation': f'PV system too small for {target_self_sufficiency}% target. '
                                f'Recommended {results[closest_idx]["battery_kwh"]} kWh based on {max_storage_days}-day storage.'
            }
        
        best_result['sweep_results'] = pd.DataFrame(results)
        best_result['max_useful_battery_kwh'] = max_recommended
        return best_result
    
    def optimize_system(
        self,
        target_self_sufficiency: float = 80.0,
        pv_step_kwp: float = 0.5,
        max_storage_days: float = 2.0,
        prioritize: str = 'performance'
    ) -> dict:
        """
        Joint optimization of PV and battery size.
        
        Finds the optimal combination of PV size and battery capacity
        to achieve target self-sufficiency while respecting physical constraints.
        
        Args:
            target_self_sufficiency: Target self-sufficiency percentage (0-100).
            pv_step_kwp: PV size increment in kWp for testing (default: 0.5 kWp).
            max_storage_days: Maximum battery storage days (default: 2.0).
            prioritize: 'performance' (max self-sufficiency) or 'economy' (min size).
            
        Returns:
            Dictionary with optimal PV+battery combination:
            - 'optimal_pv_kwp': Recommended PV size
            - 'optimal_battery_kwh': Recommended battery size
            - 'achieved_ss': Self-sufficiency achieved
            - 'result': Full SizingResult object
            - 'all_combinations': DataFrame with all tested combinations
        """
        if not 0 < target_self_sufficiency <= 100:
            raise ValueError(f"target_self_sufficiency must be between 0 and 100")
        
        if prioritize not in ['performance', 'economy']:
            raise ValueError(f"prioritize must be 'performance' or 'economy', got {prioritize}")
        
        print(f"\n{'='*70}")
        print(f"🔍 JOINT PV + BATTERY OPTIMIZATION")
        print(f"{'='*70}")
        print(f"Target: {target_self_sufficiency}% self-sufficiency")
        print(f"Roof constraint: {self._roof.max_capacity_kwp} kWp max" if self._roof.max_capacity_kwp else "No roof limit")
        print(f"Priority: {prioritize.title()}\n")
        
        # Determine PV size range
        annual_consumption = self._consumption_data.hourly.sum()
        min_pv = annual_consumption * (target_self_sufficiency / 100) / self.simulation.specific_yield
        max_pv = self._roof.max_capacity_kwp if self._roof.max_capacity_kwp else min_pv * 2
        
        # Generate PV sizes to test
        pv_sizes = []
        pv = max(0.5, min_pv * 0.5)  # Start from 50% of theoretical minimum
        while pv <= max_pv:
            pv_sizes.append(round(pv, 2))
            pv += pv_step_kwp
        if pv_sizes[-1] < max_pv:
            pv_sizes.append(round(max_pv, 2))
        
        print(f"Testing PV sizes: {min(pv_sizes):.1f} to {max(pv_sizes):.1f} kWp ({len(pv_sizes)} steps)\n")
        
        all_results = []
        best_combination = None
        best_score = 0 if prioritize == 'performance' else float('inf')
        
        for pv_kwp in pv_sizes:
            # Optimize battery for this PV size
            battery_opt = self.optimize_battery_size(
                pv_kwp=pv_kwp,
                target_self_sufficiency=target_self_sufficiency,
                max_storage_days=max_storage_days
            )
            
            optimal_battery = battery_opt['optimal_kwh']
            achieved_ss = battery_opt['achieved_ss']
            
            # Calculate result with optimal battery
            if optimal_battery > 0:
                bat_config = BatteryConfig(
                    capacity_kwh=optimal_battery,
                    power_kw=min(optimal_battery / 2, 10.0),
                    efficiency=0.95
                )
                temp_sizer = PVSystemSizer(
                    self._consumption_data,
                    self._location,
                    self._roof,
                    battery_config=bat_config
                )
            else:
                temp_sizer = PVSystemSizer(
                    self._consumption_data,
                    self._location,
                    self._roof
                )
            
            result = temp_sizer._calculate_result(pv_kwp, constrained=False)
            
            all_results.append({
                'pv_kwp': pv_kwp,
                'battery_kwh': optimal_battery,
                'self_sufficiency_pct': result.self_sufficiency_pct,
                'grid_import_kwh': result.annual_grid_import_kwh,
                'total_system_cost_units': pv_kwp * 10 + optimal_battery * 4  # Rough cost proxy
            })
            
            # Scoring based on priority
            if prioritize == 'performance':
                # Maximize self-sufficiency, minimize size as tiebreaker
                score = result.self_sufficiency_pct - (pv_kwp * 0.1 + optimal_battery * 0.05)
                if score > best_score and result.self_sufficiency_pct >= target_self_sufficiency * 0.95:
                    best_score = score
                    best_combination = {
                        'optimal_pv_kwp': pv_kwp,
                        'optimal_battery_kwh': optimal_battery,
                        'achieved_ss': result.self_sufficiency_pct,
                        'result': result
                    }
            else:  # economy
                # Minimize cost while achieving target
                if result.self_sufficiency_pct >= target_self_sufficiency:
                    cost = pv_kwp * 10 + optimal_battery * 4
                    if cost < best_score:
                        best_score = cost
                        best_combination = {
                            'optimal_pv_kwp': pv_kwp,
                            'optimal_battery_kwh': optimal_battery,
                            'achieved_ss': result.self_sufficiency_pct,
                            'result': result
                        }
            
            print(f"  PV: {pv_kwp:.1f} kWp + Battery: {optimal_battery:.1f} kWh → SS: {result.self_sufficiency_pct:.1f}%")
        
        # If target never reached, use best performing combination
        if best_combination is None:
            best_idx = max(range(len(all_results)), key=lambda i: all_results[i]['self_sufficiency_pct'])
            best = all_results[best_idx]
            
            # Recreate result for best combination
            if best['battery_kwh'] > 0:
                bat_config = BatteryConfig(
                    capacity_kwh=best['battery_kwh'],
                    power_kw=min(best['battery_kwh'] / 2, 10.0),
                    efficiency=0.95
                )
                temp_sizer = PVSystemSizer(self._consumption_data, self._location, self._roof, battery_config=bat_config)
            else:
                temp_sizer = PVSystemSizer(self._consumption_data, self._location, self._roof)
            
            result = temp_sizer._calculate_result(best['pv_kwp'], constrained=False)
            
            best_combination = {
                'optimal_pv_kwp': best['pv_kwp'],
                'optimal_battery_kwh': best['battery_kwh'],
                'achieved_ss': best['self_sufficiency_pct'],
                'result': result,
                'note': f'Target {target_self_sufficiency}% not achievable. Best: {best["self_sufficiency_pct"]:.1f}%'
            }
        
        best_combination['all_combinations'] = pd.DataFrame(all_results)
        
        print(f"\n{'='*70}")
        print(f"✅ OPTIMAL SYSTEM FOUND")
        print(f"{'='*70}")
        print(f"PV: {best_combination['optimal_pv_kwp']} kWp")
        print(f"Battery: {best_combination['optimal_battery_kwh']} kWh")
        print(f"Self-Sufficiency: {best_combination['achieved_ss']:.1f}%")
        if 'note' in best_combination:
            print(f"Note: {best_combination['note']}")
        print(f"{'='*70}\n")
        
        return best_combination
    
    def _calculate_result(self, kwp: float, constrained: bool) -> SizingResult:
        """
        Calculates comprehensive sizing result for given capacity.
        Internal method to calculate results for specific system size.
        """
        # Get aligned PV generation (now strictly aligned matches consumption index)
        pv_generation = self.simulation.scale_to_capacity(kwp)
        
        # Get native consumption data (matching alignment)
        consumption = self._consumption_data.series.series
        
        # Verify alignment
        if len(pv_generation) != len(consumption):
             print(f"WARNING: Size mismatch in _calculate_result! PV={len(pv_generation)}, Load={len(consumption)}")
             # Final safety alignment
             pv_generation = pv_generation.reindex(consumption.index).fillna(0)
        
        # Initialize battery metrics
        battery_enabled = self._battery_config is not None
        battery_soc_profile = None
        battery_charge_kwh = 0.0
        battery_discharge_kwh = 0.0
        battery_cycles = 0.0
        
        if battery_enabled:
            # Run battery simulation
            from eclipse.battery import SimpleBatterySimulator
            from eclipse.config.equipment_models import MockBattery
            
            # Create mock battery object for simulator
            mock_battery = MockBattery(
                nominal_energy_kwh=self._battery_config.capacity_kwh,
                max_charge_power_kw=self._battery_config.power_kw,
                max_discharge_power_kw=self._battery_config.power_kw,
                min_soc=self._battery_config.min_soc,
                max_soc=self._battery_config.max_soc
            )
            
            # Run simulation with efficiency override
            bat_sim = SimpleBatterySimulator(mock_battery, efficiency=self._battery_config.efficiency)
            battery_results = bat_sim.simulate(
                load_kw=consumption,
                pv_kw=pv_generation
            )
            
            # Extract battery metrics
            battery_soc_profile = battery_results['soc']
            battery_charge_kwh = battery_results[battery_results['battery_power'] < 0]['battery_power'].abs().sum()
            battery_discharge_kwh = battery_results[battery_results['battery_power'] > 0]['battery_power'].sum()
            battery_cycles = battery_discharge_kwh / self._battery_config.capacity_kwh if self._battery_config.capacity_kwh > 0 else 0
            
            # Use battery-adjusted grid flows
            grid_import = battery_results['grid_import'].values
            grid_export = battery_results['grid_export'].values
            
        else:
            # No battery: Calculate energy flows directly
            self_consumed = np.minimum(pv_generation.values, consumption.values)
            grid_export = pv_generation.values - self_consumed
            grid_import = consumption.values - self_consumed
        
        # Calculate annual totals
        annual_generation = pv_generation.sum()
        annual_consumption = consumption.sum()
        annual_grid_import = grid_import.sum()
        annual_grid_export = grid_export.sum()
        annual_self_consumed = annual_consumption - annual_grid_import
        
        # Percentages
        self_sufficiency_pct = (annual_self_consumed / annual_consumption * 100) if annual_consumption > 0 else 0
        self_consumption_pct = (annual_self_consumed / annual_generation * 100) if annual_generation > 0 else 0
        
        # Performance metrics
        specific_yield = self.simulation.specific_yield
        capacity_factor = annual_generation / (kwp * 8760) if kwp > 0 else 0
        
        # Calculate hourly self-consumed (for DataFrame)
        if battery_enabled:
            # With battery: consumption - grid_import (what we got from PV+battery)
            hourly_self_consumed = consumption.values - grid_import
        else:
            # Without battery: minimum of PV and consumption at each hour
            hourly_self_consumed = np.minimum(pv_generation.values, consumption.values)
        
        # Monthly profile
        df_combined = pd.DataFrame({
            'Consumption_kWh': consumption,
            'PV_kWh': pv_generation,
            'Self_Consumed_kWh': hourly_self_consumed,
            'Grid_Import_kWh': grid_import,
            'Grid_Export_kWh': grid_export
        }, index=consumption.index)
        
        monthly_profile = df_combined.resample('ME').sum()
        monthly_profile['Self_Sufficiency_Pct'] = (
            monthly_profile['Self_Consumed_kWh'] / monthly_profile['Consumption_kWh'] * 100
        )
        
        return SizingResult(
            recommended_kwp=round(kwp, 2),
            annual_generation_kwh=round(annual_generation, 1),
            annual_consumption_kwh=round(annual_consumption, 1),
            self_sufficiency_pct=round(self_sufficiency_pct, 2),
            self_consumption_pct=round(self_consumption_pct, 2),
            annual_self_consumed_kwh=round(annual_self_consumed, 1),
            annual_grid_import_kwh=round(annual_grid_import, 1),
            annual_grid_export_kwh=round(annual_grid_export, 1),
            specific_yield_kwh_per_kwp=round(specific_yield, 1),
            capacity_factor=round(capacity_factor, 4),
            monthly_profile=monthly_profile,
            hourly_data=df_combined,
            constrained_by_roof=constrained,
            battery_enabled=battery_enabled,
            battery_capacity_kwh=self._battery_config.capacity_kwh if battery_enabled else None,
            battery_soc_profile=battery_soc_profile,
            battery_charge_kwh=round(battery_charge_kwh, 1) if battery_enabled else None,
            battery_discharge_kwh=round(battery_discharge_kwh, 1) if battery_enabled else None,
            battery_cycles=round(battery_cycles, 1) if battery_enabled else None
        )
    
    def __repr__(self) -> str:
        return (
            f"PVSystemSizer("
            f"location=({self._location.latitude:.2f}, {self._location.longitude:.2f}), "
            f"tilt={self._roof.tilt}°, azimuth={self._roof.azimuth}°)"
        )
