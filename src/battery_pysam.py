
import pandas as pd
import PySAM.BatteryStateful as BatteryStateful
import PySAM.ResourceTools as tools
from typing import Optional
from src.config.equipments.batteries import PySAM_Test_Battery

def simulate_pysam_battery(
    load_profile_kw: pd.Series, 
    pv_production_kw: pd.Series, 
    battery: PySAM_Test_Battery,
    
    # Scaling / Overrides (Optional)
    system_kwh: Optional[float] = None, 
    system_kw: Optional[float] = None, 
    system_voltage: Optional[float] = None,
    min_soc: Optional[float] = None,
    max_soc: Optional[float] = None
) -> pd.DataFrame:
    """
    Simulates battery using PySAM's BatteryStateful module.
    Now fully driven by the MockBattery configuration object.
    
    Args:
        load_profile_kw: Net load (or consumption) in kW
        pv_production_kw: PV Generation in kW
        battery: The MockBattery configuration object
        system_kwh: Override for total capacity (e.g. for multiple units)
        system_kw: Override for total power
        system_voltage: Override for system voltage
        min_soc: Override minimum SOC
        max_soc: Override maximum SOC
    """
    
    # Defaults from Object if not overridden
    sim_kwh = system_kwh if system_kwh is not None else battery.nominal_energy_kwh
    sim_kw = system_kw if system_kw is not None else battery.max_discharge_power_kw
    sim_volt = system_voltage if system_voltage is not None else battery.nominal_voltage_v
    sim_min_soc = min_soc if min_soc is not None else battery.min_soc
    sim_max_soc = max_soc if max_soc is not None else battery.max_soc
    
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
    batt.ParamsCell.chem = battery.chem # 0=Lead, 1=Li-ion
    
    # Voltage Model (Shepherd/Table)
    # Using explicit fields from MockBattery
    batt.ParamsCell.Vnom_default = battery.v_nom_cell
    batt.ParamsCell.Vfull = battery.v_max_cell
    batt.ParamsCell.Vcut = battery.v_min_cell
    batt.ParamsCell.Qfull = battery.q_full_cell
    batt.ParamsCell.resistance = battery.resistance
    
    # Shepherd Parameters (if available) - PySAM defaults used as fallbacks
    batt.ParamsCell.Vexp = battery.v_exp if battery.v_exp else 4.05
    batt.ParamsCell.Qexp = battery.q_exp if battery.q_exp else 0.05
    batt.ParamsCell.Qnom = battery.q_nom if battery.q_nom else 3.0
    batt.ParamsCell.Vnom = battery.v_nom_curve if battery.v_nom_curve else 3.6
    batt.ParamsCell.C_rate = battery.c_rate if battery.c_rate else 1.0
    
    # Lead-Acid Specifics (if chem=0)
    # Lead-Acid Specifics (if chem=0)
    # Note: PySAM BatteryStateful might not expose KiBaM params directly on ParamsCell?
    # Commenting out for now    # Lead-Acid Specifics (if chem=0)
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
    # Extracted from model_params
    batt.ParamsCell.life_model = get_mp('life_model', 0) # Default 0 (Calendar/Cycle)
    batt.ParamsCell.calendar_choice = get_mp('calendar_choice', 0) # Default 0 (None)
    
    cycling_matrix = get_mp('cycling_matrix', None)
    if cycling_matrix:
        batt.ParamsCell.cycling_matrix = cycling_matrix
        
    # 5. Thermal & Physical (Extracted from model_params)
    batt.ParamsPack.mass = get_mp('mass', 500)
    batt.ParamsPack.surface_area = get_mp('surface_area', 2.0)
    batt.ParamsPack.Cp = get_mp('Cp', 1000)
    batt.ParamsPack.h = get_mp('h', 20)
    batt.ParamsPack.T_room_init = get_mp('T_room_init', 20)
    
    cap_vs_temp = get_mp('cap_vs_temp', None)
    if cap_vs_temp:
        batt.ParamsPack.cap_vs_temp = cap_vs_temp
        
    # 6. Losses
    batt.ParamsPack.loss_choice = get_mp('loss_choice', 0) # 0=Monthly
    batt.ParamsPack.monthly_charge_loss = get_mp('monthly_charge_loss', [0]*12)
    batt.ParamsPack.monthly_discharge_loss = get_mp('monthly_discharge_loss', [0]*12)
    batt.ParamsPack.monthly_idle_loss = get_mp('monthly_idle_loss', [0]*12)


    # --- Controls ---
    batt.Controls.control_mode = 1.0 # Power control
    batt.Controls.dt_hr = 1.0 # Hourly time step
    batt.Controls.input_power = 0.0 # Initialize

    
    # --- Simulation Loop ---
    
    # Reset state
    batt.setup()
    
    soc_log = []
    power_log = []
    
    # Ensure inputs are lists for iteration
    load = load_profile_kw.fillna(0).tolist()
    pv = pv_production_kw.fillna(0).tolist()
    
    current_soc = batt.ParamsCell.initial_SOC
    
    # Time-step simulation
    for i in range(len(load)):
        # Calculate net load (Load - PV)
        # Power is kW.
        # Positive Net Load = Deficit (Need Discharge)
        # Negative Net Load = Excess (Need Charge)
        
        net_load = load[i] - pv[i]
        
        # Dispatch Decision using BatteryStateful
        # We need to tell it what power we WANT. 
        # Positive power = Discharge, Negative = Charge
        
        power_needed = net_load 
        
        # Clamp to inverter/battery power limits
        # Using sim_kw (scaled power)
        if power_needed > sim_kw: power_needed = sim_kw
        if power_needed < -sim_kw: power_needed = -sim_kw
        
        # Pass the request to the stateful model
        batt.Controls.input_power = power_needed
        
        # Execute step (time is advanced by dt_hr defined in Controls)
        batt.execute(0)
        
        # Read state
        # StatePack contains SOC, Current, Voltage, Power etc.
        actual_power = batt.StatePack.P # Power actually delivered/absorbed
        current_soc = batt.StatePack.SOC
        
        soc_log.append(current_soc)
        power_log.append(actual_power)
        
    df = pd.DataFrame({
        'load': load,
        'pv': pv,
        'soc': soc_log,
        'battery_power': power_log # +Discharge, -Charge
    })
    
    # Calculate Grid Interaction
    # Net at User = Load - PV - BatteryDischarge
    df['grid_power'] = df['load'] - df['pv'] - df['battery_power']
    
    # Separate Import/Export
    df['grid_import'] = df['grid_power'].apply(lambda x: x if x > 0 else 0)
    df['grid_export'] = df['grid_power'].apply(lambda x: -x if x < 0 else 0)
    
    return df
