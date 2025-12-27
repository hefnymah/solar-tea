"""
Energy Module - PV System Sizing & Energy Calculations

This module provides a robust, extensible class for calculating PV system sizes
based on energy consumption, location coordinates, and configurable loss factors.

Author: Solar-Tea Project
"""

from __future__ import annotations
from dataclasses import dataclass
from typing import Optional, Tuple
import pandas as pd
import numpy as np

import pvlib
from pvlib.location import Location
from pvlib.pvsystem import PVSystem
from pvlib.modelchain import ModelChain
from pvlib.temperature import TEMPERATURE_MODEL_PARAMETERS

from eclipse.config import pv_sizing as settings


# Equipment imports removed (unused in this file)

@dataclass
class EnergyProfile:
    """
    Represents a household or site energy consumption profile.
    
    Attributes:
        daily_kwh: Average daily energy consumption in kWh.
        annual_kwh: Total annual consumption (calculated if not provided).
        hourly_profile: Optional hourly consumption data as a pandas Series.
        peak_demand_kw: Maximum instantaneous power demand.
    """
    daily_kwh: float
    annual_kwh: Optional[float] = None
    hourly_profile: Optional[pd.Series] = None
    peak_demand_kw: Optional[float] = None
    
    def __post_init__(self):
        if self.annual_kwh is None:
            self.annual_kwh = self.daily_kwh * 365
        
        if self.hourly_profile is not None and self.peak_demand_kw is None:
            self.peak_demand_kw = self.hourly_profile.max()
    
    @classmethod
    def from_annual(cls, annual_kwh: float) -> EnergyProfile:
        """Factory method to create profile from annual consumption."""
        return cls(daily_kwh=annual_kwh / 365, annual_kwh=annual_kwh)
    
    @classmethod
    def from_hourly_data(cls, hourly_series: pd.Series) -> EnergyProfile:
        """Factory method to create profile from hourly consumption data."""
        daily_avg = hourly_series.sum() / (len(hourly_series) / 24)
        return cls(
            daily_kwh=daily_avg,
            annual_kwh=hourly_series.sum(),
            hourly_profile=hourly_series,
            peak_demand_kw=hourly_series.max()
        )


@dataclass
class kWpSizingResult:
    """
    Immutable result object for PV sizing calculations.
    
    Attributes:
        recommended_kwp: Calculated system size in kWp.
        specific_yield: Expected annual yield per kWp (kWh/kWp/year).
        estimated_annual_generation: Total expected annual generation (kWh).
        self_sufficiency_target: Target self-sufficiency ratio used.
        loss_factor: System loss factor applied.
        latitude: Site latitude.
        longitude: Site longitude.
        peak_sun_hours: PSH used for calculation.
    """
    recommended_kwp: float
    specific_yield: float
    estimated_annual_generation: float
    self_sufficiency_target: float
    loss_factor: float
    latitude: float
    longitude: float
    peak_sun_hours: float
    
    def __str__(self) -> str:
        return (
            f"kWp Sizing Result:\n"
            f"  Recommended Size: {self.recommended_kwp:.1f} kWp\n"
            f"  Specific Yield: {self.specific_yield:.0f} kWh/kWp/year\n"
            f"  Est. Generation: {self.estimated_annual_generation:.0f} kWh/year\n"
            f"  Location: ({self.latitude:.4f}, {self.longitude:.4f})\n"
            f"  Peak Sun Hours: {self.peak_sun_hours:.2f} h/day\n"
            f"  Target Self-Sufficiency: {self.self_sufficiency_target:.0%}\n"
            f"  Loss Factor: {self.loss_factor:.0%}"
        )


class kWpSizer:
    """
    Main class for PV system energy calculations and sizing.
    
    This class encapsulates the logic for determining optimal PV system sizes
    based on consumption profiles, location coordinates, and configurable parameters.
    
    Attributes:
        latitude (float): Site latitude in decimal degrees.
        longitude (float): Site longitude in decimal degrees.
        peak_sun_hours (float): Average daily Peak Sun Hours (kWh/m²/day).
        loss_factor (float): Combined system losses (default: 1.15 = 15% losses).
        default_self_sufficiency (float): Default target self-sufficiency ratio.
        
    Example:
        Basic usage with explicit Peak Sun Hours:
        
            >>> from kwp_sizer import kWpSizer, EnergyProfile
            >>> 
            >>> # Initialize sizer for Zurich with known PSH
            >>> sizer = kWpSizer(
            ...     latitude=47.3769,
            ...     longitude=8.5417,
            ...     peak_sun_hours=3.8
            ... )
            >>> 
            >>> # Size from daily consumption (30 kWh/day, 80% self-sufficiency)
            >>> result = sizer.size_from_daily(30)
            >>> print(result.recommended_kwp)
            7.3
        
        Using EnergyProfile for more control:
        
            >>> profile = EnergyProfile(daily_kwh=25, peak_demand_kw=5.0)
            >>> result = sizer.size_system(profile, self_sufficiency=0.9)
            >>> print(f"Recommended: {result.recommended_kwp} kWp")
            >>> print(f"Annual Gen: {result.estimated_annual_generation} kWh")
        
        Auto-estimate PSH from latitude (no explicit PSH):
        
            >>> sizer_auto = kWpSizer(latitude=40.4168, longitude=-3.7038)
            >>> print(sizer_auto.peak_sun_hours)  # Estimated from latitude
        
        Calculate required kWp for 100% offset:
        
            >>> annual_consumption = 12000  # kWh/year
            >>> required = sizer.required_kwp_for_offset(annual_consumption, offset_target=1.0)
            >>> print(f"Need {required} kWp for 100% offset")
        
        Estimate generation for a given system size:
        
            >>> gen = sizer.estimate_generation(system_kwp=10.0)
            >>> print(f"10 kWp system generates ~{gen:.0f} kWh/year")
    """
    
    # Class-level constants (DEPRECATED: Use settings.py)
    DEFAULT_LOSS_FACTOR = settings.DEFAULT_LOSS_FACTOR
    DEFAULT_SELF_SUFFICIENCY = settings.DEFAULT_SELF_SUFFICIENCY
    DEFAULT_PSH = settings.DEFAULT_PEAK_SUN_HOURS
    
    def __init__(
        self,
        latitude: float,
        longitude: float,
        peak_sun_hours: Optional[float] = None,
        loss_factor: float = DEFAULT_LOSS_FACTOR,
        default_self_sufficiency: float = DEFAULT_SELF_SUFFICIENCY
    ):
        """
        Initialize the kWpSizer.
        
        Args:
            latitude: Site latitude in decimal degrees.
            longitude: Site longitude in decimal degrees.
            peak_sun_hours: Average daily PSH (kWh/m²/day). If None, estimated from latitude.
            loss_factor: System loss multiplier (1.0 = no losses, 1.15 = 15% losses).
            default_self_sufficiency: Default target for self-consumption (0.0-1.0).
        """
        self._latitude = latitude
        self._longitude = longitude
        self._loss_factor = loss_factor
        self._default_self_sufficiency = default_self_sufficiency
        
        # Use provided PSH or estimate from latitude
        if peak_sun_hours is not None:
            self._psh = peak_sun_hours
        else:
            self._psh = self._estimate_psh_from_latitude(latitude)
    
    @staticmethod
    def _estimate_psh_from_latitude(latitude: float) -> float:
        """
        Rough estimation of Peak Sun Hours based on latitude.
        
        This is a simplified approximation. For accurate values, use 
        PVGIS or similar irradiance databases.
        
        Returns:
            Estimated PSH in kWh/m²/day.
        """
        abs_lat = abs(latitude)
        
        # Very rough global approximation
        # Equator: ~5.5 PSH, Tropics: ~5.0, Mid-latitudes: ~4.0, High-latitudes: ~3.0
        if abs_lat < 23.5:  # Tropics
            return 5.0
        elif abs_lat < 35:  # Subtropics
            return 4.5
        elif abs_lat < 50:  # Mid-latitudes
            return 3.8
        elif abs_lat < 60:  # Higher latitudes
            return 3.2
        else:  # Polar regions
            return 2.5
    
    # --- Properties ---
    
    @property
    def latitude(self) -> float:
        """Site latitude."""
        return self._latitude
    
    @property
    def longitude(self) -> float:
        """Site longitude."""
        return self._longitude
    
    @property
    def coordinates(self) -> Tuple[float, float]:
        """Latitude and Longitude tuple."""
        return (self._latitude, self._longitude)
    
    @property
    def peak_sun_hours(self) -> float:
        """Peak Sun Hours for the current location."""
        return self._psh
    
    @peak_sun_hours.setter
    def peak_sun_hours(self, value: float) -> None:
        """Update Peak Sun Hours."""
        self._psh = value
    
    @property
    def loss_factor(self) -> float:
        """Current loss factor."""
        return self._loss_factor
    
    @loss_factor.setter
    def loss_factor(self, value: float) -> None:
        """Update loss factor."""
        self._loss_factor = value
    
    # --- Core Sizing Methods ---
    
    def size_system(
        self,
        profile: EnergyProfile,
        self_sufficiency: Optional[float] = None
    ) -> kWpSizingResult:
        """
        Calculate the recommended PV system size for the given energy profile.
        
        Args:
            profile: An EnergyProfile object with consumption data.
            self_sufficiency: Target self-sufficiency ratio (0.0-1.0). 
                              Uses default if not specified.
        
        Returns:
            kWpSizingResult object with calculated values.
        """
        target_ss = self_sufficiency if self_sufficiency is not None else self._default_self_sufficiency
        
        # Core sizing formula
        target_daily_kwh = profile.daily_kwh * target_ss
        kwp = (target_daily_kwh / self._psh) * self._loss_factor
        
        # Specific yield = PSH * 365 / loss_factor
        specific_yield = (self._psh * 365) / self._loss_factor
        
        # Estimated annual generation
        annual_gen = kwp * specific_yield
        
        return kWpSizingResult(
            recommended_kwp=round(kwp, 1),
            specific_yield=round(specific_yield, 0),
            estimated_annual_generation=round(annual_gen, 0),
            self_sufficiency_target=target_ss,
            loss_factor=self._loss_factor,
            latitude=self._latitude,
            longitude=self._longitude,
            peak_sun_hours=self._psh
        )
    
    def size_from_daily(
        self,
        daily_kwh: float,
        self_sufficiency: Optional[float] = None
    ) -> kWpSizingResult:
        """
        Convenience method to size a system directly from daily consumption.
        
        Args:
            daily_kwh: Average daily consumption in kWh.
            self_sufficiency: Target self-sufficiency ratio.
        
        Returns:
            kWpSizingResult object.
        """
        profile = EnergyProfile(daily_kwh=daily_kwh)
        return self.size_system(profile, self_sufficiency)
    
    def size_from_annual(
        self,
        annual_kwh: float,
        self_sufficiency: Optional[float] = None
    ) -> kWpSizingResult:
        """
        Convenience method to size a system from annual consumption.
        
        Args:
            annual_kwh: Total annual consumption in kWh.
            self_sufficiency: Target self-sufficiency ratio.
        
        Returns:
            kWpSizingResult object.
        """
        profile = EnergyProfile.from_annual(annual_kwh)
        return self.size_system(profile, self_sufficiency)
    
    # --- Utility Methods ---
    
    def estimate_generation(self, system_kwp: float) -> float:
        """
        Estimate annual generation for a given system size.
        
        Args:
            system_kwp: System size in kWp.
        
        Returns:
            Estimated annual generation in kWh.
        """
        specific_yield = (self._psh * 365) / self._loss_factor
        return system_kwp * specific_yield
    
    def required_kwp_for_offset(
        self,
        annual_consumption_kwh: float,
        offset_target: float = 1.0
    ) -> float:
        """
        Calculate the kWp required to offset a given percentage of consumption.
        
        Args:
            annual_consumption_kwh: Total annual consumption in kWh.
            offset_target: Target offset ratio (1.0 = 100% offset).
        
        Returns:
            Required system size in kWp.
        """
        target_gen = annual_consumption_kwh * offset_target
        specific_yield = (self._psh * 365) / self._loss_factor
        return round(target_gen / specific_yield, 1)
    
    # --- Advanced PVLib-Based Sizing ---
    
    def size_with_pvgis(
        self,
        profile: EnergyProfile,
        self_sufficiency: Optional[float] = None,
        tilt: float = settings.DEFAULT_TILT,
        azimuth: float = settings.DEFAULT_AZIMUTH,
        performance_ratio: float = settings.DEFAULT_PERFORMANCE_RATIO
    ) -> kWpSizingResult:
        """
        Advanced sizing using real irradiance data from PVGIS.
        
        This method fetches TMY (Typical Meteorological Year) data from the
        EU PVGIS API and simulates a reference 1 kWp system using pvlib to
        calculate the actual specific yield for the given location.
        
        Args:
            profile: An EnergyProfile object with consumption data.
            self_sufficiency: Target self-sufficiency ratio (0.0-1.0).
            tilt: Module tilt angle in degrees (default: 30°).
            azimuth: Module azimuth angle in degrees (default: 180° = South).
            performance_ratio: System performance ratio (default: 0.85 = 85%).
        
        Returns:
            kWpSizingResult object with accurately calculated values.
        
        Raises:
            RuntimeError: If PVGIS data cannot be fetched.
        
        Example:
            >>> sizer = kWpSizer(latitude=47.3769, longitude=8.5417)
            >>> profile = EnergyProfile(daily_kwh=30)
            >>> result = sizer.size_with_pvgis(profile)
            >>> print(result.specific_yield)  # Accurate yield from simulation
        """
        
        
        target_ss = self_sufficiency if self_sufficiency is not None else self._default_self_sufficiency
        
        # 1. Fetch weather data from PVGIS
        try:
            pvgis_data = pvlib.iotools.get_pvgis_tmy(
                self._latitude, self._longitude, map_variables=True
            )
            # Handle different pvlib versions (returns 2-4 values)
            weather = pvgis_data[0] if isinstance(pvgis_data, tuple) else pvgis_data
        except Exception as e:
            raise RuntimeError(f"Failed to fetch PVGIS data: {e}")
        
        # 2. Setup location and reference system
        location = Location(self._latitude, self._longitude)
        temp_params = TEMPERATURE_MODEL_PARAMETERS['sapm']['open_rack_glass_glass']
        
        # Reference 1 kWp system
        system_ref = PVSystem(
            surface_tilt=tilt,
            surface_azimuth=azimuth,
            module_parameters={'pdc0': 1000, 'gamma_pdc': -0.004},
            inverter_parameters={'pdc0': 1000},
            temperature_model_parameters=temp_params
        )
        
        # 3. Run simulation
        mc = ModelChain(system_ref, location, aoi_model='physical', spectral_model='no_loss')
        mc.run_model(weather)
        
        # 4. Calculate specific yield (kWh per kWp per year)
        # ModelChain output is in Watts, convert to kWh
        ref_ac_kwh = (mc.results.ac / 1000.0) * performance_ratio
        specific_yield = ref_ac_kwh.sum()
        
        # Convert to equivalent PSH for consistency
        psh_equivalent = specific_yield / 365
        
        # 5. Size the system
        target_annual_kwh = profile.annual_kwh * target_ss
        if specific_yield > 0:
            kwp = target_annual_kwh / specific_yield
        else:
            kwp = 0
        
        annual_gen = kwp * specific_yield
        
        return kWpSizingResult(
            recommended_kwp=round(kwp, 1),
            specific_yield=round(specific_yield, 0),
            estimated_annual_generation=round(annual_gen, 0),
            self_sufficiency_target=target_ss,
            loss_factor=performance_ratio,
            latitude=self._latitude,
            longitude=self._longitude,
            peak_sun_hours=round(psh_equivalent, 2)
        )
    
    def size_from_daily_pvgis(
        self,
        daily_kwh: float,
        self_sufficiency: Optional[float] = None,
        **kwargs
    ) -> kWpSizingResult:
        """
        Convenience method: Size using PVGIS from daily consumption.
        
        Args:
            daily_kwh: Average daily consumption in kWh.
            self_sufficiency: Target self-sufficiency ratio.
            **kwargs: Additional arguments passed to size_with_pvgis().
        
        Returns:
            kWpSizingResult object.
        """
        profile = EnergyProfile(daily_kwh=daily_kwh)
        return self.size_with_pvgis(profile, self_sufficiency, **kwargs)
    
    def __repr__(self) -> str:
        return (
            f"kWpSizer(lat={self._latitude:.4f}, lon={self._longitude:.4f}, "
            f"psh={self._psh:.2f}, loss_factor={self._loss_factor})"
        )


# --- Module-Level Helper Functions ---

def size_pv_kwp(
    daily_kwh: float,
    latitude: float,
    longitude: float,
    peak_sun_hours: Optional[float] = None,
    self_sufficiency: float = kWpSizer.DEFAULT_SELF_SUFFICIENCY,
    loss_factor: float = kWpSizer.DEFAULT_LOSS_FACTOR
) -> float:
    """
    Quick helper function to get recommended kWp without creating a class instance.
    
    Args:
        daily_kwh: Average daily consumption in kWh.
        latitude: Site latitude in decimal degrees.
        longitude: Site longitude in decimal degrees.
        peak_sun_hours: Average daily PSH. If None, estimated from latitude.
        self_sufficiency: Target self-sufficiency ratio (0.0-1.0).
        loss_factor: System loss multiplier (1.0 = no losses).
    
    Returns:
        Recommended system size in kWp.
    
    Example:
        >>> kwp = size_pv_kwp(daily_kwh=30, latitude=47.38, longitude=8.54)
        >>> print(f"{kwp} kWp recommended")
    """
    sizer = kWpSizer(latitude, longitude, peak_sun_hours, loss_factor)
    result = sizer.size_from_daily(daily_kwh, self_sufficiency)
    return result.recommended_kwp
