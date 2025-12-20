"""
analyze-consumption-3.py

This script processes energy consumption data from a CSV file and generates analysis plots.
It is structured into three main sections:
1. Configuration & Variables
2. Data Loading & Processing
3. Visualization & Plotting
"""

import os
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
import sys
from pathlib import Path
from scipy.interpolate import make_interp_spline
import pvlib
from pvlib.location import Location
from pvlib.pvsystem import PVSystem
from pvlib.modelchain import ModelChain
from pvlib.temperature import TEMPERATURE_MODEL_PARAMETERS

# =============================================================================
# SECTION 1: CONFIGURATION & VARIABLES
# =============================================================================

# --- File Paths ---
# Define the input CSV file path.
# Adjust this path as needed to point to your data file.
INPUT_FILENAME = "20251212_hrly-consumption.csv"
DATA_DIR = os.path.join(os.path.dirname(__file__), "data")
INPUT_FILE_PATH = os.path.join(DATA_DIR, INPUT_FILENAME)

# Define the output directory for saving plots.
OUTPUT_DIR = os.path.join(os.path.dirname(__file__), "output", "analysis_v4")

# --- Data Loading Configuration ---
# Name of the column containing the timestamp.
TIME_COLUMN = 'Zeit'

# Mapping to standardize the consumption column name.
# Input columns matching these keys (case-insensitive) will be renamed to TARGET_CONSUMPTION_COL.
TARGET_CONSUMPTION_COL = 'Consumption_kWh'
COLUMN_MAPPING = {
    'stromverbrauch_kwh': TARGET_CONSUMPTION_COL,
    'verbrauch_kwh': TARGET_CONSUMPTION_COL,
    'stromverbrauch': TARGET_CONSUMPTION_COL,
    'consumption': TARGET_CONSUMPTION_COL,
}

# --- Plotting Configuration ---
PLOT_STYLE = 'ggplot'
FIG_SIZE_WIDE = (12, 6)
FIG_SIZE_Tall = (12, 20)
FIG_SIZE_SQUARE = (10, 10)

# Colors for consistency
COLOR_CONSUMPTION = 'steelblue'
COLOR_TREND = 'navy'
COLOR_SEASONS = {'Winter': 'blue', 'Spring': 'green', 'Summer': 'red', 'Autumn': 'orange'}
COLOR_PV = 'gold'

# --- SEASONAL CONFIGURATION ---
# ... (Existing configs) ...

# --- PV SIMULATION CONFIGURATION ---
# Location: Zurich (Example)
LATITUDE = 47.38
LONGITUDE = 8.54
ALTITUDE = 400
TIMEZONE = 'Europe/Zurich'

# Roof Specs
ROOF_TILT = 30
ROOF_AZIMUTH = 180     # 180 = South
ROOF_AREA_MAX_M2 = 50
MODULE_EFFICIENCY = 0.20 # 20%
PERFORMANCE_RATIO = 0.75 # System losses

# Sizing Limits
MAX_CAPACITY_KWP = ROOF_AREA_MAX_M2 * MODULE_EFFICIENCY

# Sizing Limits
MAX_CAPACITY_KWP = ROOF_AREA_MAX_M2 * MODULE_EFFICIENCY

# --- BATTERY CONFIGURATION ---
BATTERY_CAPACITY_KWH = 10.0
BATTERY_MAX_POWER_KW = 5.0
BATTERY_EFFICIENCY = 0.95 # One-way efficiency

# --- Seasonal Representative Weeks Configuration ---
# Format: 'Season': (Month, Day)
# The script will look for a week starting on this date in the data's predominant year.
SEASONAL_WEEKS_CONFIG = {
    'Winter': (1, 15),  # Jan 15th
    'Spring': (4, 15),  # Apr 15th
    'Summer': (7, 15),  # Jul 15th
    'Autumn': (10, 15)  # Oct 15th
}

# --- Seasonal Representative Days Configuration (Real Data) ---
# Format: 'Season': (Month, Day)
# The script will look for exactly 24 hours of data starting on this date.
SEASONAL_DAYS_CONFIG = {
    'Winter': (1, 21),  # Jan 21st
    'Spring': (4, 21),  # Apr 21st
    'Summer': (7, 21),  # Jul 21st
    'Autumn': (10, 21)  # Oct 21st
}

#%%
# =============================================================================
# SECTION 2: DATA LOADING & PROCESSING
# =============================================================================

def ensure_directories():
    """Ensures that the output directory exists."""
    if not os.path.exists(OUTPUT_DIR):
        try:
            os.makedirs(OUTPUT_DIR)
            print(f"Created output directory: {OUTPUT_DIR}")
        except OSError as e:
            print(f"Error creating directory {OUTPUT_DIR}: {e}")
            sys.exit(1)

def get_season(month):
    """Returns the season for a given month (1-12)."""
    if month in (12, 1, 2):
        return 'Winter'
    elif month in (3, 4, 5):
        return 'Spring'
    elif month in (6, 7, 8):
        return 'Summer'
    else:
        return 'Autumn'

def load_and_process_data(file_path):
    """
    Loads the CSV, cleans it, and enriches it with time-based features.
    Returns a processed DataFrame.
    """
    print(f"Loading data from: {file_path}")
    
    if not os.path.exists(file_path):
        print(f"Error: File not found at {file_path}")
        sys.exit(1)

    try:
        # Load CSV with dayfirst=True for European formats (DD.MM.YYYY)
        df = pd.read_csv(file_path, sep=None, engine='python',
                         parse_dates=[TIME_COLUMN], dayfirst=True, index_col=TIME_COLUMN)
    except Exception as e:
        print(f"Error reading CSV: {e}")
        sys.exit(1)

    # 1. Standardize Column Names
    # Clean whitespace and normalize case for mapping
    df.columns = [c.strip() for c in df.columns]
    
    # Rename columns based on mapping
    rename_map = {}
    for col in df.columns:
        if col.lower() in COLUMN_MAPPING:
            rename_map[col] = COLUMN_MAPPING[col.lower()]
    
    if rename_map:
        df.rename(columns=rename_map, inplace=True)
    else:
        # Fallback: If no known column found, assume first column is consumption
        print("Warning: Could not identify consumption column by name. Using the first column.")
        df.rename(columns={df.columns[0]: TARGET_CONSUMPTION_COL}, inplace=True)

    if TARGET_CONSUMPTION_COL not in df.columns:
        print(f"Error: Could not find or map any column to '{TARGET_CONSUMPTION_COL}'")
        sys.exit(1)

    # 2. Add Derived Time Features
    # Ensure index is datetime
    if not pd.api.types.is_datetime64_any_dtype(df.index):
        df.index = pd.to_datetime(df.index)
        
    # FORCE HOURLY RESOLUTION
    # This solves issues where input might be 15-min data, causing "zigzag" (zeros) 
    # when merged with hourly PV data.
    # Assuming column is Energy (kWh), so 'sum' is correct.
    df = df.resample('h').sum()

    df['Year'] = df.index.year
    df['Month'] = df.index.month
    df['Week'] = df.index.isocalendar().week
    df['Hour'] = df.index.hour
    df['Season'] = df['Month'].apply(get_season)
    
    print(f"Successfully loaded {len(df)} records (Hourly).")
    return df

def aggregate_data(df):
    """Pre-calculates aggregated dataframes for plotting."""
    
    # Daily Sum (Trend)
    df_daily = df[TARGET_CONSUMPTION_COL].resample('D').sum()
    
    # Weekly Sum
    df_weekly = df[TARGET_CONSUMPTION_COL].resample('W').sum()
    
    # Monthly Sum
    df_monthly = df[TARGET_CONSUMPTION_COL].resample('ME').sum() # 'ME' is month end
    
    # Yearly Sum
    df_yearly = df[TARGET_CONSUMPTION_COL].resample('YE').sum() # 'YE' is year end

    # Seasonal Hourly Profile (Average typical day per season)
    # Group by Season and Hour, calculate mean
    df_seasonal_hourly = df.groupby(['Season', 'Hour'])[TARGET_CONSUMPTION_COL].mean().unstack(level=0)
    
    # Ensure all seasons exist in columns even if data is missing
    for season in ['Winter', 'Spring', 'Summer', 'Autumn']:
        if season not in df_seasonal_hourly.columns:
            df_seasonal_hourly[season] = 0.0
            
    # Reorder columns
    df_seasonal_hourly = df_seasonal_hourly[['Winter', 'Spring', 'Summer', 'Autumn']]

    return df_daily, df_weekly, df_monthly, df_yearly, df_seasonal_hourly

def extract_seasonal_weeks(df):
    """
    Extracts a 7-day hourly dataframe for each season based on configuration.
    Returns a dictionary: {'Winter': df_slice, ...}
    """
    
    # Determine the year (use the most common year in the index)
    if df.empty:
        return {}
    
    year = pd.Series(df.index.year).mode()[0]
    
    seasonal_weeks_data = {}
    
    for season, (month, day) in SEASONAL_WEEKS_CONFIG.items():
        try:
            start_date = pd.Timestamp(year=year, month=month, day=day)
            end_date = start_date + pd.Timedelta(days=7)
            
            # Slice [start, end)
            mask = (df.index >= start_date) & (df.index < end_date)
            df_slice = df.loc[mask].copy()
            
            if not df_slice.empty:
                seasonal_weeks_data[season] = df_slice
                print(f"Extracted {season} week: {start_date.date()} to {end_date.date()} ({len(df_slice)} records)")
            else:
                print(f"Warning: No data found for {season} week ({start_date.date()})")
                
        except ValueError as e:
            print(f"Error creating dates for {season}: {e}")
            
            
    return seasonal_weeks_data

def extract_seasonal_days(df):
    """
    Extracts a 24-hour hourly dataframe for each season based on configuration.
    Returns a dictionary: {'Winter': df_slice, ...}
    """
    
    if df.empty:
        return {}
    
    # Use pandas Series mode to avoid AttributeError
    year = pd.Series(df.index.year).mode()[0]
    
    seasonal_days_data = {}
    
    for season, (month, day) in SEASONAL_DAYS_CONFIG.items():
        try:
            start_date = pd.Timestamp(year=year, month=month, day=day)
            end_date = start_date + pd.Timedelta(days=1) # 24 hours
            
            # Slice [start, end)
            mask = (df.index >= start_date) & (df.index < end_date)
            df_slice = df.loc[mask].copy()
            
            if not df_slice.empty:
                seasonal_days_data[season] = df_slice
                print(f"Extracted {season} day: {start_date.date()} ({len(df_slice)} records)")
            else:
                print(f"Warning: No data found for {season} day ({start_date.date()})")
                
        except ValueError as e:
            print(f"Error creating dates for {season} day: {e}")
            
    return seasonal_days_data

def simulate_pv_generation(df_consumption):
    """
    Simulates PV generation using pvlib.
    1. Sizes the system to specific yield (Target: 100% of annual consumption).
    2. Constrains by roof area.
    3. Simulates generation.
    4. Calculates Self-Consumption metrics.
    """
    print("\n--- Starting PV Simulation ---")
    
    # 1. Annual Consumption
    total_consumption_kwh = df_consumption[TARGET_CONSUMPTION_COL].sum()
    print(f"Annual Consumption: {total_consumption_kwh:.0f} kWh")
    
    # 2. Fetch Weather Data (PVGIS)
    print("Fetching weather data from PVGIS...")
    try:
        weather, meta = pvlib.iotools.get_pvgis_tmy(LATITUDE, LONGITUDE, map_variables=True)
        # Standardize weather year to consumption year to allow alignment
        sim_year = pd.Series(df_consumption.index.year).mode()[0]
        weather.index = weather.index.map(lambda t: t.replace(year=sim_year))
        print(f"Weather data loaded for simulation year: {sim_year}")
    except Exception as e:
        print(f"Error fetching PVGIS data: {e}. Aborting PV simulation.")
        return None, None

    # 3. Reference Simulation (1 kWp) to get Specific Yield
    location = Location(LATITUDE, LONGITUDE, TIMEZONE, ALTITUDE)
    temp_params = TEMPERATURE_MODEL_PARAMETERS['sapm']['open_rack_glass_glass']
    
    system_ref = PVSystem(
        surface_tilt=ROOF_TILT,
        surface_azimuth=ROOF_AZIMUTH,
        module_parameters={'pdc0': 1000, 'gamma_pdc': -0.004},
        inverter_parameters={'pdc0': 1000},
        temperature_model_parameters=temp_params
    )
    mc_ref = ModelChain(system_ref, location, aoi_model='physical', spectral_model='no_loss')
    mc_ref.run_model(weather)
    
    # Calculate Specific Yield (kWh per kWp)
    ref_ac_kwh = (mc_ref.results.ac / 1000.0) * PERFORMANCE_RATIO
    specific_yield = ref_ac_kwh.sum()
    print(f"Specific Yield: {specific_yield:.0f} kWh/kWp/year")
    
    # 4. Sizing
    # Target: 100% Offset
    required_kwp = total_consumption_kwh / specific_yield
    print(f"Capacity needed for 100% offset: {required_kwp:.2f} kWp")
    
    if required_kwp > MAX_CAPACITY_KWP:
        installed_capacity = MAX_CAPACITY_KWP
        print(f"Limited by Roof Area! Installing max: {installed_capacity:.2f} kWp")
    else:
        installed_capacity = required_kwp
        print(f"Optimal Sizing (Fits on roof): {installed_capacity:.2f} kWp")
        
    # Scale reference results to installed capacity
    pv_generation_kwh = ref_ac_kwh * installed_capacity
    pv_generation_kwh.name = 'PV_Generation_kWh'
    
    # 5. Metrics & Alignment
    # Create combined DF for calculation
    df_combined = df_consumption.copy()
    
    # Handle Timezones and Alignment
    # PVGIS TMY is usually UTC. Consumption is local (naive or specific).
    # We strip timezone from PV to align with naive consumption timestamps.
    if pv_generation_kwh.index.tz is not None:
        pv_generation_kwh.index = pv_generation_kwh.index.tz_localize(None)
        
    # Reindex PV to match Consumption exactly (Handles missing rows or slight offsets)
    # This fills missing PV hours with 0 (e.g. night)
    pv_aligned = pv_generation_kwh.reindex(df_combined.index, fill_value=0)
    
    df_combined['PV_kWh'] = pv_aligned
    
    # Self-Consumption (SC) logic
    # Energy consumed directly from PV = min(PV, Consumption)
    df_combined['Self_Consumed_kWh'] = np.minimum(df_combined['PV_kWh'], df_combined[TARGET_CONSUMPTION_COL])
    
    # Grid Export = PV - Self_Consumed
    df_combined['Grid_Export_kWh'] = df_combined['PV_kWh'] - df_combined['Self_Consumed_kWh']
    
    # Grid Import = Consumption - Self_Consumed
    df_combined['Grid_Import_kWh'] = df_combined[TARGET_CONSUMPTION_COL] - df_combined['Self_Consumed_kWh']
    
    # Aggregates
    total_pv = df_combined['PV_kWh'].sum()
    total_sc = df_combined['Self_Consumed_kWh'].sum()
    total_cons = df_combined[TARGET_CONSUMPTION_COL].sum()
    
    metrics = {
        'Capacity_kWp': installed_capacity,
        'Specific_Yield': specific_yield,
        'Total_PV_Gen_kWh': total_pv,
        'Total_Consumption_kWh': total_cons,
        'Self_Consumption_kWh': total_sc,
        'Self_Consumption_Ratio': (total_sc / total_pv * 100) if total_pv > 0 else 0, # % of PV used
        'Self_Sufficiency_Ratio': (total_sc / total_cons * 100) if total_cons > 0 else 0 # % of Load covered
    }
    
    print("\n--- Sizing Results ---")
    print(f"Installed Capacity: {metrics['Capacity_kWp']:.2f} kWp")
    print(f"Total PV Generation: {metrics['Total_PV_Gen_kWh']:.0f} kWh")
    print(f"Self-Consumption: {metrics['Self_Consumption_Ratio']:.1f}% (of PV energy used)")
    print(f"Self-Consumption: {metrics['Self_Consumption_Ratio']:.1f}% (of PV energy used)")
    print(f"Autarchy (Sufficiency): {metrics['Self_Sufficiency_Ratio']:.1f}% (of Home energy covered)")
    
    return df_combined, metrics

def simulate_battery_storage(df_combined):
    """
    Simulates a battery storage system sequentially over the dataframe.
    """
    print("\n--- Starting Battery Simulation ---")
    
    # Prepare list for results
    battery_soc_kwh = []
    battery_power_kw = [] # + Discharging, - Charging
    current_soc = 0.0 # Start empty
    
    # Constants
    cap = BATTERY_CAPACITY_KWH
    max_p = BATTERY_MAX_POWER_KW
    eff = BATTERY_EFFICIENCY
    
    # Arrays for speed
    pv_vals = df_combined['PV_kWh'].values
    load_vals = df_combined[TARGET_CONSUMPTION_COL].values
    
    for i in range(len(df_combined)):
        pv = pv_vals[i]
        load = load_vals[i]
        
        # Net Load: Positive = Deficit (Need power), Negative = Surplus (Excess power)
        # Note: We use original load/pv, NOT the post-self-consumption values from previous step,
        # because battery can capture surplus that would have been exported.
        # Actually, let's think: 
        # Immediate Self-Consumption happens first.
        # Surplus = PV - Load (if PV > Load) -> Goes to Battery
        # Deficit = Load - PV (if Load > PV) -> Comes from Battery
        
        net_load = load - pv 
        flow = 0.0
        
        if net_load < 0: # Surplus -> Charge
            potential_charge = abs(net_load)
            # Constraints: Max Power, Max Capacity
            max_charge_by_cap = (cap - current_soc) / eff
            actual_charge = min(potential_charge, max_p, max_charge_by_cap)
            
            flow = -actual_charge
            current_soc += actual_charge * eff
            
        elif net_load > 0: # Deficit -> Discharge
            potential_discharge = net_load
            # Constraints: Max Power, Max Energy
            max_discharge_by_energy = current_soc * eff
            actual_discharge = min(potential_discharge, max_p, max_discharge_by_energy)
            
            flow = actual_discharge
            current_soc -= actual_discharge / eff
            
        # Float guard
        current_soc = max(0.0, min(cap, current_soc))
        
        battery_soc_kwh.append(current_soc)
        battery_power_kw.append(flow)
        
    # Add to DataFrame
    df_combined['Battery_SoC_kWh'] = battery_soc_kwh
    df_combined['Battery_Power_kW'] = battery_power_kw
    df_combined['Battery_SoC_Pct'] = (df_combined['Battery_SoC_kWh'] / cap) * 100
    
    # Calculate New Grid Interaction
    # Grid Import = Deficit - Battery Discharge (flow > 0)
    # Grid Export = Surplus - Battery Charge (flow < 0)
    # Note: flow is positive for discharge, negative for charge.
    
    # Re-calculate net load
    net_load_series = df_combined[TARGET_CONSUMPTION_COL] - df_combined['PV_kWh']
    
    # Adjusted Net Load = Net Load - Battery Flow (Discharge reduces load, Charge absorbs surplus)
    # If Net Load was 5 (Deficit), and Batt Discharged 3 (Flow=3), Adjusted is 2 (Import).
    # If Net Load was -5 (Surplus), and Batt Charged 3 (Flow=-3), Adjusted is -2 (Export).
    
    df_combined['Net_Load_After_Batt'] = net_load_series - df_combined['Battery_Power_kW']
    
    # Extract final import/export
    df_combined['Grid_Import_w_Batt'] = df_combined['Net_Load_After_Batt'].clip(lower=0)
    df_combined['Grid_Export_w_Batt'] = (-df_combined['Net_Load_After_Batt']).clip(lower=0)
    
    # Metrics
    original_import = df_combined['Grid_Import_kWh'].sum() # From PV only step
    new_import = df_combined['Grid_Import_w_Batt'].sum()
    
    original_export = df_combined['Grid_Export_kWh'].sum()
    new_export = df_combined['Grid_Export_w_Batt'].sum()
    
    total_cons = df_combined[TARGET_CONSUMPTION_COL].sum()
    new_autarchy = (1 - (new_import / total_cons)) * 100
    
    print(f"Battery Impact:")
    print(f"  Grid Import: {original_import:.0f} -> {new_import:.0f} kWh")
    print(f"  Grid Export: {original_export:.0f} -> {new_export:.0f} kWh")
    print(f"  Autarchy improved to: {new_autarchy:.1f}%")
    
    return df_combined


# =============================================================================
# SECTION 3: VISUALIZATION & PLOTTING
# =============================================================================

def plot_monthly(df_monthly):
    """Plots Monthly Consumption."""
    plt.style.use(PLOT_STYLE)
    fig, ax = plt.subplots(figsize=FIG_SIZE_WIDE)
    
    monthly_labels = df_monthly.index.strftime('%Y-%m')
    df_monthly.plot(kind='bar', ax=ax, color='salmon', edgecolor='black')
    ax.set_title('Monthly Consumption')
    ax.set_ylabel('kWh')
    ax.set_xticklabels(monthly_labels, rotation=45, ha='right')
    
    plt.tight_layout()
    save_path = os.path.join(OUTPUT_DIR, "monthly_consumption.png")
    plt.savefig(save_path)
    print(f"Saved monthly plot to: {save_path}")
    plt.close(fig)

def plot_weekly(df_weekly):
    """Plots Weekly Consumption."""
    plt.style.use(PLOT_STYLE)
    fig, ax = plt.subplots(figsize=FIG_SIZE_WIDE)
    
    df_weekly.plot(kind='bar', ax=ax, color='lightgreen', edgecolor='black')
    ax.set_title('Weekly Consumption')
    ax.set_ylabel('kWh')
    # Improve x-axis for weekly if needed, but default is often okay for simple views
    
    plt.tight_layout()
    save_path = os.path.join(OUTPUT_DIR, "weekly_consumption.png")
    plt.savefig(save_path)
    print(f"Saved weekly plot to: {save_path}")
    plt.close(fig)

def plot_daily(df_daily):
    """Plots Daily Consumption Trend."""
    plt.style.use(PLOT_STYLE)
    fig, ax = plt.subplots(figsize=FIG_SIZE_WIDE)
    
    df_daily.plot(kind='line', ax=ax, color=COLOR_TREND, linewidth=1)
    ax.set_title('Daily Consumption (Trend)')
    ax.set_ylabel('kWh')
    
    plt.tight_layout()
    save_path = os.path.join(OUTPUT_DIR, "daily_consumption.png")
    plt.savefig(save_path)
    print(f"Saved daily plot to: {save_path}")
    plt.close(fig)

def plot_seasonal_profile(df_seasonal_hourly):
    """Plots the typical daily profile for each season."""
    
    fig, ax = plt.subplots(figsize=FIG_SIZE_WIDE)
    
    x = df_seasonal_hourly.index.values # 0..23
    x_smooth = np.linspace(x.min(), x.max(), 300)

    for season in df_seasonal_hourly.columns:
        y = df_seasonal_hourly[season].values
        color = COLOR_SEASONS.get(season, 'black')
        
        # Smooth curve
        try:
            spl = make_interp_spline(x, y, k=3)
            y_smooth = spl(x_smooth)
            # Clip negative values from spline overshoot
            y_smooth = np.maximum(y_smooth, 0)
        except Exception:
            y_smooth = y
            x_plot = x
        else:
            x_plot = x_smooth

        ax.plot(x_plot, y_smooth, label=season, color=color, linewidth=2)

    ax.set_title('Seasonal Hourly Load Profile (Typical Day)')
    ax.set_xlabel('Hour of Day')
    ax.set_ylabel('Avg Consumption (kWh)')
    ax.set_xticks(range(0, 24))
    ax.grid(True, linestyle='--', alpha=0.5)
    ax.legend()

    save_path = os.path.join(OUTPUT_DIR, "seasonal_hourly_profile.png")
    plt.savefig(save_path)
    print(f"Saved seasonal profile to: {save_path}")
    plt.close(fig)

    save_path = os.path.join(OUTPUT_DIR, "seasonal_hourly_profile.png")
    plt.savefig(save_path)
    print(f"Saved seasonal profile to: {save_path}")
    plt.close(fig)

def plot_seasonal_weeks(seasonal_weeks_data, value_col=TARGET_CONSUMPTION_COL, color_map=None, title_suffix=""):
    """
    Plots the representative week for each season.
    Generic function: can plot Consumption or PV.
    """
    if not seasonal_weeks_data:
        print("No seasonal weekly data to plot.")
        return

    plt.style.use(PLOT_STYLE)
    
    # Use default season colors if none provided
    if color_map is None:
        color_map = COLOR_SEASONS
        
    # Determine global Y-limit
    y_max = 0
    for df_slice in seasonal_weeks_data.values():
        if not df_slice.empty and value_col in df_slice.columns:
             val = df_slice[value_col].max()
             if val > y_max: y_max = val
    y_max = y_max * 1.1

    fig, axes = plt.subplots(4, 1, figsize=(12, 16))
    if not isinstance(axes, (list, np.ndarray)):
        axes = [axes]

    season_order = ['Winter', 'Spring', 'Summer', 'Autumn']
    
    for i, season in enumerate(season_order):
        if i >= len(axes): break
        ax = axes[i]
        
        if season in seasonal_weeks_data:
            df_slice = seasonal_weeks_data[season]
            
            if value_col in df_slice.columns:
                y_vals = df_slice[value_col]
                
                # Determine color: check if color_map is a dict (by season) or a single string
                if isinstance(color_map, dict):
                    color = color_map.get(season, 'black')
                else:
                    color = color_map
                
                # Plot
                ax.plot(df_slice.index, y_vals, color=color, linewidth=1.5)
                ax.fill_between(df_slice.index, 0, y_vals, color=color, alpha=0.2)
                
                # Title & Labels
                start_str = df_slice.index.min().strftime('%Y-%m-%d')
                ax.set_title(f'{season} Week - {title_suffix} - Starting {start_str}')
                ax.set_ylabel('kWh')
                ax.set_ylim(0, y_max)
                
                # Format X-axis
                import matplotlib.dates as mdates
                ax.xaxis.set_major_locator(mdates.DayLocator())
                ax.xaxis.set_major_formatter(mdates.DateFormatter('%a\n%d.%m'))
                ax.xaxis.set_minor_locator(mdates.HourLocator(interval=6))
                ax.grid(True, which='major', linestyle='-', alpha=0.5)
                ax.grid(True, which='minor', linestyle=':', alpha=0.3)
            else:
                 ax.text(0.5, 0.5, f'Column {value_col} not found', ha='center', va='center')
            
        else:
            ax.text(0.5, 0.5, f'No Data for {season}', ha='center', va='center')
            ax.set_title(f'{season} Week - N/A')

    plt.tight_layout()
    # Unique filename based on column
    filename = f"seasonal_weeks_{value_col.replace('_', '').lower()}.png"
    save_path = os.path.join(OUTPUT_DIR, filename)
    plt.savefig(save_path)
    print(f"Saved seasonal weeks plot ({value_col}) to: {save_path}")
    plt.close(fig)

def plot_seasonal_days(seasonal_days_data):
    """Plots the representative day (real data) for each season in a 4x1 subplot."""
    if not seasonal_days_data:
        print("No seasonal daily data to plot.")
        return

    plt.style.use(PLOT_STYLE)
    
    # Determine global Y-limit
    y_max = 0
    for df_slice in seasonal_days_data.values():
        if not df_slice.empty:
             val = df_slice[TARGET_CONSUMPTION_COL].max()
             if val > y_max: y_max = val
    y_max = y_max * 1.1

    fig, axes = plt.subplots(4, 1, figsize=(12, 16))
    if not isinstance(axes, (list, np.ndarray)):
        axes = [axes]

    season_order = ['Winter', 'Spring', 'Summer', 'Autumn']
    
    for i, season in enumerate(season_order):
        if i >= len(axes): break
        ax = axes[i]
        
        if season in seasonal_days_data:
            df_slice = seasonal_days_data[season]
            y_vals = df_slice[TARGET_CONSUMPTION_COL]
            
            # Plot
            ax.plot(df_slice.index, y_vals, color=COLOR_SEASONS.get(season, 'black'), linewidth=2, marker='o', markersize=4)
            ax.fill_between(df_slice.index, 0, y_vals, color=COLOR_SEASONS.get(season, 'black'), alpha=0.2)
            
            # Title & Labels
            date_str = df_slice.index.min().strftime('%d %B %Y')
            ax.set_title(f'{season} Real Day - {date_str}')
            ax.set_ylabel('kWh')
            ax.set_ylim(0, y_max)
            
            # Format X-axis (Hours)
            import matplotlib.dates as mdates
            ax.xaxis.set_major_locator(mdates.HourLocator(interval=2))
            ax.xaxis.set_major_formatter(mdates.DateFormatter('%H:00'))
            ax.grid(True, linestyle='--', alpha=0.5)
            
        else:
            ax.text(0.5, 0.5, f'No Data for {season}', ha='center', va='center')
            ax.set_title(f'{season} Day - N/A')

    plt.tight_layout()
    save_path = os.path.join(OUTPUT_DIR, "seasonal_daily_profile_real.png")
    plt.savefig(save_path)
    print(f"Saved seasonal daily plot to: {save_path}")
    plt.close(fig)

def plot_pv_analysis(df_combined, metrics):
    """Plots PV sizing analysis: Monthly Comparison and Self-Consumption overlap."""
    if df_combined is None or metrics is None:
        return

    # 1. Monthly Comparison Stacked
    monthly_data = df_combined.resample('ME').sum()
    
    plt.style.use(PLOT_STYLE)
    fig, ax = plt.subplots(figsize=FIG_SIZE_WIDE)
    
    idx = range(len(monthly_data))
    labels = monthly_data.index.strftime('%b')
    width = 0.4
    
    # Plot Consumption (Grid Import + Self Consumed)
    # Actually standard is: Cons vs Gen
    ax.bar(idx, monthly_data[TARGET_CONSUMPTION_COL], width=width, label='Consumption', color='steelblue', align='center', alpha=0.6)
    
    # Plot PV (Generation)
    ax.bar(idx, monthly_data['PV_kWh'], width=width, label='PV Generation', color='gold', align='edge', alpha=0.6)
    
    ax.set_title(f"Monthly Consumption vs PV Generation ({metrics['Capacity_kWp']:.2f} kWp)")
    ax.set_ylabel('kWh')
    ax.set_xticks(idx)
    ax.set_xticklabels(labels)
    ax.legend()
    
    # Add metrics text box
    textstr = '\n'.join((
        f"System Size: {metrics['Capacity_kWp']:.2f} kWp",
        f"Generation: {metrics['Total_PV_Gen_kWh']:.0f} kWh/yr",
        f"Self-Cons: {metrics['Self_Consumption_Ratio']:.1f}%",
        f"Autarchy: {metrics['Self_Sufficiency_Ratio']:.1f}%"
    ))
    props = dict(boxstyle='round', facecolor='wheat', alpha=0.5)
    ax.text(0.02, 0.95, textstr, transform=ax.transAxes, fontsize=10, verticalalignment='top', bbox=props)
    
    plt.tight_layout()
    save_path = os.path.join(OUTPUT_DIR, "pv_monthly_analysis.png")
    plt.savefig(save_path)
    print(f"Saved PV monthly analysis to: {save_path}")
    plt.close(fig)
    
    # 2. Daily Profile (Summer vs Winter Sample)
    # Simple check of a good summer day vs winter day
    fig2, axes = plt.subplots(2, 1, figsize=(12, 10))
    
    # Find max PV day (Summer)
    day_max_pv = df_combined['PV_kWh'].resample('D').sum().idxmax()
    start = day_max_pv
    end = start + pd.Timedelta(hours=23)
    
    summer_day = df_combined.loc[start:end]
    ax = axes[0]
    ax.plot(summer_day.index.hour, summer_day[TARGET_CONSUMPTION_COL], label='Load', color='steelblue', linewidth=2)
    ax.plot(summer_day.index.hour, summer_day['PV_kWh'], label='PV', color='gold', linewidth=2)
    ax.fill_between(summer_day.index.hour, 0, summer_day['PV_kWh'], color='gold', alpha=0.3)
    ax.set_title(f"Best PV Day (Summer): {start.date()}")
    ax.set_xlabel("Hour")
    ax.set_ylabel("kWh")
    ax.legend()
    ax.grid(True)
    
    # Find min PV day (Winter - simple pick Jan 15)
    try:
        winter_date = pd.Timestamp(year=day_max_pv.year, month=1, day=15)
        start_w = winter_date
        end_w = winter_date + pd.Timedelta(hours=23)
        winter_day = df_combined.loc[start_w:end_w]
        
        ax = axes[1]
        ax.plot(winter_day.index.hour, winter_day[TARGET_CONSUMPTION_COL], label='Load', color='steelblue', linewidth=2)
        ax.plot(winter_day.index.hour, winter_day['PV_kWh'], label='PV', color='gold', linewidth=2)
        ax.fill_between(winter_day.index.hour, 0, winter_day['PV_kWh'], color='gold', alpha=0.3)
        ax.set_title(f"Example Winter Day: {start_w.date()}")
        ax.set_xlabel("Hour")
        ax.set_ylabel("kWh")
        ax.legend()
        ax.grid(True)
    except:
        pass

    plt.tight_layout()
    save_path2 = os.path.join(OUTPUT_DIR, "pv_daily_samples.png")
    plt.savefig(save_path2)
    print(f"Saved PV daily samples to: {save_path2}")
    plt.close(fig2)

def plot_battery_weeks(df_combined):
    """Plots battery operation for seasonal representative weeks."""
    if df_combined is None or 'Battery_SoC_Pct' not in df_combined.columns:
        return

    plt.style.use(PLOT_STYLE)
    
    # Extract seasonal weeks
    seasonal_weeks = extract_seasonal_weeks(df_combined)
    
    if not seasonal_weeks:
        return

    fig, axes = plt.subplots(2, 2, figsize=(15, 12))
    axes = axes.flatten()
    
    season_order = ['Winter', 'Spring', 'Summer', 'Autumn']
    
    for idx, season in enumerate(season_order):
        if idx >= len(axes): break
        ax1 = axes[idx]
        
        if season in seasonal_weeks:
            df_slice = seasonal_weeks[season]
            
            # Primary Axis: Power
            # Hybrid area plot
            
            # PV (Orange Area)
            ax1.fill_between(df_slice.index, 0, df_slice['PV_kWh'], color='gold', alpha=0.3, label='PV Gen')
            # Load (Black Line)
            ax1.plot(df_slice.index, df_slice[TARGET_CONSUMPTION_COL], color='black', alpha=0.7, linewidth=1.5, linestyle='--', label='Load')
            
            # Battery Power
            batt_pos = df_slice['Battery_Power_kW'].clip(lower=0)
            batt_neg = df_slice['Battery_Power_kW'].clip(upper=0)
            
            ax1.fill_between(df_slice.index, 0, batt_pos, color='green', alpha=0.6, label='Discharging')
            ax1.fill_between(df_slice.index, 0, batt_neg, color='red', alpha=0.6, label='Charging')
            
            ax1.set_ylabel('Power (kW)')
            title_soc_start = df_slice['Battery_SoC_Pct'].iloc[0]
            title_soc_end = df_slice['Battery_SoC_Pct'].iloc[-1]
            ax1.set_title(f"{season} Battery Ops\nStart SoC: {title_soc_start:.0f}% -> End: {title_soc_end:.0f}%")
            
            # Secondary Axis: SoC
            ax2 = ax1.twinx()
            ax2.plot(df_slice.index, df_slice['Battery_SoC_Pct'], color='blue', linewidth=2, label='SoC %')
            ax2.set_ylabel('SoC (%)', color='blue')
            ax2.set_ylim(0, 105)
            ax2.tick_params(axis='y', labelcolor='blue')
            ax2.grid(False) # Turn off grid for second axis to avoid clutter
            
            # Format X-axis
            import matplotlib.dates as mdates
            ax1.xaxis.set_major_formatter(mdates.DateFormatter('%a'))
            
            if idx == 0:
                # Legend handling
                lines1, labels1 = ax1.get_legend_handles_labels()
                lines2, labels2 = ax2.get_legend_handles_labels()
                ax1.legend(lines1 + lines2, labels1 + labels2, loc='upper left', fontsize='small', framealpha=0.8)
                
    plt.suptitle(f"Battery Analysis: {BATTERY_CAPACITY_KWH} kWh | {BATTERY_MAX_POWER_KW} kW", fontsize=16)
    plt.tight_layout()
    save_path = os.path.join(OUTPUT_DIR, "seasonal_weeks_battery.png")
    plt.savefig(save_path)
    print(f"Saved seasonal battery weeks to: {save_path}")
    plt.close(fig)


# =============================================================================
# MAIN EXECUTION
# =============================================================================

def main():
    print("--- Starting Consumption Analysis v3 ---")
    
    # 1. Prepare
    ensure_directories()
    
    # 2. Load & Process
    df = load_and_process_data(INPUT_FILE_PATH)
    
    # 3. Aggregate
    df_daily, df_weekly, df_monthly, df_yearly, df_seasonal_hourly = aggregate_data(df)
    
    # 4. Plot
    print("Generating plots...")
    # plot_overview(df_daily, df_weekly, df_monthly, df_yearly) # Removed as requested
    plot_monthly(df_monthly)
    plot_weekly(df_weekly)
    plot_daily(df_daily)
    
    plot_seasonal_profile(df_seasonal_hourly)
    
    # 5. Seasonal Weeks (Consumption)
    seasonal_weeks_data = extract_seasonal_weeks(df)
    plot_seasonal_weeks(seasonal_weeks_data, value_col=TARGET_CONSUMPTION_COL, color_map=COLOR_SEASONS, title_suffix="Consumption")
    
    # 6. Seasonal Days (Real)
    seasonal_days_data = extract_seasonal_days(df)
    plot_seasonal_days(seasonal_days_data)

    # 7. PV Sizing & Generation
    # Passing the full dataframe for simulation
    df_pv_combined, pv_metrics = simulate_pv_generation(df)
    plot_pv_analysis(df_pv_combined, pv_metrics)
    
    # 8. PV Seasonal Weeks (New Request)
    if df_pv_combined is not None:
         pv_weeks_data = extract_seasonal_weeks(df_pv_combined)
         plot_seasonal_weeks(pv_weeks_data, value_col='PV_kWh', color_map=COLOR_PV, title_suffix="PV Generation")

    # 9. Battery Analysis
    if df_pv_combined is not None:
        df_batt = simulate_battery_storage(df_pv_combined)
        plot_battery_weeks(df_batt)
    
    print("\nAnalysis complete.")
    print(f"Results saved in: {OUTPUT_DIR}")

if __name__ == "__main__":
    main()
