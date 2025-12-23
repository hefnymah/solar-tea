

"""
Simulates PV generation using pvlib.
1. Sizes the system to specific yield (Target: 100% of annual consumption).
2. Constrains by roof area.
3. Simulates generation.
4. Calculates Self-Consumption metrics.
"""
print("\n--- Starting PV Simulation ---")
LATITUDE = 47.38
LONGITUDE = 8.54
ALTITUDE = 400
TIMEZONE = 'Europe/Zurich'

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


#%% extract the usable PV power

ac_power = mc_ref.results.ac  # this is the average power generation during that time (hour) in kW


ac_power_hrly = mc_ref.results.ac
daily = ac_power_hrly.resample('D').sum()  # this is the daily generation in
weekly = daily.resample('W').sum()
monthly = daily.resample('M').sum()
yearly = daily.resample('Y').sum()


# After running mc.run_model(weather)
dc_daily_kwh = mc_ref.results.dc['p_mp'].resample('D').sum()  # DC max power to daily energy
ac_daily_kwh = mc_ref.results.ac.resample('D').sum()          # AC output to daily usable kWh

print("Daily DC (pre-inverter):", dc_daily_kwh.describe())
print("Daily AC (household usable):", ac_daily_kwh.describe())




#%%
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


