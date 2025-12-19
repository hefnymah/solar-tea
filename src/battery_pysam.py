
import pandas as pd
import PySAM.BatteryStateful as BatteryStateful
import PySAM.ResourceTools as tools

def simulate_pysam_battery(
    load_profile_kw: pd.Series, 
    pv_production_kw: pd.Series, 
    battery_kwh: float,
    battery_kw: float = 5.0, # Max charge/discharge
    min_soc: float = 20.0,
    max_soc: float = 95.0
) -> pd.DataFrame:
    """
    Simulates battery using PySAM's BatteryStateful module.
    This module is designed for time-step-by-time-step dispatch controls.
    """
    
    # Initialize the battery model
    batt = BatteryStateful.new()
    
    # Configure Battery Parameters
    # Capacity
    batt.ParamsPack.nominal_energy = battery_kwh
    batt.ParamsPack.nominal_voltage = 500 # Generic 500V system
    
    # Cell properties (Li-ion generic)
    batt.ParamsCell.chem = 1 # Li-ion
    
    # Constraints
    # Control mode: 0=Current, 1=Power
    batt.Controls.control_mode = 1.0 # Power control
    batt.Controls.dt_hr = 1.0 # Hourly time step
    batt.Controls.input_power = 0.0 # Initialize
    
    batt.ParamsCell.minimum_SOC = min_soc
    batt.ParamsCell.maximum_SOC = max_soc
    batt.ParamsCell.life_model = 0 # Calendar/Cycle
    batt.ParamsCell.initial_SOC = max_soc # Start full
    
    # Generic Cell Params (Li-nmc approx)
    batt.ParamsCell.Vnom_default = 3.6
    batt.ParamsCell.Vfull = 4.1
    batt.ParamsCell.Vcut = 3.0
    batt.ParamsCell.Qfull = 3.0
    batt.ParamsCell.resistance = 0.01
    
    # Shepherd Model Params
    batt.ParamsCell.Vexp = 4.05
    batt.ParamsCell.Qexp = 0.05
    batt.ParamsCell.Qnom = 3.0
    batt.ParamsCell.Vnom = 3.6
    batt.ParamsCell.C_rate = 1.0
    
    # Life Model Params (Simple)
    batt.ParamsCell.calendar_choice = 0 # None
    batt.ParamsCell.cycling_matrix = [
        [0, 0, 100],
        [50, 5000, 90],
        [100, 5000, 80] 
    ]

    
    # Thermal/Physical
    batt.ParamsPack.mass = 500
    batt.ParamsPack.surface_area = 2.0
    batt.ParamsPack.Cp = 1000
    batt.ParamsPack.h = 20
    batt.ParamsPack.T_room_init = 20
    
    # Losses
    batt.ParamsPack.loss_choice = 0
    batt.ParamsPack.monthly_charge_loss = [0]*12
    batt.ParamsPack.monthly_discharge_loss = [0]*12
    batt.ParamsPack.monthly_idle_loss = [0]*12
    
    batt.ParamsPack.cap_vs_temp = [
        [-10, 60],
        [0, 80],
        [25, 100],
        [40, 100]
    ]








    
    # Reset state
    batt.setup()
    
    soc_log = []
    power_log = []
    
    # Ensure inputs are lists for iteration
    load = load_profile_kw.fillna(0).tolist()
    pv = pv_production_kw.fillna(0).tolist()
    
    current_soc = max_soc # Start full
    
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
        if power_needed > battery_kw: power_needed = battery_kw
        if power_needed < -battery_kw: power_needed = -battery_kw
        
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
    # If Battery Discharges (+), it reduces Grid Import.
    # If Battery Charges (-), it increases Grid Import (or reduces Export).
    
    df['grid_power'] = df['load'] - df['pv'] - df['battery_power']
    
    # Separate Import/Export
    df['grid_import'] = df['grid_power'].apply(lambda x: x if x > 0 else 0)
    df['grid_export'] = df['grid_power'].apply(lambda x: -x if x < 0 else 0)
    
    return df
