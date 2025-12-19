"""
PySAM Battery Simulator
=======================
High-fidelity battery simulation using NREL PySAM BatteryStateful module.
Provides accurate physics modeling including voltage curves, thermal effects,
and degradation.
"""

import pandas as pd
import numpy as np
from typing import Optional

import PySAM.BatteryStateful as BatteryStateful

from src.battery.simulator import BatterySimulator
from src.config.equipment_models import MockBattery


class PySAMBatterySimulator(BatterySimulator):
    """
    High-fidelity battery simulator using NREL PySAM.
    
    Uses the BatteryStateful module for step-by-step dispatch control
    with detailed physics modeling.
    
    Pros:
        - Industry-standard accuracy
        - Voltage curve modeling (Shepherd model)
        - Thermal effects
        - Degradation modeling
        
    Cons:
        - Slower than simple simulator
        - Requires PySAM dependency
    """
    
    def simulate(
        self, 
        load_kw: pd.Series, 
        pv_kw: pd.Series,
        system_kwh: Optional[float] = None,
        system_kw: Optional[float] = None
    ) -> pd.DataFrame:
        """
        Run PySAM battery simulation.
        
        Args:
            load_kw: Load profile in kW
            pv_kw: PV generation profile in kW
            system_kwh: Override for capacity (default: battery.nominal_energy_kwh)
            system_kw: Override for power limit (default: battery.max_discharge_power_kw)
            
        Returns:
            DataFrame with simulation results
        """
        battery = self.battery
        
        # Resolve overrides
        sim_kwh = system_kwh if system_kwh is not None else battery.nominal_energy_kwh
        sim_kw = system_kw if system_kw is not None else battery.max_discharge_power_kw
        sim_volt = battery.nominal_voltage_v
        sim_min_soc = battery.min_soc
        sim_max_soc = battery.max_soc
        
        # Helper to safely get model_params
        mp = battery.model_params if battery.model_params else {}
        def get_mp(key, default):
            return mp.get(key, default)

        # Initialize the battery model
        batt = BatteryStateful.new()
        
        # --- Configure Battery Parameters ---
        
        # 1. Pack Specs
        batt.ParamsPack.nominal_energy = sim_kwh
        batt.ParamsPack.nominal_voltage = sim_volt
        
        # 2. Cell properties (Chemistry & Voltage)
        batt.ParamsCell.chem = battery.chem  # 0=Lead, 1=Li-ion
        
        # Voltage Model (Shepherd/Table)
        batt.ParamsCell.Vnom_default = battery.v_nom_cell
        batt.ParamsCell.Vfull = battery.v_max_cell
        batt.ParamsCell.Vcut = battery.v_min_cell
        batt.ParamsCell.Qfull = battery.q_full_cell
        batt.ParamsCell.resistance = battery.resistance
        
        # Shepherd Parameters
        batt.ParamsCell.Vexp = battery.v_exp if battery.v_exp else 4.05
        batt.ParamsCell.Qexp = battery.q_exp if battery.q_exp else 0.05
        batt.ParamsCell.Qnom = battery.q_nom if battery.q_nom else 3.0
        batt.ParamsCell.Vnom = battery.v_nom_curve if battery.v_nom_curve else 3.6
        batt.ParamsCell.C_rate = battery.c_rate if battery.c_rate else 1.0
        
        # Lead-Acid Specifics (if chem=0)
        if battery.chem == 0:
            if battery.q10: batt.ParamsCell.leadacid_q10 = battery.q10
            if battery.q20: batt.ParamsCell.leadacid_q20 = battery.q20
            if battery.qn: batt.ParamsCell.leadacid_qn = battery.qn
            if battery.tn: batt.ParamsCell.leadacid_tn = battery.tn
            
        # 3. Constraints & Initial State
        batt.ParamsCell.minimum_SOC = sim_min_soc
        batt.ParamsCell.maximum_SOC = sim_max_soc
        batt.ParamsCell.initial_SOC = getattr(battery, 'initial_soc', sim_max_soc)
        
        # 4. Life Model (Calendar/Cycle)
        batt.ParamsCell.life_model = get_mp('life_model', 0)
        batt.ParamsCell.calendar_choice = get_mp('calendar_choice', 0)
        
        cycling_matrix = get_mp('cycling_matrix', None)
        if cycling_matrix:
            batt.ParamsCell.cycling_matrix = cycling_matrix
            
        # 5. Thermal & Physical
        batt.ParamsPack.mass = get_mp('mass', 500)
        batt.ParamsPack.surface_area = get_mp('surface_area', 2.0)
        batt.ParamsPack.Cp = get_mp('Cp', 1000)
        batt.ParamsPack.h = get_mp('h', 20)
        batt.ParamsPack.T_room_init = get_mp('T_room_init', 20)
        
        cap_vs_temp = get_mp('cap_vs_temp', None)
        if cap_vs_temp:
            batt.ParamsPack.cap_vs_temp = cap_vs_temp
            
        # 6. Losses
        batt.ParamsPack.loss_choice = get_mp('loss_choice', 0)
        batt.ParamsPack.monthly_charge_loss = get_mp('monthly_charge_loss', [0]*12)
        batt.ParamsPack.monthly_discharge_loss = get_mp('monthly_discharge_loss', [0]*12)
        batt.ParamsPack.monthly_idle_loss = get_mp('monthly_idle_loss', [0]*12)

        # --- Controls ---
        batt.Controls.control_mode = 1.0  # Power control
        batt.Controls.dt_hr = 1.0  # Hourly time step
        batt.Controls.input_power = 0.0  # Initialize

        # --- Simulation Loop ---
        batt.setup()
        
        soc_log = []
        power_log = []
        
        load = load_kw.fillna(0).tolist()
        pv = pv_kw.fillna(0).tolist()
        
        for i in range(len(load)):
            # Net load: Positive = Deficit, Negative = Excess
            net_load = load[i] - pv[i]
            
            # Dispatch: Positive = Discharge, Negative = Charge
            power_needed = net_load
            
            # Clamp to power limits
            power_needed = max(-sim_kw, min(sim_kw, power_needed))
            
            batt.Controls.input_power = power_needed
            batt.execute(0)
            
            actual_power = batt.StatePack.P
            current_soc = batt.StatePack.SOC
            
            soc_log.append(current_soc)
            power_log.append(actual_power)
        
        # Build results DataFrame
        df = pd.DataFrame({
            'load': load,
            'pv': pv,
            'soc': soc_log,
            'battery_power': power_log
        })
        
        # Grid calculations
        df['grid_power'] = df['load'] - df['pv'] - df['battery_power']
        df['grid_import'] = df['grid_power'].apply(lambda x: x if x > 0 else 0)
        df['grid_export'] = df['grid_power'].apply(lambda x: -x if x < 0 else 0)
        
        return df
